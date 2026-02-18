from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserProfileViewSet, UserLocationViewSet, RegistrationViewSet

router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='userprofile')
router.register(r'locations', UserLocationViewSet, basename='userlocation')
router.register(r'register', RegistrationViewSet, basename='registration')
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]

