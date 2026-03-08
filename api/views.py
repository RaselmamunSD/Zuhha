import os
import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status
from prayer_times.models import PrayerTime
from locations.models import City
from .models import Location, UserPreference, SupportMessage
from .serializers import PrayerTimeSerializer, LocationSerializer, UserPreferenceSerializer, SupportMessageSerializer


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


ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@parser_classes([MultiPartParser, FormParser])
def share_image_upload(request):
    """
    Upload an image for WhatsApp sharing.
    Saves the image to /media/shared_images/ and returns its public URL.
    """
    image_file = request.FILES.get('image')
    if not image_file:
        return Response({'error': 'No image file provided.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validate content type
    if image_file.content_type not in ALLOWED_IMAGE_TYPES:
        return Response(
            {'error': 'Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate file size
    if image_file.size > MAX_UPLOAD_SIZE:
        return Response({'error': 'File too large. Maximum size is 5 MB.'}, status=status.HTTP_400_BAD_REQUEST)

    # Generate a unique filename to avoid collisions and path traversal
    ext = os.path.splitext(image_file.name)[1].lower()
    safe_filename = f"shared_images/{uuid.uuid4().hex}{ext}"

    saved_path = default_storage.save(safe_filename, ContentFile(image_file.read()))

    # Build absolute URL
    api_base_url = getattr(settings, 'API_BASE_URL', None)
    if api_base_url:
        image_url = f"{api_base_url.rstrip('/')}/media/{saved_path}"
    else:
        image_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{saved_path}")

    return Response({'image_url': image_url}, status=status.HTTP_201_CREATED)


class PrayerTimeViewSet(viewsets.ModelViewSet):
    queryset = PrayerTime.objects.all()
    serializer_class = PrayerTimeSerializer


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer


class UserPreferenceViewSet(viewsets.ModelViewSet):
    queryset = UserPreference.objects.all()
    serializer_class = UserPreferenceSerializer


class SupportMessageViewSet(viewsets.ModelViewSet):
    queryset = SupportMessage.objects.all()
    serializer_class = SupportMessageSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
