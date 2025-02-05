from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


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
