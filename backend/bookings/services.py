from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from inventory.availability import get_available_units
from inventory.models import EquipmentUnit

from .models import Booking, BookingItem, BookingUnit


def make_booking_code():
    prefix = timezone.now().strftime("BK%Y%m%d%H%M%S")
    sequence = Booking.objects.filter(booking_code__startswith=prefix).count() + 1
    return f"{prefix}{sequence:02d}"


def validate_booking_availability(items, start_date, end_date, exclude_booking=None):
    for item in items:
        available_units = get_available_units(
            item["equipment_model"],
            start_date,
            end_date,
            exclude_booking_id=exclude_booking.id if exclude_booking else None,
        )
        if available_units.count() < item["quantity"]:
            raise ValidationError(
                f"Only {available_units.count()} units of {item['equipment_model'].name} are available for these dates."
            )


@transaction.atomic
def create_booking(*, borrower, validated_data):
    items = validated_data.pop("items")
    validate_booking_availability(items, validated_data["start_date"], validated_data["end_date"])
    booking = Booking.objects.create(
        borrower=borrower,
        booking_code=make_booking_code(),
        **validated_data,
    )
    BookingItem.objects.bulk_create(
        [BookingItem(booking=booking, equipment_model=item["equipment_model"], quantity=item["quantity"]) for item in items]
    )
    return booking


@transaction.atomic
def approve_booking(*, booking_id, approved_by, unit_ids):
    booking = Booking.objects.select_for_update().prefetch_related("items").get(pk=booking_id)
    if booking.status != Booking.Status.PENDING:
        raise ValidationError("Only pending bookings can be approved.")

    requested_count = sum(item.quantity for item in booking.items.all())
    if len(unit_ids) != requested_count:
        raise ValidationError(f"Select exactly {requested_count} physical units.")
    if len(set(unit_ids)) != len(unit_ids):
        raise ValidationError("A physical unit cannot be assigned twice.")

    units = list(
        EquipmentUnit.objects.select_for_update().filter(
            id__in=unit_ids,
            status=EquipmentUnit.Status.AVAILABLE,
        )
    )
    if len(units) != len(unit_ids):
        raise ValidationError("Every selected unit must be available.")
    required_by_model = {item.equipment_model_id: item.quantity for item in booking.items.all()}
    actual_by_model = {}
    for unit in units:
        actual_by_model[unit.equipment_model_id] = actual_by_model.get(unit.equipment_model_id, 0) + 1
    if actual_by_model != required_by_model:
        raise ValidationError("Assigned units must match the requested equipment quantities.")

    validate_booking_availability(
        [{"equipment_model": item.equipment_model, "quantity": item.quantity} for item in booking.items.all()],
        booking.start_date,
        booking.end_date,
        exclude_booking=booking,
    )
    BookingUnit.objects.bulk_create([BookingUnit(booking=booking, equipment_unit=unit) for unit in units])
    EquipmentUnit.objects.filter(id__in=unit_ids).update(status=EquipmentUnit.Status.RESERVED)
    booking.status = Booking.Status.APPROVED
    booking.approved_by = approved_by
    booking.approved_at = timezone.now()
    booking.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    return booking
