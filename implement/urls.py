from django.urls import path
from . import views

app_name = 'implement'

urlpatterns = [
    path('', views.ImplementDashboardView.as_view(), name='dashboard'),
    path('my-numbers/', views.MyNumbersView.as_view(), name='my_numbers'),
    path('my-projects/', views.MyProjectsView.as_view(), name='my_projects'),
    path('my-todo/', views.MyTodoView.as_view(), name='my_todo'),
    path('action/create/', views.ActionCreateView.as_view(), name='action_create'),
    path('action/<int:pk>/edit/', views.ActionEditView.as_view(), name='action_edit'),
    path('action/<int:pk>/reassign/', views.ActionReassignView.as_view(), name='action_reassign'),
    path('action/<int:pk>/toggle-complete/', views.ActionToggleCompleteView.as_view(), name='action_toggle_complete'),
    path('action/<int:pk>/reject/', views.ActionRejectView.as_view(), name='action_reject'),
    path('action/<int:pk>/history/', views.ActionHistoryView.as_view(), name='action_history'),
    path('action/<int:pk>/sub-actions/', views.SubActionView.as_view(), name='sub_actions'),
    path('issue/create/', views.IssueCreateView.as_view(), name='issue_create'),
    path('project/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('project/<int:pk>/edit/', views.ProjectEditView.as_view(), name='project_edit'),
    path('project/<int:pk>/reassign/', views.ProjectReassignView.as_view(), name='project_reassign'),
    path('project/<int:pk>/toggle-complete/', views.ProjectToggleCompleteView.as_view(), name='project_toggle_complete'),
    path('project/<int:pk>/history/', views.ProjectHistoryView.as_view(), name='project_history'),
]