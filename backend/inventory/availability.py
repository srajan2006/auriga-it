from datetime import date

from django.core.exceptions import ValidationError

from bookings.models import Booking

from .models import EquipmentModel, EquipmentUnit


BLOCKING_BOOKING_STATUSES = {
    Booking.Status.PENDING,
    Booking.Status.APPROVED,
}


def validate_date_range(start_date: date, end_date: date):
    if end_date <= start_date:
        raise ValidationError("End date must be after start date.")


def get_available_units(
    equipment_model: EquipmentModel,
    start_date: date,
    end_date: date,
    exclude_booking_id: int | None = None,
):
    validate_date_range(start_date, end_date)
    units = equipment_model.units.filter(status=EquipmentUnit.Status.AVAILABLE)
    overlapping_bookings = Booking.objects.filter(
        status__in=BLOCKING_BOOKING_STATUSES,
        start_date__lt=end_date,
        end_date__gt=start_date,
        items__equipment_model=equipment_model,
    ).prefetch_related("items", "booking_units")
    if exclude_booking_id:
        overlapping_bookings = overlapping_bookings.exclude(id=exclude_booking_id)

    blocked_unit_ids = set(
        overlapping_bookings.values_list("booking_units__equipment_unit_id", flat=True)
    )
    pending_quantity = sum(
        max(
            item.quantity
            - sum(
                1
                for booking_unit in booking.booking_units.all()
                if booking_unit.equipment_unit.equipment_model_id == equipment_model.id
            ),
            0,
        )
        for booking in overlapping_bookings
        if booking.status == Booking.Status.PENDING
        for item in booking.items.all()
        if item.equipment_model_id == equipment_model.id
    )
    available_units = list(units.exclude(pk__in=blocked_unit_ids).order_by("asset_code"))
    if pending_quantity:
        available_units = available_units[pending_quantity:]
    return EquipmentUnit.objects.filter(id__in=[unit.id for unit in available_units]).order_by("asset_code")


def calculate_availability(
    equipment_model: EquipmentModel,
    start_date: date,
    end_date: date,
    exclude_booking_id: int | None = None,
):
    available_units = get_available_units(equipment_model, start_date, end_date, exclude_booking_id)
    available_asset_codes = list(available_units.values_list("asset_code", flat=True))
    total_units = equipment_model.units.count()
    return {
        "equipment_model": equipment_model.id,
        "name": equipment_model.name,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_quantity": total_units,
        "available_quantity": len(available_asset_codes),
        "requested_quantity": None,
        "available": bool(available_asset_codes),
        "available_asset_codes": available_asset_codes,
    }
