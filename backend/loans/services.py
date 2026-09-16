from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal

from django.utils import timezone

from bookings.models import Booking
from common.models import SystemSettings
from inventory.models import EquipmentUnit

from .models import LateFee, Loan, LoanItem, LoanTransfer


@transaction.atomic
def issue_booking(*, booking_id, issued_by, due_at, notes="", conditions=None):
    booking = Booking.objects.select_for_update().prefetch_related("booking_units__equipment_unit").get(pk=booking_id)
    if booking.status != Booking.Status.APPROVED:
        raise ValidationError("Only approved bookings can be issued.")
    if hasattr(booking, "loan"):
        raise ValidationError("This booking has already been issued.")

    issued_at = timezone.now()
    if due_at <= issued_at:
        raise ValidationError("Due date must be later than the issue time.")

    booking_units = list(booking.booking_units.all())
    if not booking_units:
        raise ValidationError("Approved booking has no assigned equipment units.")
    unit_ids = [booking_unit.equipment_unit_id for booking_unit in booking_units]
    units = list(
        EquipmentUnit.objects.select_for_update().filter(
            id__in=unit_ids,
            status=EquipmentUnit.Status.RESERVED,
        )
    )
    if len(units) != len(unit_ids):
        raise ValidationError("Every assigned unit must still be reserved.")

    condition_map = conditions or {}
    loan = Loan.objects.create(
        booking=booking,
        borrower=booking.borrower,
        issued_by=issued_by,
        issued_at=issued_at,
        due_at=due_at,
        notes=notes,
        status=Loan.Status.ACTIVE,
    )
    LoanItem.objects.bulk_create(
        [
            LoanItem(
                loan=loan,
                equipment_unit=unit,
                condition_at_issue=condition_map.get(str(unit.id), unit.condition),
            )
            for unit in units
        ]
    )
    EquipmentUnit.objects.filter(id__in=unit_ids).update(status=EquipmentUnit.Status.ISSUED)
    return loan


def refresh_overdue_status(loan):
    if loan.status == Loan.Status.ACTIVE and loan.returned_at is None and timezone.now() > loan.due_at:
        Loan.objects.filter(pk=loan.pk, status=Loan.Status.ACTIVE).update(status=Loan.Status.OVERDUE)
        loan.status = Loan.Status.OVERDUE
    return loan


@transaction.atomic
def return_loan(*, loan_id, returned_by, items, notes=""):
    loan = Loan.objects.select_for_update().get(pk=loan_id)
    if loan.status not in {Loan.Status.ACTIVE, Loan.Status.OVERDUE} or loan.returned_at is not None:
        raise ValidationError("This loan has already been returned or cannot be returned.")

    loan_items = {item.id: item for item in loan.items.select_related("equipment_unit").select_for_update()}
    if {item["loan_item_id"] for item in items} != set(loan_items):
        raise ValidationError("Return details must include every loan item exactly once.")

    returned_at = timezone.now()
    for item_data in items:
        loan_item = loan_items[item_data["loan_item_id"]]
        loan_item.condition_at_return = item_data["condition"]
        loan_item.notes = item_data.get("notes", "")
        loan_item.save(update_fields=["condition_at_return", "notes"])
        EquipmentUnit.objects.filter(pk=loan_item.equipment_unit_id).update(status=item_data["status"])

    late_days = max(0, (returned_at.date() - loan.due_at.date()).days)
    fee_rate = sum(
        (item.equipment_unit.equipment_model.late_fee_per_day or SystemSettings.get_solo().default_late_fee_per_day for item in loan_items.values()),
        Decimal("0"),
    )
    LateFee.objects.update_or_create(
        loan=loan,
        defaults={
            "amount": fee_rate * late_days,
            "days_late": late_days,
            "status": LateFee.Status.PENDING if late_days else LateFee.Status.WAIVED,
            "calculated_at": returned_at,
        },
    )
    loan.returned_at = returned_at
    loan.status = Loan.Status.RETURNED
    if notes:
        loan.notes = notes
    loan.save(update_fields=["returned_at", "status", "notes", "updated_at"])
    return loan


@transaction.atomic
def transfer_loan(*, loan_id, new_borrower_id, transferred_by, reason):
    loan = Loan.objects.select_for_update().select_related("borrower").get(pk=loan_id)
    if loan.status not in {Loan.Status.ACTIVE, Loan.Status.OVERDUE} or loan.returned_at is not None:
        raise ValidationError("Only active or overdue loans can be transferred.")
    if loan.borrower_id == new_borrower_id:
        raise ValidationError("The new borrower must be different from the current borrower.")
    if not reason.strip():
        raise ValidationError("A transfer reason is required.")

    user_model = loan.borrower.__class__
    new_borrower = user_model.objects.select_for_update().filter(pk=new_borrower_id).first()
    if new_borrower is None:
        raise user_model.DoesNotExist
    if not new_borrower.is_active:
        raise ValidationError("The destination borrower is inactive.")
    if new_borrower.role != user_model.Role.STUDENT:
        raise ValidationError("Loans can only be transferred to students.")

    active_statuses = {Loan.Status.ACTIVE, Loan.Status.OVERDUE}
    active_count = Loan.objects.filter(
        borrower=new_borrower,
        status__in=active_statuses,
        returned_at__isnull=True,
    ).count()
    if active_count >= SystemSettings.get_solo().max_active_loans_per_user:
        raise ValidationError("The destination borrower has reached the active-loan limit.")

    transfer = LoanTransfer.objects.create(
        loan=loan,
        previous_borrower=loan.borrower,
        new_borrower=new_borrower,
        transferred_by=transferred_by,
        reason=reason.strip(),
    )
    loan.borrower = new_borrower
    loan.save(update_fields=["borrower", "updated_at"])
    return loan, transfer
