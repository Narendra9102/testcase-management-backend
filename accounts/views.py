from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db import transaction
import uuid
from .models import Role, UserProfile
from .serializers import (
    RoleSerializer,
    RegisterSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer
)


class RoleView(APIView):
    """API to manage roles"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Retrieve all roles"""
        roles = Role.objects.all()
        serializer = RoleSerializer(roles, many=True)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Create predefined roles"""
        PREDEFINED_ROLES = {
            1: {"name": "Admin", "description": "System administrator with full access"},
            2: {"name": "Organization", "description": "Organization level user"},
            3: {"name": "Member", "description": "Project member with limited access"}
        }
        
        role_id = request.data.get("id")
        
        if not role_id or role_id not in PREDEFINED_ROLES:
            return Response({
                "success": False,
                "message": "Invalid role ID. Allowed IDs are 1 (Admin), 2 (Organization), 3 (Member)."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        role_data = PREDEFINED_ROLES[role_id]
        role, created = Role.objects.get_or_create(
            id=role_id,
            defaults=role_data
        )
        
        serializer = RoleSerializer(role)
        return Response({
            "success": True,
            "message": "Role created successfully." if created else "Role already exists.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class RegisterView(APIView):
    """User Registration API"""
    permission_classes = [AllowAny]
    
    @transaction.atomic
    def post(self, request):
        """Register a new user"""
        serializer = RegisterSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data

        if validated_data['role_id'] == 1:
            return Response({
                "success": False,
                "message": "Admin role cannot be assigned via registration. Use Django superuser instead."
            }, status=status.HTTP_400_BAD_REQUEST)
                
        # Create Django User
        user = User.objects.create_user(
            username=validated_data['email'],  
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['name']
        )
        
        # Create UserProfile with additional fields
        profile = UserProfile.objects.create(
            user=user,
            phone=validated_data['phone'],
            country=validated_data['country'],
            role_id=validated_data['role_id']
        )
        
        return Response({
            "success": True,
            "message": "User registered successfully!",
            "data": {
                "id": user.id,
                "name": user.first_name,
                "email": user.email,
                "phone": profile.phone,
                "country": profile.country,
                "role_id": profile.role.id if profile.role else None,
                "role_name": profile.role.name if profile.role else None,
                "created_at": profile.created_at
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """User Login API"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Authenticate user and generate JWT tokens"""
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        try:
            # Get user by email
            user = User.objects.select_related('profile__role').get(
                email=email,
                is_active=True
            )
            
            # Check password
            if not user.check_password(password):
                return Response({
                    "success": False,
                    "message": "Invalid email or password."
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Get profile data
            profile = user.profile
            
            return Response({
                "success": True,
                "message": "Login successful!",
                "data": {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "user": {
                        "id": user.id,
                        "name": user.first_name,
                        "email": user.email,
                        "phone": profile.phone,
                        "country": profile.country,
                        "role_id": profile.role.id if profile.role else None,
                        "role_name": profile.role.name if profile.role else None,
                        "created_at": profile.created_at.isoformat()
                    }
                }
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                "success": False,
                "message": "Invalid email or password."
            }, status=status.HTTP_401_UNAUTHORIZED)


class ForgotPasswordView(APIView):
    """Forgot Password API"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Generate password reset token"""
        serializer = ForgotPasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email, is_active=True)
            profile = user.profile
            
            reset_token = str(uuid.uuid4())
            profile.reset_token = reset_token
            profile.save(update_fields=['reset_token'])
            
            return Response({
                "success": True,
                "message": "Password reset token generated successfully.",
                "data": {
                    "reset_token": reset_token,
                    "email": email
                }
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                "success": True,
                "message": "If the email exists, a reset token has been generated."
            }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """Reset Password API"""
    permission_classes = [AllowAny]
    
    @transaction.atomic
    def post(self, request):
        """Reset password using token"""
        serializer = ResetPasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            profile = UserProfile.objects.select_related('user').get(
                reset_token=token
            )
            user = profile.user
            
            # Reset password
            user.set_password(new_password)
            user.save()
            
            # Clear reset token
            profile.reset_token = None
            profile.save(update_fields=['reset_token'])
            
            return Response({
                "success": True,
                "message": "Password reset successfully!"
            }, status=status.HTTP_200_OK)
            
        except UserProfile.DoesNotExist:
            return Response({
                "success": False,
                "message": "Invalid or expired reset token."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        