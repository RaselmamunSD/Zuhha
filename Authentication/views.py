from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from .serializers import (
    LoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    UpdateUserSerializer,
    TokenRefreshSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)


class AuthViewSet(viewsets.GenericViewSet):
    """
    ViewSet for authentication endpoints.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        User login endpoint.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Use serializer.data which includes tokens from to_representation()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        User registration endpoint.
        """
        from .serializers import UserRegistrationSerializer
        
        serializer = UserRegistrationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens for the new user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def forgot_password(self, request):
        """
        Start forgot password flow by emailing a reset link.
        """
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email=email).first()

        # Always return success response to avoid email enumeration
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Frontend reset URL (can be configured via env)
            frontend_base = getattr(settings, "FRONTEND_BASE_URL", None) or "http://localhost:3000"
            reset_path = f"/reset-password?uid={uid}&token={token}"
            reset_url = f"{frontend_base}{reset_path}"

            subject = "Password Reset Request"
            message = (
                f"Assalamu Alaikum {user.get_full_name() or user.username},\n\n"
                "We received a request to reset the password for your Salahtime account.\n\n"
                f"Please click the link below (or copy and paste it into your browser) to set a new password:\n\n"
                f"{reset_url}\n\n"
                "This link will expire shortly for security reasons.\n\n"
                "If you did not request a password reset, you can ignore this email.\n\n"
                "Jazakallahu Khair,\n"
                f"{getattr(settings, 'SITE_NAME', 'Salahtime')} Team"
            )

            try:
                send_mail(
                    subject,
                    message,
                    getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"),
                    [email],
                    fail_silently=True,
                )
            except Exception:
                # We still return success so the user isn't blocked by email issues
                pass

        return Response(
            {"detail": "If an account exists with this email, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def reset_password(self, request):
        """
        Complete password reset using uid+token from email.
        """
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        new_password = serializer.validated_data["new_password"]

        user.set_password(new_password)
        user.save()

        # Issue fresh tokens after password reset
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "detail": "Password has been reset successfully.",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_200_OK,
        )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """
        User logout endpoint.
        Note: JWT is stateless, so we just inform the client to discard the token.
        For token blacklisting, configure SimpleJWT settings.
        """
        return Response({
            'detail': 'Successfully logged out. Please discard your tokens.'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def refresh_token(self, request):
        """
        Refresh access token using refresh token.
        """
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        return Response({
            'tokens': serializer.validated_data['tokens']
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Get current authenticated user.
        """
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Change user password.
        """
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': 'Current password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Generate new tokens after password change
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'detail': 'Password changed successfully.',
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['put', 'patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """
        Update user profile.
        """
        serializer = UpdateUserSerializer(instance=request.user, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user, context={'request': request}).data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_account(self, request):
        """
        Delete user account.
        """
        user = request.user
        user.delete()
        return Response({
            'detail': 'Account deleted successfully.'
        }, status=status.HTTP_204_NO_CONTENT)


class UserTokenViewSet(viewsets.GenericViewSet):
    """
    ViewSet for managing user tokens.
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def refresh(self, request):
        """
        Refresh authentication token.
        """
        # Generate new token pair
        refresh = RefreshToken.for_user(request.user)
        
        return Response({
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)

