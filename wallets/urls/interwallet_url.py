from django.urls import path
from ..views.inter_wallet_transaction_view import (
    InterwalletTransactionListCreateView,
    InterwalletTransactionDetailView,
)

urlpatterns = [
    path(
        "",
        InterwalletTransactionListCreateView.as_view(),
        name="transaction-list-create",
    ),
    path(
        "<uuid:pk>/",
        InterwalletTransactionDetailView.as_view(),
        name="transaction-retrieve-update-delete",
    ),
    # path("history/", views.InterwalletTransactionHistoryView.as_view(), name="transaction-history"),
]
