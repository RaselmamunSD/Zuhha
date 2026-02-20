from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WhatsAppNotificationViewSet, WhatsAppNotificationLogViewSet
from .task_views import (
    send_prayer_notification_view,
    send_daily_summary_view,
    task_status_view,
    celery_health_check
)

router = DefaultRouter()
router.register(r'whatsapp', WhatsAppNotificationViewSet, basename='whatsapp-notification')
router.register(r'logs', WhatsAppNotificationLogViewSet, basename='whatsapp-notification-log')

urlpatterns = [
    path('', include(router.urls)),
    
    # Celery Task endpoints
    path('tasks/send_prayer_notification/', send_prayer_notification_view, name='send_prayer_notification'),
    path('tasks/send_daily_summary/', send_daily_summary_view, name='send_daily_summary'),
    path('tasks/status/<str:task_id>/', task_status_view, name='task_status'),
    path('tasks/health/', celery_health_check, name='celery_health'),
]

