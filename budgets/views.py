from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from common.permissions import IsStaffOrOwner
from common.utils import (
    validation_error_response,
    not_found_response,
    CustomPagination,
)
from .models import Budget
from .serializers import BudgetSerializer



class BudgetListCreateView(APIView, CustomPagination):
    """Api view to list all budgets or create a new one"""

    def get(self, request):
        """List all budgets with optional filters"""

        if request.user.is_staff:
            budgets = Budget.objects.all()
        else:
            budgets = Budget.objects.filter(user=request.user, is_deleted=False)

        paginated_budgets = self.paginate_queryset(budgets, request)
        serializer = BudgetSerializer(paginated_budgets, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):
        """Create a new budget"""
        serializer = BudgetSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return validation_error_response(serializer.errors)


class BudgetDetailView(APIView):
    """Api view to retrieve, update or delete a budget"""
    permission_classes = [IsStaffOrOwner]

    def _get_object(self, pk):
        """Get budget object with proper filtering"""
        return get_object_or_404(Budget, id=pk)

    def get(self, request, pk):
        """Retrieve a specific budget"""
        try:
            budget = self._get_object(pk)
            self.check_object_permissions(request, budget)

            serializer = BudgetSerializer(budget)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return not_found_response("Budget not found")

    def patch(self, request, pk):
        """Update a budget"""
        try:
            budget = self._get_object(pk)
            self.check_object_permissions(request, budget)
            serializer = BudgetSerializer(
                budget, data=request.data, context={"request": request}, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return validation_error_response(serializer.errors)
        except Exception as e:
            return not_found_response("Budget not found")

    def delete(self, request, pk):
        """Soft delete a budget"""
        try:
            budget = self._get_object(pk)
            self.check_object_permissions(request, budget)
            budget.is_deleted = True
            budget.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return not_found_response("Budget not found")
