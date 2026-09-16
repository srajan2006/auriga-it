from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking, BookingItem, BookingUnit
from inventory.models import Category, EquipmentModel, EquipmentUnit

from .models import Loan, LoanItem


User = get_user_model()


class LoanIssueTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(email="student@example.com", password="password-123", name="Student")
        self.other_student = User.objects.create_user(email="other@example.com", password="password-123", name="Other")
        self.staff = User.objects.create_user(
            email="staff@example.com", password="password-123", name="Staff", role=User.Role.STAFF, is_staff=True
        )
        category = Category.objects.create(name="DSLR")
        model = EquipmentModel.objects.create(
            category=category, name="Camera", manufacturer="Canon", model_number="X1",
            deposit_amount="100.00", late_fee_per_day="5.00", max_borrow_quantity=2,
        )
        self.unit = EquipmentUnit.objects.create(
            equipment_model=model, asset_code="CAM-001", condition=EquipmentUnit.Condition.EXCELLENT,
            status=EquipmentUnit.Status.RESERVED,
        )
        self.booking = Booking.objects.create(
            booking_code="BK-001", borrower=self.student, start_date="2026-10-10", end_date="2026-10-12",
            status=Booking.Status.APPROVED,
        )
        BookingItem.objects.create(booking=self.booking, equipment_model=model, quantity=1)
        BookingUnit.objects.create(booking=self.booking, equipment_unit=self.unit)

    def issue(self, **data):
        payload = {"due_at": (timezone.now() + timedelta(days=3)).isoformat(), "conditions": {str(self.unit.id): "EXCELLENT"}}
        payload.update(data)
        return self.client.post(f"/api/loans/issue-booking/{self.booking.id}/", payload, format="json")

    def test_staff_can_issue_approved_booking_and_snapshot_condition(self):
        self.client.force_authenticate(self.staff)

        response = self.issue()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        loan = Loan.objects.get(booking=self.booking)
        item = LoanItem.objects.get(loan=loan)
        self.assertEqual(loan.status, Loan.Status.ACTIVE)
        self.assertEqual(loan.borrower_id, self.student.id)
        self.assertEqual(item.condition_at_issue, EquipmentUnit.Condition.EXCELLENT)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, EquipmentUnit.Status.ISSUED)

    def test_student_cannot_issue(self):
        self.client.force_authenticate(self.student)

        response = self.issue()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unapproved_booking_cannot_be_issued(self):
        self.booking.status = Booking.Status.PENDING
        self.booking.save(update_fields=["status"])
        self.client.force_authenticate(self.staff)

        response = self.issue()

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(Loan.objects.exists())

    def test_due_date_must_be_after_issue_time(self):
        self.client.force_authenticate(self.staff)

        response = self.issue(due_at=(timezone.now() - timedelta(minutes=1)).isoformat())

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_booking_cannot_be_issued_twice(self):
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.issue().status_code, status.HTTP_201_CREATED)

        response = self.issue()

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Loan.objects.count(), 1)

    def test_student_only_sees_own_loans(self):
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.issue().status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(self.other_student)

        response = self.client.get("/api/loans/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_assigned_unit_must_be_reserved(self):
        self.unit.status = EquipmentUnit.Status.AVAILABLE
        self.unit.save(update_fields=["status"])
        self.client.force_authenticate(self.staff)

        response = self.issue()

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
