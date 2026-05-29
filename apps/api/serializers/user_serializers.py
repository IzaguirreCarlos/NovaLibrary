"""Serializers for users and authentication."""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Public user profile serializer."""
    full_name = serializers.CharField(read_only=True)
    active_loan_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name", "full_name",
            "avatar", "phone", "role", "membership_number", "membership_date",
            "dark_mode", "email_notifications", "active_loan_count",
            "is_active", "date_joined",
        ]
        read_only_fields = ["id", "email", "role", "membership_number", "date_joined"]


class UserAdminSerializer(serializers.ModelSerializer):
    """Admin-level user serializer with all fields."""

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name",
            "avatar", "phone", "role", "membership_number", "membership_date",
            "is_active", "is_staff", "date_joined", "last_login",
        ]
        read_only_fields = ["id", "date_joined", "last_login"]


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "username", "first_name", "last_name", "password", "password_confirm"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            password=validated_data["password"],
            role="member",
        )
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password": "Las contraseñas no coinciden."})
        return attrs
