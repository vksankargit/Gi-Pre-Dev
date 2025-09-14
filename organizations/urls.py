from django.urls import path
from . import views

app_name = 'organizations'

urlpatterns = [
    path('', views.OrganizationListView.as_view(), name='list'),
    path('create/', views.OrganizationCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.OrganizationEditView.as_view(), name='edit'),
    path('<int:pk>/toggle-status/', views.OrganizationToggleStatusView.as_view(), name='toggle_status'),
    path('<int:pk>/coordinators/', views.OrganizationCoordinatorsView.as_view(), name='coordinators'),
    path('users/', views.UserListView.as_view(), name='users'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('users/<int:pk>/toggle-status/', views.UserToggleStatusView.as_view(), name='user_toggle_status'),
    path('teams/', views.TeamListView.as_view(), name='teams'),
    path('teams/create/', views.TeamCreateView.as_view(), name='team_create'),
    path('teams/<int:pk>/edit/', views.TeamEditView.as_view(), name='team_edit'),
    path('teams/<int:pk>/toggle-status/', views.TeamToggleStatusView.as_view(), name='team_toggle_status'),
    path('teams/<int:pk>/members/', views.TeamMembersView.as_view(), name='team_members'),

    # Coordinator management AJAX endpoints
    path('ajax/add-coordinator/', views.AddCoordinatorView.as_view(), name='add_coordinator'),
    path('ajax/get-coordinator/<int:pk>/', views.GetCoordinatorView.as_view(), name='get_coordinator'),
    path('ajax/edit-coordinator/<int:pk>/', views.EditCoordinatorView.as_view(), name='edit_coordinator'),
    path('ajax/toggle-coordinator/<int:pk>/', views.ToggleCoordinatorView.as_view(), name='toggle_coordinator'),
    path('ajax/get-users/<int:organization_id>/', views.GetUsersView.as_view(), name='get_users'),
]