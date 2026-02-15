from django.urls import path
from .views import PrayerTimeViewSet, LocationViewSet, UserPreferenceViewSet

router = DefaultRouter()
router.register(r'prayer-times', PrayerTimeViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'user-preferences', UserPreferenceViewSet)

urlpatterns = router.urls