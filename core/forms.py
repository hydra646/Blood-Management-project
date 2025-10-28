from django import forms
from django.contrib.auth import get_user_model
from .models import DonationRequest, BLOOD_GROUPS, BloodBank

User = get_user_model()

import re

def normalize_phone(phone: str) -> str:
    """
    Normalize phone numbers to a digits-only form for uniqueness checks.
    - strips non-digit characters
    - converts leading 0 (local mobile) to country code 88 (e.g., 017... -> 88017...)
    - leaves already prefixed country codes intact
    Note: This stores digits only (no +). Adjust if you prefer +E.164.
    """
    if not phone:
        return ''
    digits = re.sub(r"\D+", "", phone)
    if digits.startswith('0'):
        # common local format like 017xxxxxxxx -> 88017xxxxxxxx
        digits = '88' + digits
    # if it's 10 digits (no leading 0) assume local and prefix 88
    if len(digits) == 10:
        digits = '88' + digits
    return digits

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=6)
    role = forms.ChoiceField(choices=[('donor','Donor'),('hospital','Hospital')], initial='donor')
    class Meta:
        model = User
        # prevent users from registering as admin via frontend
        fields = ('username','email','password','first_name','last_name','phone','city','blood_group','profile_photo')

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get('username')
        email = cleaned.get('email')
        phone = cleaned.get('phone')
        # normalize phone for consistent uniqueness checks
        if phone:
            phone = normalize_phone(phone)
            cleaned['phone'] = phone

        if username and User.objects.filter(username=username).exists():
            self.add_error('username','A user with that username already exists.')
        if email and User.objects.filter(email=email).exists():
            self.add_error('email','A user with that email already exists.')
        if phone:
            # phone field may be blank; only check when provided
            if User.objects.filter(phone=phone).exists():
                self.add_error('phone','This phone number is already used by another account.')

        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        # set role from the form (donor or hospital). Admin is not allowed via frontend.
        user.role = self.cleaned_data.get('role','donor')
        # By default, activate users immediately (no email confirmation required)
        user.is_active = True
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name','last_name','phone','city','blood_group','profile_photo')

    def clean(self):
        cleaned = super().clean()
        phone = cleaned.get('phone')
        if phone:
            cleaned['phone'] = normalize_phone(phone)
        return cleaned


class BloodBankForm(forms.ModelForm):
    class Meta:
        model = BloodBank
        fields = ('name','city','address','contact')

User = get_user_model()

class AdminUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username','email','first_name','last_name','role','phone','city','blood_group')

class DonationRequestForm(forms.ModelForm):
    class Meta:
        model = DonationRequest
        fields = ('blood_group','units','city')
    def clean_units(self):
        u = self.cleaned_data['units']
        if u <= 0:
            raise forms.ValidationError('Units must be > 0')
        return u
    def clean(self):
        cleaned = super().clean()
        # prevent duplicate pending request - requires request in view; handled in serializer for API
        return cleaned
