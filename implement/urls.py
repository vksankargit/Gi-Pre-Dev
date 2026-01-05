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
    path('action/create-sub/', views.SubActionCreateView.as_view(), name='sub_action_create'),
    path('action/<int:pk>/details/', views.SubActionDetailsView.as_view(), name='sub_action_details'),
    path('action/<int:pk>/update/', views.SubActionUpdateView.as_view(), name='sub_action_update'),
    path('action/<int:pk>/delete/', views.SubActionDeleteView.as_view(), name='sub_action_delete'),
    path('issue/create/', views.IssueCreateView.as_view(), name='issue_create'),
    path('project/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('project/<int:pk>/edit/', views.ProjectEditView.as_view(), name='project_edit'),
    path('improvement-project/<int:pk>/edit/', views.ImprovementProjectEditView.as_view(), name='improvement_project_edit'),
    path('project/<int:pk>/reassign/', views.ProjectReassignView.as_view(), name='project_reassign'),
    path('project/<int:pk>/toggle-complete/', views.ProjectToggleCompleteView.as_view(), name='project_toggle_complete'),
    path('project/<int:pk>/history/', views.ProjectHistoryView.as_view(), name='project_history'),
    path('project/<int:pk>/details/', views.ProjectDetailsView.as_view(), name='project_details'),
    path('project/<int:pk>/week-tasks/', views.WeekTasksView.as_view(), name='week_tasks'),
    path('save-number/', views.SaveNumberView.as_view(), name='save_number'),
    path('reassign-parameter/', views.ReassignParameterView.as_view(), name='reassign_parameter'),
    path('reassign-task/', views.ReassignTaskView.as_view(), name='reassign_task'),
    path('task/<int:task_id>/history/', views.TaskHistoryView.as_view(), name='task_history'),
    path('parameter/<int:param_id>/comments/', views.ParameterCommentsView.as_view(), name='parameter_comments'),
    path('get-team-members/', views.GetTeamMembersView.as_view(), name='get_team_members'),
    path('toggle-action-status/', views.ToggleActionStatusView.as_view(), name='toggle_action_status'),
]