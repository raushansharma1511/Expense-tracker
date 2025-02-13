from rest_framework import serializers
from ..models import Wallet
from account.models import User
from django.utils.text import slugify
from transactions.models import Transaction


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = [
            "id",
            "user",
            "name",
            "balance",
            "created_at",
            "updated_at",
            "is_deleted",
        ]
        read_only_fields = ["id", "balance", "created_at", "updated_at", "is_deleted"]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        request = self.context.get("request", None)

        if request and request.method in ["PATCH"]:
            self.fields["user"].read_only = True

    def validate_user(self, user):
        """Validate that staff users can only create wallets for other normal users and normal user is for himself only."""
        request_user = self.context["request"].user

        if user.is_active == False:
            raise serializers.ValidationError("User not found")

        if not request_user.is_staff and request_user != user:
            raise serializers.ValidationError(
                "You can only create wallets for yourself."
            )

        if request_user.is_staff and user.is_staff:
            raise serializers.ValidationError(
                "Staff cannot create wallets for themselves."
            )
        return user

    def _validate_wallet_name(self, value, user):
        """Ensure wallet name is unique per user."""
        value = value.strip()

        # Check the length of the wallet name
        if len(value) < 1:
            raise serializers.ValidationError(
                {"name": "The wallet name must be at least 1 characters long."}
            )

        if Wallet.objects.filter(
            user=user, name__iexact=value, is_deleted=False
        ).exists():
            raise serializers.ValidationError(
                {"name": "A wallet with this name already exists."}
            )
        return value

    def validate(self, data):
        """Object-level validations (final checks after field validations)"""
        if self.instance is None:
            user = data.get("user")
            data["name"] = self._validate_wallet_name(data["name"], user)
        else:
            if "name" in data:
                data["name"] = self._validate_wallet_name(
                    data["name"], self.instance.user
                )

        return data
