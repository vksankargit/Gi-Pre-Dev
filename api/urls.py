from django.urls import path
from . import views

urlpatterns = [
    path('user-teams/', views.UserTeamsAPIView.as_view(), name='user_teams'),
    path('issue-teams/', views.IssueTeamsAPIView.as_view(), name='issue_teams'),
    path('team-members/<int:team_id>/', views.TeamMembersAPIView.as_view(), name='team_members'),
    path('team-members-reassign/<int:team_id>/', views.TeamMembersForReassignAPIView.as_view(), name='team_members_reassign'),
    path('create-issue/', views.CreateIssueAPIView.as_view(), name='create_issue'),
    path('create-action/', views.CreateActionAPIView.as_view(), name='create_action'),
]