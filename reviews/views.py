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

        # Get FPI numbers tracking for the team
        fpi_numbers = NumbersTracking.objects.filter(
            team=meeting.team,
            source_type='fpi',
            year=prev_year,
            month_number=prev_month,
            tracking_type='monthly'
        ).select_related('fpi_parameter', 'assigned_to')

        # Group by main head for P&L format
        fpi_by_head = {}
        for number in fpi_numbers:
            main_head = number.fpi_parameter.main_head
            if main_head not in fpi_by_head:
                fpi_by_head[main_head] = []
            fpi_by_head[main_head].append(number)

        context.update({
            'meeting': meeting,
            'fpi_by_head': fpi_by_head,
            'previous_month': f"{prev_year}-{prev_month:02d}",
        })
        return context


class GPITabView(LoginRequiredMixin, TemplateView):
    """GPI tab with Weekly/Monthly radio buttons as per PRD"""
    template_name = 'reviews/tabs/gpi.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get view type from query params (weekly or monthly)
        view_type = self.request.GET.get('view', 'weekly')

        # Get GPI numbers tracking
        gpi_numbers = NumbersTracking.objects.filter(
            team=meeting.team,
            source_type='gpi',
            tracking_type=view_type
        ).select_related('gpi_parameter', 'assigned_to')

        context.update({
            'meeting': meeting,
            'gpi_numbers': gpi_numbers,
            'view_type': view_type,
        })
        return context


class PPITabView(LoginRequiredMixin, TemplateView):
    """PPI tab with project details and weekly view as per PRD"""
    template_name = 'reviews/tabs/ppi.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get PPI projects for the team
        ppi_projects = PPIProject.objects.filter(
            quarterly_plan__team=meeting.team
        ).select_related('responsible_user', 'quarterly_plan').prefetch_related('tasks')

        # Calculate PPI summary data for the template
        total_projects = ppi_projects.count()

        # For now, provide basic statistics since status tracking is complex
        # This can be enhanced later based on the actual status_history model structure
        completed_projects = 0  # Will need to implement based on actual status logic
        on_track_projects = total_projects  # Assume all are on track for now
        at_risk_projects = 0
        delayed_projects = 0

        completion_percentage = 75.0  # Placeholder percentage

        # Determine overall health based on project count for now
        if total_projects > 0:
            overall_health = 'green'
        else:
            overall_health = 'yellow'

        ppi_data = {
            'total_projects': total_projects,
            'completed_projects': completed_projects,
            'on_track_projects': on_track_projects,
            'at_risk_projects': at_risk_projects,
            'delayed_projects': delayed_projects,
            'completion_percentage': completion_percentage,
            'overall_health': overall_health,
        }

        context.update({
            'meeting': meeting,
            'ppi_projects': ppi_projects,
            'ppi_data': ppi_data,
        })
        return context


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
            if note_text:
                # Get next serial number
                last_note = meeting.review_notes.order_by('serial_number').last()
                next_serial = (last_note.serial_number + 1) if last_note else 1

                ReviewNote.objects.create(
                    review_meeting=meeting,
                    serial_number=next_serial,
                    review_note=note_text,
                    created_by=request.user
                )

        elif action == 'edit':
            note_id = request.POST.get('note_id')
            note_text = request.POST.get('review_note')
            try:
                note = meeting.review_notes.get(id=note_id)
                note.review_note = note_text
                note.save()
            except ReviewNote.DoesNotExist:
                pass

        elif action == 'delete':
            note_id = request.POST.get('note_id')
            try:
                note = meeting.review_notes.get(id=note_id)
                serial_to_delete = note.serial_number
                note.delete()

                # Renumber remaining notes
                for note in meeting.review_notes.filter(serial_number__gt=serial_to_delete):
                    note.serial_number -= 1
                    note.save()
            except ReviewNote.DoesNotExist:
                pass

        return JsonResponse({'success': True})


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
                    created_by=request.user
                )

        elif action == 'edit':
            decision_id = request.POST.get('decision_id')
            decision_text = request.POST.get('decision')
            try:
                decision = meeting.decisions.get(id=decision_id)
                decision.decision = decision_text
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


class ActionItemPopupView(LoginRequiredMixin, TemplateView):
    """Action Item popup as per PRD"""
    template_name = 'reviews/popups/action_items.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        context.update({
            'meeting': meeting,
            'action_items': meeting.review_action_items.all(),
            'teams': Team.objects.filter(is_active=True),
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

            if action_text and due_date and assigned_to_id and assigned_to_team_id:
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()

                    assigned_to = User.objects.get(id=assigned_to_id)
                    assigned_to_team = Team.objects.get(id=assigned_to_team_id)

                    ReviewActionItem.objects.create(
                        review_meeting=meeting,
                        action=action_text,
                        priority=priority,
                        due_date=datetime.strptime(due_date, '%Y-%m-%d').date(),
                        assigned_to=assigned_to,
                        assigned_to_team=assigned_to_team,
                        comments=comments,
                        created_by=request.user
                    )

                    # Also create in implement.Action for tracking
                    from implement.models import Action
                    Action.objects.create(
                        team=assigned_to_team,
                        source='review',
                        action=action_text,
                        priority=priority,
                        assigned_to=assigned_to,
                        original_due_date=datetime.strptime(due_date, '%Y-%m-%d').date(),
                        status='not_started',
                        created_by=request.user,
                        comments=f"From Review meeting: {meeting}"
                    )

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