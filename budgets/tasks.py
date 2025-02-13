from celery import shared_task
from budgets.models import Budget
from transactions.models import Transaction
from django.db.models import Sum
from decimal import Decimal
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def track_and_notify_budget(budget_id):
    """
    Asynchronously track the budget and send a notification if the limit is reached.
    """
    try:
        budget = Budget.objects.get(id=budget_id, is_deleted=False)
        
        total_spent = Transaction.objects.filter(
            user=budget.user,
            category=budget.category,
            date_time__year=budget.year,
            date_time__month=budget.month,
            is_deleted=False,
        ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0")

        total_spent_percentage = (total_spent / budget.amount) * 100

        # Check for warning and critical thresholds
        if total_spent_percentage >= budget.CRITICAL_THRESHOLD:
            send_budget_alert(budget, total_spent)
        elif total_spent_percentage >= budget.WARNING_THRESHOLD:
            send_budget_alert(budget, total_spent)

    except Budget.DoesNotExist:
        pass


def send_budget_alert(budget, total_spent):
    """Send an email notification based on budget consumption."""
    percentage = (total_spent / budget.amount) * 100
    remaining_budget = budget.amount - total_spent

    subject = (
        f"Budget Alert: {budget.category.name}"
    )

    # Message content when budget has been exceeded
    if percentage >= 100:
        message = (
            f"Dear {budget.user.name},\n\n"
            f"Your budget for the {budget.category.name} category has been completely consumed or exceeded.\n\n"
            f"Total Budget: Rs {budget.amount}\n"
            f"Amount Used: Rs {total_spent}\n\n"
            "You have exceeded your budget limit. Please review your spending."
            "\n\nBest regards,\nThe Budget Tracker Team"
        )
    # Message content when budget is near its limit (but not exceeded)
    else:
        message = (
            f"Dear {budget.user.name},\n\n"
            f"You've used Rs {total_spent} out of your Rs {budget.amount} budget for the {budget.category.name} category.\n\n"
            f"Total Budget: Rs {budget.amount}\n"
            f"Amount Used: Rs {total_spent}\n"
            f"Remaining Budget: {remaining_budget}\n\n"
            f"You’ve used {percentage:.2f}% of your budget. Be mindful of your spending to avoid exceeding your limit.\n\n"
            f"Best regards,\nThe Budget Tracker Team"
        )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [budget.user.email],
        fail_silently=False,
    )
