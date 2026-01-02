from django.urls import path
from .views import (
    ProjectListCreateView,
    ProjectDetailView,
    InviteMemberView,
    AcceptInvitationView,
    RejectInvitationView,
    MyInvitationsView,
    RemoveMemberView,
    TestCaseListCreateView,
    TestCaseDetailView,
    ProjectStatsView,
    ExecuteTestCaseView,
    ExecutionHistoryView,
    ExecutionDetailView
)

urlpatterns = [
    # Project URLs
    path('projects/', ProjectListCreateView.as_view(), name='project-list-create'),
    path('projects/<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('projects/<int:project_id>/stats/', ProjectStatsView.as_view(), name='project-stats'),
    
    # Project Member URLs
    path('projects/<int:project_id>/invite/', InviteMemberView.as_view(), name='invite-member'),
    path('projects/<int:project_id>/members/<int:member_id>/remove/', RemoveMemberView.as_view(), name='remove-member'),
    
    # Invitation URLs
    path('invitations/', MyInvitationsView.as_view(), name='my-invitations'),
    path('invitations/<int:invitation_id>/accept/', AcceptInvitationView.as_view(), name='accept-invitation'),
    path('invitations/<int:invitation_id>/reject/', RejectInvitationView.as_view(), name='reject-invitation'),
    
    # TestCase URLs
    path('testcases/', TestCaseListCreateView.as_view(), name='testcase-list-create'),
    path('testcases/<int:pk>/', TestCaseDetailView.as_view(), name='testcase-detail'),

    # Execution APIs
    path('testcases/<int:testcase_id>/execute/', ExecuteTestCaseView.as_view(), name='execute-testcase'),
    path('executions/', ExecutionHistoryView.as_view(), name='execution-history'),
    path('executions/<int:execution_id>/', ExecutionDetailView.as_view(), name='execution-detail'),
]