from django.core.validators import RegexValidator, MinLengthValidator
from rest_framework.serializers import ValidationError
import re


username_validator = RegexValidator(
    regex=r"^[a-zA-Z0-9_.-]+$",
    message="Username must contain only letters, numbers, underscores, dots, or hyphens.",
    code="invalid_username",
)

phone_number_validator = RegexValidator(
    r"^\+91\d{10}$",  # Matches +91 followed by exactly 10 digits
    "Enter a valid phone number in the format: +91XXXXXXXXXX.",
)

def validate_password(value):
        """
        Validates the password with the following conditions:
        - Must be at least 8 characters long.
        - Must contain at least one letter.
        - Must contain at least one digit.
        - Must contain at least one special character.
        """
        min_length = 8
        special_char_pattern = r'[!@#$%^&*(),.?":{}|<>]'
        digit_pattern = r'\d'
        letter_pattern = r'[a-zA-Z]'

        # Check if password length is at least 8 characters
        if len(value) < min_length:
            raise ValidationError("Password must be at least 8 characters long.")

        # Check if password contains at least one letter
        if not re.search(letter_pattern, value):
            raise ValidationError("Password must contain at least one letter.")

        # Check if password contains at least one digit
        if not re.search(digit_pattern, value):
            raise ValidationError("Password must contain at least one digit.")

        # Check if password contains at least one special character
        if not re.search(special_char_pattern, value):
            raise ValidationError("Password must contain at least one special character.")

        return value