from rest_framework import serializers
from .models import WhatsAppNotification, WhatsAppNotificationLog


class WhatsAppNotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for WhatsApp notification subscriptions.
    """
    full_phone = serializers.CharField(read_only=True)
    
    class Meta:
        model = WhatsAppNotification
        fields = [
            'id', 'phone_number', 'country_code', 'full_phone',
            'user', 'notification_types', 'language', 'city',
            'is_active', 'is_verified', 'verification_code',
            'verified_at', 'notification_minutes_before', 'admin_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['is_verified', 'verified_at', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # If user is authenticated, associate with user
        request = self.context.get('request')
        if request and request.user.is_authenticated and not validated_data.get('user'):
            validated_data['user'] = request.user
        return super().create(validated_data)


class WhatsAppNotificationListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing WhatsApp notifications.
    """
    full_phone = serializers.CharField(read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    
    class Meta:
        model = WhatsAppNotification
        fields = [
            'id', 'phone_number', 'country_code', 'full_phone',
            'user', 'user_username', 'city', 'city_name',
            'language', 'is_active', 'is_verified',
            'notification_minutes_before', 'created_at'
        ]


class WhatsAppNotificationLogSerializer(serializers.ModelSerializer):
    """
    Serializer for WhatsApp notification logs.
    """
    whatsapp_phone = serializers.CharField(source='whatsapp.phone_number', read_only=True)
    
    class Meta:
        model = WhatsAppNotificationLog
        fields = [
            'id', 'whatsapp', 'whatsapp_phone', 'message',
            'prayer_name', 'status', 'twilio_sid', 'error_message',
            'sent_at', 'delivered_at'
        ]
        read_only_fields = fields

