from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BloodBankViewSet, BloodInventoryViewSet,
    DonationRequestViewSet, DonationViewSet, UserViewSet, admin_stats
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('blood-banks', BloodBankViewSet, basename='bloodbank')
router.register('inventory', BloodInventoryViewSet, basename='inventory')
router.register('requests', DonationRequestViewSet, basename='request')
router.register('donations', DonationViewSet, basename='donation')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/stats/', admin_stats, name='admin-stats'),
]
