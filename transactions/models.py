# transactions/models.py
from django.db import models
from account.models import User
from categories.models import Category
import uuid


# Transaction model to store income and expenses
class Transaction(models.Model):
    TYPE_CHOICES = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transactions"
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.type.capitalize()} - {self.amount} ({self.category})"
