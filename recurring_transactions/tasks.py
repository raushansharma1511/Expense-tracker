from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from transactions.models import Transaction
from .models import RecurringTransaction
from transactions.tasks import handle_transaction


@shared_task
def send_transaction_notification(
    user_name,
    user_email,
    amount,
    type_name,
    category_name,
    wallet_name,
    transaction_date,
    next_run_date,
):
    """
    Asynchronously send email notification to user about the recurring transaction
    """
    type_name = type_name.upper()

    subject = f"Recurring {type_name} Transaction Processed"

    message = (
        f"Dear {user_name},\n\n"
        f"Your recurring {type_name} transaction has been processed successfully.\n\n"
        f"Transaction Details:\n\n"
        f"Amount: Rs {amount}\n"
        f"Category: {category_name}\n"
        f"Wallet: {wallet_name}\n"
        f"Transaction Date: {transaction_date.strftime('%B %d, %Y')}\n"  # Only showing the date
        f"Next Scheduled Transaction: {next_run_date.strftime('%B %d, %Y')}\n\n"
        f"We are pleased to inform you that your transaction has been processed smoothly.\n"
        f"You can check your transaction history anytime in your account.\n\n"
        f"This is an automated message. Please do not reply to this email.\n\n"
        f"Best regards,\nYour Finance Team"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send email notification: {str(e)}")


@shared_task
def process_recurring_transactions():
    """Process all due recurring transactions"""
    now = timezone.now()

    # Get all non-deleted recurring transactions that are due
    recurring_transactions = RecurringTransaction.objects.filter(
        next_run__lte=now, is_deleted=False
    )

    for rec_txn in recurring_transactions:
        with transaction.atomic():
            # Check if related objects are deleted or if end_date has passed
            if (
                not rec_txn.user.is_active
                or rec_txn.wallet.is_deleted
                or rec_txn.category.is_deleted
                or (
                    rec_txn.end_date
                    and rec_txn.end_date.date() < rec_txn.next_run.date()
                )
            ):

                # Soft delete the recurring transaction
                rec_txn.is_deleted = True
                rec_txn.save()
                continue

            # Create the actual transaction
            new_transaction = Transaction.objects.create(
                user=rec_txn.user,
                wallet=rec_txn.wallet,
                category=rec_txn.category,
                type=rec_txn.type,
                amount=rec_txn.amount,
                date_time=rec_txn.next_run,
                description=rec_txn.description,
            )
            handle_transaction.delay(new_transaction.id)

            # Update wallet balance
            if rec_txn.type == "credit":
                rec_txn.wallet.balance += rec_txn.amount
            else:
                rec_txn.wallet.balance -= rec_txn.amount
            rec_txn.wallet.save()

            # Update next run date
            rec_txn.next_run = rec_txn.get_next_run_date(rec_txn.next_run)
            rec_txn.save()

            rec_txn.refresh_from_db()

            # Send email notification asynchronously
            send_transaction_notification.delay(
                user_name=rec_txn.user.name,
                user_email=rec_txn.user.email,
                amount=str(rec_txn.amount),
                type_name=rec_txn.type,
                category_name=rec_txn.category.name,
                wallet_name=rec_txn.wallet.name,
                transaction_date=new_transaction.date_time,
                next_run_date=rec_txn.next_run,
            )
