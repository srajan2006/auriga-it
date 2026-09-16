from rest_framework.permissions import BasePermission

from .models import User


class IsStaffOrAdmin(BasePermission):
    message = "Staff or admin access is required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in {User.Role.STAFF, User.Role.ADMIN}
        )


class IsAdmin(BasePermission):
    message = "Admin access is required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
        )


class IsStudent(BasePermission):
    message = "Student access is required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.STUDENT
        )
