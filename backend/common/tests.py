from django.contrib.auth import get_user_model
from datetime import date
from rest_framework import status
from rest_framework.test import APITestCase

from .models import SystemSettings
from inventory.models import Category, EquipmentModel, EquipmentUnit


User = get_user_model()


class SystemSettingsApiTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(email="settings-student@example.com", password="password-123", name="Student")
        self.staff = User.objects.create_user(email="settings-staff@example.com", password="password-123", name="Staff", role=User.Role.STAFF, is_staff=True)
        self.admin = User.objects.create_user(email="settings-admin@example.com", password="password-123", name="Admin", role=User.Role.ADMIN, is_staff=True, is_superuser=True)

    def test_authenticated_users_can_read_settings(self):
        self.client.force_authenticate(self.student)
        response = self.client.get("/api/settings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("max_active_loans_per_user", response.data)

    def test_only_admin_can_modify_settings(self):
        payload = {"max_active_loans_per_user": 7, "max_units_per_booking": 8, "default_late_fee_per_day": "35.00"}
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.patch("/api/settings/", payload, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.patch("/api/settings/", payload, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.admin)
        response = self.client.patch("/api/settings/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        settings = SystemSettings.get_solo()
        self.assertEqual(settings.max_active_loans_per_user, 7)
        self.assertEqual(settings.max_units_per_booking, 8)

    def test_max_units_per_booking_is_enforced_by_booking_api(self):
        settings = SystemSettings.get_solo()
        settings.max_units_per_booking = 1
        settings.save(update_fields=["max_units_per_booking", "updated_at"])
        category = Category.objects.create(name="Settings Camera")
        model = EquipmentModel.objects.create(
            category=category,
            name="Settings Camera",
            manufacturer="Test",
            model_number="S1",
            deposit_amount="10.00",
            late_fee_per_day="1.00",
            max_borrow_quantity=2,
        )
        EquipmentUnit.objects.create(equipment_model=model, asset_code="SETTINGS-001")
        self.client.force_authenticate(self.student)

        response = self.client.post(
            "/api/bookings/",
            {
                "start_date": date(2026, 11, 1).isoformat(),
                "end_date": date(2026, 11, 2).isoformat(),
                "purpose": "Settings test",
                "items": [{"equipment_model": model.id, "quantity": 2}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)