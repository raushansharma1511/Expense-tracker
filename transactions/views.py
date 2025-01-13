from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied

from django.db.models import Sum
from datetime import datetime, timedelta
from .models import Transaction, Category
from .serializers import TransactionSerializer


# View for listing and creating transactions
class TransactionListCreateView(APIView):
    """Api view for listing all transactions and creating a new transaction"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get method to list all transactions for a particular user and staff user can access all the transactions.
        """

        paginator = PageNumberPagination()  # Instantiate the paginator
        paginator.page_size = 10  # Override the default page size

        if request.user.is_staff:
            transactions = Transaction.objects.all()
        else:
            transactions = Transaction.objects.filter(
                user=request.user, is_deleted=False
            )

        # Paginate the queryset
        paginated_transactions = paginator.paginate_queryset(transactions, request)
        serializer = TransactionSerializer(paginated_transactions, many=True)

        # Return paginated response
        return paginator.get_paginated_response(serializer.data)

    # Create a new transaction
    def post(self, request):
        """
        Post method to create a new transaction.
        """
        serializer = TransactionSerializer(
            data=request.data, context={"request": request}
        )  # Pass request to context

        if serializer.is_valid():
            serializer.save(user=request.user)  # Automatically set the user
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(
            {
                "messege": "Invalid data provided",
                "error": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


# View for retrieving, updating, or deleting a specific transaction
class TransactionDetailView(APIView):
    """Api view for retrieving, updating, deleting a specific transaction"""

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):
        """Helper method to get the transaction object by primary key"""

        try:
            transaction = Transaction.objects.get(pk=pk, is_deleted=False)
            if transaction.user == request.user or request.user.is_staff:
                return transaction
            else:
                raise PermissionDenied(
                    "You do not have permission to access this transaction."
                )
        except Transaction.DoesNotExist:
            return None

    def get(self, request, pk):
        """Get method to retrieve a specfic transaction by its id"""

        transaction = self.get_object(pk, request)
        if transaction:
            serializer = TransactionSerializer(transaction)
            return Response(serializer.data)
        return Response(
            {"error": "Transaction not found or access denied."},
            status=status.HTTP_404_NOT_FOUND,
        )

    def put(self, request, pk):
        """
        Fully update a specific transaction.
        Requires all parameters to be passed in the request.
        """
        transaction = self.get_object(pk, request)
        if transaction:
            serializer = TransactionSerializer(
                transaction,
                data=request.data,
                context={"request": request},
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"error": "Transaction not found or access denied."},
            status=status.HTTP_404_NOT_FOUND,
        )

    def patch(self, request, pk):
        """
        Partially update a specific transaction.
        Allows updating only specific fields.
        """
        print("called patch update")
        transaction = self.get_object(pk, request)
        if transaction:
            serializer = TransactionSerializer(
                transaction, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"error": "Transaction not found or access denied."},
            status=status.HTTP_404_NOT_FOUND,
        )

    def delete(self, request, pk):
        """
        Delete a specific transction by id
        """
        transaction = self.get_object(pk, request)
        if transaction:
            transaction.is_deleted = True
            transaction.save()
            return Response(
                {"messege": "Transaction deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        return Response(
            {"error": "Transaction not found or access denied."},
            status=status.HTTP_404_NOT_FOUND,
        )


class MonthlySummaryView(APIView):
    """
    view for the showing the monthly summary report of income , expense and balance of user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the current month and year
        today = datetime.today()
        start_of_month = today.replace(day=1)
        end_of_month = (today.replace(day=28) + timedelta(days=4)).replace(
            day=1
        ) - timedelta(days=1)

        # Filter transactions for the current user and the current month
        transactions = Transaction.objects.filter(
            user=request.user,
            date__gte=start_of_month,
            date__lte=end_of_month,
            is_deleted=False,
        )

        # Calculate total income, total expenses, and balance
        total_income = (
            transactions.filter(type="income").aggregate(Sum("amount"))["amount__sum"]
            or 0
        )
        total_expense = (
            transactions.filter(type="expense").aggregate(Sum("amount"))["amount__sum"]
            or 0
        )
        balance = total_income - total_expense

        summary = {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
        }

        return Response(summary)
