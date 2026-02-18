from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import PrayerTime, MonthlyPrayerTime, PrayerTimeAdjustment
from .serializers import PrayerTimeSerializer, MonthlyPrayerTimeSerializer, PrayerTimeAdjustmentSerializer


class PrayerTimeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing prayer times.
    """
    queryset = PrayerTime.objects.all()
    serializer_class = PrayerTimeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['date']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's prayer times."""
        today = timezone.now().date()
        try:
            prayer_time = PrayerTime.objects.get(date=today)
            serializer = self.get_serializer(prayer_time)
            return Response(serializer.data)
        except PrayerTime.DoesNotExist:
            return Response({'detail': 'Prayer times not found for today.'}, status=404)
    
    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """Get prayer times for a specific date."""
        date = request.query_params.get('date')
        if not date:
            return Response({'detail': 'Date parameter is required.'}, status=400)
        try:
            prayer_time = PrayerTime.objects.get(date=date)
            serializer = self.get_serializer(prayer_time)
            return Response(serializer.data)
        except PrayerTime.DoesNotExist:
            return Response({'detail': 'Prayer times not found for the specified date.'}, status=404)
        except ValueError:
            return Response({'detail': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)


class MonthlyPrayerTimeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing monthly prayer times.
    """
    queryset = MonthlyPrayerTime.objects.all()
    serializer_class = MonthlyPrayerTimeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['city__name']
    ordering_fields = ['year', 'month', 'day']
    ordering = ['year', 'month', 'day']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        city_id = self.request.query_params.get('city')
        year = self.request.query_params.get('year')
        month = self.request.query_params.get('month')
        
        if city_id:
            queryset = queryset.filter(city_id=city_id)
        if year:
            queryset = queryset.filter(year=year)
        if month:
            queryset = queryset.filter(month=month)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def current_month(self, request):
        """Get current month's prayer times for a city."""
        city_id = request.query_params.get('city')
        if not city_id:
            return Response({'detail': 'City parameter is required.'}, status=400)
        
        today = timezone.now().date()
        prayer_times = MonthlyPrayerTime.objects.filter(
            city_id=city_id,
            year=today.year,
            month=today.month
        )
        serializer = self.get_serializer(prayer_times, many=True)
        return Response(serializer.data)


class PrayerTimeAdjustmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing prayer time adjustments.
    """
    queryset = PrayerTimeAdjustment.objects.all()
    serializer_class = PrayerTimeAdjustmentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['city__name', 'prayer_name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset

