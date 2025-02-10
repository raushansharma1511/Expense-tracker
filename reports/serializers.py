from rest_framework import serializers
from transactions.models import Transaction
from wallets.models import InterWalletTransaction

class TransactionReportSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name')
    wallet = serializers.CharField(source='wallet.name')
    date = serializers.DateTimeField(source='date_time')

    class Meta:
        model = Transaction
        fields = ['category', 'amount', 'wallet', 'date']
    
    def get_date(self, obj):
        return obj.date_time.date()

class InterWalletTransactionReportSerializer(serializers.ModelSerializer):
    source_wallet = serializers.CharField(source='source_wallet.name')
    destination_wallet = serializers.CharField(source='destination_wallet.name')

    class Meta:
        model = InterWalletTransaction
        fields = ['source_wallet', 'destination_wallet', 'amount', 'date']