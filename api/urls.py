from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrayerTimeViewSet, LocationViewSet, UserPreferenceViewSet

router = DefaultRouter()
router.register(r'prayertimes', PrayerTimeViewSet, basename='prayertime')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'preferences', UserPreferenceViewSet, basename='userpreference')

urlpatterns = [
    path('', include(router.urls)),
]

