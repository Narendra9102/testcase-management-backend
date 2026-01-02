from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Role, UserProfile
import re


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model"""
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile"""
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'country', 'role', 'reset_token', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for Django User with profile"""
    
    profile = UserProfileSerializer(read_only=True)
    phone = serializers.CharField(write_only=True, required=True)
    country = serializers.CharField(write_only=True, required=True)
    role_id = serializers.IntegerField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'phone', 'country', 'role_id', 'profile',
            'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True},
        }


class RegisterSerializer(serializers.Serializer):
    """Serializer for registration"""
    name = serializers.CharField(required=True, max_length=100)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, min_length=8, write_only=True)
    phone = serializers.CharField(required=True, max_length=15)
    country = serializers.CharField(required=True, max_length=50)
    role_id = serializers.IntegerField(required=True)
    
    def validate_email(self, value):
        """Check if email is unique"""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Email is already registered.")
        return value.lower()
    
    def validate_phone(self, value):
        """Check if phone is unique and valid"""
        if not re.match(r'^\+?[0-9]{10,15}$', value):
            raise serializers.ValidationError("Phone number must be 10-15 digits.")
        if UserProfile.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Phone number is already registered.")
        return value
    
    def validate_password(self, value):
        """Validate password strength"""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        return value
    
    def validate_role_id(self, value):
        """Validate role exists"""
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid role ID.")
        return value


class LoginSerializer(serializers.Serializer):
    """Serializer for login request"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate_email(self, value):
        return value.lower()


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password request"""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        return value.lower()


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for reset password request"""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8, write_only=True)
    
    def validate_new_password(self, value):
        """Validate password strength"""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        return value