from django.conf import settings
from django.db import models

from bookings.models import Booking
from inventory.models import EquipmentUnit


class Loan(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        OVERDUE = "OVERDUE", "Overdue"
        RETURNED = "RETURNED", "Returned"
        LOST = "LOST", "Lost"

    booking = models.OneToOneField(Booking, on_delete=models.PROTECT, related_name="loan")
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="loans")
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="issued_loans")
    issued_at = models.DateTimeField()
    due_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Loan {self.pk} for {self.borrower.email}"


class LoanItem(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="items")
    equipment_unit = models.ForeignKey(EquipmentUnit, on_delete=models.PROTECT, related_name="loan_items")
    condition_at_issue = models.CharField(max_length=20, choices=EquipmentUnit.Condition.choices)
    condition_at_return = models.CharField(max_length=20, choices=EquipmentUnit.Condition.choices, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["loan", "equipment_unit"], name="unique_loan_unit"),
        ]

    def __str__(self):
        return f"{self.loan_id}: {self.equipment_unit.asset_code}"


class LateFee(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        WAIVED = "WAIVED", "Waived"

    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name="late_fee")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    days_late = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    calculated_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Late fee for loan {self.loan_id}: {self.amount}"


class LoanTransfer(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="transfers")
    previous_borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="outgoing_loan_transfers"
    )
    new_borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="incoming_loan_transfers"
    )
    transferred_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="performed_loan_transfers"
    )
    reason = models.CharField(max_length=500)
    transferred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transferred_at", "-id"]

    def __str__(self):
        return f"Loan {self.loan_id}: {self.previous_borrower_id} -> {self.new_borrower_id}"
