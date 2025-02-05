from rest_framework import serializers
from .models import Category
import re
from django.utils.text import slugify


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "user", "is_predefined", "is_deleted", "type"]
        read_only_fields = ["id", "is_predefined", "is_deleted"]

    def __init__(self, *args, **kwargs):
        """Override __init__ to make the user field read-only during patch requests."""
        super().__init__(*args, **kwargs)

        request = self.context.get("request", None)
        if request and request.method == "PATCH":
            # Set the user and type fields as read-only during patch (update) requests
            self.fields["user"].read_only = True
            self.fields["type"].read_only = True

    # def normalize_category_name(self, name: str) -> str:
    #     """Normalize category name by removing extra spaces and punctuation."""
    #     name = name.strip().lower()
    #     name = re.sub(r"[^\w\s]", "", name)
    #     name = re.sub(r"\s+", " ", name)
    #     return name

    def validate_user(self, user):
        """Validate the user field."""
        request = self.context["request"]

        if user.is_active == False:
            raise serializers.ValidationError("User not found")

        if not request.user.is_staff:
            if request.user != user:
                raise serializers.ValidationError(
                    "You can create categories for yourself only."
                )
        else:
            if user != request.user and user.is_staff:
                raise serializers.ValidationError(
                    "You cannot create a category on behalf of other staff user"
                )

        return user

    def _validate_category_name(self, value, user, type):
        """Ensure the category name is unique for the user or predefined categories."""
        normalized_value = slugify(value)

        if (
            Category.objects.filter(
                name__iexact=normalized_value, user=user, is_deleted=False, type=type
            ).exists()
            or Category.objects.filter(
                name__iexact=normalized_value,
                is_predefined=True,
                is_deleted=False,
                type=type
            ).exists()
        ):
            raise serializers.ValidationError({"name": "This category already exists."})
        return normalized_value

    def validate(self, data):
        """
        Validate category data, ensuring the name and user fields are correct.
        """
        request = self.context["request"]
        # category_name = data["name"]

        if self.instance is None:
            # when there is create request
            user = data.get("user")

            if "name" in data:
                data["name"] = self._validate_category_name(data["name"], user,data["type"])

            data["user"] = user
            data["is_predefined"] = user.is_staff

        else:
            # when there is update request
            if "name" in data:  # Only validate name if provided
                data["name"] = self._validate_category_name(
                    data["name"], self.instance.user,self.instance.type
                )

        return data

    def create(self, validated_data):
        """Create a new category."""
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update an existing category."""
        return super().update(instance, validated_data)
