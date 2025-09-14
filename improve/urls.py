from django.urls import path
from . import views

app_name = 'improve'

urlpatterns = [
    path('', views.ImproveDashboardView.as_view(), name='dashboard'),
    path('upload/', views.ImprovementProjectUploadView.as_view(), name='upload'),
    path('download-template/', views.ImprovementProjectTemplateDownloadView.as_view(), name='download_template'),
    path('history/', views.ImprovementProjectHistoryView.as_view(), name='history'),
    path('download-file/<int:project_id>/', views.ImprovementProjectFileDownloadView.as_view(), name='download_file'),
    path('error-log/<int:project_id>/', views.ImprovementProjectErrorLogView.as_view(), name='error_log'),
]