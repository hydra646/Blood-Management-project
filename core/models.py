from django.db import models
from django.contrib.auth.models import AbstractUser

BLOOD_GROUPS = [('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-')]
ROLE_CHOICES = [('admin','Admin'),('donor','Donor'),('hospital','Hospital')]

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='donor')
    phone = models.CharField(max_length=20, blank=True, null=True, unique=True)
    city = models.CharField(max_length=100, blank=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    email = models.EmailField(unique=True)
    # track whether user has confirmed their email address
    email_confirmed = models.BooleanField(default=False)

class BloodBank(models.Model):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    contact = models.CharField(max_length=50, blank=True)
    def __str__(self):
        return f"{self.name} ({self.city})"

class BloodInventory(models.Model):
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE, related_name='inventory')
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS)
    units = models.PositiveIntegerField(default=0)
    class Meta:
        unique_together = ('blood_bank','blood_group')

class DonationRequest(models.Model):
    STATUS_CHOICES = [('pending','Pending'),('approved','Approved'),('rejected','Rejected')]
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS)
    units = models.PositiveIntegerField()
    city = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_requests')

class Donation(models.Model):
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations')
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.SET_NULL, null=True, related_name='donations')
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS)
    units = models.PositiveIntegerField(default=1)
    date = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='donation_approvals')
