from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
from .models import Transaction, Category
from .serializers import TransactionSerializer
from common.utils import (
    CustomPagination,
    validation_error_response,
    not_found_response,
)
from common.permissions import IsStaffOrOwner
from .tasks import track_and_notify_budget


# View for listing and creating transactions
class TransactionListCreateView(APIView, CustomPagination):
    """Api view for listing all transactions and creating a new transaction"""

    def get(self, request):
        """
        Get method to list all transactions for a particular user and staff user can access all the transactions.
        """
        if request.user.is_staff:
            queryset = Transaction.objects.all().order_by("-date_time")
        else:
            queryset = Transaction.objects.filter(
                user=request.user, is_deleted=False
            ).order_by("-date_time")

        paginated_data = self.paginate_queryset(queryset, request)
        serializer = TransactionSerializer(paginated_data, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):
        """Post method to create a new transaction."""

        serializer = TransactionSerializer(
            data=request.data, context={"request": request}
        )  # Pass request to context

        if serializer.is_valid():
            transaction = serializer.save()
            track_and_notify_budget.delay(transaction.id)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        return validation_error_response(serializer.errors)


class TransactionDetailView(APIView):
    """Api view for retrieving, updating, deleting a specific transaction"""

    permission_classes = [IsStaffOrOwner]

    def get_object(self, id):
        """Helper method to get the transaction object by primary key"""
        return get_object_or_404(Transaction, id=id)

    def get(self, request, id):
        """Get method to retrieve a specific transaction by its id"""
        try:
            transaction = self.get_object(id)
            self.check_object_permissions(request, transaction)
        except Exception as e:
            return not_found_response("Transaction not found.")

        serializer = TransactionSerializer(transaction)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id):
        """update a specific transaction."""
        try:
            transaction = self.get_object(id)
            self.check_object_permissions(request, transaction)
        except Exception as e:
            return not_found_response("Transaction not found.")

        serializer = TransactionSerializer(
            transaction, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            transaction = serializer.save()
            track_and_notify_budget.delay(transaction.id)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return validation_error_response(serializer.errors)

    def delete(self, request, id):
        """Delete a specific transaction by id"""
        try:
            transaction = self.get_object(id)
            self.check_object_permissions(request, transaction)
        except Exception as e:
            return not_found_response("Transaction not found.")

        wallet = transaction.wallet
        with db_transaction.atomic():  # Ensure atomicity
            if transaction.type == "debit":
                wallet.balance += transaction.amount  # Revert deduction
            else:
                wallet.balance -= transaction.amount  # Revert addition
                if wallet.balance < 0:
                    wallet.balance = 0

            wallet.save()
            transaction.is_deleted = True
            transaction.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

