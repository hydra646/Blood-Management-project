from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import BloodBank, BloodInventory, DonationRequest, Donation, BLOOD_GROUPS
from django.db import transaction
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed demo data for Blood Management (idempotent)'

    def handle(self, *args, **options):
        with transaction.atomic():
            admin, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com', 'role': 'admin'})
            if created:
                admin.set_password('adminpass')
                # Do not make app-level admin a Django superuser/staff to keep roles separate
                # If you need a real site superuser, create a separate user named 'superadmin'
                admin.save()
                self.stdout.write('Created admin (app-level)')
            else:
                self.stdout.write('Admin user exists, reusing')

            hosp, _ = User.objects.get_or_create(username='city_hospital', defaults={'email': 'hospital@example.com', 'role': 'hospital'})
            self.stdout.write('Ensured hospital user')

            # create blood banks if missing
            banks = list(BloodBank.objects.all())
            if not banks:
                for i in range(1, 4):
                    BloodBank.objects.create(name=f'Central Blood Bank {i}', city='Dhaka', address=f'Address {i}', contact='0123456789')
                banks = list(BloodBank.objects.all())
                self.stdout.write('Created blood banks')
            else:
                self.stdout.write('Blood banks exist')

            # inventory: ensure at least one row per bank per group
            for b in banks:
                for g, _ in BLOOD_GROUPS:
                    inv, inv_created = BloodInventory.objects.get_or_create(blood_bank=b, blood_group=g, defaults={'units': random.randint(5, 20)})
            self.stdout.write('Ensured inventory rows')

            # donors: ensure at least 6 donors
            donors = list(User.objects.filter(role='donor'))
            if len(donors) < 6:
                for i in range(1, 8):
                    username = f'donor{i}'
                    if not User.objects.filter(username=username).exists():
                        u = User.objects.create_user(username=username, email=f'{username}@example.com', password='donorpass', role='donor', blood_group=random.choice([g for g, _ in BLOOD_GROUPS]), city='Dhaka')
                        donors.append(u)
                self.stdout.write('Created donors')
            else:
                self.stdout.write('Sufficient donors exist')

            # requests: create a few if none exist
            if DonationRequest.objects.count() < 5:
                for i in range(1, 6):
                    requester = random.choice(donors)
                    DonationRequest.objects.create(requester=requester, blood_group=random.choice([g for g, _ in BLOOD_GROUPS]), units=random.randint(1, 3), city='Dhaka')
                self.stdout.write('Created sample requests')
            else:
                self.stdout.write('Donation requests exist')

            # donations: create a few if none exist
            if Donation.objects.count() < 5:
                for i in range(1, 6):
                    donor = random.choice(donors)
                    Donation.objects.create(donor=donor, blood_bank=random.choice(banks), blood_group=donor.blood_group or random.choice([g for g, _ in BLOOD_GROUPS]), units=1, approved=True, approved_by=admin)
                self.stdout.write('Created sample donations')
            else:
                self.stdout.write('Donations exist')

            self.stdout.write(self.style.SUCCESS('Demo data ensured successfully'))
