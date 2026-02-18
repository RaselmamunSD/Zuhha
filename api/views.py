from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from prayer_times.models import PrayerTime
from locations.models import City
from .models import Location, UserPreference
from .serializers import PrayerTimeSerializer, LocationSerializer, UserPreferenceSerializer


class PrayerTimeViewSet(viewsets.ModelViewSet):
    queryset = PrayerTime.objects.all()
    serializer_class = PrayerTimeSerializer


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer


class UserPreferenceViewSet(viewsets.ModelViewSet):
    queryset = UserPreference.objects.all()
    serializer_class = UserPreferenceSerializer
