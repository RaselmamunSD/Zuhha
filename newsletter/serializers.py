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
    class Meta:
        model = NewsletterSubscription
        fields = ['email']

    def create(self, validated_data):
        """
        Create or get existing subscription.
        If email already exists, return the existing subscription.
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
