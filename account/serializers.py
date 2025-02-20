from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
import re
from .validators import validate_password

from .models import User, ActiveAccessToken
from .tokens import TokenHandler
from .tasks import soft_delete_user_related_objects


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "email",
            "name",
            "phone_number",
            "created_at",
            "updated_at",
            "is_active",
            "is_staff",
        ]
        extra_kwargs = {"password": {"write_only": True}}
        read_only_fields = ["id", "is_staff", "created_at", "updated_at", "is_active"]

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        """Override the create method to use the custom user manager for creating users."""
        user = User.objects.create_user(**validated_data)
        return user


class LogInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError({"detail": "Invalid credentials"})
        return user


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(required=True)

    def validate_refresh_token(self, refresh_token):
        try:
            token = RefreshToken(refresh_token)
            request = self.context["request"]

            # Check if the user in the refresh token matches the user making the request
            if token.get("user_id") != str(request.user.id):
                raise serializers.ValidationError(
                    {
                        "refresh_token": "This refresh token does not belong to the authenticated user."
                    }
                )
            TokenHandler.blacklist_refresh_token(refresh_token)
        except Exception:
            raise serializers.ValidationError(
                {"refresh_token": "Invalid refresh token or already blacklisted."}
            )


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "name",
            "phone_number",
            "created_at",
            "updated_at",
            "is_active",
            "is_staff",
        ]
        read_only_fields = ["id", "is_staff", "created_at", "updated_at", "is_active"]


class UserDeleteSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=False)

    def validate(self, attrs):
        request_user = self.context["request"].user
        target_user = self.context["target_user"]
        password = attrs.get("password")

        # Staff user validation
        if request_user.is_staff:
            return attrs

        if not password:
            raise serializers.ValidationError(
                {"detail": "Password is required."}
            )
        # Validate password
        if not check_password(password, request_user.password):
            raise serializers.ValidationError({"password": "Invalid password."})

        return attrs

    def delete_user(self, user):
        user.is_active = False
        user.save()
        soft_delete_user_related_objects.delay(user.id)


class UpdatePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True)
    confirm_new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        request_user = self.context["request"].user
        target_user = self.context["target_user"]

        current_password = attrs.get("current_password")
        new_password = attrs["new_password"]
        confirm_new_password = attrs["confirm_new_password"]

        if new_password != confirm_new_password:
            raise serializers.ValidationError(
                {"confirm_new_password": "New passwords do not match."}
            )

        if request_user.is_superuser:
            return attrs

        if not current_password:
            raise serializers.ValidationError(
                {"current_password": "Current password is required."}
            )
        if not request_user.check_password(current_password):
            raise serializers.ValidationError(
                {"current_password": "Invalid current password."}
            )
        if current_password == new_password:
            raise serializers.ValidationError(
                {"new_password": "New password cannot be the same as the old password."}
            )

        return attrs

    def update_password(self):
        target_user = self.context["target_user"]
        new_password = self.validated_data["new_password"]

        target_user.set_password(new_password)  # Hash and update the password
        target_user.save()

        # Invalidate all active tokens except the current session
        current_token = self.context["request"].auth
        ActiveAccessToken.objects.filter(user=target_user).exclude(
            access_token=current_token
        ).delete()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)

    def validate_password(self, value):
        validate_password(value)
        return value
