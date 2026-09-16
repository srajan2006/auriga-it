from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import LateFee, Loan, LoanItem, LoanTransfer

User = get_user_model()


class BorrowerSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "student_id"]


class LoanItemSerializer(serializers.ModelSerializer):
    asset_code = serializers.CharField(source="equipment_unit.asset_code", read_only=True)
    equipment_name = serializers.CharField(source="equipment_unit.equipment_model.name", read_only=True)

    class Meta:
        model = LoanItem
        fields = ["id", "equipment_unit", "asset_code", "equipment_name", "condition_at_issue", "condition_at_return", "notes"]
        read_only_fields = ["id", "asset_code", "equipment_name", "condition_at_return"]


class LoanSerializer(serializers.ModelSerializer):
    borrower_name = serializers.CharField(source="borrower.name", read_only=True)
    issued_by_name = serializers.CharField(source="issued_by.name", read_only=True)
    booking_code = serializers.CharField(source="booking.booking_code", read_only=True)
    items = LoanItemSerializer(many=True, read_only=True)
    late_fee = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            "id", "booking", "booking_code", "borrower", "borrower_name", "issued_by", "issued_by_name",
            "issued_at", "due_at", "returned_at", "status", "notes", "items", "late_fee", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "booking", "booking_code", "borrower", "borrower_name", "issued_by", "issued_by_name",
            "issued_at", "returned_at", "status", "items", "late_fee", "created_at", "updated_at",
        ]

    def get_late_fee(self, obj):
        fee = getattr(obj, "late_fee", None)
        return LateFeeSerializer(fee).data if fee else None


class LateFeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LateFee
        fields = ["id", "loan", "amount", "days_late", "status", "calculated_at", "created_at"]
        read_only_fields = fields


class LoanTransferSerializer(serializers.ModelSerializer):
    previous_borrower = BorrowerSummarySerializer(read_only=True)
    new_borrower = BorrowerSummarySerializer(read_only=True)
    transferred_by = BorrowerSummarySerializer(read_only=True)

    class Meta:
        model = LoanTransfer
        fields = ["id", "loan", "previous_borrower", "new_borrower", "transferred_by", "reason", "transferred_at"]
        read_only_fields = fields


class TransferSerializer(serializers.Serializer):
    new_borrower_id = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=500)


class IssueSerializer(serializers.Serializer):
    due_at = serializers.DateTimeField()
    notes = serializers.CharField(required=False, allow_blank=True)
    conditions = serializers.DictField(child=serializers.ChoiceField(choices=[choice[0] for choice in LoanItem._meta.get_field("condition_at_issue").choices]), required=False)


class ReturnItemSerializer(serializers.Serializer):
    loan_item_id = serializers.IntegerField(min_value=1)
    condition = serializers.ChoiceField(choices=[choice[0] for choice in LoanItem._meta.get_field("condition_at_return").choices if choice[0]])
    status = serializers.ChoiceField(choices=["AVAILABLE", "DAMAGED", "MAINTENANCE", "LOST"])
    notes = serializers.CharField(required=False, allow_blank=True)


class ReturnSerializer(serializers.Serializer):
    items = ReturnItemSerializer(many=True)
    notes = serializers.CharField(required=False, allow_blank=True)
