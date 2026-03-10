from rest_framework import serializers
from .models import NewsletterSubscription, NewsletterLog


class NewsletterSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscription
        fields = ['id', 'email', 'is_active', 'is_verified', 'prayer_updates', 'important_announcements', 'subscribed_at', 'updated_at']
        read_only_fields = ['id', 'subscribed_at', 'updated_at', 'is_verified']


class NewsletterSubscribeSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/subscribing to newsletter.
    """
    # Remove DRF's auto-applied UniqueValidator so existing emails are
    # handled by the get_or_create logic in create() rather than rejected.
    email = serializers.EmailField(validators=[])

    class Meta:
        model = NewsletterSubscription
        fields = ['email']

    def create(self, validated_data):
        """
        Create or reactivate existing subscription.
        """
        email = validated_data.get('email')
        subscription, created = NewsletterSubscription.objects.get_or_create(
            email=email,
            defaults={
                'is_active': True,
                'prayer_updates': True,
                'important_announcements': True
            }
        )
        if not created and not subscription.is_active:
            # Reactivate a previously unsubscribed user
            subscription.is_active = True
            subscription.unsubscribed_at = None
            subscription.save(update_fields=['is_active', 'unsubscribed_at', 'updated_at'])
        return subscription

    def to_representation(self, instance):
        """
        Return the full subscription details.
        """
        return NewsletterSubscriptionSerializer(instance).data


class NewsletterLogSerializer(serializers.ModelSerializer):
    subscription_email = serializers.CharField(source='subscription.email', read_only=True)

    class Meta:
        model = NewsletterLog
        fields = ['id', 'subscription_email', 'subject', 'message', 'status', 'sent_at', 'created_at']
        read_only_fields = ['id', 'sent_at', 'created_at']
