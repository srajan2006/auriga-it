from datetime import date

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from inventory.models import Category, EquipmentModel, EquipmentUnit

from .models import Booking, BookingItem, BookingUnit


User = get_user_model()


class BookingApiTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(email="student@example.com", password="password-123", name="Student")
        self.other_student = User.objects.create_user(email="other@example.com", password="password-123", name="Other")
        self.staff = User.objects.create_user(
            email="staff@example.com", password="password-123", name="Staff", role=User.Role.STAFF, is_staff=True
        )
        category = Category.objects.create(name="DSLR")
        self.camera = EquipmentModel.objects.create(
            category=category, name="Camera", manufacturer="Canon", model_number="X1",
            deposit_amount="100.00", late_fee_per_day="5.00", max_borrow_quantity=2,
        )
        self.unit_one = EquipmentUnit.objects.create(equipment_model=self.camera, asset_code="CAM-001")
        self.unit_two = EquipmentUnit.objects.create(equipment_model=self.camera, asset_code="CAM-002")

    def post_booking(self, **overrides):
        data = {
            "start_date": "2026-10-10",
            "end_date": "2026-10-12",
            "purpose": "Film project",
            "items": [{"equipment_model": self.camera.id, "quantity": 1}],
        }
        data.update(overrides)
        return self.client.post("/api/bookings/", data, format="json")

    def test_student_can_create_booking_request(self):
        self.client.force_authenticate(self.student)

        response = self.post_booking()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Booking.Status.PENDING)
        self.assertEqual(response.data["borrower"], self.student.id)
        self.assertEqual(BookingItem.objects.count(), 1)

    def test_student_only_sees_own_bookings(self):
        Booking.objects.create(
            booking_code="BK-OTHER", borrower=self.other_student,
            start_date=date(2026, 10, 10), end_date=date(2026, 10, 12),
        )
        self.client.force_authenticate(self.student)

        response = self.client.get("/api/bookings/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_overlapping_request_is_rejected_but_adjacent_request_is_allowed(self):
        existing = Booking.objects.create(
            booking_code="BK-EXISTING", borrower=self.other_student,
            start_date=date(2026, 10, 10), end_date=date(2026, 10, 12), status=Booking.Status.APPROVED,
        )
        BookingUnit.objects.create(booking=existing, equipment_unit=self.unit_one)
        self.client.force_authenticate(self.student)

        overlap = self.post_booking()
        adjacent = self.post_booking(start_date="2026-10-12", end_date="2026-10-14")

        self.assertEqual(overlap.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(adjacent.status_code, status.HTTP_201_CREATED)

    def test_overlapping_pending_request_reserves_requested_quantity(self):
        self.client.force_authenticate(self.student)
        first = self.post_booking().data["id"]
        second = self.post_booking()

        self.assertTrue(first)
        self.assertEqual(second.status_code, status.HTTP_409_CONFLICT)

    def test_quantity_limit_and_insufficient_quantity_are_backend_validated(self):
        self.client.force_authenticate(self.student)

        too_many = self.post_booking(items=[{"equipment_model": self.camera.id, "quantity": 3}])
        self.assertEqual(too_many.status_code, status.HTTP_400_BAD_REQUEST)

        EquipmentUnit.objects.filter(id=self.unit_two.id).update(status=EquipmentUnit.Status.MAINTENANCE)
        unavailable = self.post_booking(items=[{"equipment_model": self.camera.id, "quantity": 2}])
        self.assertEqual(unavailable.status_code, status.HTTP_409_CONFLICT)

    def test_student_cannot_approve_or_reject(self):
        self.client.force_authenticate(self.student)
        booking = self.post_booking().data["id"]

        approve = self.client.post(f"/api/bookings/{booking}/approve/", {"unit_ids": [self.unit_one.id]}, format="json")
        reject = self.client.post(f"/api/bookings/{booking}/reject/", {}, format="json")

        self.assertEqual(approve.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(reject.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_approval_requires_exact_units_and_assigns_them(self):
        self.client.force_authenticate(self.student)
        booking_id = self.post_booking().data["id"]
        self.client.force_authenticate(self.staff)

        wrong_count = self.client.post(f"/api/bookings/{booking_id}/approve/", {"unit_ids": []}, format="json")
        approved = self.client.post(
            f"/api/bookings/{booking_id}/approve/", {"unit_ids": [self.unit_one.id]}, format="json"
        )

        self.assertEqual(wrong_count.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(approved.status_code, status.HTTP_200_OK)
        self.assertEqual(approved.data["status"], Booking.Status.APPROVED)
        self.assertEqual(approved.data["booking_units"][0]["equipment_unit"], self.unit_one.id)
        self.unit_one.refresh_from_db()
        self.assertEqual(self.unit_one.status, EquipmentUnit.Status.RESERVED)

    def test_conflicting_approval_is_rejected(self):
        self.client.force_authenticate(self.student)
        first_id = self.post_booking().data["id"]
        second = self.post_booking(start_date="2026-10-10", end_date="2026-10-12")
        self.client.force_authenticate(self.staff)

        first_approval = self.client.post(f"/api/bookings/{first_id}/approve/", {"unit_ids": [self.unit_one.id]}, format="json")
        second_approval = self.client.post(f"/api/bookings/{second.data['id']}/approve/", {"unit_ids": [self.unit_one.id]}, format="json")

        self.assertEqual(first_approval.status_code, status.HTTP_200_OK)
        self.assertEqual(second_approval.status_code, status.HTTP_409_CONFLICT)

    def test_student_can_cancel_own_booking_and_release_units(self):
        self.client.force_authenticate(self.student)
        booking_id = self.post_booking().data["id"]
        self.client.force_authenticate(self.staff)
        self.client.post(f"/api/bookings/{booking_id}/approve/", {"unit_ids": [self.unit_one.id]}, format="json")
        self.client.force_authenticate(self.student)

        response = self.client.post(f"/api/bookings/{booking_id}/cancel/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.unit_one.refresh_from_db()
        self.assertEqual(self.unit_one.status, EquipmentUnit.Status.AVAILABLE)