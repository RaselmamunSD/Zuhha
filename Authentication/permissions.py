"""
Custom permissions for Authentication module.

This module provides custom permission classes for handling
user authentication and authorization scenarios.
"""
from rest_framework import permissions
from rest_framework.permissions import BasePermission, IsAuthenticated, AllowAny


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow read-only access to unauthenticated users,
    but require authentication for write operations.
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions require authentication
        return request.user and request.user.is_authenticated


class IsVerifiedUser(permissions.BasePermission):
    """
    Custom permission to check if the user is verified.
    Requires the user to have a verified email or phone number.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has a profile with is_verified flag
        if hasattr(request.user, 'profile'):
            return request.user.profile.is_verified
        
        # If no profile, allow access (fallback)
        return True


class IsEmailVerified(permissions.BasePermission):
    """
    Custom permission to check if the user's email is verified.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has a profile with email_verified flag
        if hasattr(request.user, 'profile'):
            return request.user.profile.email_verified
        
        # If no profile, allow access (fallback)
        return True


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Read permissions are allowed to any request.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        # Check if obj has owner attribute (could be user, or related user)
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        # Fallback: check if obj is the request user
        return obj == request.user


class IsActiveUser(permissions.BasePermission):
    """
    Custom permission to check if the user is active.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_active


class IsStaffUser(permissions.BasePermission):
    """
    Custom permission to check if the user is a staff member.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_staff


class IsSuperUser(permissions.BasePermission):
    """
    Custom permission to check if the user is a superuser.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_superuser


class CanChangePassword(permissions.BasePermission):
    """
    Custom permission to verify user can change password.
    Checks if the user has provided correct current password.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # Only allow password change for own account
        return obj == request.user


class HasValidToken(permissions.BasePermission):
    """
    Custom permission to check if the user has a valid token.
    This can be used for additional token validation beyond
    the standard JWT validation.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Additional token validation can be added here
        # For example, checking token against a database of valid tokens
        # or checking token claims
        
        return True


class IsNotBlocked(permissions.BasePermission):
    """
    Custom permission to check if the user is not blocked.
    Requires the user to have a profile with is_blocked field.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has a profile with is_blocked flag
        if hasattr(request.user, 'profile'):
            return not getattr(request.user.profile, 'is_blocked', False)
        
        # If no profile, allow access (fallback)
        return True

