from rest_framework import serializers
from .models import Subscription, SubscriptionLog


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model."""
    city_name = serializers.CharField(source='city.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'email', 'phone', 'subscription_type', 'city',
            'city_name', 'is_active', 'activated_at', 'unsubscribed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'activation_token', 'activated_at', 'unsubscribed_at', 'created_at', 'updated_at']
        extra_kwargs = {
            'email': {'required': True},
            'activation_token': {'read_only': True}
        }


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating subscriptions."""
    email = serializers.EmailField(required=True)
    
    class Meta:
        model = Subscription
        fields = ['email', 'phone', 'subscription_type', 'city']
    
    def create(self, validated_data):
        # Generate activation token (in production, use proper token generation)
        import uuid
        validated_data['activation_token'] = str(uuid.uuid4())
        return super().create(validated_data)


class SubscriptionLogSerializer(serializers.ModelSerializer):
    """Serializer for SubscriptionLog model."""
    
    class Meta:
        model = SubscriptionLog
        fields = '__all__'
        read_only_fields = ['sent_at']

