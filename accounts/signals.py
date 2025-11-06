from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
from .models import LoginAttempt


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    LoginAttempt.objects.create(
        email=user.email,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
        successful=True
    )


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    LoginAttempt.objects.create(
        email=credentials.get('username', ''),
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
        successful=False,
        failure_reason='Invalid credentials'
    )
