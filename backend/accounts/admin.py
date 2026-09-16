from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class AVaultUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "name", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("email", "name", "student_id")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal information", {"fields": ("name", "student_id", "phone")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "name", "password1", "password2", "role", "is_staff", "is_active"),
        }),
    )
    readonly_fields = ("created_at", "updated_at", "last_login")
