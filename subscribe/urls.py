from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubscriptionViewSet, SubscriptionLogViewSet

router = DefaultRouter()
router.register(r'', SubscriptionViewSet, basename='subscription')
router.register(r'logs', SubscriptionLogViewSet, basename='subscriptionlog')

urlpatterns = [
    path('', include(router.urls)),
]

