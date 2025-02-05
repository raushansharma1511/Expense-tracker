from django.db import models
from account.models import User
import uuid
from common.base import BaseModel


class Category(BaseModel):
    """Category model to store categories of transactions"""
    CATEGORY_TYPES = (
        ("debit", "Debit"),
        ("credit", "Credit"),
    )
    name = models.CharField(max_length=100)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    is_predefined = models.BooleanField(
        default=False
    )  # To differentiate predefined categories

    def __str__(self):
        return self.name
