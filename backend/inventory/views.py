from datetime import date

from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsStaffOrAdmin

from .models import Category, EquipmentModel, EquipmentUnit
from .availability import calculate_availability
from .permissions import ReadOnlyOrStaff
from .serializers import CategorySerializer, EquipmentModelSerializer, EquipmentUnitSerializer
from django.core.exceptions import ValidationError as DjangoValidationError


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [ReadOnlyOrStaff]


class EquipmentModelViewSet(viewsets.ModelViewSet):
    serializer_class = EquipmentModelSerializer
    permission_classes = [ReadOnlyOrStaff]

    def get_queryset(self):
        queryset = EquipmentModel.objects.select_related("category").prefetch_related("units")
        if not self.request.user.role in {"STAFF", "ADMIN"}:
            queryset = queryset.filter(is_active=True)

        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(manufacturer__icontains=search)
                | Q(model_number__icontains=search)
                | Q(description__icontains=search)
                | Q(category__name__icontains=search)
            )

        category_id = self.request.query_params.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        availability = self.request.query_params.get("availability")
        if availability == "available" and not (start_date or end_date):
            queryset = queryset.filter(units__status=EquipmentUnit.Status.AVAILABLE).distinct()
        elif availability == "unavailable" and not (start_date or end_date):
            queryset = queryset.exclude(units__status=EquipmentUnit.Status.AVAILABLE).distinct()

        if start_date or end_date:
            if not start_date or not end_date:
                raise ValidationError({"message": "Both start_date and end_date are required."})
            try:
                requested_start = date.fromisoformat(start_date)
                requested_end = date.fromisoformat(end_date)
                if requested_end <= requested_start:
                    raise ValueError("End date must be after start date.")
            except ValueError as error:
                raise ValidationError({"message": str(error)}) from error

            available_model_ids = [
                equipment_model.id
                for equipment_model in queryset
                if calculate_availability(equipment_model, requested_start, requested_end)["available"]
            ]
            if availability == "unavailable":
                queryset = queryset.filter(id__in=set(queryset.values_list("id", flat=True)) - set(available_model_ids))
            else:
                queryset = queryset.filter(id__in=available_model_ids)

        active_filter = self.request.query_params.get("is_active")
        if active_filter in {"true", "false"} and self.request.user.role in {"STAFF", "ADMIN"}:
            queryset = queryset.filter(is_active=active_filter == "true")

        return queryset

    @action(detail=True, methods=["get"])
    def availability(self, request, pk=None):
        equipment_model = self.get_object()
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if start_date or end_date:
            if not start_date or not end_date:
                return Response(
                    {"success": False, "message": "Both start_date and end_date are required."},
                    status=400,
                )
            try:
                result = calculate_availability(
                    equipment_model,
                    date.fromisoformat(start_date),
                    date.fromisoformat(end_date),
                )
            except (ValueError, DjangoValidationError) as error:
                message = error.message if hasattr(error, "message") else str(error)
                return Response({"success": False, "message": message}, status=400)
            return Response(result)

        counts = {
            status: equipment_model.units.filter(status=status).count()
            for status, _ in EquipmentUnit.Status.choices
        }
        return Response(
            {
                "equipment_model": equipment_model.id,
                "name": equipment_model.name,
                "total_quantity": equipment_model.total_quantity,
                "available_quantity": equipment_model.available_quantity,
                "status_counts": counts,
            }
        )


class EquipmentUnitViewSet(viewsets.ModelViewSet):
    queryset = EquipmentUnit.objects.select_related("equipment_model", "equipment_model__category")
    serializer_class = EquipmentUnitSerializer
    permission_classes = [IsStaffOrAdmin]
