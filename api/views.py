from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from prayer_times.models import PrayerTime
from locations.models import City
from .models import Location, UserPreference
from .serializers import PrayerTimeSerializer, LocationSerializer, UserPreferenceSerializer


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_root(request):
    """
    API Root endpoint that provides information about available endpoints
    """
    return Response({
        'message': 'Welcome to Salahtime API',
        'version': '1.0',
        'endpoints': {
            'auth': '/api/auth/',
            'prayer_times': '/api/prayer-times/',
            'locations': '/api/locations/',
            'users': '/api/users/',
            'subscribe': '/api/subscribe/',
            'mosques': '/api/mosques/',
            'api': '/api/',
        },
        'documentation': 'Use Django Admin at /admin/ or DRF browsable API for more details'
    })


class PrayerTimeViewSet(viewsets.ModelViewSet):
    queryset = PrayerTime.objects.all()
    serializer_class = PrayerTimeSerializer


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer


class UserPreferenceViewSet(viewsets.ModelViewSet):
    queryset = UserPreference.objects.all()
    serializer_class = UserPreferenceSerializer
