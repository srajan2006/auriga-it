from django.core.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from bookings.models import Booking

from .models import LateFee, Loan
from .permissions import IsStaffOrAdmin
from .serializers import (
    IssueSerializer,
    LateFeeSerializer,
    LoanSerializer,
    LoanTransferSerializer,
    ReturnSerializer,
    TransferSerializer,
)
from .services import issue_booking, refresh_overdue_status, return_loan, transfer_loan


class LoanViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = LoanSerializer
    queryset = Loan.objects.select_related("booking", "borrower", "issued_by").prefetch_related("items__equipment_unit__equipment_model", "late_fee")

    def get_permissions(self):
        if self.action in {"issue", "return_loan", "transfer"}:
            return [IsStaffOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        for loan in self.queryset.filter(status=Loan.Status.ACTIVE, returned_at__isnull=True):
            refresh_overdue_status(loan)
        if self.request.user.role == "STUDENT":
            return self.queryset.filter(borrower=self.request.user)
        return self.queryset

    @action(detail=False, methods=["post"], url_path="issue-booking/(?P<booking_id>[^/.]+)")
    def issue(self, request, booking_id=None):
        serializer = IssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            loan = issue_booking(
                booking_id=booking_id,
                issued_by=request.user,
                due_at=serializer.validated_data["due_at"],
                notes=serializer.validated_data.get("notes", ""),
                conditions=serializer.validated_data.get("conditions", {}),
            )
        except Booking.DoesNotExist:
            return Response({"success": False, "message": "Booking not found."}, status=404)
        except ValidationError as error:
            return Response({"success": False, "message": str(error)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(loan).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="return")
    def return_loan(self, request, pk=None):
        serializer = ReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            loan = return_loan(
                loan_id=pk,
                returned_by=request.user,
                items=serializer.validated_data["items"],
                notes=serializer.validated_data.get("notes", ""),
            )
        except Loan.DoesNotExist:
            return Response({"success": False, "message": "Loan not found."}, status=404)
        except ValidationError as error:
            return Response({"success": False, "message": str(error)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(loan).data)

    @action(detail=True, methods=["post"])
    def transfer(self, request, pk=None):
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            loan, _ = transfer_loan(
                loan_id=pk,
                new_borrower_id=serializer.validated_data["new_borrower_id"],
                transferred_by=request.user,
                reason=serializer.validated_data["reason"],
            )
        except Loan.DoesNotExist:
            return Response({"success": False, "message": "Loan not found."}, status=404)
        except request.user.__class__.DoesNotExist:
            return Response({"success": False, "message": "Destination borrower not found."}, status=404)
        except ValidationError as error:
            return Response({"success": False, "message": str(error)}, status=status.HTTP_409_CONFLICT)
        return Response({"success": True, "message": "Loan transferred successfully.", "loan": self.get_serializer(loan).data})

    @action(detail=True, methods=["get"])
    def transfers(self, request, pk=None):
        loan = self.get_object()
        return Response(LoanTransferSerializer(loan.transfers.select_related("previous_borrower", "new_borrower", "transferred_by"), many=True).data)


class LateFeeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LateFeeSerializer
    queryset = LateFee.objects.select_related("loan", "loan__borrower")

    def get_queryset(self):
        if self.request.user.role == "STUDENT":
            return self.queryset.filter(loan__borrower=self.request.user)
        return self.queryset

    @action(detail=True, methods=["post"], permission_classes=[IsStaffOrAdmin])
    def pay(self, request, pk=None):
        fee = self.get_object()
        fee.status = LateFee.Status.PAID
        fee.save(update_fields=["status"])
        return Response(self.get_serializer(fee).data)

    @action(detail=True, methods=["post"], permission_classes=[IsStaffOrAdmin])
    def waive(self, request, pk=None):
        fee = self.get_object()
        fee.status = LateFee.Status.WAIVED
        fee.save(update_fields=["status"])
        return Response(self.get_serializer(fee).data)
