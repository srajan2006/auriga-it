from types import SimpleNamespace

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsAdmin, IsStaffOrAdmin, IsStudent


User = get_user_model()


class AuthenticationApiTests(APITestCase):
    def test_registration_creates_student_with_hashed_password(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "name": "Asha Student",
                "email": "asha@example.com",
                "password": "secure-pass-123",
                "password_confirm": "secure-pass-123",
                "student_id": "STU-001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="asha@example.com")
        self.assertEqual(user.role, User.Role.STUDENT)
        self.assertTrue(user.check_password("secure-pass-123"))
        self.assertNotEqual(user.password, "secure-pass-123")
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_registration_rejects_password_mismatch(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "name": "Asha Student",
                "email": "asha@example.com",
                "password": "secure-pass-123",
                "password_confirm": "different-pass",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="asha@example.com").exists())

    def test_login_returns_jwt_and_me_requires_authentication(self):
        user = User.objects.create_user(
            email="student@example.com",
            password="secure-pass-123",
            name="Asha Student",
        )

        unauthenticated_response = self.client.get("/api/auth/me/")
        self.assertEqual(unauthenticated_response.status_code, status.HTTP_401_UNAUTHORIZED)

        login_response = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "secure-pass-123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        me_response = self.client.get("/api/auth/me/")
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["user"]["email"], user.email)
        self.assertEqual(me_response.data["user"]["role"], User.Role.STUDENT)

    def test_logout_blacklists_refresh_token(self):
        user = User.objects.create_user(
            email="student@example.com",
            password="secure-pass-123",
            name="Asha Student",
        )
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        logout_response = self.client.post(
            "/api/auth/logout/",
            {"refresh": str(refresh)},
            format="json",
        )
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        refresh_response = self.client.post(
            "/api/auth/refresh/",
            {"refresh": str(refresh)},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)


class RolePermissionTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="student@example.com", password="password-123", name="Student"
        )
        self.staff = User.objects.create_user(
            email="staff@example.com",
            password="password-123",
            name="Staff",
            role=User.Role.STAFF,
            is_staff=True,
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="password-123",
            name="Admin",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )

    def test_student_cannot_use_staff_or_admin_permissions(self):
        request = SimpleNamespace(user=self.student)
        self.assertFalse(IsStaffOrAdmin().has_permission(request, None))
        self.assertFalse(IsAdmin().has_permission(request, None))
        self.assertTrue(IsStudent().has_permission(request, None))

    def test_staff_can_use_staff_permission_but_not_admin_permission(self):
        request = SimpleNamespace(user=self.staff)
        self.assertTrue(IsStaffOrAdmin().has_permission(request, None))
        self.assertFalse(IsAdmin().has_permission(request, None))

    def test_admin_can_use_staff_and_admin_permissions(self):
        request = SimpleNamespace(user=self.admin)
        self.assertTrue(IsStaffOrAdmin().has_permission(request, None))
        self.assertTrue(IsAdmin().has_permission(request, None))
