from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    """
    Project model - Only ORGANIZATION users (role_id=2) can create projects
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_projects'  # Changed from 'projects'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.created_by.first_name}"
    
    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_by']),
            models.Index(fields=['is_active']),
        ]


class ProjectMember(models.Model):
    """
    Project Member model - Tracks which MEMBERS (role_id=3) are invited to which projects
    """
    STATUS_PENDING = 'Pending'
    STATUS_ACCEPTED = 'Accepted'
    STATUS_REJECTED = 'Rejected'
    
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
    )
    
    ROLE_VIEWER = 'Viewer'
    ROLE_TESTER = 'Tester'
    ROLE_CONTRIBUTOR = 'Contributor'
    
    ROLE_CHOICES = (
        (ROLE_VIEWER, 'Viewer'),        # Can only view testcases
        (ROLE_TESTER, 'Tester'),        # Can create/edit testcases
        (ROLE_CONTRIBUTOR, 'Contributor'),  # Can create/edit/delete testcases
    )
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='members'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_memberships'
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_invitations'
    )
    role_in_project = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_TESTER
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'project_members'
        unique_together = ('project', 'user')  # User can't be invited twice to same project
        ordering = ['-invited_at']
        indexes = [
            models.Index(fields=['project', 'user']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.first_name} in {self.project.name}"


class TestCase(models.Model):
    """
    TestCase model - Can be created by:
    1. Project owner (ORGANIZATION - role_id=2)
    2. Invited members (MEMBER - role_id=3) with Tester/Contributor role
    """
    
    PRIORITY_LOW = 'Low'
    PRIORITY_MEDIUM = 'Medium'
    PRIORITY_HIGH = 'High'
    
    PRIORITY_CHOICES = (
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    steps = models.TextField(help_text="Test execution steps")
    expected_result = models.TextField(help_text="Expected outcome")
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_MEDIUM
    )
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='testcases'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_testcases'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} - {self.priority}"
    
    class Meta:
        db_table = 'testcases'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project']),
            models.Index(fields=['created_by']),
            models.Index(fields=['priority']),
            models.Index(fields=['is_active']),
        ]


class TestExecution(models.Model):
    """
    Tracks test case execution history
    Supports both simulated and AI-driven executions
    """
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Running', 'Running'),
        ('Passed', 'Passed'),
        ('Failed', 'Failed'),
    )
    
    testcase = models.ForeignKey(
        TestCase,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    executed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )
    execution_time = models.FloatField(null=True, blank=True)  # in seconds
    error_message = models.TextField(null=True, blank=True)
    execution_log = models.JSONField(null=True, blank=True)  # Stores step-by-step log
    ai_used = models.BooleanField(default=False)  # Was AI used for this execution?
    ai_provider = models.CharField(max_length=20, null=True, blank=True)  # openai/anthropic
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.testcase.title} - {self.status} ({self.started_at})"
    
    class Meta:
        db_table = 'test_executions'
        ordering = ['-started_at']
        