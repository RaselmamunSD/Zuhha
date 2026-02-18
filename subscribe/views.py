from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from .models import Subscription, SubscriptionLog
from .serializers import SubscriptionSerializer, SubscriptionCreateSerializer, SubscriptionLogSerializer


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subscriptions.
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email', 'phone', 'subscription_type']
    ordering_fields = ['created_at', 'subscription_type']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['create', 'activate', 'unsubscribe']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SubscriptionCreateSerializer
        return SubscriptionSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and not user.is_superuser:
            return Subscription.objects.filter(user=user)
        return Subscription.objects.all()
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=False, methods=['post'])
    def activate(self, request):
        """Activate a subscription using the activation token."""
        token = request.data.get('token')
        if not token:
            return Response({'detail': 'Activation token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            subscription = Subscription.objects.get(activation_token=token)
            subscription.is_active = True
            subscription.activated_at = timezone.now()
            subscription.activation_token = ''
            subscription.save()
            return Response({'detail': 'Subscription activated successfully.'})
        except Subscription.DoesNotExist:
            return Response({'detail': 'Invalid activation token.'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def unsubscribe(self, request):
        """Unsubscribe using email."""
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            subscription = Subscription.objects.get(email=email)
            subscription.is_active = False
            subscription.unsubscribed_at = timezone.now()
            subscription.save()
            return Response({'detail': 'Unsubscribed successfully.'})
        except Subscription.DoesNotExist:
            return Response({'detail': 'Subscription not found.'}, status=status.HTTP_404_NOT_FOUND)


class SubscriptionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing subscription logs (read-only).
    """
    queryset = SubscriptionLog.objects.all()
    serializer_class = SubscriptionLogSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ['sent_at', 'status']
    ordering = ['-sent_at']
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return SubscriptionLog.objects.filter(subscription__user=user)
        return SubscriptionLog.objects.none()

