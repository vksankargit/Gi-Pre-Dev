from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    path('', views.ReviewHomeView.as_view(), name='home'),
    path('create/', views.ReviewCreateView.as_view(), name='create'),
    path('<int:pk>/meeting/', views.ReviewMeetingView.as_view(), name='meeting'),
    path('<int:pk>/participants/', views.ReviewParticipantsView.as_view(), name='participants'),
    path('meeting/<int:meeting_id>/notes/', views.ReviewNotesView.as_view(), name='notes'),
    path('meeting/<int:meeting_id>/decisions/', views.ReviewDecisionsView.as_view(), name='decisions'),
    path('meeting/<int:meeting_id>/actions/', views.ReviewActionsView.as_view(), name='actions'),
    path('meeting/<int:meeting_id>/issues/', views.ReviewIssuesView.as_view(), name='issues'),
]