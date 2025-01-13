from django.db import models
from account.models import User
import uuid


class Category(models.Model):
    """Category model to store categories of transactions"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="categories",
        null=True,
        blank=True,
    )
    is_predefined = models.BooleanField(
        default=False
    )  # To differentiate predefined categories
    is_deleted = models.BooleanField(default=False)  # check category is deleted or not.

    def __str__(self):
        return self.name
