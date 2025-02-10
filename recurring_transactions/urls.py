from django.urls import path
from .views import RecurringTransactionListCreateView, RecurringTransactionDetailView

urlpatterns = [
    path("", RecurringTransactionListCreateView.as_view(), name="recurring-transactions-list"),
    path("<uuid:id>/", RecurringTransactionDetailView.as_view(), name="recurring-transaction-detail"),
]
