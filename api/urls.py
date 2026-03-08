from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrayerTimeViewSet, LocationViewSet, UserPreferenceViewSet, SupportMessageViewSet, share_image_upload

router = DefaultRouter()
router.register(r'prayertimes', PrayerTimeViewSet, basename='prayertime')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'preferences', UserPreferenceViewSet, basename='userpreference')
router.register(r'support-messages', SupportMessageViewSet, basename='support-message')

urlpatterns = [
    path('', include(router.urls)),
    path('share/upload/', share_image_upload, name='share-image-upload'),
]

