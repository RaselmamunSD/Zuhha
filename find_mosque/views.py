from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Mosque, MosqueImage, FavoriteMosque
from .serializers import (
    MosqueSerializer,
    MosqueListSerializer,
    MosqueImageSerializer,
    RegisterMosqueSerializer,
    FavoriteMosqueSerializer,
)


class MosqueViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing mosques.
    """
    queryset = Mosque.objects.all()
    serializer_class = MosqueSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'address', 'city__name', 'city__country__name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MosqueListSerializer
        return MosqueSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()

        is_staff_user = self.request.user.is_authenticated and self.request.user.is_staff
        if not is_staff_user:
            queryset = queryset.filter(is_verified=True)
        
        # Filter by city
        city_id = self.request.query_params.get('city')
        if city_id:
            queryset = queryset.filter(city_id=city_id)
        
        # Filter by country
        country_id = self.request.query_params.get('country')
        if country_id:
            queryset = queryset.filter(city__country_id=country_id)
        
        # Filter by verified status
        is_verified = self.request.query_params.get('is_verified')
        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified.lower() == 'true')
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        else:
            # Default to showing only active mosques
            queryset = queryset.filter(is_active=True)
        
        # Filter by facilities
        has_parking = self.request.query_params.get('has_parking')
        if has_parking is not None:
            queryset = queryset.filter(has_parking=has_parking.lower() == 'true')
        
        has_jumuah = self.request.query_params.get('has_jumuah')
        if has_jumuah is not None:
            queryset = queryset.filter(has_jumuah=has_jumuah.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Find mosques near a location."""
        lat = request.query_params.get('latitude')
        lng = request.query_params.get('longitude')
        radius = request.query_params.get('radius', 10)  # Default 10km
        
        if not lat or not lng:
            return Response({'detail': 'Latitude and longitude are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            lat = float(lat)
            lng = float(lng)
            radius = float(radius)
        except ValueError:
            return Response({'detail': 'Invalid coordinates or radius.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Simple distance filter (not accurate - use PostGIS for production)
        # Filter mosques with coordinates
        mosques = Mosque.objects.filter(
            is_active=True,
            is_verified=True,
            latitude__isnull=False,
            longitude__isnull=False
        )
        
        nearby_mosques = []
        for mosque in mosques:
            # Very simplified distance calculation
            distance = ((float(mosque.latitude) - lat)**2 + (float(mosque.longitude) - lng)**2)**0.5
            # Approximate conversion: 1 degree ≈ 111km
            distance_km = distance * 111
            if distance_km <= radius:
                nearby_mosques.append({
                    'mosque': mosque,
                    'distance_km': round(distance_km, 2)
                })
        
        # Sort by distance
        nearby_mosques.sort(key=lambda x: x['distance_km'])
        
        serializer = MosqueListSerializer(
            [item['mosque'] for item in nearby_mosques[:20]], 
            many=True,
            context={'request': request}
        )
        
        # Add distance to response
        result = []
        for i, data in enumerate(serializer.data):
            data['distance_km'] = nearby_mosques[i]['distance_km']
            result.append(data)
        
        return Response(result)
    
    @action(detail=True, methods=['get'])
    def prayer_times(self, request, pk=None):
        """Get today's prayer times for a specific mosque with next prayer calculation."""
        mosque = self.get_object()
        
        # Get current time
        now = timezone.now()
        current_time = now.time()
        current_date = now.date()
        
        # Prayer times data structure
        prayer_times = []
        
        # Fajr
        if mosque.fajr_beginning and mosque.fajr_jamaah:
            prayer_times.append({
                'name': 'Fajr',
                'beginning': mosque.fajr_beginning.strftime('%I:%M %p'),
                'jamaah': mosque.fajr_jamaah.strftime('%I:%M %p'),
                'beginning_time': mosque.fajr_beginning,
                'jamaah_time': mosque.fajr_jamaah,
            })
        
        # Sunrise (no jamaah)
        if mosque.sunrise:
            prayer_times.append({
                'name': 'Sunrise',
                'time': mosque.sunrise.strftime('%I:%M %p'),
                'time_obj': mosque.sunrise,
            })
        
        # Dhuhr
        if mosque.dhuhr_beginning and mosque.dhuhr_jamaah:
            prayer_times.append({
                'name': 'Dhuhr',
                'beginning': mosque.dhuhr_beginning.strftime('%I:%M %p'),
                'jamaah': mosque.dhuhr_jamaah.strftime('%I:%M %p'),
                'beginning_time': mosque.dhuhr_beginning,
                'jamaah_time': mosque.dhuhr_jamaah,
            })
        
        # Asr
        if mosque.asr_beginning and mosque.asr_jamaah:
            prayer_times.append({
                'name': 'Asr',
                'beginning': mosque.asr_beginning.strftime('%I:%M %p'),
                'jamaah': mosque.asr_jamaah.strftime('%I:%M %p'),
                'beginning_time': mosque.asr_beginning,
                'jamaah_time': mosque.asr_jamaah,
            })
        
        # Maghrib
        if mosque.maghrib_sunset and mosque.maghrib_jamaah:
            prayer_times.append({
                'name': 'Maghrib',
                'sunset': mosque.maghrib_sunset.strftime('%I:%M %p'),
                'jamaah': mosque.maghrib_jamaah.strftime('%I:%M %p'),
                'sunset_time': mosque.maghrib_sunset,
                'jamaah_time': mosque.maghrib_jamaah,
            })
        
        # Isha
        if mosque.isha_beginning and mosque.isha_jamaah:
            prayer_times.append({
                'name': 'Isha',
                'beginning': mosque.isha_beginning.strftime('%I:%M %p'),
                'jamaah': mosque.isha_jamaah.strftime('%I:%M %p'),
                'beginning_time': mosque.isha_beginning,
                'jamaah_time': mosque.isha_jamaah,
            })
        
        # Find next prayer
        next_prayer_index = None
        next_prayer_time = None
        time_until_next = None
        
        for i, prayer in enumerate(prayer_times):
            if prayer['name'] == 'Sunrise':
                prayer_time = prayer.get('time_obj')
            else:
                prayer_time = prayer.get('jamaah_time')
            
            if prayer_time and current_time < prayer_time:
                next_prayer_index = i
                next_prayer_time = prayer_time
                
                # Calculate time until next prayer
                now_datetime = datetime.combine(current_date, current_time)
                next_datetime = datetime.combine(current_date, next_prayer_time)
                time_diff = next_datetime - now_datetime
                
                hours = time_diff.seconds // 3600
                minutes = (time_diff.seconds % 3600) // 60
                
                if hours > 0:
                    time_until_next = f"{hours}h {minutes}m"
                else:
                    time_until_next = f"{minutes}m"
                
                break
        
        # If no prayer found today, next prayer is Fajr tomorrow
        if next_prayer_index is None and prayer_times:
            next_prayer_index = 0
            time_until_next = "Tomorrow"
        
        return Response({
            'mosque_id': mosque.id,
            'mosque_name': mosque.name,
            'date': current_date.strftime('%A, %B %d, %Y'),
            'prayer_times': prayer_times,
            'next_prayer_index': next_prayer_index,
            'next_prayer_name': prayer_times[next_prayer_index]['name'] if next_prayer_index is not None else None,
            'time_until_next': time_until_next,
        })
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a mosque (admin only)."""
        mosque = self.get_object()
        if not request.user.is_superuser:
            return Response({'detail': 'Only admins can verify mosques.'}, status=status.HTTP_403_FORBIDDEN)
        
        mosque.is_verified = True
        mosque.save()
        serializer = self.get_serializer(mosque)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer = RegisterMosqueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mosque = serializer.save()

        return Response({
            'message': 'Mosque registration submitted successfully. Awaiting admin approval.',
            'mosque_id': mosque.id,
            'is_verified': mosque.is_verified,
            'is_active': mosque.is_active,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Add or remove a mosque from user's favorites."""
        mosque = self.get_object()

        if request.method == 'POST':
            favorite, created = FavoriteMosque.objects.get_or_create(
                user=request.user,
                mosque=mosque,
            )
            serializer = FavoriteMosqueSerializer(favorite, context={'request': request})
            return Response(
                {
                    'detail': 'Mosque added to favorites.' if created else 'Mosque is already in favorites.',
                    'favorite': serializer.data,
                    'is_favorite': True,
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )

        deleted_count, _ = FavoriteMosque.objects.filter(
            user=request.user,
            mosque=mosque,
        ).delete()

        if deleted_count == 0:
            return Response({'detail': 'Mosque is not in favorites.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                'detail': 'Mosque removed from favorites.',
                'is_favorite': False,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def favorites(self, request):
        """Get current user's favorite mosques."""
        favorites = FavoriteMosque.objects.filter(user=request.user).select_related('mosque', 'mosque__city', 'mosque__city__country')
        serializer = FavoriteMosqueSerializer(favorites, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class MosqueImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing mosque images.
    """
    queryset = MosqueImage.objects.all()
    serializer_class = MosqueImageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['is_primary', 'created_at']
    ordering = ['-is_primary', '-created_at']
    
    def get_queryset(self):
        return MosqueImage.objects.filter(mosque_id=self.kwargs.get('mosque_pk'))
    
    def perform_create(self, serializer):
        mosque_id = self.kwargs.get('mosque_pk')
        mosque = Mosque.objects.get(pk=mosque_id)
        
        # If this is set as primary, remove primary from other images
        if serializer.validated_data.get('is_primary', False):
            MosqueImage.objects.filter(mosque=mosque).update(is_primary=False)
        
        serializer.save(mosque=mosque)

