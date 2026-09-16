from django.contrib import admin

from .models import Category, EquipmentModel, EquipmentUnit


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name", "description")


@admin.register(EquipmentModel)
class EquipmentModelAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "manufacturer", "is_active", "available_quantity")
    list_filter = ("category", "is_active")
    search_fields = ("name", "manufacturer", "model_number")


@admin.register(EquipmentUnit)
class EquipmentUnitAdmin(admin.ModelAdmin):
    list_display = ("asset_code", "equipment_model", "status", "condition", "location")
    list_filter = ("status", "condition", "equipment_model__category")
    search_fields = ("asset_code", "serial_number")
