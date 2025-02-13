from django.db import models
from common.models import BaseModel # Import BaseModel from base.py
from account.models import User


# Wallet Model
class Wallet(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets')
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

# InterWalletTransaction Model
class InterWalletTransaction(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interwallet_transactions")
    source_wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="source_transactions")
    destination_wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="destination_transactions")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date_time = models.DateTimeField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user} | {self.source_wallet} -> {self.destination_wallet} | {self.amount}"
