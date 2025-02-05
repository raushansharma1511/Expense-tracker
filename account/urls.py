# account/urls.py
from django.urls import path
from .views import (
    UpdatePasswordView,
    UserDetailView,
    RegisterView,
    LoginView,
    LogoutView,
    UserListView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path(
        "auth/password-reset/",
        PasswordResetRequestView.as_view(),
        name="password-reset",
    ),
    path("auth/password-reset/confirm/<str:uidb64>/<str:token>/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("users/", UserListView.as_view(), name="get-users"),
    path("users/<uuid:id>/", UserDetailView.as_view(), name="get-update-delete-user"),
    path(
        "users/<uuid:id>/change-password/",
        UpdatePasswordView.as_view(),
        name="change-password",
    ),
]
