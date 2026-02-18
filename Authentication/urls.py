from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, UserTokenViewSet

router = DefaultRouter()
router.register(r'', AuthViewSet, basename='auth')
router.register(r'token', UserTokenViewSet, basename='token')

urlpatterns = [
    path('', include(router.urls)),
]

