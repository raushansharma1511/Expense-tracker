from rest_framework import serializers
from .models import Category


# Serializer for Category model
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "user", "is_predefined"]
        read_only_fields = ["id", "user", "is_predefined"]

    def validate_name(self, value):
        """
        Ensure the category name is unique for the user or predefined categories.
        """
        normalized_value = value.strip().lower()

        # Check if a category with the same name already exists
        if (
            Category.objects.filter(
                name__iexact=normalized_value, user=self.context["request"].user
            ).exists()
            or Category.objects.filter(
                name__iexact=normalized_value, is_predefined=True
            ).exists()
        ):
            raise serializers.ValidationError("This category already exists.")
        return value
