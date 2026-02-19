from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WhatsAppNotificationViewSet, WhatsAppNotificationLogViewSet

router = DefaultRouter()
router.register(r'whatsapp', WhatsAppNotificationViewSet, basename='whatsapp-notification')
router.register(r'logs', WhatsAppNotificationLogViewSet, basename='whatsapp-notification-log')

urlpatterns = [
    path('', include(router.urls)),
]

