from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import ReviewMeeting, Commitment, ReviewNote, ActionItem
from organizations.models import Team
from plans.models import FinancialYear
from datetime import date
from django.utils import timezone


class ReviewDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get user's teams
        user_teams = []
        if user.role == 'general':
            user_teams = Team.objects.filter(members__member=user, members__is_active=True)
        else:
            user_teams = Team.objects.filter(is_active=True)

        # Get recent meetings
        recent_meetings = ReviewMeeting.objects.filter(
            team__in=user_teams
        ).select_related('team', 'financial_year', 'conducted_by')[:10]

        # Get upcoming meetings (draft status)
        upcoming_meetings = ReviewMeeting.objects.filter(
            team__in=user_teams,
            status='draft',
            meeting_date__gte=date.today()
        ).select_related('team', 'financial_year', 'conducted_by')

        # Statistics
        total_meetings = ReviewMeeting.objects.filter(team__in=user_teams).count()
        completed_meetings = ReviewMeeting.objects.filter(team__in=user_teams, status='completed').count()
        pending_actions = ActionItem.objects.filter(
            review_meeting__team__in=user_teams,
            status__in=['open', 'in_progress']
        ).count()

        context.update({
            'recent_meetings': recent_meetings,
            'upcoming_meetings': upcoming_meetings,
            'total_meetings': total_meetings,
            'completed_meetings': completed_meetings,
            'pending_actions': pending_actions,
            'user_teams': user_teams,
        })

        return context


class NewReviewView(LoginRequiredMixin, CreateView):
    model = ReviewMeeting
    template_name = 'reviews/new_review.html'
    fields = ['team', 'financial_year', 'meeting_type', 'meeting_date', 'week_number', 'month_number', 'quarter_number']
    success_url = reverse_lazy('reviews:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get user's teams
        if user.role == 'general':
            teams = Team.objects.filter(members__member=user, members__is_active=True)
        else:
            teams = Team.objects.filter(is_active=True)

        context.update({
            'teams': teams,
            'financial_years': FinancialYear.objects.all().order_by('-start_date'),
        })
        return context

    def form_valid(self, form):
        form.instance.conducted_by = self.request.user
        messages.success(self.request, 'Review meeting created successfully.')
        return super().form_valid(form)


class EditReviewView(LoginRequiredMixin, UpdateView):
    model = ReviewMeeting
    template_name = 'reviews/edit_review.html'
    fields = ['meeting_date', 'status', 'summary', 'key_decisions', 'next_steps']
    success_url = reverse_lazy('reviews:dashboard')

    def form_valid(self, form):
        messages.success(self.request, 'Review meeting updated successfully.')
        return super().form_valid(form)


class ReviewMeetingView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/meeting.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        context.update({
            'meeting': meeting,
            'commitments': meeting.commitments.all(),
            'notes': meeting.notes.all(),
            'action_items': meeting.action_items.all(),
        })

        return context


class CommitmentsTabView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/tabs/commitments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])
        context['meeting'] = meeting
        context['commitments'] = meeting.commitments.all().select_related('committed_by')
        return context


class FPITabView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/tabs/fpi.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get FPI data from plans app
        from plans.models import FPIParameter
        from implement.models import NumbersTracking

        fpi_parameters = FPIParameter.objects.filter(
            quarterly_plan__team=meeting.team
        ).select_related('responsible_user')

        # Get numbers tracking for FPI
        fpi_numbers = NumbersTracking.objects.filter(
            team=meeting.team,
            source_type='fpi'
        ).select_related('fpi_parameter', 'assigned_to')

        context.update({
            'meeting': meeting,
            'fpi_parameters': fpi_parameters,
            'fpi_numbers': fpi_numbers,
        })
        return context


class GPITabView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/tabs/gpi.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get GPI data from plans app
        from plans.models import GPIParameter
        from implement.models import NumbersTracking

        gpi_parameters = GPIParameter.objects.filter(
            quarterly_plan__team=meeting.team
        ).select_related('responsible_user')

        # Get numbers tracking for GPI
        gpi_numbers = NumbersTracking.objects.filter(
            team=meeting.team,
            source_type='gpi'
        ).select_related('gpi_parameter', 'assigned_to')

        context.update({
            'meeting': meeting,
            'gpi_parameters': gpi_parameters,
            'gpi_numbers': gpi_numbers,
        })
        return context


class PPITabView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/tabs/ppi.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get PPI data from plans app
        from plans.models import PPIProject
        from implement.models import ProjectStatus

        ppi_projects = PPIProject.objects.filter(
            quarterly_plan__team=meeting.team
        ).select_related('responsible_user', 'quarterly_plan').prefetch_related('status_history')

        context.update({
            'meeting': meeting,
            'ppi_projects': ppi_projects,
        })
        return context


class IssuesTabView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/tabs/issues.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get issues from implement app
        from implement.models import Issue

        issues = Issue.objects.filter(
            team=meeting.team
        ).select_related('reported_by')

        context.update({
            'meeting': meeting,
            'issues': issues,
        })
        return context


class ActionSummaryTabView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/tabs/action_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get actions from implement app
        from implement.models import Action

        actions = Action.objects.filter(
            team=meeting.team
        ).select_related('assigned_to', 'created_by')

        context.update({
            'meeting': meeting,
            'actions': actions,
            'meeting_action_items': meeting.action_items.all(),
        })
        return context


class FinalizeReviewView(LoginRequiredMixin, TemplateView):
    template_name = 'reviews/finalize.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])
        context['meeting'] = meeting
        return context

    def post(self, request, pk):
        meeting = get_object_or_404(ReviewMeeting, pk=pk)
        meeting.status = 'completed'
        meeting.finalized_by = request.user
        meeting.finalized_at = timezone.now()
        meeting.save()

        messages.success(request, 'Review meeting finalized successfully.')
        return redirect('reviews:dashboard')
