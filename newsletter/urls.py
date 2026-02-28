from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NewsletterSubscriptionViewSet,
    NewsletterLogViewSet,
    subscribe_newsletter,
    unsubscribe_newsletter,
)

router = DefaultRouter()
router.register(r'subscriptions', NewsletterSubscriptionViewSet, basename='newsletter-subscription')
router.register(r'logs', NewsletterLogViewSet, basename='newsletter-log')

urlpatterns = [
    # Direct endpoints
    path('subscribe/', subscribe_newsletter, name='newsletter-subscribe'),
    path('unsubscribe/', unsubscribe_newsletter, name='newsletter-unsubscribe'),
    # Router endpoints
    path('', include(router.urls)),
]

