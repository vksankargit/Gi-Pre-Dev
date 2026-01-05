from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # Main Review Pages
    path('', views.ReviewDashboardView.as_view(), name='dashboard'),
    path('new/', views.NewReviewView.as_view(), name='new_review'),
    path('<int:pk>/meeting/', views.ReviewMeetingView.as_view(), name='meeting'),

    # Tab Views
    path('<int:pk>/meeting/commitments/', views.CommitmentsTabView.as_view(), name='commitments'),
    path('<int:pk>/meeting/fpi/', views.FPITabView.as_view(), name='fpi'),
    path('<int:pk>/meeting/gpi/', views.GPITabView.as_view(), name='gpi'),
    path('<int:pk>/meeting/ppi/', views.PPITabView.as_view(), name='ppi'),
    path('<int:pk>/meeting/issues/', views.IssuesTabView.as_view(), name='issues'),
    path('<int:pk>/meeting/action-summary/', views.ActionSummaryTabView.as_view(), name='action_summary'),

    # Popup Views - GET for display, POST for actions
    path('<int:pk>/notes/', views.ReviewNotesView.as_view(), name='review_notes'),
    path('<int:pk>/decisions/', views.DecisionsView.as_view(), name='decisions'),
    path('<int:pk>/action-items/', views.ActionItemPopupView.as_view(), name='action_items'),
    path('<int:pk>/parameter-actions/', views.ParameterActionItemsView.as_view(), name='parameter_actions'),
    path('<int:pk>/issues/', views.ParameterIssuesView.as_view(), name='issues'),

    # Data saving endpoints
    path('<int:pk>/save-fpi-data/', views.SaveFPIDataView.as_view(), name='save_fpi_data'),
    path('<int:pk>/save-gpi-data/', views.SaveGPIDataView.as_view(), name='save_gpi_data'),
    path('<int:pk>/update-project-status/', views.UpdateProjectStatusView.as_view(), name='update_project_status'),

    # Project details and week tasks
    path('<int:pk>/project-details/', views.ProjectDetailsView.as_view(), name='project_details'),
    path('<int:pk>/week-tasks/', views.WeekTasksView.as_view(), name='week_tasks'),

    # Parameter details
    path('<int:pk>/fpi-details/', views.FPIDetailsView.as_view(), name='fpi_details'),
    path('<int:pk>/gpi-details/', views.GPIDetailsView.as_view(), name='gpi_details'),

    # GPI data loading endpoints
    path('<int:pk>/gpi-weekly-data/', views.GPIWeeklyDataView.as_view(), name='gpi_weekly_data'),
    path('<int:pk>/gpi-monthly-data/', views.GPIMonthlyDataView.as_view(), name='gpi_monthly_data'),
    path('<int:pk>/gpi-quarterly-data/', views.GPIQuarterlyDataView.as_view(), name='gpi_quarterly_data'),
    path('<int:pk>/gpi-annual-data/', views.GPIAnnualDataView.as_view(), name='gpi_annual_data'),

    # PPI endpoints
    path('<int:pk>/ppi-details/', views.PPIDetailsView.as_view(), name='ppi_details'),
    path('<int:pk>/update-ppi-status/', views.UpdatePPIStatusView.as_view(), name='update_ppi_status'),

    # Issue status updates
    path('<int:pk>/update-issue-status/', views.UpdateIssueStatusView.as_view(), name='update_issue_status'),
    path('<int:pk>/revert-issue-status/', views.RevertIssueStatusView.as_view(), name='revert_issue_status'),

    # Action deletion
    path('<int:pk>/delete-action/', views.DeleteActionView.as_view(), name='delete_action'),

    # Action status changes (Commitments tab)
    path('action/mark-done/', views.mark_action_done, name='mark_action_done'),
    path('action/mark-complete/', views.mark_action_complete, name='mark_action_complete'),
    path('action/undo-status/', views.undo_action_status, name='undo_action_status'),
    path('action/mark-on-hold/', views.mark_action_on_hold, name='mark_action_on_hold'),
    path('action/resume/', views.resume_action, name='resume_action'),
    path('action/drop/', views.drop_action, name='drop_action'),
    path('action/mark-active/', views.mark_action_active, name='mark_action_active'),

    # Meeting finalization and PDF
    path('<int:pk>/finalize/', views.FinalizeMeetingView.as_view(), name='finalize_meeting'),
    path('<int:pk>/download-pdf/', views.DownloadPDFView.as_view(), name='download_pdf'),
]