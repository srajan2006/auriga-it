from rest_framework import serializers

from .models import Category, EquipmentModel, EquipmentUnit


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class EquipmentUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentUnit
        fields = [
            "id",
            "equipment_model",
            "asset_code",
            "serial_number",
            "status",
            "condition",
            "location",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {"serial_number": {"allow_blank": True, "allow_null": True}}


class EquipmentModelSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)
    available_quantity = serializers.IntegerField(read_only=True)
    units = EquipmentUnitSerializer(many=True, read_only=True)

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or user.role not in {"STAFF", "ADMIN"}:
            fields.pop("units", None)
        return fields

    class Meta:
        model = EquipmentModel
        fields = [
            "id",
            "category",
            "category_name",
            "name",
            "description",
            "manufacturer",
            "model_number",
            "deposit_amount",
            "late_fee_per_day",
            "max_borrow_quantity",
            "image",
            "is_active",
            "total_quantity",
            "available_quantity",
            "units",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "category_name",
            "total_quantity",
            "available_quantity",
            "units",
            "created_at",
            "updated_at",
        ]

    def validate_max_borrow_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Maximum borrow quantity must be at least 1.")
        return value
