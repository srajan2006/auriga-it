from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.permissions import IsStaffOrAdmin


class ReadOnlyOrStaff(IsStaffOrAdmin):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return super().has_permission(request, view)
