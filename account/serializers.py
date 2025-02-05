from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
import re
from django.contrib.auth.password_validation import validate_password

from .models import User, ActiveAccessToken
from .tokens import TokenHandler


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "email",
            "name",
            "phone_no",
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

    def validate_phone_no(self, value):
        """Validate the phone number format to ensure it matches the expected format: +91XXXXXXXXXX."""
        if value and not re.match(r"^\+91\d{10}$", value):
            raise serializers.ValidationError(
                "Phone number must be in the format +91XXXXXXXXXX."
            )
        return value

    def create(self, validated_data):
        """Override the create method to use the custom user manager for creating users."""
        user = User.objects.create_user(**validated_data)
        return user


class LogInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data["username"], password=data["password"])
        if user is None:
            raise serializers.ValidationError({"detail":"Invalid credentials"})
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
        fields = ["id", "username", "email", "name", "phone_no", "is_staff"]
        read_only_fields = ["id", "is_staff"]

    def validate_phone_no(self, value):
        """
        Validate the phone number format to ensure it matches the expected format: +91XXXXXXXXXX.
        """
        if value and not re.match(r"^\+91\d{10}$", value):
            raise serializers.ValidationError(
                "Phone number must be in the format +91XXXXXXXXXX."
            )
        return value


class UserDeleteSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=False)
    refresh_token = serializers.CharField(write_only=True, required=False)

    def validate(self, attrs):
        request_user = self.context["request"].user
        target_user = self.context["target_user"]
        password = attrs.get("password")
        refresh_token = attrs.get("refresh_token")

        # Staff user validation
        if request_user.is_staff:
            return attrs

        if not password or not refresh_token:
            raise serializers.ValidationError(
                {"detail": "Password and refresh token both are required."}
            )
        # Validate password
        if not check_password(password, request_user.password):
            raise serializers.ValidationError({"password": "Invalid password."})

        # Validate and blacklist refresh token
        try:
            token = RefreshToken(refresh_token)
            if str(token["user_id"]) != str(request_user.id):
                raise serializers.ValidationError(
                    {"refresh_token": "Invalid refresh token."}
                )
            token.blacklist()
        except Exception:
            raise serializers.ValidationError(
                {"refresh_token": "Invalid refresh token."}
            )
        return attrs

    def delete_user(self, user):
        user.is_active = False
        user.save()
        TokenHandler.invalidate_user_tokens(user)


class UpdatePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        request_user = self.context["request"].user

        current_password = attrs.get("current_password")
        new_password = attrs["new_password"]

        if not request_user.is_staff:
            if not current_password:
                raise serializers.ValidationError(
                    {"current_password": "Current password is required."}
                )
            if not check_password(current_password, request_user.password):
                raise serializers.ValidationError(
                    {"current_password": "Invalid current password."}
                )
            if current_password == new_password:
                raise serializers.ValidationError(
                    {"new_password":"New password cannot be the same as the old password."}
                )

        return attrs

    def update_password(self):
        target_user = self.context["target_user"]
        target_user.set_password(self.validated_data["new_password"])
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
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        return value
    
    
class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)

    def validate_password(self, value):
        validate_password(value)
        return value
