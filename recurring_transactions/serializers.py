from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import datetime

from common.utils import is_valid_uuid
from account.models import User
from .models import RecurringTransaction


class RecurringTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringTransaction
        fields = [
            "id",
            "user",
            "wallet",
            "category",
            "type",
            "amount",
            "frequency",
            "start_date",
            "end_date",
            "next_run",
            "description",
        ]
        read_only_fields = ["id", "next_run", "status"]

    def __init__(self, *args, **kwargs):
        """Ensure user field is ignored silently if present for normal users."""
        super().__init__(*args, **kwargs)
        request = self.context.get("request", None)

        if request and request.method in ["PATCH", "PUT"]:
            self.fields["user"].read_only = True
            self.fields["type"].read_only = True

    def _get_recurring_transaction_user(self):
        """Helper method to get and validate the recurring transaction user"""
        if self.instance:
            return self.instance.user

        if "user" not in self.initial_data:
            return None

        user_id = self.initial_data.get("user")

        if not is_valid_uuid(user_id):
            return None

        user = User.objects.filter(id=user_id, is_active=True).first()
        return user

    def _get_recurring_transaction_type(self):
        """Helper method to get recurring transaction type"""
        if self.instance:
            return self.instance.type
        type = self.initial_data.get("type")
        return type

    def validate_user(self, user):
        """Validate user field with comprehensive checks"""
        request_user = self.context["request"].user

        if not user.is_active:
            raise serializers.ValidationError("User not found")

        if not request_user.is_staff and user != request_user:
            raise serializers.ValidationError(
                "You can only create recurring transactions for yourself."
            )
        if request_user.is_staff and user.is_staff:
            raise serializers.ValidationError(
                "Staff can only create recurring transactions for non-staff users."
            )
        return user

    def validate_amount(self, amount):
        """Validate transaction amount"""
        if amount <= 0:
            raise serializers.ValidationError("Amount must be a positive value.")
        return amount

    def validate_category(self, category):
        """Comprehensive category validation"""
        if category.is_deleted:
            raise serializers.ValidationError("Category not found.")

        user = self._get_recurring_transaction_user()
        transaction_type = self._get_recurring_transaction_type()

        if not category.is_predefined and category.user != user:
            raise serializers.ValidationError(
                "Category does not belong to the provided user."
            )

        if category.type != transaction_type:
            raise serializers.ValidationError(
                "Category type must match the transaction type."
            )

        return category

    def validate_wallet(self, wallet):
        """Comprehensive wallet validation"""
        if wallet.is_deleted:
            raise serializers.ValidationError("Wallet not found.")

        user = self._get_recurring_transaction_user()

        if not user or wallet.user != user:
            raise serializers.ValidationError(
                "Wallet must belong to the specified user."
            )
        return wallet

    def validate_start_date(self, start_date):
        """Validate start date"""
        today = datetime.date.today()
        if start_date.date() < today:
            raise serializers.ValidationError("Start date cannot be in the past.")
        return start_date

    def validate(self, attrs):
        """Cross-field validations"""
        instance = self.instance

        # Validate end_date must be after start_date
        if "end_date" in attrs:
            start_date = attrs.get(
                "start_date", instance.start_date if instance else None
            )
            if attrs["end_date"].date() <= start_date.date():
                raise serializers.ValidationError(
                    {"End_date": "End date must be after start date."}
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Create with next_run set to start_date
        validated_data["next_run"] = validated_data["start_date"]
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        if "start_date" in validated_data:
            # If start_date is updated, set next_run to new start_date
            validated_data["next_run"] = validated_data["start_date"]
        return super().update(instance, validated_data)
