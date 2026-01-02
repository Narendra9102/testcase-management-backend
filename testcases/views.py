from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Project, TestCase, ProjectMember
from .serializers import (
    ProjectSerializer,
    TestCaseSerializer,
    ProjectMemberSerializer,
    InviteMemberSerializer
)


def get_user_role(user):
    """Helper function to get user's role_id"""
    try:
        return user.profile.role.id
    except:
        return None


class ProjectListCreateView(APIView):
    """
    API to list all projects and create new project
    Only ORGANIZATION users (role_id=2) can create projects
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get all projects:
        - ORGANIZATION (role_id=2): See their own projects
        - MEMBER (role_id=3): See projects they're invited to
        """
        user_role = get_user_role(request.user)
        
        if user_role == 2:  # Organization
            projects = Project.objects.filter(
                created_by=request.user,
                is_active=True
            ).prefetch_related('testcases', 'members')
        
        elif user_role == 3:  # Member
            project_ids = ProjectMember.objects.filter(
                user=request.user,
                status='Accepted'
            ).values_list('project_id', flat=True)
            
            projects = Project.objects.filter(
                id__in=project_ids,
                is_active=True
            ).prefetch_related('testcases', 'members')
        
        else:
            return Response({
                "success": False,
                "message": "Invalid user role."
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ProjectSerializer(projects, many=True)
        
        return Response({
            "success": True,
            "count": projects.count(),
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    @transaction.atomic
    def post(self, request):
        """
        Create new project
        Only ORGANIZATION users (role_id=2) can create projects
        """
        user_role = get_user_role(request.user)
        
        if user_role != 2:
            return Response({
                "success": False,
                "message": "Only Organization users can create projects."
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ProjectSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        project = serializer.save(created_by=request.user)
        
        return Response({
            "success": True,
            "message": "Project created successfully!",
            "data": ProjectSerializer(project).data
        }, status=status.HTTP_201_CREATED)


class ProjectDetailView(APIView):
    """API to get, update, delete specific project"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk, user):
        """Get project and verify access"""
        user_role = get_user_role(user)
        
        if user_role == 2:  # Organization - must be owner
            return get_object_or_404(
                Project,
                pk=pk,
                created_by=user,
                is_active=True
            )
        elif user_role == 3:  # Member - must be invited
            membership = ProjectMember.objects.filter(
                project_id=pk,
                user=user,
                status='Accepted'
            ).first()
            
            if not membership:
                return None
            
            return get_object_or_404(Project, pk=pk, is_active=True)
        
        return None
    
    def get(self, request, pk):
        """Get single project with testcases"""
        project = self.get_object(pk, request.user)
        
        if not project:
            return Response({
                "success": False,
                "message": "Project not found or access denied."
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProjectSerializer(project)
        
        testcases = TestCase.objects.filter(
            project=project,
            is_active=True
        )
        testcase_serializer = TestCaseSerializer(testcases, many=True)
        
        members = ProjectMember.objects.filter(project=project)
        member_serializer = ProjectMemberSerializer(members, many=True)
        
        return Response({
            "success": True,
            "data": {
                "project": serializer.data,
                "testcases": testcase_serializer.data,
                "members": member_serializer.data
            }
        }, status=status.HTTP_200_OK)
    
    @transaction.atomic
    def put(self, request, pk):
        """Update project - Only project owner can update"""
        user_role = get_user_role(request.user)
        
        if user_role != 2:
            return Response({
                "success": False,
                "message": "Only project owner can update project."
            }, status=status.HTTP_403_FORBIDDEN)
        
        project = get_object_or_404(
            Project,
            pk=pk,
            created_by=request.user,
            is_active=True
        )
        
        serializer = ProjectSerializer(project, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        return Response({
            "success": True,
            "message": "Project updated successfully!",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    @transaction.atomic
    def delete(self, request, pk):
        """Delete project - Only project owner can delete"""
        user_role = get_user_role(request.user)
        
        if user_role != 2:
            return Response({
                "success": False,
                "message": "Only project owner can delete project."
            }, status=status.HTTP_403_FORBIDDEN)
        
        project = get_object_or_404(
            Project,
            pk=pk,
            created_by=request.user,
            is_active=True
        )
        
        project.is_active = False
        project.save()
        
        TestCase.objects.filter(project=project).update(is_active=False)
        
        return Response({
            "success": True,
            "message": "Project deleted successfully!"
        }, status=status.HTTP_200_OK)


class InviteMemberView(APIView):
    """
    API to invite MEMBER users (role_id=3) to projects
    Only project owner (ORGANIZATION) can invite
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, project_id):
        """Invite a member to project"""
        user_role = get_user_role(request.user)
        
        if user_role != 2:
            return Response({
                "success": False,
                "message": "Only Organization users can invite members."
            }, status=status.HTTP_403_FORBIDDEN)
        
        project = get_object_or_404(
            Project,
            id=project_id,
            created_by=request.user,
            is_active=True
        )
        
        serializer = InviteMemberSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['user_email']
        role_in_project = serializer.validated_data['role_in_project']
        
        try:
            member_user = User.objects.get(email=email, is_active=True)
            member_role = get_user_role(member_user)
            
            if member_role != 3:
                return Response({
                    "success": False,
                    "message": "Only Member users (role_id=3) can be invited to projects."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            existing = ProjectMember.objects.filter(
                project=project,
                user=member_user
            ).first()
            
            if existing:
                return Response({
                    "success": False,
                    "message": f"User already invited. Status: {existing.status}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            invitation = ProjectMember.objects.create(
                project=project,
                user=member_user,
                invited_by=request.user,
                role_in_project=role_in_project,
                status='Pending'
            )
            
            return Response({
                "success": True,
                "message": "Member invited successfully!",
                "data": ProjectMemberSerializer(invitation).data
            }, status=status.HTTP_201_CREATED)
            
        except User.DoesNotExist:
            return Response({
                "success": False,
                "message": "User with this email not found."
            }, status=status.HTTP_404_NOT_FOUND)


class AcceptInvitationView(APIView):
    """
    API for MEMBER users to accept project invitations
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, invitation_id):
        """Accept invitation"""
        user_role = get_user_role(request.user)
        
        if user_role != 3:
            return Response({
                "success": False,
                "message": "Only Member users can accept invitations."
            }, status=status.HTTP_403_FORBIDDEN)
        
        invitation = get_object_or_404(
            ProjectMember,
            id=invitation_id,
            user=request.user,
            status='Pending'
        )
        
        invitation.status = 'Accepted'
        invitation.accepted_at = timezone.now()
        invitation.save()
        
        return Response({
            "success": True,
            "message": "Invitation accepted successfully!",
            "data": ProjectMemberSerializer(invitation).data
        }, status=status.HTTP_200_OK)


class RejectInvitationView(APIView):
    """
    API for MEMBER users to reject project invitations
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, invitation_id):
        """Reject invitation"""
        user_role = get_user_role(request.user)
        
        if user_role != 3:
            return Response({
                "success": False,
                "message": "Only Member users can reject invitations."
            }, status=status.HTTP_403_FORBIDDEN)
        
        invitation = get_object_or_404(
            ProjectMember,
            id=invitation_id,
            user=request.user,
            status='Pending'
        )
        
        invitation.status = 'Rejected'
        invitation.save()
        
        return Response({
            "success": True,
            "message": "Invitation rejected successfully!"
        }, status=status.HTTP_200_OK)


class MyInvitationsView(APIView):
    """
    API for MEMBER users to see all their pending invitations
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all invitations for current member"""
        user_role = get_user_role(request.user)
        
        if user_role != 3:
            return Response({
                "success": False,
                "message": "Only Member users can view invitations."
            }, status=status.HTTP_403_FORBIDDEN)
        
        invitations = ProjectMember.objects.filter(
            user=request.user
        ).select_related('project', 'invited_by')
        
        serializer = ProjectMemberSerializer(invitations, many=True)
        
        return Response({
            "success": True,
            "count": invitations.count(),
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class RemoveMemberView(APIView):
    """
    API for ORGANIZATION to remove members from their projects
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def delete(self, request, project_id, member_id):
        """Remove member from project"""
        user_role = get_user_role(request.user)
        
        if user_role != 2:
            return Response({
                "success": False,
                "message": "Only project owner can remove members."
            }, status=status.HTTP_403_FORBIDDEN)
        
        project = get_object_or_404(
            Project,
            id=project_id,
            created_by=request.user,
            is_active=True
        )
        
        membership = get_object_or_404(
            ProjectMember,
            id=member_id,
            project=project
        )
        
        membership.delete()
        
        return Response({
            "success": True,
            "message": "Member removed from project successfully!"
        }, status=status.HTTP_200_OK)


class TestCaseListCreateView(APIView):
    """
    API to list and create testcases
    - ORGANIZATION: Can create in their own projects
    - MEMBER: Can create in projects they're invited to (with Tester/Contributor role)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get all testcases user has access to"""
        user_role = get_user_role(request.user)
        project_id = request.query_params.get('project_id')
        priority = request.query_params.get('priority')
        
        if user_role == 2:  # Organization
            testcases = TestCase.objects.filter(
                project__created_by=request.user,
                is_active=True
            )
        elif user_role == 3:  # Member
            project_ids = ProjectMember.objects.filter(
                user=request.user,
                status='Accepted'
            ).values_list('project_id', flat=True)
            
            testcases = TestCase.objects.filter(
                project_id__in=project_ids,
                is_active=True
            )
        else:
            return Response({
                "success": False,
                "message": "Invalid user role."
            }, status=status.HTTP_403_FORBIDDEN)
        
        if project_id:
            testcases = testcases.filter(project_id=project_id)
        
        if priority:
            testcases = testcases.filter(priority=priority)
        
        testcases = testcases.select_related('project', 'created_by')
        serializer = TestCaseSerializer(testcases, many=True)
        
        return Response({
            "success": True,
            "count": testcases.count(),
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    @transaction.atomic
    def post(self, request):
        """Create new testcase"""
        user_role = get_user_role(request.user)
        project_id = request.data.get('project')
        
        if not project_id:
            return Response({
                "success": False,
                "message": "Project ID is required."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if user_role == 2:  # Organization
            project = get_object_or_404(
                Project,
                id=project_id,
                created_by=request.user,
                is_active=True
            )
        elif user_role == 3:  # Member
            membership = ProjectMember.objects.filter(
                project_id=int(project_id),  # ✅ Ensure integer
                user_id=int(request.user.id),
                status='Accepted',
                role_in_project__in=['Tester', 'Contributor']
            ).first()
            
            if not membership:
                return Response({
                    "success": False,
                    "message": "You don't have permission to create testcases in this project."
                }, status=status.HTTP_403_FORBIDDEN)
            
            project = membership.project
        else:
            return Response({
                "success": False,
                "message": "Invalid user role."
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TestCaseSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        testcase = serializer.save(created_by=request.user)
        
        return Response({
            "success": True,
            "message": "Test case created successfully!",
            "data": TestCaseSerializer(testcase).data
        }, status=status.HTTP_201_CREATED)


class TestCaseDetailView(APIView):
    """API to get, update, delete specific testcase"""
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk, user):
        """Get testcase and verify access"""
        user_role = get_user_role(user)
        
        if user_role == 2:  # Organization
            return get_object_or_404(
                TestCase,
                pk=pk,
                project__created_by=user,
                is_active=True
            )
        elif user_role == 3:  # Member
            testcase = get_object_or_404(TestCase, pk=pk, is_active=True)
            
            membership = ProjectMember.objects.filter(
                project=testcase.project,
                user=user,
                status='Accepted'
            ).first()
            
            if not membership:
                return None
            
            return testcase
        
        return None
    
    def get(self, request, pk):
        """Get single testcase"""
        testcase = self.get_object(pk, request.user)
        
        if not testcase:
            return Response({
                "success": False,
                "message": "TestCase not found or access denied."
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TestCaseSerializer(testcase)
        
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    @transaction.atomic
    def put(self, request, pk):
        """Update testcase"""
        user_role = get_user_role(request.user)
        testcase = self.get_object(pk, request.user)
        
        if not testcase:
            return Response({
                "success": False,
                "message": "TestCase not found or access denied."
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if member has edit permission
        if user_role == 3:
            membership = ProjectMember.objects.filter(
                project=testcase.project,
                user=request.user,
                status='Accepted',
                role_in_project__in=['Tester', 'Contributor']
            ).first()
            
            if not membership:
                return Response({
                    "success": False,
                    "message": "You don't have permission to edit testcases in this project."
                }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TestCaseSerializer(testcase, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Validation failed.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        return Response({
            "success": True,
            "message": "Test case updated successfully!",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    @transaction.atomic
    def delete(self, request, pk):
        """Delete testcase"""
        user_role = get_user_role(request.user)
        testcase = self.get_object(pk, request.user)
        
        if not testcase:
            return Response({
                "success": False,
                "message": "TestCase not found or access denied."
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if member has delete permission
        if user_role == 3:
            membership = ProjectMember.objects.filter(
                project=testcase.project,
                user=request.user,
                status='Accepted',
                role_in_project='Contributor'  # Only Contributors can delete
            ).first()
            
            if not membership:
                return Response({
                    "success": False,
                    "message": "You don't have permission to delete testcases in this project."
                }, status=status.HTTP_403_FORBIDDEN)
        
        testcase.is_active = False
        testcase.save()
        
        return Response({
            "success": True,
            "message": "Test case deleted successfully!"
        }, status=status.HTTP_200_OK)


class ProjectStatsView(APIView):
    """
    API to get statistics for a project
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, project_id):
        """Get project statistics"""
        user_role = get_user_role(request.user)
        
        # Verify access
        if user_role == 2:  # Organization
            project = get_object_or_404(
                Project,
                id=project_id,
                created_by=request.user,
                is_active=True
            )
        elif user_role == 3:  # Member
            membership = ProjectMember.objects.filter(
                project_id=project_id,
                user=request.user,
                status='Accepted'
            ).first()
            
            if not membership:
                return Response({
                    "success": False,
                    "message": "Project not found or access denied."
                }, status=status.HTTP_404_NOT_FOUND)
            
            project = membership.project
        else:
            return Response({
                "success": False,
                "message": "Invalid user role."
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get statistics
        testcases = TestCase.objects.filter(project=project, is_active=True)
        
        stats = {
            "project_name": project.name,
            "total_testcases": testcases.count(),
            "priority_breakdown": {
                "High": testcases.filter(priority='High').count(),
                "Medium": testcases.filter(priority='Medium').count(),
                "Low": testcases.filter(priority='Low').count(),
            },
            "total_members": ProjectMember.objects.filter(
                project=project,
                status='Accepted'
            ).count(),
            "pending_invitations": ProjectMember.objects.filter(
                project=project,
                status='Pending'
            ).count(),
        }
        
        return Response({
            "success": True,
            "data": stats
        }, status=status.HTTP_200_OK)
    
