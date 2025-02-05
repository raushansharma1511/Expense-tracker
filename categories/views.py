from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.response import Response
from django.db.models import Q
from django.db import transaction

from .serializers import CategorySerializer
from .models import Category
from transactions.models import Transaction

from .permissions import CanManageCategories
from common.utils import (
    CustomPagination,
    not_found_response,
    validation_error_response,
)


class CategoryListCreateView(APIView, CustomPagination):
    """view to create and list categories"""

    def get(self, request):
        """
        Retrieve all categories with custom pagination.
        """
        if request.user.is_staff:
            categories = Category.objects.all()
        else:
            categories = Category.objects.filter(is_deleted=False).filter(
                Q(is_predefined=True) | Q(user=request.user)
            )
        # Apply custom pagination
        paginated_categories = self.paginate_queryset(categories, request)
        serializer = CategorySerializer(paginated_categories, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):
        """Add a new category."""
        serializer = CategorySerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return validation_error_response(serializer.errors)


class CategoryDetailView(APIView):
    """Api View to update, view and delete specific category"""

    permission_classes = [CanManageCategories]

    def get_object(self, id):
        """Method to get a specific category object by its id."""
        return Category.objects.get(id=id)

    def get(self, request, pk):
        """Retrieve a specific category."""
        try:
            category = self.get_object(id=pk)
            self.check_object_permissions(request, category)
        except Exception as e:
            return not_found_response("Category not found")
        
        serializer = CategorySerializer(category)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """Update a specific category."""
        try:
            category = self.get_object(pk)
            self.check_object_permissions(request, category)
        except Exception as e:
            return not_found_response("Category not found")

        serializer = CategorySerializer(
            category, data=request.data, context={"request": request}, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return validation_error_response(serializer.errors)

    def delete(self, request, pk):
        """Soft delete a specific category."""
        try:
            category = self.get_object(pk)
            self.check_object_permissions(request, category)
        except Exception as e:
            return not_found_response("Category not found")
        
        with transaction.atomic():  # Use atomic transaction to ensure data consistency
            Transaction.objects.filter(category=category).update(category=None)

        category.is_deleted = True
        category.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
