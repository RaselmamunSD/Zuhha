from rest_framework import serializers
from .models import Subscription, SubscriptionLog
from find_mosque.models import Mosque


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model."""
    city_name = serializers.CharField(source='city.name', read_only=True, allow_null=True)
    selected_mosques = serializers.PrimaryKeyRelatedField(
        queryset=Mosque.objects.filter(is_active=True), many=True, required=False
    )
    selected_mosques_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'email', 'phone', 'subscription_type', 'city',
            'city_name', 'notification_method', 'selected_mosques', 'selected_mosques_details',
            'duration_days', 'notification_minutes_before', 'selected_prayers',
            'is_active', 'activated_at', 'unsubscribed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'activation_token', 'activated_at', 'unsubscribed_at', 'created_at', 'updated_at']
        extra_kwargs = {
            'email': {'required': True},
            'activation_token': {'read_only': True}
        }

    def get_selected_mosques_details(self, obj):
        return [
            {
                'id': mosque.id,
                'name': mosque.name,
                'city': mosque.city.name if mosque.city else None,
                'address': mosque.address,
            }
            for mosque in obj.selected_mosques.all()
        ]


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating subscriptions."""
    email = serializers.EmailField(required=True)
    selected_mosques = serializers.PrimaryKeyRelatedField(
        queryset=Mosque.objects.filter(is_active=True), many=True, required=True
    )

    def validate(self, attrs):
        method = attrs.get('notification_method', 'whatsapp')
        phone = attrs.get('phone', '').strip()
        selected_prayers = attrs.get('selected_prayers', [])
        duration_days = attrs.get('duration_days', 30)
        reminder_minutes = attrs.get('notification_minutes_before', 10)

        if method == 'whatsapp' and not phone:
            raise serializers.ValidationError({'phone': 'WhatsApp number is required for WhatsApp notifications.'})

        if duration_days not in [7, 15, 30]:
            raise serializers.ValidationError({'duration_days': 'Duration must be 7, 15, or 30 days.'})

        if reminder_minutes not in [10, 20, 30]:
            raise serializers.ValidationError({'notification_minutes_before': 'Reminder minutes must be 10, 20, or 30.'})

        if not selected_prayers:
            raise serializers.ValidationError({'selected_prayers': 'Select at least one prayer.'})

        return attrs
    
    class Meta:
        model = Subscription
        fields = [
            'email',
            'phone',
            'subscription_type',
            'city',
            'notification_method',
            'selected_mosques',
            'duration_days',
            'notification_minutes_before',
            'selected_prayers',
        ]

    def _sync_whatsapp_subscription(self, subscription):
        if subscription.notification_method != 'whatsapp' or not subscription.phone:
            return

        try:
            from push_notification.models import WhatsAppNotification
        except Exception:
            return

        phone_value = subscription.phone.strip()
        country_code = '+880'
        phone_number = phone_value

        if phone_value.startswith('+880'):
            country_code = '+880'
            phone_number = phone_value[4:]

        phone_number = phone_number.strip().lstrip('0')
        if not phone_number:
            return

        first_mosque = subscription.selected_mosques.first()
        city = first_mosque.city if first_mosque and first_mosque.city else subscription.city

        whatsapp, _ = WhatsAppNotification.objects.update_or_create(
            phone_number=phone_number,
            defaults={
                'country_code': country_code,
                'user': subscription.user,
                'city': city,
                'notification_types': subscription.selected_prayers,
                'notification_minutes_before': subscription.notification_minutes_before,
                'is_active': subscription.is_active,
            }
        )
        return whatsapp
    
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        selected_mosques = validated_data.pop('selected_mosques', [])

        # Generate activation token (in production, use proper token generation)
        import uuid

        subscription, created = Subscription.objects.get_or_create(
            email=validated_data['email'],
            defaults={
                'phone': validated_data.get('phone', ''),
                'subscription_type': validated_data.get('subscription_type', 'daily'),
                'city': validated_data.get('city'),
                'notification_method': validated_data.get('notification_method', 'whatsapp'),
                'duration_days': validated_data.get('duration_days', 30),
                'notification_minutes_before': validated_data.get('notification_minutes_before', 10),
                'selected_prayers': validated_data.get('selected_prayers', []),
                'user': user,
                'activation_token': str(uuid.uuid4()),
            }
        )

        if not created:
            subscription.phone = validated_data.get('phone', subscription.phone)
            subscription.subscription_type = validated_data.get('subscription_type', subscription.subscription_type)
            subscription.city = validated_data.get('city', subscription.city)
            subscription.notification_method = validated_data.get('notification_method', subscription.notification_method)
            subscription.duration_days = validated_data.get('duration_days', subscription.duration_days)
            subscription.notification_minutes_before = validated_data.get(
                'notification_minutes_before', subscription.notification_minutes_before
            )
            subscription.selected_prayers = validated_data.get('selected_prayers', subscription.selected_prayers)
            if user:
                subscription.user = user
            subscription.is_active = True
            subscription.unsubscribed_at = None
            if not subscription.activation_token:
                subscription.activation_token = str(uuid.uuid4())
            subscription.save()

        if selected_mosques:
            subscription.selected_mosques.set(selected_mosques)

        if not subscription.city and subscription.selected_mosques.exists():
            first_mosque = subscription.selected_mosques.first()
            if first_mosque and first_mosque.city:
                subscription.city = first_mosque.city
                subscription.save(update_fields=['city'])

        self._sync_whatsapp_subscription(subscription)

        return subscription


class SubscriptionLogSerializer(serializers.ModelSerializer):
    """Serializer for SubscriptionLog model."""
    
    class Meta:
        model = SubscriptionLog
        fields = '__all__'
        read_only_fields = ['sent_at']

