from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Project, TestCase, ProjectMember
from accounts.models import UserProfile


class ProjectMemberSerializer(serializers.ModelSerializer):
    """Serializer for ProjectMember"""
    user_name = serializers.CharField(source='user.first_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.first_name', read_only=True)
    
    class Meta:
        model = ProjectMember
        fields = [
            'id', 'project', 'user', 'user_name', 'user_email',
            'invited_by', 'invited_by_name', 'role_in_project',
            'status', 'invited_at', 'accepted_at'
        ]
        read_only_fields = ['id', 'invited_by', 'invited_at']


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model"""
    created_by_name = serializers.CharField(source='created_by.first_name', read_only=True)
    testcase_count = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'created_by', 'created_by_name',
            'testcase_count', 'member_count', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_by_name', 'created_at', 'updated_at']
    
    def get_testcase_count(self, obj):
        """Get total testcases in this project"""
        return obj.testcases.filter(is_active=True).count()
    
    def get_member_count(self, obj):
        """Get total members in this project"""
        return obj.members.filter(status='Accepted').count()
    
    def validate_name(self, value):
        """Validate project name"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Project name must be at least 3 characters long.")
        return value.strip()


class TestCaseSerializer(serializers.ModelSerializer):
    """Serializer for TestCase model"""
    created_by_name = serializers.CharField(source='created_by.first_name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = TestCase
        fields = [
            'id', 'title', 'description', 'steps', 'expected_result',
            'priority', 'priority_display', 'project', 'project_name',
            'created_by', 'created_by_name', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_by_name', 'project_name', 'created_at', 'updated_at']
    
    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters long.")
        return value.strip()
    
    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long.")
        return value.strip()
    
    def validate_steps(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Steps must be at least 10 characters long.")
        return value.strip()
    
    def validate_expected_result(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Expected result must be at least 5 characters long.")
        return value.strip()


class InviteMemberSerializer(serializers.Serializer):
    """Serializer for inviting members to project"""
    user_email = serializers.EmailField(required=True)
    role_in_project = serializers.ChoiceField(
        choices=ProjectMember.ROLE_CHOICES,
        default='Tester'
    )