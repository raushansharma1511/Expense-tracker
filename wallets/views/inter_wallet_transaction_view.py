from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
from ..models import InterWalletTransaction
from ..serializers.inter_wallet_transaction_serializer import (
    InterWalletTransactionSerializer,
)
from common.permissions import IsStaffOrOwner
from rest_framework.permissions import IsAuthenticated

from common.utils import CustomPagination, validation_error_response, not_found_response


class InterwalletTransactionListCreateView(APIView, CustomPagination):
    """List all transactions or create a new one."""

    def get(self, request):
        """Fetch all transactions (staff can see all, normal users see their own)."""
        if request.user.is_staff:
            transactions = InterWalletTransaction.objects.all().order_by("created_at")
        else:
            transactions = InterWalletTransaction.objects.filter(
                user=request.user, is_deleted=False
            ).order_by("created_at")

        paginated_trasactions = self.paginate_queryset(transactions, request)
        serializer = InterWalletTransactionSerializer(paginated_trasactions, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):
        """Create a new inter-wallet transaction."""
        serializer = InterWalletTransactionSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return validation_error_response(serializer.errors)


class InterwalletTransactionDetailView(APIView):
    """Retrieve, update, or delete an inter-wallet transaction."""

    permission_classes = [IsStaffOrOwner]

    def get_object(self, pk):
        return get_object_or_404(InterWalletTransaction, id=pk)

    def get(self, request, pk):
        """Retrieve transaction details."""
        try:
            transaction = self.get_object(pk)
            self.check_object_permissions(request, transaction)
        except Exception as e:
            return not_found_response("Transaction Not Found")

        serializer = InterWalletTransactionSerializer(transaction)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """Update transaction details (source, destination, amount)."""
        try:
            transaction = self.get_object(pk)
            self.check_object_permissions(request, transaction)
        except Exception as e:
            return not_found_response("Transaction Not Found")

        serializer = InterWalletTransactionSerializer(
            transaction, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return validation_error_response(serializer.errors)

    def delete(self, request, pk):
        """Soft delete a transaction."""
        try:
            transaction = self.get_object(pk)
            self.check_object_permissions(request, transaction)
        except Exception as e:
            return not_found_response("Transaction Not Found")
        
        with db_transaction.atomic():
            # Revert balances
            source_wallet = transaction.source_wallet
            destination_wallet = transaction.destination_wallet

            source_wallet.balance += transaction.amount
            destination_wallet.balance -= transaction.amount

            source_wallet.save(update_fields=["balance"])
            destination_wallet.save(update_fields=["balance"])

            transaction.is_deleted = True
            transaction.save(update_fields=["is_deleted"])
            return Response(status=status.HTTP_204_NO_CONTENT)
