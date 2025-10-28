from django.core.management.base import BaseCommand, CommandError
from core.models import User
from django.core.cache import cache
from django.conf import settings
from django.core.mail import send_mail
import random

class Command(BaseCommand):
    help = 'Send a 6-digit verification code to the given user email (for testing)'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='The user email to send the code to')

    def handle(self, *args, **options):
        email = options['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError('User with that email not found')

        code = f"{random.randint(0, 999999):06d}"
        cache_key = f"email_code:{user.pk}"
        cache.set(cache_key, code, 180)
        subject = 'Your verification code'
        body = f"Hi {user.get_full_name() or user.username},\n\nUse the following 6-digit code to confirm your email address:\n\n{code}\n\nThis code will expire in 3 minutes. If you didn't request this, ignore this email.\n"

        # Don't suppress SMTP errors here — we want to see them during testing
        send_mail(subject, body, getattr(settings, 'DEFAULT_FROM_EMAIL', 'webmaster@localhost'), [user.email], fail_silently=False)
        self.stdout.write(self.style.SUCCESS(f'Verification code sent to {email} (code: {code})'))
