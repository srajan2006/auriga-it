from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class EquipmentModel(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="equipment_models")
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    manufacturer = models.CharField(max_length=120, blank=True)
    model_number = models.CharField(max_length=120, blank=True)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    late_fee_per_day = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    max_borrow_quantity = models.PositiveIntegerField(default=1)
    image = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "manufacturer", "model_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["manufacturer", "model_number", "name"],
                name="unique_equipment_model_identity",
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def total_quantity(self):
        return self.units.count()

    @property
    def available_quantity(self):
        return self.units.filter(status=EquipmentUnit.Status.AVAILABLE).count()


class EquipmentUnit(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        RESERVED = "RESERVED", "Reserved"
        ISSUED = "ISSUED", "Issued"
        OVERDUE = "OVERDUE", "Overdue"
        MAINTENANCE = "MAINTENANCE", "Maintenance"
        DAMAGED = "DAMAGED", "Damaged"
        LOST = "LOST", "Lost"

    class Condition(models.TextChoices):
        EXCELLENT = "EXCELLENT", "Excellent"
        GOOD = "GOOD", "Good"
        FAIR = "FAIR", "Fair"
        DAMAGED = "DAMAGED", "Damaged"

    equipment_model = models.ForeignKey(EquipmentModel, on_delete=models.CASCADE, related_name="units")
    asset_code = models.CharField(max_length=80, unique=True)
    serial_number = models.CharField(max_length=120, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.GOOD)
    location = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["asset_code"]

    def __str__(self):
        return self.asset_code
