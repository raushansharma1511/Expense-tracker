from django.urls import path
from .views import CategoriesView, CategoriesDetailView

urlpatterns = [
    path("", CategoriesView.as_view(), name="categories-view"),
    path("<uuid:pk>/", CategoriesDetailView.as_view(), name="categories-detail-view"),
]
