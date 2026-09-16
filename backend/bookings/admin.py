from django.contrib import admin

from .models import Booking, BookingItem, BookingUnit


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("booking_code", "borrower", "start_date", "end_date", "status")
    list_filter = ("status", "start_date", "end_date")
    search_fields = ("booking_code", "borrower__email")


@admin.register(BookingUnit)
class BookingUnitAdmin(admin.ModelAdmin):
    list_display = ("booking", "equipment_unit")
    search_fields = ("booking__booking_code", "equipment_unit__asset_code")


@admin.register(BookingItem)
class BookingItemAdmin(admin.ModelAdmin):
    list_display = ("booking", "equipment_model", "quantity")
    search_fields = ("booking__booking_code", "equipment_model__name")
