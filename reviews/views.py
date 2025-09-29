from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import date, datetime
from calendar import monthrange
import json

from .models import ReviewMeeting, ReviewCommitment, ReviewNote, ReviewActionItem, ReviewDecision
from organizations.models import Team
from plans.models import FinancialYear
from implement.models import Action, Issue, NumbersTracking
from plans.models import FPIParameter, GPIParameter, PPIProject


class ReviewDashboardView(LoginRequiredMixin, TemplateView):
    """Review Home Page as per PRD specifications"""
    template_name = 'reviews/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get user's teams where user is in charge (manager)
        if user.role == 'general':
            user_teams = Team.objects.filter(manager=user, is_active=True)
        else:
            user_teams = Team.objects.filter(is_active=True)

        # Filter parameters from request
        team_filter = self.request.GET.get('team', '')
        review_type_filter = self.request.GET.get('review_type', '')
        month_year_filter = self.request.GET.get('month_year', '')

        # Base queryset
        meetings = ReviewMeeting.objects.filter(team__in=user_teams)

        # Apply filters
        if team_filter:
            meetings = meetings.filter(team__id=team_filter)
        if review_type_filter:
            meetings = meetings.filter(review_type=review_type_filter)
        if month_year_filter:
            try:
                month, year = month_year_filter.split('-')
                meetings = meetings.filter(
                    review_date__year=int(year),
                    review_date__month=int(month)
                )
            except ValueError:
                pass

        # Get available months/years for filter dropdown
        available_dates = ReviewMeeting.objects.filter(
            team__in=user_teams
        ).dates('review_date', 'month', order='DESC')

        context.update({
            'user_teams': user_teams,
            'meetings': meetings.select_related('team', 'created_by'),
            'review_types': ReviewMeeting.REVIEW_TYPES,
            'available_dates': available_dates,
            'current_filters': {
                'team': team_filter,
                'review_type': review_type_filter,
                'month_year': month_year_filter,
            }
        })

        return context


