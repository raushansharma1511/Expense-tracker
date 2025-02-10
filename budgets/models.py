from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from account.models import User
from categories.models import Category
from common.models import BaseModel


class Budget(BaseModel):
    """
    Budget model with threshold crossing detection and spam prevention.
    """

    WARNING_THRESHOLD = Decimal("90.00")
    CRITICAL_THRESHOLD = Decimal("100.00")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="budgets",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="budgets",
    )
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(12),
        ]
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("1"))]
    )

    class Meta:
        ordering = ["-year", "-month"]
