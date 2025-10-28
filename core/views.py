from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from django.contrib.auth import get_user_model

from .models import BloodBank, BloodInventory, DonationRequest, Donation
from .serializers import (
    BloodBankSerializer, BloodInventorySerializer,
    DonationRequestSerializer, DonationSerializer, UserSerializer
)
from .permissions import IsAdminUserRole
from django.core.mail import send_mail
from django.conf import settings

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get','post','put','patch','delete']

class BloodBankViewSet(viewsets.ModelViewSet):
    queryset = BloodBank.objects.all()
    serializer_class = BloodBankSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name','city']

class BloodInventoryViewSet(viewsets.ModelViewSet):
    queryset = BloodInventory.objects.select_related('blood_bank').all()
    serializer_class = BloodInventorySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['blood_group','blood_bank']

class DonationRequestViewSet(viewsets.ModelViewSet):
    queryset = DonationRequest.objects.all().order_by('-created_at')
    serializer_class = DonationRequestSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status','blood_group','requester__city']
    search_fields = ['requester__username','city']

    def perform_create(self, serializer):
        dr: DonationRequest = serializer.save(requester=self.request.user)
        # Notify requester that the request was received
        try:
            subject = f"Your blood request: {dr.blood_group} x{dr.units} received"
            body = (
                f"Hi {self.request.user.username}, your request for {dr.units} unit(s) of {dr.blood_group}"
                f" in {dr.city or 'your area'} has been received. We'll notify matching donors."
            )
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [self.request.user.email], fail_silently=True)
        except Exception:
            pass
        # Notify donors of the same blood group
        try:
            donors = User.objects.filter(role='donor', blood_group=dr.blood_group).exclude(email='')
            donor_emails = [d.email for d in donors if d.email]
            if donor_emails:
                subject = f"Donor Alert: {dr.blood_group} needed"
                body = (
                    f"A new blood request has been submitted by {self.request.user.username} for "
                    f"{dr.units} unit(s) of {dr.blood_group} in {dr.city or 'their area'}."
                )
                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, donor_emails, fail_silently=True)
        except Exception:
            pass

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def mine(self, request):
        """Return only the authenticated user's requests ordered by newest first."""
        qs = DonationRequest.objects.filter(requester=request.user).order_by('-created_at')
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUserRole])
    def approve(self, request, pk=None):
        req = self.get_object()
        if req.status != 'pending':
            return Response({'detail': 'Already processed.'}, status=status.HTTP_400_BAD_REQUEST)
        req.status = 'approved'
        req.approved_by = request.user
        req.save()
        # notify requester
        try:
            send_mail(f'Request approved: {req.blood_group}', f'Your request for {req.units} unit(s) of {req.blood_group} has been approved.', settings.DEFAULT_FROM_EMAIL, [req.requester.email], fail_silently=True)
        except Exception:
            pass
        return Response(self.get_serializer(req).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUserRole])
    def reject(self, request, pk=None):
        req = self.get_object()
        req.status = 'rejected'
        req.approved_by = request.user
        req.save()
        try:
            send_mail(f'Request rejected: {req.blood_group}', f'Your request for {req.units} unit(s) of {req.blood_group} has been rejected.', settings.DEFAULT_FROM_EMAIL, [req.requester.email], fail_silently=True)
        except Exception:
            pass
        return Response(self.get_serializer(req).data)

class DonationViewSet(viewsets.ModelViewSet):
    queryset = Donation.objects.all().order_by('-date')
    serializer_class = DonationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['donor__id','blood_group','approved']
    search_fields = ['donor__username','blood_bank__name']

    def perform_create(self, serializer):
        serializer.save(donor=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUserRole])
    def approve(self, request, pk=None):
        donation = self.get_object()
        if donation.approved:
            return Response({'detail': 'Donation already approved.'}, status=status.HTTP_400_BAD_REQUEST)
        donation.approved = True
        donation.approved_by = request.user
        donation.save()
        # Notify donor of approval
        try:
            subject = 'Your donation has been approved'
            body = (
                f"Hi {donation.donor.username}, your donation of {donation.units} unit(s) of {donation.blood_group} "
                f"to {donation.blood_bank.name if donation.blood_bank else 'the selected blood bank'} has been approved."
            )
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [donation.donor.email], fail_silently=True)
        except Exception:
            pass
        return Response(self.get_serializer(donation).data)

@api_view(['GET'])
@permission_classes([IsAdminUserRole])
def admin_stats(request):
    total_donors = User.objects.filter(role='donor').count()
    total_requests = DonationRequest.objects.count()
    pending_requests = DonationRequest.objects.filter(status='pending').count()
    inventory = BloodInventory.objects.values('blood_group').annotate(total_units=Sum('units'))
    return Response({
        'total_donors': total_donors,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'inventory': list(inventory),
    })
