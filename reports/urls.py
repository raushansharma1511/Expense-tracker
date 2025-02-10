from django.urls import path
from .views import TransactionReportAPI,SpendingTrendsView

urlpatterns = [
    path("", TransactionReportAPI.as_view(), name="transaction-report"),
    path("trends/", SpendingTrendsView.as_view(), name="transaction-report"),
    
]
