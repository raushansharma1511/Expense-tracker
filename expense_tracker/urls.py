"""
URL configuration for expense_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from account.views import HealthCheckView


schema_view = get_schema_view(
    openapi.Info(
        title="Expense Tracker API",
        default_version="v1",
        description="API documentation for my Django project",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="raushan@gkmit.co"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="swagger-docs"
    ),
    path("api/", include("account.urls")),
    path("api/transactions/", include("transactions.urls")),
    path("api/categories/", include("categories.urls")),
    path("api/wallets/", include("wallets.urls.wallet_url")),
    path("api/budgets/", include("budgets.urls")),
    path("api/interwallet-transactions/", include("wallets.urls.interwallet_url")),
    path("api/recurring-transactions/", include("recurring_transactions.urls")),
    path("api/", include("reports.urls")),
    path("api/health-check/", HealthCheckView.as_view(), name="health-check"),
]
