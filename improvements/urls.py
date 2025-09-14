from django.urls import path
from . import views

app_name = 'improvements'

urlpatterns = [
    path('', views.ImprovementDashboardView.as_view(), name='dashboard'),
    path('upload/', views.ImprovementUploadView.as_view(), name='upload'),
    path('template/', views.ImprovementTemplateDownloadView.as_view(), name='template'),
    path('history/', views.ImprovementHistoryView.as_view(), name='history'),
    path('analyse/', views.ImprovementAnalysisView.as_view(), name='analyse'),
]