from django.urls import path
from . import frontend_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', frontend_views.home, name='home'),
    path('register/', frontend_views.register_view, name='register'),
    path('login/', frontend_views.login_view, name='login'),
    path('logout/', frontend_views.logout_view, name='logout'),
    path('donor/dashboard/', frontend_views.donor_dashboard, name='donor-dashboard'),
    path('hospital/dashboard/', frontend_views.hospital_dashboard, name='hospital-dashboard'),
    # Use a non-conflicting path for the frontend admin dashboard
    path('site-admin/', frontend_views.admin_dashboard, name='admin-dashboard'),
    path('site-admin/banks/', frontend_views.manage_banks, name='manage-banks'),
    path('site-admin/banks/new/', frontend_views.edit_bank, name='new-bank'),
    path('site-admin/banks/<int:pk>/edit/', frontend_views.edit_bank, name='edit-bank'),
    path('site-admin/banks/<int:pk>/delete/', frontend_views.delete_bank, name='delete-bank'),
    path('site-admin/donors/', frontend_views.manage_donors, name='manage-donors'),
    path('site-admin/donors/<int:pk>/edit/', frontend_views.edit_donor, name='edit-donor'),
    path('site-admin/requests/', frontend_views.manage_requests, name='manage-requests'),
    path('site-admin/requests/<int:pk>/reject/', frontend_views.reject_request, name='reject-request'),
    path('profile/', frontend_views.profile_view, name='profile'),
    path('request/new/', frontend_views.create_request, name='create-request'),
    path('requests/<int:pk>/approve/', frontend_views.approve_request, name='approve-request'),
    path('search/', frontend_views.search_donors, name='search-donors'),
    path('my-requests/', frontend_views.my_requests, name='my-requests'),
    path('analytics/', frontend_views.analytics_dashboard, name='analytics-dashboard'),
    path('set-language/', frontend_views.set_language, name='set_language'),
    # Password reset feature removed — no routes provided for forgotten passwords.
    # Keep a 'resend-confirmation' route to avoid template reverse errors;
    # email verification is disabled, the view will redirect to login with a message.
    path('resend-confirmation/', frontend_views.resend_confirmation, name='resend-confirmation'),
]
