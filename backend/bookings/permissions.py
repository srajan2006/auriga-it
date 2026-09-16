from rest_framework.permissions import BasePermission

from accounts.models import User


class IsStaffOrAdmin(BasePermission):
    message = "Staff or admin access is required."

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role in {User.Role.STAFF, User.Role.ADMIN})