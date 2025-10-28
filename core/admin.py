from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, BloodBank, BloodInventory, DonationRequest, Donation
# Restrict access to the Django admin UI to Django superusers only.
# By default Django allows any user with is_staff=True to log in to the admin.
# We override the AdminSite.has_permission method so only is_superuser users
# (and active) can access the admin pages. This preserves existing model
# registrations (we're monkey-patching the existing admin.site instance).
def _admin_has_permission(request):
    return bool(request.user and request.user.is_active and request.user.is_superuser)

admin.site.has_permission = _admin_has_permission

# Replace the admin login form so that only Django superusers may log in via
# the admin login page. The default AdminAuthenticationForm enforces
# is_active and is_staff; we replace the check to require is_superuser.
from django.contrib.admin.forms import AdminAuthenticationForm
from django import forms


class SuperuserAdminAuthenticationForm(AdminAuthenticationForm):
    def confirm_login_allowed(self, user):
        # Only allow active superusers to login to Django admin.
        if not (user and user.is_active and user.is_superuser):
            raise forms.ValidationError(
                "This account does not have access to the admin site.",
                code="no_admin",
            )


admin.site.login_form = SuperuserAdminAuthenticationForm


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'blood_group', 'city')

admin.site.register(BloodBank)
admin.site.register(BloodInventory)
admin.site.register(DonationRequest)
admin.site.register(Donation)
