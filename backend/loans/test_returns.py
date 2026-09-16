from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from bookings.models import Booking
from inventory.models import Category, EquipmentModel, EquipmentUnit

from .models import LateFee, Loan, LoanItem


User = get_user_model()


class LoanReturnTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(email="returner@example.com", password="password-123", name="Returner")
        self.other_student = User.objects.create_user(email="other-returner@example.com", password="password-123", name="Other")
        self.staff = User.objects.create_user(
            email="return-staff@example.com", password="password-123", name="Staff", role=User.Role.STAFF, is_staff=True
        )
        category = Category.objects.create(name="Return DSLR")
        model = EquipmentModel.objects.create(
            category=category, name="Return Camera", manufacturer="Canon", model_number="R1",
            deposit_amount="100.00", late_fee_per_day="25.00", max_borrow_quantity=1,
        )
        self.unit = EquipmentUnit.objects.create(
            equipment_model=model, asset_code="RETURN-001", status=EquipmentUnit.Status.ISSUED,
        )
        booking = Booking.objects.create(
            booking_code="RETURN-BK", borrower=self.student, start_date="2026-10-10", end_date="2026-10-12",
            status=Booking.Status.APPROVED,
        )
        self.loan = Loan.objects.create(
            booking=booking, borrower=self.student, issued_by=self.staff,
            issued_at=timezone.now() - timedelta(days=2), due_at=timezone.now() + timedelta(days=1),
            status=Loan.Status.ACTIVE,
        )
        LoanItem.objects.create(loan=self.loan, equipment_unit=self.unit, condition_at_issue=EquipmentUnit.Condition.GOOD)

    def return_loan(self, status_value="AVAILABLE", condition="GOOD"):
        self.client.force_authenticate(self.staff)
        return self.client.post(
            f"/api/loans/{self.loan.id}/return/",
            {"items": [{"loan_item_id": self.loan.items.get().id, "condition": condition, "status": status_value}]},
            format="json",
        )

    def test_on_time_return_has_no_fee_and_makes_unit_available(self):
        response = self.return_loan()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.loan.refresh_from_db()
        self.unit.refresh_from_db()
        fee = LateFee.objects.get(loan=self.loan)
        self.assertEqual(self.loan.status, Loan.Status.RETURNED)
        self.assertEqual(fee.days_late, 0)
        self.assertEqual(fee.amount, Decimal("0.00"))
        self.assertEqual(fee.status, LateFee.Status.WAIVED)
        self.assertEqual(self.unit.status, EquipmentUnit.Status.AVAILABLE)

    def test_late_return_calculates_non_negative_fee(self):
        self.loan.due_at = timezone.now() - timedelta(days=3)
        self.loan.save(update_fields=["due_at"])
        response = self.return_loan()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fee = LateFee.objects.get(loan=self.loan)
        self.assertGreaterEqual(fee.days_late, 3)
        self.assertEqual(fee.amount, Decimal("25.00") * fee.days_late)
        self.assertEqual(fee.status, LateFee.Status.PENDING)

    def test_damaged_return_updates_condition_and_unit_status(self):
        response = self.return_loan(status_value="DAMAGED", condition="DAMAGED")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, EquipmentUnit.Status.DAMAGED)
        self.assertEqual(self.loan.items.get().condition_at_return, EquipmentUnit.Condition.DAMAGED)

    def test_maintenance_return_updates_unit_status(self):
        response = self.return_loan(status_value="MAINTENANCE", condition="FAIR")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, EquipmentUnit.Status.MAINTENANCE)

    def test_repeated_return_is_rejected(self):
        self.assertEqual(self.return_loan().status_code, status.HTTP_200_OK)
        response = self.return_loan()
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(LateFee.objects.count(), 1)

    def test_student_sees_only_own_fees_and_cannot_return(self):
        self.assertEqual(self.return_loan().status_code, status.HTTP_200_OK)
        other_student = User.objects.create_user(email="third@example.com", password="password-123", name="Third")
        self.client.force_authenticate(other_student)
        fees = self.client.get("/api/late-fees/")
        loans = self.client.get("/api/loans/")
        attempted_return = self.client.post(f"/api/loans/{self.loan.id}/return/", {}, format="json")
        self.assertEqual(fees.status_code, status.HTTP_200_OK)
        self.assertEqual(len(fees.data), 0)
        self.assertEqual(loans.data, [])
        self.assertEqual(attempted_return.status_code, status.HTTP_403_FORBIDDEN)
