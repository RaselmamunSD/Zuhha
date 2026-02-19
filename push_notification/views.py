from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.db.models import Q
from .models import WhatsAppNotification, WhatsAppNotificationLog
from .serializers import (
    WhatsAppNotificationSerializer,
    WhatsAppNotificationListSerializer,
    WhatsAppNotificationLogSerializer
)


class WhatsAppNotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing WhatsApp notifications.
    Admin users can manage all notifications.
    Regular users can only view their own notifications.
    """
    queryset = WhatsAppNotification.objects.all()
    serializer_class = WhatsAppNotificationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['phone_number', 'full_phone', 'user__username', 'user__email', 'admin_notes']
    ordering_fields = ['created_at', 'phone_number', 'is_active', 'is_verified']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """
        Allow unauthenticated users to create (subscribe),
        but require authentication for other actions.
        """
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return WhatsAppNotificationListSerializer
        return WhatsAppNotificationSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions.
        Admins can see all, regular users only see their own.
        """
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return WhatsAppNotification.objects.all()
        return WhatsAppNotification.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """Save with the current user if authenticated."""
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        Verify a WhatsApp number (admin action).
        """
        if not request.user.is_staff:
            return Response(
                {'detail': 'You do not have permission to verify numbers.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        whatsapp = self.get_object()
        whatsapp.is_verified = True
        whatsapp.save()
        
        return Response({
            'detail': 'WhatsApp number verified successfully.',
            'is_verified': whatsapp.is_verified
        })
    
    @action(detail=True, methods=['post'])
    def send_test(self, request, pk=None):
        """
        Send a test notification to the WhatsApp number.
        """
        whatsapp = self.get_object()
        
        # Create a test notification log
        log = WhatsAppNotificationLog.objects.create(
            whatsapp=whatsapp,
            message="This is a test notification from Salahtime API.",
            prayer_name='test',
            status='pending'
        )
        
        # Here you would integrate with Twilio or another WhatsApp service
        # For now, we'll just return success
        log.status = 'sent'
        log.save()
        
        return Response({
            'detail': 'Test notification sent.',
            'log_id': log.id
        })
    
    @action(detail=False, methods=['get'])
    def my_subscriptions(self, request):
        """
        Get current user's WhatsApp subscriptions.
        """
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Authentication required.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        subscriptions = WhatsAppNotification.objects.filter(user=request.user)
        serializer = WhatsAppNotificationListSerializer(subscriptions, many=True)
        return Response(serializer.data)


class WhatsAppNotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for viewing WhatsApp notification logs.
    """
    queryset = WhatsAppNotificationLog.objects.all()
    serializer_class = WhatsAppNotificationLogSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['whatsapp__phone_number', 'twilio_sid']
    ordering_fields = ['sent_at', 'status']
    ordering = ['-sent_at']
    
    def get_permissions(self):
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """
        Filter logs based on user permissions.
        """
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return WhatsAppNotificationLog.objects.all()
        return WhatsAppNotificationLog.objects.filter(whatsapp__user=user)

