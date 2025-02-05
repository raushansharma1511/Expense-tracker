from django.core.validators import RegexValidator, MinLengthValidator


username_validator = RegexValidator(
    regex=r"^[a-zA-Z0-9_.-]+$",
    message="Username must contain only letters, numbers, underscores, dots, or hyphens.",
    code="invalid_username",
)

phone_number_validator = RegexValidator(
    r"^\+91\d{10}$",  # Matches +91 followed by exactly 10 digits
    "Enter a valid phone number in the format: +912345678904.",
)
