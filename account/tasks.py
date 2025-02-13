from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from .models import User
from .tokens import TokenHandler


@shared_task
def send_reset_password_email(email, reset_link):
    print(f"Sending email to {email} with reset link: {reset_link}")
    subject = "Password Reset Request"
    message = f"Click on the link below to reset your password:\n{reset_link}"
    recepient_list = [email]
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recepient_list,
        fail_silently=False,
    )


@shared_task
def soft_delete_user_related_objects(user_id):
    try:

        user = User.objects.get(id=user_id)

        # Start a transaction to ensure data consistency
        with transaction.atomic():
            user.categories.update(is_deleted=True)

            user.transactions.update(is_deleted=True)

            user.budgets.update(is_deleted=True)

            user.wallets.update(is_deleted=True)

            user.recurring_transactions.update(is_deleted=True)

            user.interwallet_transactions.update(is_deleted=True)

            TokenHandler.invalidate_user_tokens(user)

        return f"User {user_id} and related objects soft deleted."

    except User.DoesNotExist:
        return f"User {user_id} does not exist."
    except Exception as e:
        return str(e)
