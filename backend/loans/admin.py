from django.contrib import admin

from .models import LateFee, Loan, LoanItem, LoanTransfer


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("id", "booking", "borrower", "issued_by", "issued_at", "due_at", "status")
    list_filter = ("status", "issued_at", "due_at")
    search_fields = ("borrower__email", "booking__booking_code")


@admin.register(LoanItem)
class LoanItemAdmin(admin.ModelAdmin):
    list_display = ("loan", "equipment_unit", "condition_at_issue", "condition_at_return")
    list_filter = ("condition_at_issue", "condition_at_return")
    search_fields = ("equipment_unit__asset_code",)


@admin.register(LateFee)
class LateFeeAdmin(admin.ModelAdmin):
    list_display = ("loan", "amount", "days_late", "status", "calculated_at")
    list_filter = ("status", "calculated_at")


@admin.register(LoanTransfer)
class LoanTransferAdmin(admin.ModelAdmin):
    list_display = ("loan", "previous_borrower", "new_borrower", "transferred_by", "transferred_at")
    list_filter = ("transferred_at",)
    search_fields = ("loan__id", "previous_borrower__email", "new_borrower__email", "reason")