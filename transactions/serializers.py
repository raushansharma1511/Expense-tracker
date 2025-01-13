from rest_framework import serializers
from .models import Transaction, Category
from datetime import datetime, date


# Serializer for Transaction model
class TransactionSerializer(serializers.ModelSerializer):
    # category = serializers.UUIDField()

    class Meta:
        model = Transaction
        fields = ["id", "type", "amount", "date", "category", "description", "user"]
        read_only_fields = ["user"]  # Automatically set user based on request

    def validate_category(self, category):
        """
        Validates the category field to ensure proper permissions and state.
        """
        print("hello2")
        if category:
            request_user = self.context["request"].user
            if (
                not category.is_predefined
                and category.user != request_user
                or category.is_deleted
            ):
                raise serializers.ValidationError(
                    "You do not have permission to use this category."
                )
        return category

    def create(self, validated_data):
        # create transaction with validated data
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # update transaction with validated data
        return super().update(instance, validated_data)
