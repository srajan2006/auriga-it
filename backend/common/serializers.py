from rest_framework import serializers

from .models import SystemSettings


class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = ["id", "max_active_loans_per_user", "max_units_per_booking", "default_late_fee_per_day", "updated_at"]
        read_only_fields = ["id", "updated_at"]
