from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking, BookingItem, BookingUnit
from common.models import SystemSettings
from inventory.availability import calculate_availability
from inventory.models import Category, EquipmentModel, EquipmentUnit

from .models import LateFee, Loan, LoanItem, LoanTransfer


User = get_user_model()


class CompleteTransferLifecycleTests(APITestCase):
    def setUp(self):
        self.student_a = User.objects.create_user(
            email="lifecycle-a@example.com", password="password-123", name="Student A", student_id="LIFE-A"
        )
        self.student_b = User.objects.create_user(
            email="lifecycle-b@example.com", password="password-123", name="Student B", student_id="LIFE-B"
        )
        self.staff = User.objects.create_user(
            email="lifecycle-staff@example.com", password="password-123", name="Staff",
            role=User.Role.STAFF, is_staff=True,
        )
        category = Category.objects.create(name="Lifecycle DSLR")
        model = EquipmentModel.objects.create(
            category=category,
            name="Lifecycle DSLR",
            manufacturer="Canon",
            model_number="LIFE-1",
            deposit_amount="100.00",
            late_fee_per_day="20.00",
            max_borrow_quantity=1,
        )
        self.unit = EquipmentUnit.objects.create(
            equipment_model=model,
            asset_code="LIFE-001",
            condition=EquipmentUnit.Condition.GOOD,
        )
        self.model = model
        self.due_at = timezone.now() + timedelta(days=3)

    def auth(self, user):
        self.client.force_authenticate(user=user)

    def create_booking(self):
        self.auth(self.student_a)
        response = self.client.post(
            "/api/bookings/",
            {
                "start_date": "2026-12-01",
                "end_date": "2026-12-03",
                "purpose": "Lifecycle project",
                "items": [{"equipment_model": self.model.id, "quantity": 1}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return Booking.objects.get(pk=response.data["id"])

    def issue_booking(self, booking):
        self.auth(self.staff)
        approval = self.client.post(
            f"/api/bookings/{booking.id}/approve/",
            {"unit_ids": [self.unit.id]},
            format="json",
        )
        self.assertEqual(approval.status_code, status.HTTP_200_OK)
        issue = self.client.post(
            f"/api/loans/issue-booking/{booking.id}/",
            {"due_at": self.due_at.isoformat()},
            format="json",
        )
        self.assertEqual(issue.status_code, status.HTTP_201_CREATED)
        return Loan.objects.get(pk=issue.data["id"])

    def test_complete_student_transfer_overdue_return_lifecycle(self):
        booking = self.create_booking()
        loan = self.issue_booking(booking)
        original_loan_id = loan.id
        original_due_at = loan.due_at
        original_item_id = loan.items.get().id
        original_unit_id = loan.items.get().equipment_unit_id

        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, EquipmentUnit.Status.ISSUED)
        self.assertFalse(calculate_availability(self.model, booking.start_date, booking.end_date)["available"])

        self.auth(self.staff)
        transfer = self.client.post(
            f"/api/loans/{loan.id}/transfer/",
            {"new_borrower_id": self.student_b.id, "reason": "Project handover"},
            format="json",
        )
        self.assertEqual(transfer.status_code, status.HTTP_200_OK)

        loan.refresh_from_db()
        self.unit.refresh_from_db()
        self.assertEqual(loan.id, original_loan_id)
        self.assertEqual(loan.borrower_id, self.student_b.id)
        self.assertEqual(loan.due_at, original_due_at)
        self.assertEqual(loan.status, Loan.Status.ACTIVE)
        self.assertEqual(loan.items.get().id, original_item_id)
        self.assertEqual(loan.items.get().equipment_unit_id, original_unit_id)
        self.assertEqual(self.unit.status, EquipmentUnit.Status.ISSUED)
        self.assertEqual(Loan.objects.filter(booking=booking).count(), 1)
        self.assertEqual(LoanItem.objects.filter(loan=loan).count(), 1)
        self.assertEqual(LoanTransfer.objects.filter(loan=loan).count(), 1)

        self.auth(self.student_a)
        self.assertEqual(self.client.get("/api/loans/").data, [])
        self.auth(self.student_b)
        self.assertEqual(len(self.client.get("/api/loans/").data), 1)

        overdue_due_at = timezone.now() - timedelta(days=2)
        Loan.objects.filter(pk=loan.id).update(due_at=overdue_due_at, status=Loan.Status.OVERDUE)
        self.auth(self.staff)
        overdue_transfer = self.client.post(
            f"/api/loans/{loan.id}/transfer/",
            {"new_borrower_id": self.student_a.id, "reason": "Return coordination"},
            format="json",
        )
        self.assertEqual(overdue_transfer.status_code, status.HTTP_200_OK)
        loan.refresh_from_db()
        self.assertEqual(loan.status, Loan.Status.OVERDUE)
        self.assertEqual(loan.due_at, overdue_due_at)
        self.assertEqual(loan.id, original_loan_id)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, EquipmentUnit.Status.ISSUED)

        # The current borrower is responsible for the staff-processed physical return.
        return_response = self.client.post(
            f"/api/loans/{loan.id}/return/",
            {
                "items": [{
                    "loan_item_id": original_item_id,
                    "condition": "GOOD",
                    "status": "AVAILABLE",
                }],
            },
            format="json",
        )
        self.assertEqual(return_response.status_code, status.HTTP_200_OK)
        loan.refresh_from_db()
        self.unit.refresh_from_db()
        fee = LateFee.objects.get(loan=loan)
        self.assertEqual(loan.status, Loan.Status.RETURNED)
        self.assertEqual(loan.borrower_id, self.student_a.id)
        self.assertEqual(self.unit.status, EquipmentUnit.Status.AVAILABLE)
        self.assertGreaterEqual(fee.days_late, 2)
        self.assertEqual(fee.amount, Decimal("20.00") * fee.days_late)
        self.assertEqual(Loan.objects.filter(pk=original_loan_id).count(), 1)
        self.assertEqual(LoanItem.objects.filter(loan_id=original_loan_id).count(), 1)
        self.assertEqual(LoanTransfer.objects.filter(loan_id=original_loan_id).count(), 2)
