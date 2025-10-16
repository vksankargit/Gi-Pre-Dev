from django.urls import path
from . import views

app_name = 'plans'

urlpatterns = [
    path('', views.PlanDashboardView.as_view(), name='dashboard'),
    path('annual/upload/', views.AnnualPlanUploadView.as_view(), name='annual_upload'),
    path('annual/download-template/', views.AnnualPlanTemplateDownloadView.as_view(), name='annual_template'),
    path('annual/history/', views.AnnualPlanHistoryView.as_view(), name='annual_history'),
    path('quarterly/upload/', views.QuarterlyPlanUploadView.as_view(), name='quarterly_upload'),
    path('quarterly/download-template/', views.QuarterlyPlanTemplateDownloadView.as_view(), name='quarterly_template'),
    path('quarterly/history/', views.QuarterlyPlanHistoryView.as_view(), name='quarterly_history'),
    path('download-file/<int:plan_id>/<str:plan_type>/', views.PlanFileDownloadView.as_view(), name='download_file'),
    path('download-history-file/<int:history_id>/<str:plan_type>/', views.PlanHistoryFileDownloadView.as_view(), name='download_history_file'),
    path('error-log/<int:plan_id>/<str:plan_type>/', views.PlanErrorLogView.as_view(), name='error_log'),
]