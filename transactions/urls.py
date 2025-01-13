from django.urls import path
from .views import TransactionListCreateView, TransactionDetailView, MonthlySummaryView

urlpatterns = [
    path("", TransactionListCreateView.as_view(), name="transaction-list-create"),
    path("<uuid:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
    path("monthly-summary/", MonthlySummaryView.as_view(), name="monthly-summary"),
]
