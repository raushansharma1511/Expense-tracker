from rest_framework import serializers
from django.db.models import Sum
from django.db import transaction
from decimal import Decimal


from common.utils import is_valid_uuid
from account.models import User
from .models import Transaction, Category


# Serializer for Transaction model
class TransactionSerializer(serializers.ModelSerializer):
    # category = serializers.UUIDField(required=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "type",
            "amount",
            "category",
            "wallet",
            "user",
            "date_time",
            "description",
            "created_at",
            "updated_at",
            "is_deleted",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_deleted"]

    def __init__(self, *args, **kwargs):
        """Ensure user field is ignored silently if present for normal users."""
        super().__init__(*args, **kwargs)
        request = self.context.get("request", None)

        if request and request.method in ["PATCH", "PUT"]:
            self.fields["user"].read_only = True
            self.fields["type"].read_only = True

    def validate_type(self, type_value):
        """
        Validate and set transaction type
        If not provided, default to 'debit'
        """
        return type_value if type_value else "debit"

    def validate_amount(self, amount):
        if amount <= 0:
            raise serializers.ValidationError("Amount must be a positive value.")
        return amount

    def validate_user(self, user):
        """
        Validate user field:
        - User field is mandatory for both staff and normal users
        - Staff can create transactions for non-staff users
        """
        request_user = self.context["request"].user

        if user.is_active == False:
            raise serializers.ValidationError("User not found")

        # Staff validation: can only create for non-staff users
        if not request_user.is_staff and user != request_user:
            raise serializers.ValidationError(
                "You can only create transactions for yourself."
            )
        if request_user.is_staff and user.is_staff:
            raise serializers.ValidationError(
                "Staff can only create transactions for non-staff users."
            )
        return user

    def _get_transaction_user(self):
        """Helper method to get and validate the transaction user based on context."""
        if self.instance:
            return self.instance.user

        if "user" not in self.initial_data:
            return None

        user_id = self.initial_data.get("user")

        if not is_valid_uuid(user_id):
            return None

        user = User.objects.filter(id=user_id, is_active=True).first()
        return user

    def validate_category(self, category):
        """Ensure category belongs to the provided user and matches transaction type"""
        if category.is_deleted:
            raise serializers.ValidationError("Category not found.")

        user = self._get_transaction_user()
        transaction_type = self._get_transaction_type()

        if not category.is_predefined and category.user != user:
            raise serializers.ValidationError(
                "Category does not belong to the provided user."
            )

        if category.type != transaction_type:
            raise serializers.ValidationError(
                "Category type must match the transaction type."
            )

        return category

    def _validate_transaction_amount(self):
        """Helper method to validate transaction amount"""
        amount = self.initial_data.get("amount")
        if not amount:
            return None
        try:
            return Decimal(str(amount))
        except (TypeError, ValueError):
            return None

    def _get_transaction_type(self):
        """Helper method to get transaction type"""
        if self.instance:
            return self.instance.type
        type = self.initial_data.get("type", "debit")
        if not type:
            return "debit"
        return type

    def validate_wallet(self, wallet):
        """Ensure wallet belongs to the provided user and has sufficient balance for debit transactions"""
        if wallet.is_deleted:
            raise serializers.ValidationError("Wallet not found.")

        user = self._get_transaction_user()
        type = self._get_transaction_type()

        if not user or wallet.user != user:
            raise serializers.ValidationError(
                "Wallet must belong to the specified user."
            )
        return wallet

    def validate(self, data):
        """
        Ensure at least one field is provided for partial updates.
        """
        return data

    @transaction.atomic
    def create(self, validated_data):
        if "type" not in validated_data:
            validated_data["type"] = "debit"

        transaction_obj = super().create(validated_data)

        if transaction_obj.type == "credit":
            transaction_obj.wallet.balance += transaction_obj.amount
            transaction_obj.wallet.save()
        else:
            transaction_obj.wallet.balance -= transaction_obj.amount
            transaction_obj.wallet.save()

        return transaction_obj

    @transaction.atomic
    def update(self, instance, validated_data):

        if "amount" in validated_data or "wallet" in validated_data:
            old_wallet = instance.wallet
            old_amount = instance.amount
            new_wallet = validated_data.get("wallet", old_wallet)
            new_amount = validated_data.get("amount", old_amount)

            # Revert old transaction
            if instance.type == "credit":
                old_wallet.balance -= old_amount
            else:
                old_wallet.balance += old_amount
            old_wallet.save()

            new_wallet.refresh_from_db()

            # Apply new transaction
            if instance.type == "credit":
                new_wallet.balance += new_amount
            else:
                new_wallet.balance -= new_amount

            # Only save new wallet if different from old wallet
            if new_wallet != old_wallet:
                new_wallet.save()
            old_wallet.save()

        return super().update(instance, validated_data)


class MonthlySummarySerializer(serializers.Serializer):
    total_credit = serializers.FloatField()
    total_debit = serializers.FloatField()
    balance = serializers.FloatField()
    category_wise = serializers.DictField(child=serializers.DictField())

    @staticmethod
    def calculate_summary(transactions):
        # Calculate overall totals
        total_credit = (
            transactions.filter(type="credit").aggregate(Sum("amount"))["amount__sum"]
            or 0
        )
        total_debit = (
            transactions.filter(type="debit").aggregate(Sum("amount"))["amount__sum"]
            or 0
        )
        balance = total_credit - total_debit

        # Calculate category-wise totals
        category_summary = transactions.values("category__name", "type").annotate(
            total=Sum("amount")
        )
        category_wise = {}

        for entry in category_summary:
            category = (
                entry["category__name"] or "Unknown Category"
            )  # Handle null category
            if category not in category_wise:
                category_wise[category] = {"credit": 0, "debit": 0}
            if entry["type"] == "credit":
                category_wise[category]["credit"] += entry["total"]
            else:
                category_wise[category]["debit"] += entry["total"]

        return {
            "total_credit": total_credit,
            "total_debit": total_debit,
            "balance": balance,
            "category_wise": category_wise,
        }
