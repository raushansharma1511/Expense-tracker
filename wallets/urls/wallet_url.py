from django.urls import path
from ..views.wallet_view import WalletListCreateView, WalletDetailAPIView


urlpatterns = [
    path("", WalletListCreateView.as_view(), name=""),
    path("<uuid:pk>/", WalletDetailAPIView.as_view()),
]
