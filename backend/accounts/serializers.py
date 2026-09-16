from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "role", "student_id", "phone", "created_at"]
        read_only_fields = ["id", "role", "created_at"]


class StudentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "student_id"]
        read_only_fields = fields


class RegistrationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)
    student_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)

    def validate_email(self, value):
        normalized_email = value.lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return normalized_email

    def validate_student_id(self, value):
        if value and User.objects.filter(student_id=value).exists():
            raise serializers.ValidationError("This student ID is already registered.")
        return value or None

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(
            role=User.Role.STUDENT,
            **validated_data,
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs["email"].lower()
        user = authenticate(email=email, password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")
        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
