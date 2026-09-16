from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from inventory.models import EquipmentUnit
from inventory.models import EquipmentModel


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"
        COMPLETED = "COMPLETED", "Completed"

    booking_code = models.CharField(max_length=30, unique=True)
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings")
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    purpose = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_bookings",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_date", "booking_code"]
        indexes = [models.Index(fields=["start_date", "end_date", "status"])]

    def clean(self):
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date.")

    def __str__(self):
        return self.booking_code


class BookingItem(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="items")
    equipment_model = models.ForeignKey(EquipmentModel, on_delete=models.PROTECT, related_name="booking_items")
    quantity = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["booking", "equipment_model"],
                name="unique_booking_equipment_model",
            ),
        ]

    def clean(self):
        if self.quantity < 1:
            raise ValidationError("Booking quantity must be at least 1.")
        if self.quantity > self.equipment_model.max_borrow_quantity:
            raise ValidationError(
                f"Quantity cannot exceed {self.equipment_model.max_borrow_quantity} for this equipment."
            )

    def __str__(self):
        return f"{self.booking.booking_code}: {self.equipment_model.name} x {self.quantity}"


class BookingUnit(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="booking_units")
    equipment_unit = models.ForeignKey(EquipmentUnit, on_delete=models.PROTECT, related_name="booking_units")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["booking", "equipment_unit"], name="unique_booking_unit"),
        ]

    def __str__(self):
        return f"{self.booking.booking_code}: {self.equipment_unit.asset_code}"