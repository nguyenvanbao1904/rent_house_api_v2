from django.core.mail import send_mail
from RentHouseApi import settings

def send_mails(subject, message, recipients):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=False,
    )
