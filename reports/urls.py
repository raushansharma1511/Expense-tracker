from django.urls import path
from .views import (
    TransactionReportAPI,
    SpendingTrendsView,
    TransactionHistoryExportView,
)

urlpatterns = [
    path(
        "transaction-report/", TransactionReportAPI.as_view(), name="transaction-report"
    ),
    path(
        "transaction-report/trends/", SpendingTrendsView.as_view(), name="transaction-trends"
    ),
    path(
        "transaction-report/export/",
        TransactionHistoryExportView.as_view(),
        name="transaction-history-export",
    ),
]
