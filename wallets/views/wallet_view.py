from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from ..models import Wallet, InterWalletTransaction
from transactions.models import Transaction
from ..serializers.wallet_serializer import WalletSerializer

# from .permissions import IsOwnerOrStaffManagingOthers

from common.utils import (
    validation_error_response,
    CustomPagination,
    not_found_response,
)
from common.permissions import IsStaffOrOwner


class WalletListCreateView(APIView, CustomPagination):
    # permission_classes = [IsOwnerOrStaffManagingOthers]

    def get(self, request):
        """Retrieve wallets (Staff see all, normal users see their own)"""
        if request.user.is_staff:
            wallets = Wallet.objects.filter(is_deleted=False)
        else:
            wallets = Wallet.objects.filter(user=request.user, is_deleted=False)

        paginated_wallets = self.paginate_queryset(wallets, request)
        serializer = WalletSerializer(paginated_wallets, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):
        """Create wallet (Staff must assign to another user)"""
        serializer = WalletSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return validation_error_response(serializer.errors)


class WalletDetailAPIView(APIView):
    """Retrieve, Update, and Soft Delete Wallets"""

    permission_classes = [IsStaffOrOwner]

    def get_object(self, pk, request):
        """Retrieve wallet object"""
        return get_object_or_404(Wallet, id=pk)

    def get(self, request, pk):
        """Retrieve a single wallet"""
        try:
            wallet = self.get_object(pk, request)
            self.check_object_permissions(request, wallet)
        except Exception as e:
            return not_found_response("Object Not Found")

        serializer = WalletSerializer(wallet)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """Update wallet details (Normal: only name, Staff: can change user if no transactions exist)"""
        try:
            wallet = self.get_object(pk, request)
            self.check_object_permissions(request, wallet)
        except Exception as e:
            return not_found_response("Object Not Found")

        serializer = WalletSerializer(
            wallet, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return validation_error_response(serializer.errors)

    def delete(self, request, pk):
        """Soft delete a wallet (Only if balance is 0)"""
        try:
            wallet = self.get_object(pk, request)
            self.check_object_permissions(request, wallet)
        except Exception as e:
            return not_found_response("Object Not Found")

        if wallet.balance != 0:
            return Response(
                {"error": "Cannot delete wallet with non-zero balance."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            InterWalletTransaction.objects.filter(
                source_wallet=wallet, is_deleted=False
            ).exists()
            or InterWalletTransaction.objects.filter(
                destination_wallet=wallet, is_deleted=False
            ).exists()
            or Transaction.objects.filter(wallet=wallet, is_deleted=False).exists()
        ):
            return Response(
                {
                    "error": "Cannot delete this wallet as there are existing transactions associated with it."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        wallet.is_deleted = True
        wallet.save()
        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )
