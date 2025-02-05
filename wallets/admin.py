from django.contrib import admin
from .models import Wallet, InterWalletTransaction

# Register your models here.

admin.site.register(Wallet)
admin.site.register(InterWalletTransaction)
