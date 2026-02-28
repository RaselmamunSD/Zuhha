from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    profile_image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'profile_image']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return data
    
    def create(self, validated_data):
        from users.models import UserProfile
        profile_image = validated_data.pop('profile_image', None)
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        
        # Update user profile with profile image if provided
        # The post_save signal already creates a UserProfile, so we just update it
        if profile_image:
            user.profile.profile_image = profile_image
            user.profile.save()
        
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if email and password:
            # Find user by email - use filter().first() to handle duplicate emails
            user = User.objects.filter(email=email).first()
            
            if not user:
                raise serializers.ValidationError("Invalid email or password.")
            
            if not user.check_password(password):
                raise serializers.ValidationError("Invalid email or password.")
            
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
        else:
            raise serializers.ValidationError("Must include email and password.")
        
        data['user'] = user
        return data
    
    def to_representation(self, instance):
        """Generate JWT tokens for the user."""
        user = instance['user']
        refresh = RefreshToken.for_user(user)
        request = self.context.get('request')
        
        return {
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }


class TokenRefreshSerializer(serializers.Serializer):
    """Serializer for refreshing JWT tokens."""
    refresh = serializers.CharField()
    
    def validate(self, data):
        try:
            refresh = RefreshToken(data['refresh'])
        except Exception as e:
            raise serializers.ValidationError(str(e))
        
        data['tokens'] = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return data


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details."""
    profile_image = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'is_staff', 'profile_image']
        read_only_fields = ['id', 'date_joined', 'is_staff']
    
    def get_profile_image(self, obj):
        """Get the profile image URL from the related UserProfile."""
        try:
            if hasattr(obj, 'profile') and obj.profile.profile_image:
                request = self.context.get('request')
                if request and obj.profile.profile_image.url:
                    # Return full URL if request is available
                    return request.build_absolute_uri(obj.profile.profile_image.url)
                return obj.profile.profile_image.url
        except Exception:
            pass
        return None


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, required=True, min_length=8)
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return data


class UpdateUserSerializer(serializers.ModelSerializer):
    """Serializer for updating user information."""
    # Note: email is intentionally excluded because:
    # 1. Users cannot change their email (it's disabled in the form)
    # 2. Email validation would fail if email is already taken
    profile_image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'profile_image']
    
    def update(self, instance, validated_data):
        profile_image = validated_data.pop('profile_image', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile image if provided
        if profile_image is not None:
            instance.profile.profile_image = profile_image
            instance.profile.save()
        
        return instance


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for requesting password reset."""
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password using token."""
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data["new_password"] != data["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )

        try:
            uid = force_str(urlsafe_base64_decode(data["uid"]))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            raise serializers.ValidationError({"uid": "Invalid user identifier."})

        if not default_token_generator.check_token(user, data["token"]):
            raise serializers.ValidationError({"token": "Invalid or expired token."})

        data["user"] = user
        return data
    

