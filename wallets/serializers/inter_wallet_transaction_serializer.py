from rest_framework import serializers
from wallets.models import InterWalletTransaction
from wallets.models import Wallet
from account.models import User
from django.db import transaction as db_transaction
from common.utils import is_valid_uuid
from django.db import IntegrityError



class InterWalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterWalletTransaction
        fields = [
            "id",
            "user",
            "source_wallet",
            "destination_wallet",
            "amount",
            "description",
            "date_time",
            "is_deleted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_deleted", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        """Ensure user field is ignored silently if present for normal users."""
        super().__init__(*args, **kwargs)
        request = self.context.get("request", None)

        if request and request.method in ["PATCH", "PUT"]:
            self.fields["user"].read_only = True

    def validate_user(self, user):
        """Ensure staff can only create transactions for others, and normal users for themselves."""
        request_user = self.context["request"].user
        
        if user.is_active == False:
            raise serializers.ValidationError("User not found")

        if request_user.is_staff:
            if user.is_staff or request_user == user:
                raise serializers.ValidationError(
                    "Staff cannot create transactions for themselves."
                )
        else:
            if request_user != user:
                raise serializers.ValidationError(
                    "You can only create transactions for yourself."
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

    def validate_source_wallet(self, source_wallet):
        """Ensure the source wallet belongs to the correct user."""

        transaction_user = self._get_transaction_user()

        if source_wallet.is_deleted:
            raise serializers.ValidationError("Source wallet not found.")

        if source_wallet.user != transaction_user:
            raise serializers.ValidationError(
                "The source wallet does not belong to the transaction user."
            )

        return source_wallet

    def validate_destination_wallet(self, destination_wallet):
        """Ensure the destination wallet belongs to the correct user."""

        transaction_user = self._get_transaction_user()

        if destination_wallet.is_deleted:
            raise serializers.ValidationError("Destination wallet not found.")

        if destination_wallet.user != transaction_user:
            raise serializers.ValidationError(
                "The destination wallet does not belong to the transaction user."
            )

        return destination_wallet

    def validate_amount(self, amount):
        """Ensure the transaction amount is greater than zero."""
        if amount <= 0:
            raise serializers.ValidationError(
                "Transaction amount must be greater than zero."
            )
        return amount

    def validate(self, data):
        """Perform all object-level validations."""

        instance = self.instance  # Get the existing transaction if updating
        user = self.context["request"].user

        # Get updated fields or keep existing ones
        source_wallet = data.get(
            "source_wallet", instance.source_wallet if instance else None
        )
        destination_wallet = data.get(
            "destination_wallet", instance.destination_wallet if instance else None
        )
        amount = data.get("amount", instance.amount if instance else None)

        # Prevent same source and destination wallets
        if source_wallet == destination_wallet:
            raise serializers.ValidationError(
                {
                    "source_wallet": "Source wallet cannot be the same as destination wallet."
                }
            )

        return data

    def create(self, validated_data):
        """Create a new inter-wallet transaction and update wallet balances atomically."""
        with db_transaction.atomic():
            source_wallet = validated_data["source_wallet"]
            destination_wallet = validated_data["destination_wallet"]
            amount = validated_data["amount"]

            # Deduct from source wallet
            with db_transaction.atomic():
                source_wallet.balance -= amount
                source_wallet.save()

                # Add to destination wallet
                destination_wallet.balance += amount
                destination_wallet.save()

                return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update an existing transaction and auto-adjust wallet balances."""

        with db_transaction.atomic():
            old_amount = instance.amount
            new_amount = validated_data.get("amount", old_amount)
            source_wallet = validated_data.get("source_wallet", instance.source_wallet)
            destination_wallet = validated_data.get(
                "destination_wallet", instance.destination_wallet
            )

            # If source/destination wallet is changing, adjust balances
            if (
                source_wallet != instance.source_wallet
                or destination_wallet != instance.destination_wallet
                or new_amount != old_amount
            ):

                # Revert old transaction
                instance.source_wallet.balance += old_amount
                instance.destination_wallet.balance -= old_amount
                instance.source_wallet.save()
                instance.destination_wallet.save()

                source_wallet.refresh_from_db()
                destination_wallet.refresh_from_db()

                # Apply new transaction
                source_wallet.balance -= new_amount
                destination_wallet.balance += new_amount
                source_wallet.save()
                destination_wallet.save()

            return super().update(instance, validated_data)
