from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, UserLocation


class UserSerializer(serializers.ModelSerializer):
    """Serializer for Django's built-in User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    current_city_name = serializers.CharField(source='current_city.name', read_only=True, allow_null=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'username', 'email', 'first_name', 'last_name',
            'phone', 'date_of_birth', 'profile_image',
            'current_city', 'current_city_name',
            'calculation_method', 'juristic_method', 'high_latitude_adjustment',
            'fajr_notification', 'dhuhr_notification', 'asr_notification',
            'maghrib_notification', 'isha_notification', 'notification_minutes_before',
            'is_verified', 'email_verified', 'language', 'theme',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_verified', 'email_verified', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        return super().update(instance, validated_data)


class UserLocationSerializer(serializers.ModelSerializer):
    """Serializer for UserLocation model."""
    city_name = serializers.CharField(source='city.name', read_only=True)
    country_name = serializers.CharField(source='city.country.name', read_only=True)
    
    class Meta:
        model = UserLocation
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

