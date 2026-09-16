from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class SystemSettings(models.Model):
    max_active_loans_per_user = models.PositiveIntegerField(default=3)
    max_units_per_booking = models.PositiveIntegerField(default=5)
    default_late_fee_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("25.00"),
        validators=[MinValueValidator(0)],
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "system settings"
        verbose_name_plural = "system settings"

    def __str__(self):
        return "AVault system settings"

    @classmethod
    def get_solo(cls):
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings
