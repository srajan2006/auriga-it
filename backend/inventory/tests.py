from django.contrib.auth import get_user_model
from datetime import date
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, EquipmentModel, EquipmentUnit
from bookings.models import Booking, BookingUnit


User = get_user_model()


class InventoryApiTests(APITestCase):
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
        self.category = Category.objects.create(name="DSLR", description="Cameras")
        self.camera = EquipmentModel.objects.create(
            category=self.category,
            name="Canon EOS 1500D",
            manufacturer="Canon",
            model_number="EOS-1500D",
            deposit_amount="5000.00",
            late_fee_per_day="50.00",
            max_borrow_quantity=2,
        )
        EquipmentUnit.objects.create(equipment_model=self.camera, asset_code="DSLR-001")
        EquipmentUnit.objects.create(
            equipment_model=self.camera,
            asset_code="DSLR-002",
            status=EquipmentUnit.Status.MAINTENANCE,
        )
        self.booked_unit = EquipmentUnit.objects.create(equipment_model=self.camera, asset_code="DSLR-003")
        self.booking = Booking.objects.create(
            booking_code="BK-001",
            borrower=self.student,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 15),
            status=Booking.Status.APPROVED,
        )
        BookingUnit.objects.create(booking=self.booking, equipment_unit=self.booked_unit)

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_student_can_browse_equipment_with_availability_summary(self):
        self.authenticate(self.student)

        response = self.client.get("/api/equipment/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["name"], "Canon EOS 1500D")
        self.assertEqual(response.data[0]["total_quantity"], 3)
        self.assertEqual(response.data[0]["available_quantity"], 2)
        self.assertNotIn("asset_code", response.data[0])

    def test_student_can_search_and_filter_equipment(self):
        self.authenticate(self.student)

        search_response = self.client.get("/api/equipment/?search=canon")
        empty_response = self.client.get("/api/equipment/?search=projector")
        available_response = self.client.get("/api/equipment/?availability=available")

        self.assertEqual(search_response.data[0]["id"], self.camera.id)
        self.assertEqual(empty_response.data, [])
        self.assertEqual(available_response.data[0]["id"], self.camera.id)

    def test_student_cannot_manage_inventory_units_or_models(self):
        self.authenticate(self.student)

        model_response = self.client.post(
            "/api/equipment/",
            {
                "category": self.category.id,
                "name": "Student Camera",
                "deposit_amount": "10.00",
                "late_fee_per_day": "1.00",
                "max_borrow_quantity": 1,
            },
            format="json",
        )
        unit_response = self.client.get("/api/equipment-units/")

        self.assertEqual(model_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(unit_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_create_category_model_and_unit(self):
        self.authenticate(self.staff)

        category_response = self.client.post(
            "/api/categories/", {"name": "Projector", "description": "Projection"}, format="json"
        )
        self.assertEqual(category_response.status_code, status.HTTP_201_CREATED)

        model_response = self.client.post(
            "/api/equipment/",
            {
                "category": category_response.data["id"],
                "name": "Epson Projector",
                "manufacturer": "Epson",
                "model_number": "EB-X06",
                "deposit_amount": "3000.00",
                "late_fee_per_day": "30.00",
                "max_borrow_quantity": 1,
            },
            format="json",
        )
        self.assertEqual(model_response.status_code, status.HTTP_201_CREATED)

        unit_response = self.client.post(
            "/api/equipment-units/",
            {
                "equipment_model": model_response.data["id"],
                "asset_code": "PROJECTOR-001",
                "condition": "GOOD",
            },
            format="json",
        )
        self.assertEqual(unit_response.status_code, status.HTTP_201_CREATED)

    def test_availability_endpoint_reports_status_counts(self):
        self.authenticate(self.student)

        response = self.client.get(f"/api/equipment/{self.camera.id}/availability/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["available_quantity"], 2)
        self.assertEqual(response.data["status_counts"]["MAINTENANCE"], 1)

    def test_overlapping_booking_excludes_unit(self):
        self.authenticate(self.student)

        response = self.client.get(
            f"/api/equipment/{self.camera.id}/availability/?start_date=2026-09-12&end_date=2026-09-14"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["available_quantity"], 1)
        self.assertEqual(response.data["available_asset_codes"], ["DSLR-001"])

    def test_adjacent_booking_does_not_conflict(self):
        self.authenticate(self.student)

        response = self.client.get(
            f"/api/equipment/{self.camera.id}/availability/?start_date=2026-09-15&end_date=2026-09-20"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["available_quantity"], 2)
        self.assertEqual(response.data["available_asset_codes"], ["DSLR-001", "DSLR-003"])

    def test_date_inside_existing_booking_conflicts(self):
        self.authenticate(self.student)

        response = self.client.get(
            f"/api/equipment/{self.camera.id}/availability/?start_date=2026-09-01&end_date=2026-09-10"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["available_quantity"], 2)

    def test_pending_booking_also_reserves_unit(self):
        self.booking.status = Booking.Status.PENDING
        self.booking.save(update_fields=["status"])
        self.authenticate(self.student)

        response = self.client.get(
            f"/api/equipment/{self.camera.id}/availability/?start_date=2026-09-11&end_date=2026-09-12"
        )

        self.assertEqual(response.data["available_quantity"], 1)

    def test_rejected_booking_does_not_reserve_unit(self):
        self.booking.status = Booking.Status.REJECTED
        self.booking.save(update_fields=["status"])
        self.authenticate(self.student)

        response = self.client.get(
            f"/api/equipment/{self.camera.id}/availability/?start_date=2026-09-12&end_date=2026-09-14"
        )

        self.assertEqual(response.data["available_quantity"], 2)

    def test_unavailable_status_is_excluded_even_without_booking(self):
        self.booked_unit.status = EquipmentUnit.Status.ISSUED
        self.booked_unit.save(update_fields=["status"])
        self.authenticate(self.student)

        response = self.client.get(
            f"/api/equipment/{self.camera.id}/availability/?start_date=2026-09-15&end_date=2026-09-20"
        )

        self.assertEqual(response.data["available_quantity"], 1)

    def test_invalid_or_incomplete_date_range_returns_bad_request(self):
        self.authenticate(self.student)

        reversed_response = self.client.get(
            f"/api/equipment/{self.camera.id}/availability/?start_date=2026-09-20&end_date=2026-09-15"
        )
        incomplete_response = self.client.get(
            f"/api/equipment/{self.camera.id}/availability/?start_date=2026-09-20"
        )

        self.assertEqual(reversed_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(incomplete_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_equipment_list_can_filter_by_date_range(self):
        self.authenticate(self.student)

        available_response = self.client.get(
            "/api/equipment/?availability=available&start_date=2026-09-12&end_date=2026-09-14"
        )
        unavailable_response = self.client.get(
            "/api/equipment/?availability=unavailable&start_date=2026-09-12&end_date=2026-09-14"
        )

        self.assertEqual(available_response.data[0]["id"], self.camera.id)
        self.assertEqual(unavailable_response.data, [])
