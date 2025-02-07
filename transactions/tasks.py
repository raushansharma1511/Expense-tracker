from celery import shared_task
from django.utils import timezone
from budgets.models import Budget
from transactions.models import Transaction
from django.db.models import Sum
from decimal import Decimal
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def track_and_notify_budget(transaction_id):
    """
    Asynchronously track the budget and send a notification if the limit is reached.
    """
    try:
        # Fetch the transaction from the database by ID
        transaction = Transaction.objects.get(id=transaction_id)

        # Get the budget for the category and time of the transaction
        budget = Budget.objects.filter(
            user=transaction.user,
            category=transaction.category,
            year=transaction.date_time.year,
            month=transaction.date_time.month,
            is_deleted=False,
        ).first()

        # Calculate the total spending for the category and time period
        total_spent = Transaction.objects.filter(
            user=transaction.user,
            category=transaction.category,
            date_time__year=transaction.date_time.year,
            date_time__month=transaction.date_time.month,
            is_deleted=False,
        ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0")

        # Check if the spending has exceeded any thresholds
        total_spent_percentage = (total_spent / budget.amount) * 100

        # Check for warning and critical thresholds
        if total_spent_percentage >= budget.CRITICAL_THRESHOLD:
            send_budget_alert(budget, total_spent, transaction.amount)
        elif total_spent_percentage >= budget.WARNING_THRESHOLD:
            send_budget_alert(budget, total_spent, transaction.amount)

    except Transaction.DoesNotExist:
        pass  # No budget for this category/time, so do nothing


def send_budget_alert(budget, total_spent, new_spent):
    """Send an email notification based on budget consumption."""
    percentage = (total_spent / budget.amount) * 100
    remaining_budget = budget.amount - total_spent

    # Subject for both cases
    subject = (
        f"Budget Alert: {budget.category.name} - {percentage:.1f}% of your budget used!"
    )

    # Case when the budget has been exceeded (100% or more)
    if percentage >= 100:
        message = (
            f"Dear {budget.user.name},\n\n"
            f"Your budget for the {budget.category.name} category has been completely consumed or exceeded.\n\n"
            f"Total Budget: {budget.amount}\n"
            f"Amount Used: {total_spent}\n\n"
            "You have exceeded your budget limit. Please review your spending."
            "\n\nBest regards,\nThe Budget Tracker Team"
        )
    # Case when the budget is near its limit (but not exceeded)
    elif percentage >= 90:
        message = (
            f"Dear {budget.user.name},\n\n"
            f"You've used {total_spent} out of your {budget.amount} budget for the {budget.category.name} category.\n\n"
            f"Total Budget: {budget.amount}\n"
            f"Amount Used: {total_spent}\n"
            f"Remaining Budget: {remaining_budget}\n\n"
            f"You’ve used {percentage}% of your budget. Be mindful of your spending to avoid exceeding your limit.\n\n"
            f"Best regards,\nThe Budget Tracker Team"
        )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [budget.user.email],
        fail_silently=False,
    )
