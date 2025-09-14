from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('', views.ReviewDashboardView.as_view(), name='dashboard'),
    path('new/', views.NewReviewView.as_view(), name='new_review'),
    path('<int:pk>/edit/', views.EditReviewView.as_view(), name='edit_review'),
    path('<int:pk>/meeting/', views.ReviewMeetingView.as_view(), name='meeting'),
    path('<int:pk>/meeting/commitments/', views.CommitmentsTabView.as_view(), name='commitments'),
    path('<int:pk>/meeting/fpi/', views.FPITabView.as_view(), name='fpi'),
    path('<int:pk>/meeting/gpi/', views.GPITabView.as_view(), name='gpi'),
    path('<int:pk>/meeting/ppi/', views.PPITabView.as_view(), name='ppi'),
    path('<int:pk>/meeting/issues/', views.IssuesTabView.as_view(), name='issues'),
    path('<int:pk>/meeting/action-summary/', views.ActionSummaryTabView.as_view(), name='action_summary'),
    path('<int:pk>/finalize/', views.FinalizeReviewView.as_view(), name='finalize'),
]