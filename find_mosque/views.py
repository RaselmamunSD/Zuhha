from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.db.models import Q
from .models import Mosque, MosqueImage
from .serializers import MosqueSerializer, MosqueListSerializer, MosqueImageSerializer


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

