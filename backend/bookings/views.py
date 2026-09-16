from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Booking, BookingUnit
from .permissions import IsStaffOrAdmin
from .serializers import BookingDecisionSerializer, BookingSerializer
from .services import approve_booking, create_booking


class BookingViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "head", "options"]
    serializer_class = BookingSerializer
    queryset = Booking.objects.select_related("borrower", "approved_by").prefetch_related("items", "booking_units")

    def get_permissions(self):
        if self.action in {"approve", "reject"}:
            return [IsStaffOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = self.queryset
        if self.request.user.role == "STUDENT":
            return queryset.filter(borrower=self.request.user)
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            booking = create_booking(borrower=request.user, validated_data=serializer.validated_data)
        except ValidationError as error:
            return Response({"success": False, "message": str(error)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(booking).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        serializer = BookingDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            booking = approve_booking(
                booking_id=pk,
                approved_by=request.user,
                unit_ids=serializer.validated_data.get("unit_ids", []),
            )
        except Booking.DoesNotExist:
            return Response({"success": False, "message": "Booking not found."}, status=404)
        except ValidationError as error:
            return Response({"success": False, "message": str(error)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(booking).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        booking = self.get_object()
        if booking.status != Booking.Status.PENDING:
            return Response({"success": False, "message": "Only pending bookings can be rejected."}, status=409)
        booking.status = Booking.Status.REJECTED
        booking.notes = request.data.get("reason", booking.notes)
        booking.save(update_fields=["status", "notes", "updated_at"])
        return Response(self.get_serializer(booking).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.borrower_id != request.user.id and request.user.role == "STUDENT":
            return Response({"success": False, "message": "You cannot cancel this booking."}, status=403)
        if booking.status not in {Booking.Status.PENDING, Booking.Status.APPROVED}:
            return Response({"success": False, "message": "This booking cannot be cancelled."}, status=409)
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        if booking.booking_units.exists():
            from inventory.models import EquipmentUnit

            EquipmentUnit.objects.filter(booking_units__booking=booking).update(
                status=EquipmentUnit.Status.AVAILABLE
            )
        return Response(self.get_serializer(booking).data)