from django.db import models
from django.utils import timezone
from account.models import User
from categories.models import Category
from wallets.models import Wallet
from common.models import BaseModel
import uuid


class Transaction(BaseModel):
    TYPE_CHOICES = [
        ("credit", "Credit"),  # credit, debit
        ("debit", "Debit"),
    ]
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transactions"
    )
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="transactions"
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="debit")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="transactions"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_time = models.DateTimeField(default=timezone.now)  # default to today's date
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user} - {self.type} - {self.amount}"
