from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import User, BloodBank, BloodInventory, DonationRequest, Donation
from .forms import RegisterForm, ProfileForm, DonationRequestForm
from .forms import BloodBankForm, AdminUserForm
from django.db.models import Sum, Count
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.core import signing
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from django.utils.translation import activate
from django.http import HttpResponseRedirect
import random
import json

def home(request):
    return render(request, 'core/home.html')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            # Email confirmation has been disabled; users are active immediately.
            messages.success(request, 'Registration successful. You can now log in.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})


def confirm_email(request, token):
    try:
        data = signing.loads(token, salt='email-confirm', max_age=60*60*24)  # 1 day
        pk = data.get('pk')
    except signing.SignatureExpired:
        return render(request, 'core/confirm_email_failed.html', {'reason': 'expired'})
    except signing.BadSignature:
        return render(request, 'core/confirm_email_failed.html', {'reason': 'invalid'})

    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return render(request, 'core/confirm_email_failed.html', {'reason': 'missing'})

    if user.is_active and user.email_confirmed:
        return render(request, 'core/confirm_email_success.html', {'already': True})

    user.is_active = True
    user.email_confirmed = True
    user.save()
    return render(request, 'core/confirm_email_success.html', {'already': False})


def confirm_code(request):
    """View to accept a 6-digit code and validate the pending user's email."""
    pk = request.session.get('email_verification_pk')
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        # allow passing pk as hidden field too
        if not pk:
            pk = request.POST.get('pk')
        if not pk:
            messages.error(request, 'No pending verification found. Please request a new code.')
            return redirect('resend-confirmation')
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('register')

        cache_key = f"email_code:{user.pk}"
        real_code = cache.get(cache_key)
        if real_code and real_code == code:
            user.is_active = True
            user.email_confirmed = True
            user.save()
            cache.delete(cache_key)
            # clear session flag
            request.session.pop('email_verification_pk', None)
            messages.success(request, 'Email verified. You can now login.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid or expired code. Please request a new code.')
            return redirect('resend-confirmation')

    return render(request, 'core/confirm_code.html', {'pk': pk})


def resend_confirmation(request):
    # Email verification has been disabled for this site. Keep this route so
    # templates that link to 'resend-confirmation' don't break — just inform
    # the user and redirect to login.
    messages.info(request, 'Email confirmation is disabled. You can log in directly or reset your password if needed.')
    return redirect('login')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            if not user.is_active:
                messages.error(request, 'Account inactive. Please confirm your email before logging in.')
            else:
                login(request, user)
                if user.role == 'admin':
                    return redirect('admin-dashboard')
                if user.role == 'hospital':
                    return redirect('hospital-dashboard')
                return redirect('donor-dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def donor_dashboard(request):
    if request.user.role != 'donor':
        return redirect('home')
    # Show all donations approved by admin, newest first
    donations = request.user.donations.filter(approved=True).order_by('-date')
    requests_qs = request.user.requests.all().order_by('-created_at')
    available = BloodInventory.objects.values('blood_group').annotate(total=Sum('units'))
    return render(request, 'core/donor_dashboard.html', {'donations': donations, 'available': available, 'requests': requests_qs})


@login_required
def hospital_dashboard(request):
    if request.user.role != 'hospital':
        return redirect('home')
    requests_qs = request.user.requests.all().order_by('-created_at')
    return render(request, 'core/hospital_dashboard.html', {
        'requests': requests_qs,
    })

@login_required
@user_passes_test(lambda u: u.role=='admin')
def admin_dashboard(request):
    total_donors = User.objects.filter(role='donor').count()
    total_requests = DonationRequest.objects.count()
    pending = DonationRequest.objects.filter(status='pending')
    inventory = BloodInventory.objects.values('blood_group').annotate(total_units=Sum('units'))
    return render(request, 'core/admin_dashboard.html', {
        'total_donors': total_donors, 'total_requests': total_requests,
        'pending': pending, 'inventory': inventory
    })


@login_required
@user_passes_test(lambda u: u.role=='admin')
def manage_banks(request):
    banks = BloodBank.objects.all()
    return render(request, 'core/admin_banks.html', {'banks': banks})


@login_required
@user_passes_test(lambda u: u.role=='admin')
def edit_bank(request, pk=None):
    bank = None
    if pk:
        bank = get_object_or_404(BloodBank, pk=pk)
    if request.method == 'POST':
        form = BloodBankForm(request.POST, instance=bank)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bank saved.')
            return redirect('manage-banks')
    else:
        form = BloodBankForm(instance=bank)
    return render(request, 'core/admin_bank_form.html', {'form': form, 'bank': bank})


@login_required
@user_passes_test(lambda u: u.role=='admin')
def delete_bank(request, pk):
    b = get_object_or_404(BloodBank, pk=pk)
    b.delete()
    messages.success(request, 'Bank deleted.')
    return redirect('manage-banks')


@login_required
@user_passes_test(lambda u: u.role=='admin')
def manage_donors(request):
    donors = User.objects.filter(role='donor')
    return render(request, 'core/admin_donors.html', {'donors': donors})


@login_required
@user_passes_test(lambda u: u.role=='admin')
def edit_donor(request, pk):
    donor = get_object_or_404(User, pk=pk, role='donor')
    if request.method == 'POST':
        form = AdminUserForm(request.POST, instance=donor)
        if form.is_valid():
            user = form.save(commit=False)
            # Prevent upgrading to admin unless current user is a Django superuser
            if user.role == 'admin' and not request.user.is_superuser:
                messages.error(request, 'Only site superusers can grant admin role.')
                return redirect('manage-donors')
            user.save()
            messages.success(request, 'Donor updated.')
            return redirect('manage-donors')
    else:
        form = AdminUserForm(instance=donor)
    return render(request, 'core/admin_donor_form.html', {'form': form, 'donor': donor})


@login_required
@user_passes_test(lambda u: u.role=='admin')
def manage_requests(request):
    reqs = DonationRequest.objects.all().order_by('-created_at')
    return render(request, 'core/admin_requests.html', {'reqs': reqs})


@login_required
@user_passes_test(lambda u: u.role=='admin')
def reject_request(request, pk):
    req = get_object_or_404(DonationRequest, pk=pk)
    if req.status == 'pending':
        req.status = 'rejected'
        req.approved_by = request.user
        req.save()
        messages.success(request, 'Request rejected.')
    return redirect('manage-requests')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'core/profile.html', {'form': form})

@login_required
def create_request(request):
    if request.method == 'POST':
        form = DonationRequestForm(request.POST)
        if form.is_valid():
            dr = form.save(commit=False)
            dr.requester = request.user
            dr.save()
            messages.success(request, 'Donation request submitted.')
            # notify admins/hospitals and matching donors via email (console in dev)
            subject = f"New blood request: {dr.blood_group} x{dr.units}"
            body = f"A new blood request has been submitted by {request.user.username} for {dr.units} unit(s) of {dr.blood_group} in {dr.city}."
            # notify requester
            send_mail(subject, f"Your request has been received.\n\n{body}", settings.DEFAULT_FROM_EMAIL, [request.user.email], fail_silently=True)
            # notify donors of same group
            donors = User.objects.filter(role='donor', blood_group=dr.blood_group).exclude(email='')
            donor_emails = [d.email for d in donors if d.email]
            if donor_emails:
                send_mail(f"Donor Alert: {dr.blood_group} needed", body, settings.DEFAULT_FROM_EMAIL, donor_emails, fail_silently=True)
            return redirect('donor-dashboard')
    else:
        form = DonationRequestForm()
    return render(request, 'core/create_request.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.role=='admin')
def approve_request(request, pk):
    req = get_object_or_404(DonationRequest, pk=pk)
    if req.status == 'pending':
        req.status = 'approved'
        req.approved_by = request.user
        req.save()
        # optionally update inventory (not implemented complex matching)
        messages.success(request, 'Request approved.')
    return redirect('admin-dashboard')

def search_donors(request):
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

    q_bg = request.GET.get('blood_group', '')
    q_city = request.GET.get('city', '')

    qs = User.objects.filter(
        role='donor', is_active=True, is_superuser=False, is_staff=False
    ).order_by('username')

    # Filter by selected options
    if q_bg:
        qs = qs.filter(blood_group=q_bg)
    if q_city:
        qs = qs.filter(city__icontains=q_city)

    # Blood group choices for the dropdown
    blood_groups = User._meta.get_field('blood_group').choices

    # Pagination
    page = request.GET.get('page', 1)
    per_page = 10
    paginator = Paginator(qs, per_page)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Results meta for template
    try:
        start_index = page_obj.start_index()
        end_index = page_obj.end_index()
    except Exception:
        start_index = 0
        end_index = 0

    context = {
        'donors': page_obj,  # keep existing name for loop compatibility
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': paginator.num_pages > 1,
        'blood_groups': blood_groups,
        'q_bg': q_bg,
        'q_city': q_city,
        'total_count': paginator.count,
        'start_index': start_index,
        'end_index': end_index,
    }
    return render(request, 'core/search.html', context)


@login_required
@user_passes_test(lambda u: u.role=='admin')
def analytics_dashboard(request):
    """Admin analytics page with charts for blood availability and donation trends."""
    # Blood availability by group
    inventory_data = BloodInventory.objects.values('blood_group').annotate(total=Sum('units')).order_by('blood_group')
    inventory_labels = [item['blood_group'] for item in inventory_data]
    inventory_values = [item['total'] for item in inventory_data]
    
    # Donation trends (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    donations_over_time = Donation.objects.filter(date__gte=thirty_days_ago, approved=True)\
        .extra(select={'day': 'date(date)'})\
        .values('day')\
        .annotate(count=Count('id'))\
        .order_by('day')
    donation_labels = [str(item['day']) for item in donations_over_time]
    donation_values = [item['count'] for item in donations_over_time]
    
    # Blood group distribution of donors
    donor_distribution = User.objects.filter(role='donor').values('blood_group')\
        .annotate(count=Count('id'))\
        .order_by('blood_group')
    donor_labels = [item['blood_group'] if item['blood_group'] else 'Unknown' for item in donor_distribution]
    donor_values = [item['count'] for item in donor_distribution]
    
    # Request status breakdown
    request_status = DonationRequest.objects.values('status').annotate(count=Count('id'))
    status_labels = [item['status'].capitalize() for item in request_status]
    status_values = [item['count'] for item in request_status]
    
    context = {
        'inventory_labels': json.dumps(inventory_labels),
        'inventory_values': json.dumps(inventory_values),
        'donation_labels': json.dumps(donation_labels),
        'donation_values': json.dumps(donation_values),
        'donor_labels': json.dumps(donor_labels),
        'donor_values': json.dumps(donor_values),
        'status_labels': json.dumps(status_labels),
        'status_values': json.dumps(status_values),
    }
    return render(request, 'core/analytics.html', context)


def set_language(request):
    """Language switcher view."""
    lang_code = request.GET.get('language', 'en')
    if lang_code in ['en', 'bn']:
        activate(lang_code)
        response = HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
        return response
    return redirect('home')


@login_required
def my_requests(request):
    """A simple page for users to track the status of their blood requests."""
    requests_qs = request.user.requests.all().order_by('-created_at')
    return render(request, 'core/my_requests.html', {'requests': requests_qs})
