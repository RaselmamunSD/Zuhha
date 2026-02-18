from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Country, City
from .serializers import CountrySerializer, CitySerializer, CityListSerializer


class CountryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing countries.
    """
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset


class CityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing cities.
    """
    queryset = City.objects.all()
    serializer_class = CitySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'country__name']
    ordering_fields = ['name', 'country__name']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CityListSerializer
        return CitySerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        country_id = self.request.query_params.get('country')
        is_active = self.request.query_params.get('is_active')
        is_capital = self.request.query_params.get('is_capital')
        
        if country_id:
            queryset = queryset.filter(country_id=country_id)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if is_capital is not None:
            queryset = queryset.filter(is_capital=is_capital.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search cities by name."""
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response({'detail': 'Query must be at least 2 characters.'}, status=400)
        
        cities = City.objects.filter(name__icontains=query, is_active=True)[:10]
        serializer = CityListSerializer(cities, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_coordinates(self, request):
        """Find nearest city by coordinates."""
        lat = request.query_params.get('latitude')
        lng = request.query_params.get('longitude')
        
        if not lat or not lng:
            return Response({'detail': 'Latitude and longitude are required.'}, status=400)
        
        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            return Response({'detail': 'Invalid coordinates.'}, status=400)
        
        # Simple distance calculation (not accurate for large distances)
        # In production, use PostGIS or proper distance calculation
        cities = City.objects.filter(is_active=True)
        
        # Get closest city (simplified)
        closest_city = None
        min_distance = float('inf')
        
        for city in cities:
            # Very simplified - just use absolute difference
            distance = abs(float(city.latitude) - lat) + abs(float(city.longitude) - lng)
            if distance < min_distance:
                min_distance = distance
                closest_city = city
        
        if closest_city:
            serializer = CitySerializer(closest_city)
            return Response(serializer.data)
        
        return Response({'detail': 'No cities found.'}, status=404)

