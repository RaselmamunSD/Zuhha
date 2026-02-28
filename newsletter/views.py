from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import NewsletterSubscription, NewsletterLog
from .serializers import NewsletterSubscriptionSerializer, NewsletterSubscribeSerializer, NewsletterLogSerializer
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def subscribe_newsletter(request):
    """
    Direct endpoint for subscribing to newsletter.
    
    POST /api/newsletter/subscribe/
    {
        "email": "user@example.com"
    }
    """
    try:
        serializer = NewsletterSubscribeSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            return Response(
                {
                    'message': 'Successfully subscribed to newsletter',
                    'email': instance.email,
                    'is_active': instance.is_active
                },
                status=status.HTTP_201_CREATED
            )
        logger.error(f"Validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error in subscribe_newsletter: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def unsubscribe_newsletter(request):
    """
    Direct endpoint for unsubscribing from newsletter.
    
    POST /api/newsletter/unsubscribe/
    {
        "email": "user@example.com"
    }
    """
    try:
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription = NewsletterSubscription.objects.get(email=email)
        subscription.is_active = False
        subscription.unsubscribed_at = None
        subscription.save()
        return Response(
            {'message': f'Successfully unsubscribed {email} from newsletter'},
            status=status.HTTP_200_OK
        )
    except NewsletterSubscription.DoesNotExist:
        return Response(
            {'error': f'Email {email} is not subscribed to newsletter'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error in unsubscribe_newsletter: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class NewsletterSubscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for newsletter subscriptions.
    - GET /api/newsletter/subscriptions/ : List all newsletter subscriptions (admin only)
    """
    queryset = NewsletterSubscription.objects.all()
    serializer_class = NewsletterSubscriptionSerializer
    permission_classes = [AllowAny]
    lookup_field = 'email'

    def get_serializer_class(self):
        if self.action == 'subscribe':
            return NewsletterSubscribeSerializer
        return NewsletterSubscriptionSerializer





class NewsletterLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing newsletter send logs (admin only).
    - GET /api/newsletter/logs/ : List all newsletter logs
    """
    queryset = NewsletterLog.objects.all()
    serializer_class = NewsletterLogSerializer

