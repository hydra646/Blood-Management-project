from django.test import TestCase
from django.contrib.auth import get_user_model
from core.forms import RegisterForm

User = get_user_model()

class RegistrationDuplicateTests(TestCase):
    def setUp(self):
        # create an existing user
        User.objects.create_user(username='existing', email='exist@example.com', password='pass1234', phone='8801712345678')

    def test_duplicate_username_rejected(self):
        form = RegisterForm(data={
            'username': 'existing',
            'email': 'new@example.com',
            'password': 'pass1234',
            'phone': '01712345678'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_duplicate_email_rejected(self):
        form = RegisterForm(data={
            'username': 'newuser',
            'email': 'exist@example.com',
            'password': 'pass1234',
            'phone': '01712340000'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_phone_rejected_after_normalization(self):
        # existing user phone normalized is '8801712345678'
        form = RegisterForm(data={
            'username': 'newuser2',
            'email': 'unique2@example.com',
            'password': 'pass1234',
            'phone': '017-1234-5678'  # different formatting but same digits
        })
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)
