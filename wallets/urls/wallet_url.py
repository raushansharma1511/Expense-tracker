from django.urls import path
from ..views.wallet_view import WalletListCreateView, WalletDetailAPIView


urlpatterns = [
    path("", WalletListCreateView.as_view(), name="wallet-list-create-view"),
    path("<uuid:pk>/", WalletDetailAPIView.as_view(),name="wallet-detail-view"),
]
