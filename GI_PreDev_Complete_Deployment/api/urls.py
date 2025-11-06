from django.urls import path
from . import views

urlpatterns = [
    path('user-teams/', views.UserTeamsAPIView.as_view(), name='user_teams'),
    path('issue-teams/', views.IssueTeamsAPIView.as_view(), name='issue_teams'),
    path('team-members/<int:team_id>/', views.TeamMembersAPIView.as_view(), name='team_members'),
    path('team-members-reassign/<int:team_id>/', views.TeamMembersForReassignAPIView.as_view(), name='team_members_reassign'),
    path('create-issue/', views.CreateIssueAPIView.as_view(), name='create_issue'),
    path('create-action/', views.CreateActionAPIView.as_view(), name='create_action'),
    path('parameter-actions/', views.ParameterActionsAPIView.as_view(), name='parameter_actions'),
    path('parameter-issues/', views.ParameterIssuesAPIView.as_view(), name='parameter_issues'),
    path('project-actions/', views.ProjectActionsAPIView.as_view(), name='project_actions'),
    path('project-issues/', views.ProjectIssuesAPIView.as_view(), name='project_issues'),
    path('action-issues/', views.ActionIssuesAPIView.as_view(), name='action_issues'),
    path('action-actions/', views.ActionActionsAPIView.as_view(), name='action_actions'),
]