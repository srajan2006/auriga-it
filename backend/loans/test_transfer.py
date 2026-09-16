from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking
from common.models import SystemSettings
from inventory.models import Category, EquipmentModel, EquipmentUnit

from .models import LateFee, Loan, LoanItem, LoanTransfer


User = get_user_model()


class LoanTransferTests(APITestCase):
    def setUp(self):
        self.student_a = User.objects.create_user(email="a@example.com", password="password-123", name="Rahul", student_id="A")
        self.student_b = User.objects.create_user(email="b@example.com", password="password-123", name="Aman", student_id="B")
        self.student_c = User.objects.create_user(email="c@example.com", password="password-123", name="Priya", student_id="C")
        self.staff = User.objects.create_user(email="staff@example.com", password="password-123", name="Staff", role=User.Role.STAFF, is_staff=True)
        self.admin = User.objects.create_user(email="admin@example.com", password="password-123", name="Admin", role=User.Role.ADMIN, is_staff=True, is_superuser=True)
        self.staff_destination = User.objects.create_user(email="staff-d@example.com", password="password-123", name="Staff destination", role=User.Role.STAFF, is_staff=True)
        self.inactive = User.objects.create_user(email="inactive@example.com", password="password-123", name="Inactive", is_active=False, student_id="INACTIVE")
        category = Category.objects.create(name="Transfer DSLR")
        model = EquipmentModel.objects.create(category=category, name="Transfer Camera", manufacturer="Canon", model_number="T1", deposit_amount="100.00", late_fee_per_day="10.00", max_borrow_quantity=1)
        self.unit = EquipmentUnit.objects.create(equipment_model=model, asset_code="TRANSFER-001", status=EquipmentUnit.Status.ISSUED)
        booking = Booking.objects.create(booking_code="TRANSFER-BK", borrower=self.student_a, start_date="2026-09-20", end_date="2026-09-25", status=Booking.Status.APPROVED)
        self.loan = Loan.objects.create(booking=booking, borrower=self.student_a, issued_by=self.staff, issued_at=timezone.now() - timedelta(days=2), due_at=timezone.now() + timedelta(days=3), status=Loan.Status.ACTIVE)
        LoanItem.objects.create(loan=self.loan, equipment_unit=self.unit, condition_at_issue=EquipmentUnit.Condition.GOOD)

    def transfer(self, destination, user=None, reason="Equipment handed over"):
        self.client.force_authenticate(user or self.staff)
        return self.client.post(f"/api/loans/{self.loan.id}/transfer/", {"new_borrower_id": destination.id, "reason": reason}, format="json")

    def test_successful_transfer_preserves_loan_unit_and_due_date(self):
        old_id = self.loan.id
        old_due = self.loan.due_at
        response = self.transfer(self.student_b)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.loan.refresh_from_db()
        self.unit.refresh_from_db()
        self.assertEqual(self.loan.id, old_id)
        self.assertEqual(self.loan.borrower_id, self.student_b.id)
        self.assertEqual(self.loan.due_at, old_due)
        self.assertEqual(self.loan.items.get().equipment_unit_id, self.unit.id)
        self.assertEqual(self.unit.status, EquipmentUnit.Status.ISSUED)

    def test_previous_student_loses_access_and_new_student_gains_access(self):
        self.assertEqual(self.transfer(self.student_b).status_code, status.HTTP_200_OK)
        self.client.force_authenticate(self.student_a)
        self.assertEqual(self.client.get("/api/loans/").data, [])
        self.client.force_authenticate(self.student_b)
        self.assertEqual(len(self.client.get("/api/loans/").data), 1)

    def test_overdue_loan_can_transfer_without_resetting_status_or_due_date(self):
        self.loan.status = Loan.Status.OVERDUE
        self.loan.due_at = timezone.now() - timedelta(days=2)
        old_due = self.loan.due_at
        self.loan.save(update_fields=["status", "due_at"])

        response = self.transfer(self.student_b)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.loan.refresh_from_db()
        self.assertEqual(self.loan.status, Loan.Status.OVERDUE)
        self.assertEqual(self.loan.due_at, old_due)

    def test_transfer_preserves_existing_late_fee_timeline(self):
        self.loan.status = Loan.Status.OVERDUE
        self.loan.due_at = timezone.now() - timedelta(days=2)
        self.loan.save(update_fields=["status", "due_at"])
        fee = LateFee.objects.create(
            loan=self.loan,
            amount="20.00",
            days_late=2,
            status=LateFee.Status.PENDING,
            calculated_at=timezone.now(),
        )

        self.assertEqual(self.transfer(self.student_b).status_code, status.HTTP_200_OK)

        fee.refresh_from_db()
        self.assertEqual(fee.amount, "20.00")
        self.assertEqual(fee.days_late, 2)
        self.assertEqual(fee.status, LateFee.Status.PENDING)

    def test_student_staff_and_admin_destinations_are_rejected(self):
        self.assertEqual(self.transfer(self.staff_destination).status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(self.transfer(self.admin).status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(self.transfer(self.inactive).status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(self.loan.borrower_id, self.student_a.id)

    def test_student_cannot_transfer_and_returned_or_lost_loans_cannot_transfer(self):
        self.assertEqual(self.transfer(self.student_b, user=self.student_a).status_code, status.HTTP_403_FORBIDDEN)
        for loan_status in [Loan.Status.RETURNED, Loan.Status.LOST]:
            self.loan.status = loan_status
            self.loan.save(update_fields=["status"])
            self.assertEqual(self.transfer(self.student_b).status_code, status.HTTP_409_CONFLICT)

    def test_transfer_history_and_multiple_transfers_are_preserved(self):
        old_due = self.loan.due_at
        self.assertEqual(self.transfer(self.student_b).status_code, status.HTTP_200_OK)
        self.assertEqual(self.transfer(self.student_c).status_code, status.HTTP_200_OK)
        self.loan.refresh_from_db()
        history = list(LoanTransfer.objects.filter(loan=self.loan).order_by("transferred_at"))
        self.assertEqual(self.loan.borrower_id, self.student_c.id)
        self.assertEqual(len(history), 2)
        self.assertEqual((history[0].previous_borrower_id, history[0].new_borrower_id), (self.student_a.id, self.student_b.id))
        self.assertEqual((history[1].previous_borrower_id, history[1].new_borrower_id), (self.student_b.id, self.student_c.id))
        self.assertEqual(self.loan.due_at, old_due)

    def test_destination_active_loan_limit_is_enforced(self):
        settings = SystemSettings.get_solo()
        settings.max_active_loans_per_user = 1
        settings.save(update_fields=["max_active_loans_per_user", "updated_at"])
        category = Category.objects.get(name="Transfer DSLR")
        other_booking = Booking.objects.create(booking_code="OTHER-BK", borrower=self.student_b, start_date="2026-09-01", end_date="2026-09-02", status=Booking.Status.COMPLETED)
        other_loan = Loan.objects.create(booking=other_booking, borrower=self.student_b, issued_by=self.staff, issued_at=timezone.now(), due_at=timezone.now() + timedelta(days=1), status=Loan.Status.ACTIVE)
        LoanItem.objects.create(loan=other_loan, equipment_unit=self.unit, condition_at_issue=EquipmentUnit.Condition.GOOD)

        response = self.transfer(self.student_b)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.loan.refresh_from_db()
        self.assertEqual(self.loan.borrower_id, self.student_a.id)