from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction

from .models import RecurringTransaction
from .serializers import RecurringTransactionSerializer
from common.utils import CustomPagination, validation_error_response, not_found_response
from common.permissions import IsStaffOrOwner


class RecurringTransactionListCreateView(APIView, CustomPagination):
    """Comprehensive list and create view for recurring transactions"""

    def get(self, request):
        """List recurring transactions with comprehensive filtering"""
        if request.user.is_staff:
            queryset = RecurringTransaction.objects.all().order_by("-created_at")
        else:
            queryset = RecurringTransaction.objects.filter(
                user=request.user, is_deleted=False
            ).order_by("-created_at")

        paginated_data = self.paginate_queryset(queryset, request)
        serializer = RecurringTransactionSerializer(paginated_data, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):
        """Create a new recurring transaction"""
        serializer = RecurringTransactionSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        return validation_error_response(serializer.errors)


class RecurringTransactionDetailView(APIView):
    """Comprehensive detail view for recurring transactions"""

    permission_classes = [IsStaffOrOwner]

    def get_object(self, id, request):
        """Retrieve recurring transaction with comprehensive permissions"""
        return get_object_or_404(RecurringTransaction, id=id)

    def get(self, request, id):
        """Retrieve specific recurring transaction"""
        try:
            recurring_transaction = self.get_object(id, request)
            self.check_object_permissions(request, recurring_transaction)
            serializer = RecurringTransactionSerializer(recurring_transaction)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return not_found_response("Recurring Transaction not found.")

    def patch(self, request, id):
        """Update specific recurring transaction"""
        try:
            recurring_transaction = self.get_object(id, request)
            self.check_object_permissions(request, recurring_transaction)
            serializer = RecurringTransactionSerializer(
                recurring_transaction,
                data=request.data,
                partial=True,
                context={"request": request},
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return validation_error_response(serializer.errors)

        except Exception as e:
            return not_found_response("Recurring Transaction not found.")

    def delete(self, request, id):
        """Soft delete recurring transaction"""
        try:
            recurring_transaction = self.get_object(id, request)
            self.check_object_permissions(request, recurring_transaction)
            with db_transaction.atomic():
                recurring_transaction.is_deleted = True
                recurring_transaction.save()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            return not_found_response("Recurring Transaction not found.")
