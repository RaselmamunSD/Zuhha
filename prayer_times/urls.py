from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrayerTimeViewSet, MonthlyPrayerTimeViewSet, PrayerTimeAdjustmentViewSet

router = DefaultRouter()
router.register(r'', PrayerTimeViewSet, basename='prayertime')
router.register(r'monthly', MonthlyPrayerTimeViewSet, basename='monthlyprayertime')
router.register(r'adjustments', PrayerTimeAdjustmentViewSet, basename='prayertimeadjustment')

urlpatterns = [
    path('', include(router.urls)),
]

