from django.contrib import admin

from .models import SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "max_active_loans_per_user", "max_units_per_booking", "default_late_fee_per_day", "updated_at")