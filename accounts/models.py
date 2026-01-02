from django.db import models
from django.contrib.auth.models import User 


class Role(models.Model):
    """
    Role model for role-based access control
    1 = Admin (Django superuser - NOT for API use)
    2 = Organization (Can create projects via API)
    3 = Member (Invited to projects)
    """
    
    ADMIN = 1
    ORGANIZATION = 2
    MEMBER = 3
    
    ROLE_CHOICES = (
        (ADMIN, 'Admin'),
        (ORGANIZATION, 'Organization'),
        (MEMBER, 'Member'),
    )
    
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'roles'
        ordering = ['id']


class UserProfile(models.Model):
    """
    Extended user profile with additional fields
    This extends Django's default User model
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone = models.CharField(max_length=15, unique=True)
    country = models.CharField(max_length=50)
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name='user_profiles',
        null=True,
        blank=True
    )
    reset_token = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.phone}"
    
    class Meta:
        db_table = 'user_profiles'
        ordering = ['-created_at']
        