from celery import shared_task
from budgets.models import Budget
from transactions.models import Transaction
from budgets.tasks import track_and_notify_budget

@shared_task
def handle_transaction(transaction_id):
    """
    Asynchronously handle the transaction and trigger budget tracking if a budget exists.
    """
    try:
        # Fetch the transaction from the database by ID
        transaction = Transaction.objects.get(id=transaction_id)

        # Check if a budget exists for this transaction's category and user
        budget = Budget.objects.filter(
            user=transaction.user,
            category=transaction.category,
            year=transaction.date_time.year,
            month=transaction.date_time.month,
            is_deleted=False,
        ).first()

        if budget:
            track_and_notify_budget.delay(budget.id)

    except Transaction.DoesNotExist:
        pass  # No transaction found, do nothing
