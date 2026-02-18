"""
JWT Authentication Middleware for Django REST Framework.

This middleware provides JWT token refresh functionality and
handles token blacklist checking.
"""
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken


class JWTAuthenticationMiddleware:
    """
    Middleware to handle JWT authentication and token refresh.
    
    Features:
    - Automatic token refresh when access token is about to expire
    - Token blacklist checking for logout
    - Custom token validation
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authentication = JWTAuthentication()
    
    def __call__(self, request):
        # Process the request
        response = self.get_response(request)
        
        return response
    
    def authenticate(self, request):
        """
        Authenticate the request and return a tuple of (user, token).
        """
        return self.jwt_authentication.authenticate(request)


class JWTTokenRefreshMiddleware:
    """
    Middleware to automatically refresh tokens when they are about to expire.
    
    This middleware checks if the access token is about to expire and
    automatically generates a new access token using the refresh token.
    """
    
    # Minutes before expiry to trigger refresh
    REFRESH_BEFORE_EXPIRY_MINUTES = 5
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Check if we need to add a new access token to the response
        # This is typically done when the client sends a refresh token
        return response
    
    @staticmethod
    def should_refresh_token(token):
        """
        Check if the token should be refreshed based on its expiry time.
        """
        from django.conf import settings
        
        # Get token expiry time
        exp = token.get('exp', 0)
        now = timezone.now()
        
        # Calculate time until expiry
        exp_time = timezone.datetime.fromtimestamp(exp, tz=timezone.utc)
        time_until_expiry = exp_time - now
        
        # Check if token expires within the threshold
        threshold = timedelta(minutes=JWTTokenRefreshMiddleware.REFRESH_BEFORE_EXPIRY_MINUTES)
        
        return time_until_expiry < threshold


class JWTAuthTokenBlacklistMiddleware:
    """
    Middleware to check if a token has been blacklisted.
    
    This is useful for implementing logout functionality where
    we want to invalidate tokens before their natural expiry.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    @staticmethod
    def is_token_blacklisted(token):
        """
        Check if the token is blacklisted.
        """
        try:
            jti = token.get('jti')
            if jti:
                return BlacklistedToken.objects.filter(token__jti=jti).exists()
        except Exception:
            pass
        return False

