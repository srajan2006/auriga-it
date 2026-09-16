from rest_framework import serializers

from inventory.models import EquipmentModel
from common.models import SystemSettings

from .models import Booking, BookingItem, BookingUnit


class BookingItemSerializer(serializers.ModelSerializer):
    equipment_name = serializers.CharField(source="equipment_model.name", read_only=True)
    available_quantity = serializers.SerializerMethodField()

    class Meta:
        model = BookingItem
        fields = ["id", "equipment_model", "equipment_name", "quantity", "available_quantity"]
        read_only_fields = ["id", "equipment_name", "available_quantity"]

    def get_available_quantity(self, obj):
        return obj.equipment_model.available_quantity


class BookingUnitSerializer(serializers.ModelSerializer):
    asset_code = serializers.CharField(source="equipment_unit.asset_code", read_only=True)

    class Meta:
        model = BookingUnit
        fields = ["id", "equipment_unit", "asset_code"]
        read_only_fields = ["id", "asset_code"]


class BookingSerializer(serializers.ModelSerializer):
    borrower_name = serializers.CharField(source="borrower.name", read_only=True)
    items = BookingItemSerializer(many=True)
    booking_units = BookingUnitSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "booking_code", "borrower", "borrower_name", "start_date", "end_date",
            "status", "purpose", "notes", "approved_by", "approved_at", "items", "booking_units",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "booking_code", "borrower", "borrower_name", "status", "approved_by",
            "approved_at", "booking_units", "created_at", "updated_at",
        ]

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({"end_date": "End date must be after start date."})
        items = attrs.get("items", [])
        if not items:
            raise serializers.ValidationError({"items": "At least one equipment item is required."})
        if len({item["equipment_model"].id for item in items}) != len(items):
            raise serializers.ValidationError({"items": "Each equipment model may appear only once."})
        if sum(item["quantity"] for item in items) > SystemSettings.get_solo().max_units_per_booking:
            raise serializers.ValidationError({"items": "The booking exceeds the maximum units allowed per booking."})
        return attrs

    def validate_items(self, items):
        for item in items:
            equipment_model = item["equipment_model"]
            quantity = item["quantity"]
            if not equipment_model.is_active:
                raise serializers.ValidationError(f"{equipment_model.name} is not active.")
            if quantity > equipment_model.max_borrow_quantity:
                raise serializers.ValidationError(
                    f"Quantity for {equipment_model.name} cannot exceed {equipment_model.max_borrow_quantity}."
                )
        return items


class BookingDecisionSerializer(serializers.Serializer):
    unit_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False, allow_empty=True
    )
    reason = serializers.CharField(required=False, allow_blank=True)