class NewReviewView(LoginRequiredMixin, TemplateView):
    """New Review Screen as per PRD specifications"""
    template_name = 'reviews/new_review.html'

    def get_context_data(self, **kwargs):
        print(f"=== NewReviewView GET request ===")
        print(f"User: {self.request.user}")
        print(f"GET parameters: {dict(self.request.GET)}")

        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get user's teams where user is in charge (manager)
        if user.role == 'general':
            teams = Team.objects.filter(manager=user, is_active=True)
        else:
            teams = Team.objects.filter(is_active=True)

        print(f"Found {teams.count()} teams for user")

        context.update({
            'teams': teams,
            'review_types': ReviewMeeting.REVIEW_TYPES,
        })
        return context

    def post(self, request, *args, **kwargs):
        print(f"=== NewReviewView POST request ===")
        print(f"POST data: {dict(request.POST)}")

        team_id = request.POST.get('team')
        review_type = request.POST.get('review_type')
        review_date = request.POST.get('review_date')
        review_time = request.POST.get('review_time')
        manager_name = request.POST.get('manager_name')
        participants = request.POST.getlist('participants')

        print(f"Parsed values:")
        print(f"  team_id: {team_id}")
        print(f"  review_type: {review_type}")
        print(f"  review_date: {review_date}")
        print(f"  review_time: {review_time}")
        print(f"  manager_name: {manager_name}")
        print(f"  participants: {participants}")

        # Basic validation
        if not all([team_id, review_type, review_date, review_time, manager_name]):
            missing_fields = []
            if not team_id: missing_fields.append('team')
            if not review_type: missing_fields.append('review_type')
            if not review_date: missing_fields.append('review_date')
            if not review_time: missing_fields.append('review_time')
            if not manager_name: missing_fields.append('manager_name')

            error_msg = f'Missing required fields: {", ".join(missing_fields)}'
            print(f"Validation error: {error_msg}")
            messages.error(request, error_msg)
            return redirect('reviews:new_review')

        try:
            # Combine date and time
            review_datetime = datetime.strptime(f"{review_date} {review_time}", "%Y-%m-%d %H:%M")
            print(f"Combined datetime: {review_datetime}")

            # Create review meeting
            team = get_object_or_404(Team, id=team_id)
            print(f"Found team: {team}")

            meeting = ReviewMeeting.objects.create(
                # New columns
                team=team,
                review_type=review_type,
                review_date=review_datetime,
                manager_name=manager_name,
                created_by=request.user,

                # Required legacy columns to match database constraints
                meeting_type=review_type,
                meeting_date=review_datetime.date(),
                conducted_by=request.user,
                financial_year=FinancialYear.objects.first(),
                status='scheduled',
                summary='',
                key_decisions='',
                next_steps='',
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            print(f"Created meeting: {meeting}")

            # Add participants
            if participants:
                meeting.participants.set(participants)
                print(f"Added {len(participants)} participants")

            messages.success(request, 'Review meeting created successfully.')
            print(f"Redirecting to meeting: {meeting.id}")
            return redirect('reviews:meeting', pk=meeting.id)

        except Exception as e:
            print(f"Exception occurred: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            messages.error(request, f'Error creating review: {str(e)}')
            return redirect('reviews:new_review')


class ReviewMeetingView(LoginRequiredMixin, TemplateView):
    """Edit/View Review Meeting Screen as per PRD specifications"""
    template_name = 'reviews/meeting.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Check if this review is editable (PRD: if subsequent review exists, view only)
        subsequent_reviews = ReviewMeeting.objects.filter(
            team=meeting.team,
            review_date__gt=meeting.review_date
        ).exists()

        is_editable = not subsequent_reviews

        context.update({
            'meeting': meeting,
            'is_editable': is_editable,
        })

        return context


class CommitmentsTabView(LoginRequiredMixin, TemplateView):
    """Commitments tab - shows pending actions from previous meetings"""
    template_name = 'reviews/tabs/commitments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get all commitments from previous meetings for this team
        commitments = ReviewCommitment.objects.filter(
            review_meeting__team=meeting.team,
            review_meeting__review_date__lt=meeting.review_date
        ).select_related('committed_by', 'review_meeting').order_by('-review_meeting__review_date')

        # Calculate summary statistics
        total_commitments = commitments.count()
        completed = commitments.filter(status='completed').count()
        in_progress = commitments.filter(status='in_progress').count()
        overdue = commitments.filter(target_date__lt=timezone.now().date(), status__in=['pending', 'in_progress']).count()
        due_today = commitments.filter(target_date=timezone.now().date(), status__in=['pending', 'in_progress']).count()

        summary = {
            'total': total_commitments,
            'completed': completed,
            'in_progress': in_progress,
            'overdue': overdue,
            'due_today': due_today,
        }

        context.update({
            'meeting': meeting,
            'commitments': commitments[:20],  # Limit to recent 20 commitments
            'summary': summary,
            'today': timezone.now().date().strftime('%Y-%m-%d'),
        })
        return context


class FPITabView(LoginRequiredMixin, TemplateView):
    """FPI tab with P&L format as per PRD"""
    template_name = 'reviews/tabs/fpi.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Calculate previous month based on review meeting date
        review_date = meeting.review_date.date()
        if review_date.month == 1:
            prev_month = 12
            prev_year = review_date.year - 1
        else:
            prev_month = review_date.month - 1
            prev_year = review_date.year

        # Get the current financial year and quarter
        from plans.models import FinancialYear, QuarterlyPlan
        try:
            current_fy = FinancialYear.objects.filter(
                start_date__lte=review_date,
                end_date__gte=review_date
            ).first()

            if current_fy:
                # Determine current quarter based on review date
                current_quarter = self.get_current_quarter(review_date, current_fy)

                # Get quarterly plan for this team
                quarterly_plan = QuarterlyPlan.objects.filter(
                    team=meeting.team,
                    financial_year=current_fy,
                    quarter=current_quarter
                ).first()

                fpi_by_head = {}
                if quarterly_plan:
                    # Get FPI parameters from quarterly plan, grouped by main head
                    fpi_parameters = quarterly_plan.fpi_parameters.select_related('responsible_user').prefetch_related('milestones')

                    for param in fpi_parameters:
                        main_head = param.get_main_head_display()
                        if main_head not in fpi_by_head:
                            fpi_by_head[main_head] = []

                        # Calculate budget values for previous month
                        prev_month_budget = 0
                        if prev_month <= 3:  # Within current quarter
                            milestone = param.milestones.filter(month_number=prev_month).first()
                            if milestone:
                                prev_month_budget = milestone.budget_value

                        # Calculate next month budget
                        next_month = prev_month + 1 if prev_month < 12 else 1
                        next_month_budget = 0
                        if next_month <= 3:  # Within current quarter
                            milestone = param.milestones.filter(month_number=next_month).first()
                            if milestone:
                                next_month_budget = milestone.budget_value

                        fpi_data = {
                            'parameter': param,
                            'sub_head': param.sub_head,
                            'responsible_user': param.responsible_user,
                            'last_month_budget': prev_month_budget,
                            'last_month_plan': param.current_month_plan or 0,
                            'last_month_actual': param.last_month_actual or 0,
                            'next_month_budget': next_month_budget,
                            'next_month_plan': param.current_month_plan or 0,
                            'explanation': param.explanation,
                        }
                        fpi_by_head[main_head].append(fpi_data)
            else:
                fpi_by_head = {}

        except Exception as e:
            print(f"Error loading FPI data: {e}")
            fpi_by_head = {}

        context.update({
            'meeting': meeting,
            'fpi_by_head': fpi_by_head,
            'previous_month': f"{prev_year}-{prev_month:02d}",
        })
        return context

    def get_current_quarter(self, date, financial_year):
        """Determine current quarter based on date and financial year"""
        start_date = financial_year.start_date
        months_diff = (date.year - start_date.year) * 12 + (date.month - start_date.month)

        if months_diff < 3:
            return '1'
        elif months_diff < 6:
            return '2'
        elif months_diff < 9:
            return '3'
        else:
            return '4'


class GPITabView(LoginRequiredMixin, TemplateView):
    """GPI tab with Weekly/Monthly radio buttons as per PRD"""
    template_name = 'reviews/tabs/gpi.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get view type from query params (weekly or monthly)
        view_type = self.request.GET.get('view', 'weekly')

        # Get the current financial year and quarter
        from plans.models import FinancialYear, QuarterlyPlan
        review_date = meeting.review_date.date()

        current_fy = FinancialYear.objects.filter(
            start_date__lte=review_date,
            end_date__gte=review_date
        ).first()

        quarterly_plan = None
        current_quarter = None
        if current_fy:
            # Determine current quarter based on review date
            current_quarter = self.get_current_quarter(review_date, current_fy)

            # Get quarterly plan for this team
            quarterly_plan = QuarterlyPlan.objects.filter(
                team=meeting.team,
                financial_year=current_fy,
                quarter=current_quarter
            ).first()

        gpi_parameters = []
        if quarterly_plan:
            # Get GPI parameters from quarterly plan, filtered by tracking type
            gpi_parameters = quarterly_plan.gpi_parameters.filter(
                tracking_type=view_type
            ).select_related('responsible_user').prefetch_related('milestones')

        # Calculate current period (week or month) based on review date and financial year
        current_period = 1
        if current_fy and quarterly_plan:
            if view_type == 'weekly':
                # Calculate week within quarter (1-12) based on financial year
                quarter_start_month = ((int(current_quarter) - 1) * 3) + current_fy.start_date.month
                if quarter_start_month > 12:
                    quarter_start_month -= 12
                    quarter_start_year = current_fy.start_date.year + 1
                else:
                    quarter_start_year = current_fy.start_date.year

                from datetime import date
                quarter_start = date(quarter_start_year, quarter_start_month, 1)
                days_diff = (review_date - quarter_start).days
                current_period = min(12, max(1, (days_diff // 7) + 1))
            else:  # monthly
                # Calculate month within quarter (1-3)
                months_since_fy_start = (review_date.year - current_fy.start_date.year) * 12 + (review_date.month - current_fy.start_date.month)
                months_since_quarter_start = months_since_fy_start - ((int(current_quarter) - 1) * 3)
                current_period = max(1, min(3, months_since_quarter_start + 1))

        # Structure GPI data with milestones
        gpi_data = []
        for parameter in gpi_parameters:
            # Get milestones for this parameter
            milestones = parameter.milestones.all().order_by('period_number')
            milestone_data = {}
            for milestone in milestones:
                milestone_data[milestone.period_number] = milestone.budget_value

            # Calculate cumulative values up to current period
            cumulative_budget = sum(milestone_data.get(i, 0) for i in range(1, current_period + 1))

            # For now, use budget as plan/actual (will be enhanced with actual tracking later)
            from decimal import Decimal
            cumulative_plan = cumulative_budget
            cumulative_actual = cumulative_budget * Decimal('0.8')  # Placeholder - 80% achievement

            # Calculate achievement percentage
            if cumulative_budget > 0:
                achievement_percentage = float(cumulative_actual) / float(cumulative_budget) * 100
            else:
                achievement_percentage = 0

            gpi_data.append({
                'parameter': parameter,
                'milestones': milestone_data,
                'cumulative_budget': cumulative_budget,
                'cumulative_plan': cumulative_plan,
                'cumulative_actual': cumulative_actual,
                'current_period': current_period,
                'achievement_percentage': round(achievement_percentage, 1),
            })

        context.update({
            'meeting': meeting,
            'gpi_data': gpi_data,
            'view_type': view_type,
            'current_period': current_period,
            'quarter': current_quarter if current_fy else None,
            'financial_year': current_fy.year if current_fy else None,
        })
        return context

    def get_current_quarter(self, date, financial_year):
        """Determine current quarter based on date and financial year"""
        start_date = financial_year.start_date
        months_diff = (date.year - start_date.year) * 12 + (date.month - start_date.month)

        if months_diff < 3:
            return '1'
        elif months_diff < 6:
            return '2'
        elif months_diff < 9:
            return '3'
        else:
            return '4'


class PPITabView(LoginRequiredMixin, TemplateView):
    """PPI tab with project details and weekly view as per PRD"""
    template_name = 'reviews/tabs/ppi.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get the current financial year and quarter
        from plans.models import FinancialYear, QuarterlyPlan
        review_date = meeting.review_date.date()

        current_fy = FinancialYear.objects.filter(
            start_date__lte=review_date,
            end_date__gte=review_date
        ).first()

        quarterly_plan = None
        current_week = 1
        current_quarter = None
        if current_fy:
            # Determine current quarter based on review date
            current_quarter = self.get_current_quarter(review_date, current_fy)

            # Calculate current week within quarter based on financial year
            quarter_start_month = ((int(current_quarter) - 1) * 3) + current_fy.start_date.month
            if quarter_start_month > 12:
                quarter_start_month -= 12
                quarter_start_year = current_fy.start_date.year + 1
            else:
                quarter_start_year = current_fy.start_date.year

            from datetime import date
            quarter_start = date(quarter_start_year, quarter_start_month, 1)
            days_diff = (review_date - quarter_start).days
            current_week = min(13, max(1, (days_diff // 7) + 1))

            # Get quarterly plan for this team
            quarterly_plan = QuarterlyPlan.objects.filter(
                team=meeting.team,
                financial_year=current_fy,
                quarter=current_quarter
            ).first()

        ppi_projects = []
        if quarterly_plan:
            # Get PPI projects for the team with task details
            ppi_projects = quarterly_plan.ppi_projects.select_related(
                'responsible_user'
            ).prefetch_related(
                'tasks', 'tasks__assigned_to'
            ).all()

        # Enhanced PPI data calculation with task-level analysis
        total_projects = len(ppi_projects)
        completed_projects = 0
        on_track_projects = 0
        at_risk_projects = 0
        delayed_projects = 0
        total_tasks = 0
        completed_tasks = 0

        ppi_project_details = []
        for project in ppi_projects:
            # Get all tasks for this project
            project_tasks = project.tasks.all()
            total_tasks += project_tasks.count()

            # Tasks completed
            project_completed_tasks = project_tasks.filter(is_completed=True)
            completed_tasks += project_completed_tasks.count()

            # Tasks due by current week
            tasks_due_by_now = project_tasks.filter(week_number__lte=current_week)
            completed_by_now = project_completed_tasks.filter(week_number__lte=current_week)

            # Project status calculation
            if tasks_due_by_now.count() == 0:
                project_status = 'not_started'
                project_health = 'yellow'
            else:
                completion_rate = completed_by_now.count() / tasks_due_by_now.count()
                if completion_rate >= 0.9:
                    project_status = 'on_track'
                    project_health = 'green'
                    on_track_projects += 1
                elif completion_rate >= 0.7:
                    project_status = 'at_risk'
                    project_health = 'yellow'
                    at_risk_projects += 1
                else:
                    project_status = 'delayed'
                    project_health = 'red'
                    delayed_projects += 1

            # Check if project is completed (all tasks done)
            if project_tasks.count() > 0 and project_completed_tasks.count() == project_tasks.count():
                completed_projects += 1
                project_status = 'completed'
                project_health = 'green'

            # Weekly task breakdown
            weekly_tasks = {}
            for week in range(1, 14):  # 13 weeks in quarter
                week_tasks = project_tasks.filter(week_number=week)
                weekly_tasks[week] = {
                    'planned': week_tasks.count(),
                    'completed': week_tasks.filter(is_completed=True).count(),
                    'tasks': week_tasks
                }

            ppi_project_details.append({
                'project': project,
                'status': project_status,
                'health': project_health,
                'total_tasks': project_tasks.count(),
                'completed_tasks': project_completed_tasks.count(),
                'completion_percentage': (project_completed_tasks.count() / project_tasks.count() * 100) if project_tasks.count() > 0 else 0,
                'weekly_tasks': weekly_tasks,
                'tasks_due_by_now': tasks_due_by_now.count(),
                'completed_by_now': completed_by_now.count(),
            })

        # Overall completion percentage
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Overall health determination
        if total_projects == 0:
            overall_health = 'gray'
        elif delayed_projects > total_projects * 0.3:
            overall_health = 'red'
        elif at_risk_projects > total_projects * 0.5:
            overall_health = 'yellow'
        else:
            overall_health = 'green'

        ppi_data = {
            'total_projects': total_projects,
            'completed_projects': completed_projects,
            'on_track_projects': on_track_projects,
            'at_risk_projects': at_risk_projects,
            'delayed_projects': delayed_projects,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_percentage': round(completion_percentage, 1),
            'overall_health': overall_health,
        }

        context.update({
            'meeting': meeting,
            'ppi_project_details': ppi_project_details,
            'ppi_data': ppi_data,
            'current_week': current_week,
            'quarter': current_quarter if current_fy else None,
            'financial_year': current_fy.year if current_fy else None,
        })
        return context

    def get_current_quarter(self, date, financial_year):
        """Determine current quarter based on date and financial year"""
        start_date = financial_year.start_date
        months_diff = (date.year - start_date.year) * 12 + (date.month - start_date.month)

        if months_diff < 3:
            return '1'
        elif months_diff < 6:
            return '2'
        elif months_diff < 9:
            return '3'
        else:
            return '4'


class IssuesTabView(LoginRequiredMixin, TemplateView):
    """Issues tab for issue log management as per PRD"""
    template_name = 'reviews/tabs/issues.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get issues for the team
        issues = Issue.objects.filter(
            team=meeting.team
        ).select_related('reported_by')

        context.update({
            'meeting': meeting,
            'issues': issues,
        })
        return context


class ActionSummaryTabView(LoginRequiredMixin, TemplateView):
    """Action Summary tab - shows actions added during this review meeting"""
    template_name = 'reviews/tabs/action_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get action items created during this review meeting
        meeting_actions = meeting.review_action_items.all()

        context.update({
            'meeting': meeting,
            'meeting_actions': meeting_actions,
        })
        return context


# AJAX Views for popups and dynamic content

class ReviewNotesView(LoginRequiredMixin, TemplateView):
    """Review Notes popup as per PRD"""
    template_name = 'reviews/popups/review_notes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        context.update({
            'meeting': meeting,
            'notes': meeting.review_notes.all(),
        })
        return context

    def post(self, request, pk):
        meeting = get_object_or_404(ReviewMeeting, pk=pk)
        action = request.POST.get('action')

        if action == 'add':
            note_text = request.POST.get('review_note')
            note_title = request.POST.get('title', 'Review Note')  # Default title
            if note_text:
                ReviewNote.objects.create(
                    review_meeting=meeting,
                    title=note_title,
                    content=note_text,
                    note_type='general',  # Default type
                    created_by=request.user,
                    created_at=timezone.now()
                )

        elif action == 'edit':
            note_id = request.POST.get('note_id')
            note_text = request.POST.get('review_note')
            note_title = request.POST.get('title', 'Review Note')
            try:
                note = meeting.review_notes.get(id=note_id)
                note.content = note_text
                note.title = note_title
                note.save()
            except ReviewNote.DoesNotExist:
                pass

        elif action == 'delete':
            note_id = request.POST.get('note_id')
            try:
                note = meeting.review_notes.get(id=note_id)
                note.delete()
            except ReviewNote.DoesNotExist:
                pass

        return JsonResponse({'success': True})

    def patch(self, request, pk):
        meeting = get_object_or_404(ReviewMeeting, pk=pk)
        try:
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'move':
                note_id = data.get('note_id')
                direction = data.get('direction')

                try:
                    note = meeting.review_notes.get(id=note_id)
                    notes = list(meeting.review_notes.all().order_by('created_at', 'id'))
                    current_index = notes.index(note)

                    if direction == 'up' and current_index > 0:
                        # Swap creation times with previous note
                        prev_note = notes[current_index - 1]
                        note.created_at, prev_note.created_at = prev_note.created_at, note.created_at
                        note.save()
                        prev_note.save()
                    elif direction == 'down' and current_index < len(notes) - 1:
                        # Swap creation times with next note
                        next_note = notes[current_index + 1]
                        note.created_at, next_note.created_at = next_note.created_at, note.created_at
                        note.save()
                        next_note.save()
                    elif direction == 'top' and current_index > 0:
                        # Move to top - set creation time before the first note
                        first_note = notes[0]
                        note.created_at = first_note.created_at - timezone.timedelta(seconds=1)
                        note.save()
                    elif direction == 'bottom' and current_index < len(notes) - 1:
                        # Move to bottom - set creation time after the last note
                        last_note = notes[-1]
                        note.created_at = last_note.created_at + timezone.timedelta(seconds=1)
                        note.save()

                    return JsonResponse({'success': True})
                except ReviewNote.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Note not found'})

            return JsonResponse({'success': False, 'error': 'Invalid action'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class DecisionsView(LoginRequiredMixin, TemplateView):
    """Decisions popup as per PRD"""
    template_name = 'reviews/popups/decisions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        context.update({
            'meeting': meeting,
            'decisions': meeting.decisions.all(),
        })
        return context

    def post(self, request, pk):
        meeting = get_object_or_404(ReviewMeeting, pk=pk)
        action = request.POST.get('action')

        if action == 'add':
            decision_text = request.POST.get('decision')
            if decision_text:
                # Get next serial number
                last_decision = meeting.decisions.order_by('serial_number').last()
                next_serial = (last_decision.serial_number + 1) if last_decision else 1

                ReviewDecision.objects.create(
                    review_meeting=meeting,
                    serial_number=next_serial,
                    decision=decision_text,
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )

        elif action == 'edit':
            decision_id = request.POST.get('decision_id')
            decision_text = request.POST.get('decision')
            try:
                decision = meeting.decisions.get(id=decision_id)
                decision.decision = decision_text
                decision.updated_at = timezone.now()
                decision.save()
            except ReviewDecision.DoesNotExist:
                pass

        elif action == 'delete':
            decision_id = request.POST.get('decision_id')
            try:
                decision = meeting.decisions.get(id=decision_id)
                serial_to_delete = decision.serial_number
                decision.delete()

                # Renumber remaining decisions
                for decision in meeting.decisions.filter(serial_number__gt=serial_to_delete):
                    decision.serial_number -= 1
                    decision.save()
            except ReviewDecision.DoesNotExist:
                pass

        return JsonResponse({'success': True})

    def patch(self, request, pk):
        meeting = get_object_or_404(ReviewMeeting, pk=pk)
        try:
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'move':
                decision_id = data.get('decision_id')
                direction = data.get('direction')

                try:
                    decision = meeting.decisions.get(id=decision_id)
                    decisions = list(meeting.decisions.all().order_by('serial_number'))
                    current_index = decisions.index(decision)

                    if direction == 'up' and current_index > 0:
                        # Swap serial numbers with previous decision using temporary value
                        prev_decision = decisions[current_index - 1]
                        temp_serial = 9999  # Temporary serial number

                        current_serial = decision.serial_number
                        prev_serial = prev_decision.serial_number

                        # Move current decision to temp position
                        decision.serial_number = temp_serial
                        decision.save()

                        # Move previous decision to current position
                        prev_decision.serial_number = current_serial
                        prev_decision.save()

                        # Move current decision to previous position
                        decision.serial_number = prev_serial
                        decision.save()

                    elif direction == 'down' and current_index < len(decisions) - 1:
                        # Swap serial numbers with next decision using temporary value
                        next_decision = decisions[current_index + 1]
                        temp_serial = 9999  # Temporary serial number

                        current_serial = decision.serial_number
                        next_serial = next_decision.serial_number

                        # Move current decision to temp position
                        decision.serial_number = temp_serial
                        decision.save()

                        # Move next decision to current position
                        next_decision.serial_number = current_serial
                        next_decision.save()

                        # Move current decision to next position
                        decision.serial_number = next_serial
                        decision.save()

                    elif direction == 'top' and current_index > 0:
                        # Move to top - shift all decisions down by 1
                        original_serial = decision.serial_number
                        # First move current decision to temporary position
                        decision.serial_number = 9999
                        decision.save()

                        # Shift all decisions with serial < original_serial down by 1
                        for d in decisions[:current_index]:
                            d.serial_number += 1
                            d.save()

                        # Move decision to position 1
                        decision.serial_number = 1
                        decision.save()

                    elif direction == 'bottom' and current_index < len(decisions) - 1:
                        # Move to bottom - shift all decisions up by 1
                        original_serial = decision.serial_number
                        max_serial = len(decisions)

                        # First move current decision to temporary position
                        decision.serial_number = 9999
                        decision.save()

                        # Shift all decisions with serial > original_serial up by 1
                        for d in decisions[current_index + 1:]:
                            d.serial_number -= 1
                            d.save()

                        # Move decision to bottom position
                        decision.serial_number = max_serial
                        decision.save()

                    return JsonResponse({'success': True})
                except ReviewDecision.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Decision not found'})

            return JsonResponse({'success': False, 'error': 'Invalid action'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class ActionItemPopupView(LoginRequiredMixin, TemplateView):
    """Action Item popup as per PRD"""
    template_name = 'reviews/popups/action_items.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get action items for this meeting
        action_items = meeting.review_action_items.all()

        # Calculate action summary statistics
        action_summary = {
            'total': action_items.count(),
            'high_priority': action_items.filter(priority='high').count(),
            'due_today': action_items.filter(due_date=timezone.now().date()).count(),
            'completed': action_items.filter(status='completed').count(),
        }

        # Get team members from the meeting's team
        from django.contrib.auth import get_user_model
        User = get_user_model()
        team_members = User.objects.filter(is_active=True).order_by('first_name', 'last_name')

        # Get all active teams
        available_teams = Team.objects.filter(is_active=True).order_by('name')

        context.update({
            'meeting': meeting,
            'action_items': action_items,
            'action_summary': action_summary,
            'team_members': team_members,
            'available_teams': available_teams,
            'today': timezone.now().date().strftime('%Y-%m-%d'),
        })
        return context

    def post(self, request, pk):
        meeting = get_object_or_404(ReviewMeeting, pk=pk)
        action = request.POST.get('action')

        if action == 'add':
            action_text = request.POST.get('action_description')
            priority = request.POST.get('priority')
            due_date = request.POST.get('due_date')
            assigned_to_id = request.POST.get('assigned_to')
            assigned_to_team_id = request.POST.get('assigned_to_team')
            comments = request.POST.get('comments', '')

            if action_text and due_date and assigned_to_id:
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()

                    assigned_to = User.objects.get(id=assigned_to_id)

                    ReviewActionItem.objects.create(
                        review_meeting=meeting,
                        action_description=action_text,
                        priority=priority,
                        due_date=datetime.strptime(due_date, '%Y-%m-%d').date(),
                        assigned_to=assigned_to,
                        status='pending',
                        completion_notes=comments,
                        created_at=timezone.now(),
                        updated_at=timezone.now()
                    )

                    # Note: Review action item created successfully
                    # Optional: Could sync to implement.Action later if needed

                except Exception as e:
                    return JsonResponse({'success': False, 'error': str(e)})

        elif action == 'edit':
            # Handle edit action
            pass

        elif action == 'delete':
            item_id = request.POST.get('item_id')
            try:
                item = meeting.review_action_items.get(id=item_id)
                item.delete()
            except ReviewActionItem.DoesNotExist:
                pass

        return JsonResponse({'success': True})