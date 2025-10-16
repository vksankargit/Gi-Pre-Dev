from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, UpdateView, View
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from datetime import date, datetime
from calendar import monthrange
import json

from .models import ReviewMeeting, ReviewCommitment, ReviewNote, ReviewActionItem, ReviewDecision
from organizations.models import Team
from plans.models import FinancialYear
from implement.models import Action, Issue, NumbersTracking
from plans.models import FPIParameter, GPIParameter, PPIProject
from accounts.utils import get_effective_user


class ReviewDashboardView(LoginRequiredMixin, TemplateView):
    """Review Home Page as per PRD specifications"""
    template_name = 'reviews/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_effective_user(self.request)

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

            # Calculate week/month number for the review based on review date
            meeting_date = review_datetime.date()
            current_month = meeting_date.month

            # Determine financial year and quarter
            if current_month >= 4:
                fy_start_year = meeting_date.year
                current_quarter_num = ((current_month - 4) // 3) + 1
            else:
                fy_start_year = meeting_date.year - 1
                current_quarter_num = 4

            # Get financial year
            fy_end_year = fy_start_year + 1
            current_fy_string = f"FY {fy_start_year % 100:02d}-{fy_end_year % 100:02d}"
            financial_year = FinancialYear.objects.filter(year=current_fy_string).first()
            if not financial_year:
                financial_year = FinancialYear.objects.first()

            # Calculate week/month number within quarter
            quarter_start_months = {1: 4, 2: 7, 3: 10, 4: 1}
            quarter_start_month = quarter_start_months[current_quarter_num]

            if current_quarter_num == 4:
                quarter_start_year = fy_start_year + 1
            else:
                quarter_start_year = fy_start_year

            quarter_start_date = meeting_date.replace(year=quarter_start_year, month=quarter_start_month, day=1)
            days_into_quarter = (meeting_date - quarter_start_date).days
            week_in_quarter = (days_into_quarter // 7) + 1
            month_in_quarter = ((current_month - quarter_start_month) % 12) + 1
            if month_in_quarter > 3:
                month_in_quarter = ((current_month - quarter_start_month + 12) % 12) + 1

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
                financial_year=financial_year,
                status='scheduled',
                summary='',
                key_decisions='',
                next_steps='',
                created_at=timezone.now(),
                updated_at=timezone.now(),

                # Add week/month/quarter numbers
                week_number=week_in_quarter if review_type == 'weekly' else None,
                month_number=month_in_quarter if review_type == 'monthly' else None,
                quarter_number=current_quarter_num
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
    """Commitments tab - shows all actions from previous review meetings for this team"""
    template_name = 'reviews/tabs/commitments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get all actions from previous review meetings for this team
        previous_actions = ReviewActionItem.objects.filter(
            review_meeting__team=meeting.team,
            review_meeting__review_date__lt=meeting.review_date
        ).select_related('assigned_to', 'assigned_to_team', 'review_meeting').order_by('-review_meeting__review_date', '-created_at')

        # Calculate summary statistics
        total_actions = previous_actions.count()
        completed = previous_actions.filter(status='completed').count()
        in_progress = previous_actions.filter(status='in_progress').count()
        pending = previous_actions.filter(status='pending').count()
        overdue = previous_actions.filter(due_date__lt=timezone.now().date(), status__in=['pending', 'in_progress']).count()
        due_today = previous_actions.filter(due_date=timezone.now().date(), status__in=['pending', 'in_progress']).count()

        summary = {
            'total': total_actions,
            'completed': completed,
            'in_progress': in_progress,
            'pending': pending,
            'overdue': overdue,
            'due_today': due_today,
        }

        context.update({
            'meeting': meeting,
            'actions': previous_actions,
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

                    # Calculate current quarter month numbers (1-3 within quarter)
                    current_month = review_date.month
                    quarter_start_month = ((int(current_quarter) - 1) * 3) + current_fy.start_date.month
                    if quarter_start_month > 12:
                        quarter_start_month -= 12
                    current_quarter_month = current_month - quarter_start_month + 1
                    if current_quarter_month <= 0:
                        current_quarter_month += 12  # Handle year boundary
                    current_quarter_month = max(1, min(3, current_quarter_month))

                    last_quarter_month = current_quarter_month - 1 if current_quarter_month > 1 else 3

                    for param in fpi_parameters:
                        # Add budget values to the parameter object like Implement page does
                        last_month_milestone = param.milestones.filter(month_number=last_quarter_month).first()
                        current_month_milestone = param.milestones.filter(month_number=current_quarter_month).first()

                        param.last_month_budget = last_month_milestone.budget_value if last_month_milestone else 0
                        param.current_month_budget = current_month_milestone.budget_value if current_month_milestone else 0

                        main_head = param.get_main_head_display()
                        # Convert spaces to underscores for template compatibility
                        main_head_key = main_head.replace(' ', '_')
                        if main_head_key not in fpi_by_head:
                            fpi_by_head[main_head_key] = []

                        fpi_data = {
                            'parameter': param,
                            'sub_head': param.sub_head,
                            'responsible_user': param.responsible_user,
                            'main_head_display': main_head,  # Store original display name
                        }
                        fpi_by_head[main_head_key].append(fpi_data)

                # Calculate totals for each main head section
                section_totals = {}
                for main_head, parameters in fpi_by_head.items():
                    totals = {
                        'last_month_budget': 0,
                        'last_month_goal': 0,
                        'last_month_actual': 0,
                        'current_month_budget': 0,
                        'current_month_plan': 0,
                    }

                    for param_data in parameters:
                        param = param_data['parameter']
                        totals['last_month_budget'] += float(param.last_month_budget or 0)
                        totals['last_month_goal'] += float(param.last_month_goal or 0)
                        totals['last_month_actual'] += float(param.last_month_actual or 0)
                        totals['current_month_budget'] += float(param.current_month_budget or 0)
                        totals['current_month_plan'] += float(param.current_month_plan or 0)

                    # Store section totals for calculations
                    section_totals[main_head] = totals

                    # Add totals to the first parameter data for easy access in template
                    if parameters:
                        parameters[0]['totals'] = totals

                # Calculate derived sections using underscore keys
                revenue_totals = section_totals.get('Revenue', {})
                variable_cost_totals = section_totals.get('Variable_Cost', {})
                operating_expenses_totals = section_totals.get('Operating_Expenses', {})
                other_expenses_totals = section_totals.get('Other_Expenses', {})

                # Gross Profit = Revenue - Variable Cost
                gross_profit_totals = {
                    'last_month_budget': revenue_totals.get('last_month_budget', 0) - variable_cost_totals.get('last_month_budget', 0),
                    'last_month_goal': revenue_totals.get('last_month_goal', 0) - variable_cost_totals.get('last_month_goal', 0),
                    'last_month_actual': revenue_totals.get('last_month_actual', 0) - variable_cost_totals.get('last_month_actual', 0),
                    'current_month_budget': revenue_totals.get('current_month_budget', 0) - variable_cost_totals.get('current_month_budget', 0),
                    'current_month_plan': revenue_totals.get('current_month_plan', 0) - variable_cost_totals.get('current_month_plan', 0),
                }

                # EBITDA = Gross Profit - Operating Expenses
                ebitda_totals = {
                    'last_month_budget': gross_profit_totals['last_month_budget'] - operating_expenses_totals.get('last_month_budget', 0),
                    'last_month_goal': gross_profit_totals['last_month_goal'] - operating_expenses_totals.get('last_month_goal', 0),
                    'last_month_actual': gross_profit_totals['last_month_actual'] - operating_expenses_totals.get('last_month_actual', 0),
                    'current_month_budget': gross_profit_totals['current_month_budget'] - operating_expenses_totals.get('current_month_budget', 0),
                    'current_month_plan': gross_profit_totals['current_month_plan'] - operating_expenses_totals.get('current_month_plan', 0),
                }

                # Net Profit = EBITDA - Other Expenses
                net_profit_totals = {
                    'last_month_budget': ebitda_totals['last_month_budget'] - other_expenses_totals.get('last_month_budget', 0),
                    'last_month_goal': ebitda_totals['last_month_goal'] - other_expenses_totals.get('last_month_goal', 0),
                    'last_month_actual': ebitda_totals['last_month_actual'] - other_expenses_totals.get('last_month_actual', 0),
                    'current_month_budget': ebitda_totals['current_month_budget'] - other_expenses_totals.get('current_month_budget', 0),
                    'current_month_plan': ebitda_totals['current_month_plan'] - other_expenses_totals.get('current_month_plan', 0),
                }

                # Store calculated sections for template access (use underscore keys)
                # Always create calculated sections, even with zero values
                calculated_sections = {
                    'Gross_Profit': gross_profit_totals,
                    'EBITDA': ebitda_totals,
                    'Net_Profit': net_profit_totals,
                }


            else:
                fpi_by_head = {}
                # Create empty calculated sections even when no data
                calculated_sections = {
                    'Gross_Profit': {
                        'last_month_budget': 0, 'last_month_goal': 0, 'last_month_actual': 0,
                        'current_month_budget': 0, 'current_month_plan': 0
                    },
                    'EBITDA': {
                        'last_month_budget': 0, 'last_month_goal': 0, 'last_month_actual': 0,
                        'current_month_budget': 0, 'current_month_plan': 0
                    },
                    'Net_Profit': {
                        'last_month_budget': 0, 'last_month_goal': 0, 'last_month_actual': 0,
                        'current_month_budget': 0, 'current_month_plan': 0
                    }
                }

        except Exception as e:
            print(f"Error loading FPI data: {e}")
            fpi_by_head = {}
            # Create empty calculated sections even on error
            calculated_sections = {
                'Gross_Profit': {
                    'last_month_budget': 0, 'last_month_goal': 0, 'last_month_actual': 0,
                    'current_month_budget': 0, 'current_month_plan': 0
                },
                'EBITDA': {
                    'last_month_budget': 0, 'last_month_goal': 0, 'last_month_actual': 0,
                    'current_month_budget': 0, 'current_month_plan': 0
                },
                'Net_Profit': {
                    'last_month_budget': 0, 'last_month_goal': 0, 'last_month_actual': 0,
                    'current_month_budget': 0, 'current_month_plan': 0
                }
            }

        context.update({
            'meeting': meeting,
            'fpi_by_head': fpi_by_head,
            'calculated_sections': calculated_sections,
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
    """GPI tab with Weekly/Monthly tabs - displays GPI data from quarterly plan"""
    template_name = 'reviews/tabs/gpi.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get the current financial year and quarter
        from plans.models import FinancialYear, QuarterlyPlan
        review_date = meeting.review_date.date()

        weekly_gpi_data = []
        monthly_gpi_data = []

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

                if quarterly_plan:
                    # Calculate current week and month within quarter
                    quarter_start_month = ((int(current_quarter) - 1) * 3) + current_fy.start_date.month
                    if quarter_start_month > 12:
                        quarter_start_month -= 12
                        quarter_start_year = current_fy.start_date.year + 1
                    else:
                        quarter_start_year = current_fy.start_date.year

                    from datetime import date
                    quarter_start = date(quarter_start_year, quarter_start_month, 1)
                    days_diff = (review_date - quarter_start).days
                    current_week = min(12, max(1, (days_diff // 7) + 1))
                    last_week = current_week - 1 if current_week > 1 else 12

                    # Calculate current month within quarter (1-3)
                    current_month = review_date.month
                    current_quarter_month = current_month - quarter_start_month + 1
                    if current_quarter_month <= 0:
                        current_quarter_month += 12
                    current_quarter_month = max(1, min(3, current_quarter_month))
                    last_quarter_month = current_quarter_month - 1 if current_quarter_month > 1 else 3

                    # Get WEEKLY GPI parameters from quarterly plan
                    weekly_parameters = quarterly_plan.gpi_parameters.filter(
                        tracking_type='weekly'
                    ).select_related('responsible_user').prefetch_related('milestones')

                    for param in weekly_parameters:
                        # Get budget values from milestones (weeks)
                        last_week_milestone = param.milestones.filter(period_number=last_week).first()
                        current_week_milestone = param.milestones.filter(period_number=current_week).first()

                        param.last_week_budget = last_week_milestone.budget_value if last_week_milestone else 0
                        param.current_week_budget = current_week_milestone.budget_value if current_week_milestone else 0

                        weekly_gpi_data.append({
                            'parameter': param,
                            'last_week_budget': param.last_week_budget,
                            'last_week_goal': param.last_week_goal if hasattr(param, 'last_week_goal') else '',
                            'last_week_actual': param.last_week_actual if hasattr(param, 'last_week_actual') else '',
                            'current_week_budget': param.current_week_budget,
                            'current_week_goal': param.current_week_plan if hasattr(param, 'current_week_plan') else '',
                            'comments': param.explanation if hasattr(param, 'explanation') else '',
                        })

                    # Get MONTHLY GPI parameters from quarterly plan
                    monthly_parameters = quarterly_plan.gpi_parameters.filter(
                        tracking_type='monthly'
                    ).select_related('responsible_user').prefetch_related('milestones')

                    for param in monthly_parameters:
                        # Get budget values from milestones (months) - GPIMilestone uses period_number for both weeks and months
                        last_month_milestone = param.milestones.filter(period_number=last_quarter_month).first()
                        current_month_milestone = param.milestones.filter(period_number=current_quarter_month).first()

                        param.last_month_budget = last_month_milestone.budget_value if last_month_milestone else 0
                        param.current_month_budget = current_month_milestone.budget_value if current_month_milestone else 0

                        monthly_gpi_data.append({
                            'parameter': param,
                            'last_month_budget': param.last_month_budget,
                            'last_month_goal': param.last_month_goal if hasattr(param, 'last_month_goal') else '',
                            'last_month_actual': param.last_month_actual if hasattr(param, 'last_month_actual') else '',
                            'current_month_budget': param.current_month_budget,
                            'current_month_goal': param.current_month_plan if hasattr(param, 'current_month_plan') else '',
                            'comments': param.explanation if hasattr(param, 'explanation') else '',
                        })

        except Exception as e:
            print(f"Error loading GPI data: {e}")
            import traceback
            traceback.print_exc()

        context.update({
            'meeting': meeting,
            'weekly_gpi_data': weekly_gpi_data,
            'monthly_gpi_data': monthly_gpi_data,
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

        # Get both PPI projects and Improvement projects for the TEAM (not just user)
        ppi_projects = []
        improvement_projects = []

        if quarterly_plan:
            # Get PPI projects for the team with task details and status history
            ppi_projects = quarterly_plan.ppi_projects.select_related(
                'responsible_user'
            ).prefetch_related(
                'tasks', 'tasks__assigned_to', 'status_history'
            ).all()

        # Get improvement projects for the team in this quarter
        from improve.models import ImprovementProject
        if current_fy and current_quarter:
            # Format FY string (e.g., "FY 25-26")
            fy_string = current_fy.year
            quarter_string = f"Q{current_quarter}"

            # Get improvement projects for this team, quarter, and FY
            # The quarter field contains both FY and quarter like "FY 25-26 – Q2"
            from django.db.models import Q
            improvement_projects = ImprovementProject.objects.filter(
                Q(upload__team=meeting.team) &
                Q(upload__quarter__icontains=quarter_string) &
                Q(upload__quarter__icontains=fy_string)
            ).select_related(
                'upload__team',
                'upload__financial_year',
                'responsible_user'
            ).prefetch_related('tasks')

        # Combine all projects for unified processing
        all_projects = []

        # Process PPI projects
        for project in ppi_projects:
            project.project_type = 'PPI'
            project.project_name = project.name
            project.completion_criteria = project.completion_criteria
            project.original_due_date = project.end_date
            project.team = quarterly_plan.team if quarterly_plan else meeting.team
            all_projects.append(project)

        # Process Improvement projects - wrap them to match PPI interface
        for imp_project in improvement_projects:
            # Create wrapper to make improvement project compatible
            class ImpProjectWrapper:
                def __init__(self, imp_proj):
                    self.id = imp_proj.id
                    self.project_type = 'Improvement'
                    self.project_name = imp_proj.name
                    self.completion_criteria = imp_proj.completion_criteria
                    self.original_due_date = imp_proj.end_date
                    self.responsible_user = imp_proj.responsible_user
                    self.team = imp_proj.upload.team
                    self._imp_project = imp_proj

                def tasks(self):
                    return self._imp_project.tasks

                @property
                def tasks(self):
                    return self._imp_project.tasks

            wrapped_project = ImpProjectWrapper(imp_project)
            # Copy tasks relationship
            wrapped_project._tasks_qs = imp_project.tasks
            all_projects.append(wrapped_project)

        # Enhanced PPI data calculation with task-level analysis
        total_projects = len(all_projects)
        completed_projects = 0
        on_track_projects = 0
        at_risk_projects = 0
        delayed_projects = 0
        total_tasks = 0
        completed_tasks = 0

        ppi_project_details = []
        for project in all_projects:
            # Get tasks from either PPI project or wrapped improvement project
            if hasattr(project, '_tasks_qs'):
                project_tasks = project._tasks_qs.all()
            else:
                project_tasks = project.tasks.all()

            total_tasks += project_tasks.count()

            # Tasks completed
            project_completed_tasks = project_tasks.filter(is_completed=True)
            completed_tasks += project_completed_tasks.count()

            # Tasks due by current week
            tasks_due_by_now = project_tasks.filter(week_number__lte=current_week)
            completed_by_now = project_completed_tasks.filter(week_number__lte=current_week)

            # Get actual project status from database
            project_status = 'on_track'  # Default status
            project_health = 'green'
            completion_percentage_from_status = None

            if project.project_type == 'Improvement':
                # For improvement projects, get status from the model directly
                project_status = project._imp_project.status if hasattr(project, '_imp_project') else 'on_track'
            else:
                # For PPI projects, get latest status from prefetched status_history
                if hasattr(project, 'status_history') and project.status_history.exists():
                    latest_status = project.status_history.first()  # Already ordered by -updated_at in model
                    project_status = latest_status.status
                    completion_percentage_from_status = float(latest_status.completion_percentage)
                else:
                    # If no status history, calculate based on completion
                    if tasks_due_by_now.count() == 0:
                        project_status = 'on_track'
                    else:
                        completion_rate = completed_by_now.count() / tasks_due_by_now.count()
                        if completion_rate >= 0.9:
                            project_status = 'on_track'
                        elif completion_rate >= 0.7:
                            project_status = 'at_risk'
                        else:
                            project_status = 'danger'

            # Map status to health
            if project_status == 'completed':
                project_health = 'green'
                completed_projects += 1
            elif project_status == 'on_track':
                project_health = 'green'
                on_track_projects += 1
            elif project_status == 'at_risk':
                project_health = 'yellow'
                at_risk_projects += 1
            elif project_status in ['danger', 'delayed']:
                project_health = 'red'
                delayed_projects += 1
            else:
                project_health = 'yellow'

            # Weekly task breakdown
            weekly_tasks = {}
            for week in range(1, 14):  # 13 weeks in quarter
                week_tasks = project_tasks.filter(week_number=week)
                weekly_tasks[week] = {
                    'planned': week_tasks.count(),
                    'completed': week_tasks.filter(is_completed=True).count(),
                    'tasks': week_tasks
                }

            # Get status display text
            status_display_map = {
                'on_track': 'On Track',
                'at_risk': 'At Risk',
                'delayed': 'Danger',
                'danger': 'Danger',
                'completed': 'Completed',
                'not_started': 'Not Started',
                'on_hold': 'On Hold'
            }

            # Get revised due date (for PPI projects from status history, for Improvement from model)
            revised_due_date = None
            if project.project_type == 'Improvement':
                # For improvement projects, check if there's a status history with revised date
                from improve.models import ImprovementProjectStatus
                latest_status = ImprovementProjectStatus.objects.filter(
                    project_id=project.id
                ).order_by('-updated_at').first()
                if latest_status:
                    revised_due_date = latest_status.revised_due_date
            else:
                # For PPI projects, check status_history
                from implement.models import ProjectStatus
                latest_status = ProjectStatus.objects.filter(
                    project_id=project.id
                ).order_by('-updated_at').first()
                if latest_status:
                    revised_due_date = latest_status.revised_due_date

            # Use completion percentage from status history if available, otherwise calculate from tasks
            if completion_percentage_from_status is not None:
                display_completion_percentage = completion_percentage_from_status
            else:
                display_completion_percentage = (project_completed_tasks.count() / project_tasks.count() * 100) if project_tasks.count() > 0 else 0

            # Check if all tasks are completed
            all_tasks_completed = project_tasks.count() > 0 and project_completed_tasks.count() == project_tasks.count()

            # Get previous status (second latest from history)
            previous_status = None
            if project.project_type == 'Improvement':
                from improve.models import ImprovementProjectStatus
                status_history = ImprovementProjectStatus.objects.filter(
                    project_id=project.id
                ).order_by('-updated_at')
                if status_history.count() >= 2:
                    previous_status = status_history[1].status
            else:
                from implement.models import ProjectStatus
                status_history = ProjectStatus.objects.filter(
                    project_id=project.id
                ).order_by('-updated_at')
                if status_history.count() >= 2:
                    previous_status = status_history[1].status

            ppi_project_details.append({
                'project': project,
                'status': project_status,
                'status_display': status_display_map.get(project_status, project_status.replace('_', ' ').title()),
                'health': project_health,
                'total_tasks': project_tasks.count(),
                'completed_tasks': project_completed_tasks.count(),
                'completion_percentage': display_completion_percentage,
                'weekly_tasks': weekly_tasks,
                'tasks_due_by_now': tasks_due_by_now.count(),
                'completed_by_now': completed_by_now.count(),
                'revised_due_date': revised_due_date,
                'all_tasks_completed': all_tasks_completed,
                'previous_status': previous_status,
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

        # Create quarter display string
        current_quarter_display = f"{current_quarter} - {current_fy.year}" if current_fy and current_quarter else "No Quarter Data"

        context.update({
            'meeting': meeting,
            'ppi_project_details': ppi_project_details,
            'ppi_data': ppi_data,
            'current_week': current_week,
            'quarter': current_quarter if current_fy else None,
            'financial_year': current_fy.year if current_fy else None,
            'current_quarter_display': current_quarter_display,
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

        # Get issues for the team with action counts
        issues = Issue.objects.filter(
            team=meeting.team
        ).select_related('reported_by', 'escalated_to_team').prefetch_related('related_actions')

        # Add action counts to each issue
        issues_with_counts = []
        for issue in issues:
            total_actions = issue.related_actions.count()
            completed_actions = issue.related_actions.filter(status='completed').count()
            issue.action_count = f"{completed_actions}/{total_actions}" if total_actions > 0 else "0/0"
            issues_with_counts.append(issue)

        # Get teams where user is a member (for escalation)
        from django.db.models import Q
        user_teams = Team.objects.filter(
            Q(manager=self.request.user) |
            Q(members__member=self.request.user, members__is_active=True),
            is_active=True
        ).distinct().exclude(id=meeting.team.id)

        context.update({
            'meeting': meeting,
            'issues': issues_with_counts,
            'user_teams': user_teams,
        })
        return context


class ActionSummaryTabView(LoginRequiredMixin, TemplateView):
    """Action Summary tab - shows actions added during this review meeting"""
    template_name = 'reviews/tabs/action_summary.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get action items created during this review meeting
        action_items = meeting.review_action_items.all()

        # Calculate summary statistics
        total = action_items.count()
        completed = action_items.filter(status='completed').count()
        in_progress = action_items.filter(status='in_progress').count()
        pending = action_items.filter(status='pending').count()
        overdue = action_items.filter(due_date__lt=timezone.now().date(), status__in=['pending', 'in_progress']).count()
        completion_rate = (completed / total * 100) if total > 0 else 0

        # Group by category (parameter_type)
        by_category = {
            'commitments': action_items.filter(parameter_type__isnull=True).count(),
            'review_items': action_items.filter(parameter_type='fpi').count() + action_items.filter(parameter_type='gpi').count() + action_items.filter(parameter_type='ppi').count(),
            'issues': 0,  # Not tracked separately yet
            'improvements': 0,  # Not tracked separately yet
        }

        action_summary = {
            'total': total,
            'completed': completed,
            'in_progress': in_progress,
            'pending': pending,
            'overdue': overdue,
            'completion_rate': completion_rate,
            'by_category': by_category,
        }

        context.update({
            'meeting': meeting,
            'action_items': action_items,
            'action_summary': action_summary,
            'today': timezone.now().date().strftime('%Y-%m-%d'),
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
                return JsonResponse({
                    'success': True,
                    'note': {
                        'review_note': note.content,
                        'title': note.title
                    }
                })
            except ReviewNote.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Note not found'})

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
        from django.db import transaction
        meeting = get_object_or_404(ReviewMeeting, pk=pk)
        try:
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'move':
                decision_id = data.get('decision_id')
                direction = data.get('direction')

                try:
                    with transaction.atomic():
                        decision = meeting.decisions.get(id=decision_id)
                        decisions = list(meeting.decisions.all().order_by('serial_number'))
                        current_index = decisions.index(decision)

                        if direction == 'up' and current_index > 0:
                            # Swap serial numbers with previous decision using negative temporary value
                            prev_decision = decisions[current_index - 1]
                            temp_serial = -decision.id  # Use negative ID to ensure uniqueness

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
                            # Swap serial numbers with next decision using negative temporary value
                            next_decision = decisions[current_index + 1]
                            temp_serial = -decision.id  # Use negative ID to ensure uniqueness

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
                            # First move current decision to temporary negative position
                            decision.serial_number = -decision.id
                            decision.save()

                            # Shift all decisions with serial < original_serial down by 1
                            # Process in reverse order to avoid UNIQUE constraint violations
                            for d in reversed(decisions[:current_index]):
                                d.serial_number += 1
                                d.save()

                            # Move decision to position 1
                            decision.serial_number = 1
                            decision.save()

                        elif direction == 'bottom' and current_index < len(decisions) - 1:
                            # Move to bottom - shift all decisions up by 1
                            original_serial = decision.serial_number
                            max_serial = len(decisions)

                            # First move current decision to temporary negative position
                            decision.serial_number = -decision.id
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

    def get_template_names(self):
        # Check if this is an edit, reassign, or history request
        action = self.request.GET.get('action')
        if action == 'edit':
            return ['reviews/popups/edit_action_item.html']
        elif action == 'reassign':
            return ['reviews/popups/reassign_action.html']
        elif action == 'history':
            return ['reviews/popups/action_history.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Check if this is an edit, reassign, or history request
        action = self.request.GET.get('action')
        action_id = self.request.GET.get('id')

        if action in ['edit', 'reassign', 'history'] and action_id:
            # Load action for editing/reassigning
            action_item = get_object_or_404(ReviewActionItem, id=action_id)

            # Get team members and available teams
            from django.contrib.auth import get_user_model
            User = get_user_model()
            team_members = User.objects.filter(is_active=True).order_by('first_name', 'last_name')

            available_teams = Team.objects.filter(
                is_active=True,
                manager=self.request.user
            ).order_by('name')

            context.update({
                'meeting': meeting,
                'action': action_item,
                'team_members': team_members,
                'available_teams': available_teams,
            })
            return context

        # Check if parameter context is provided
        parameter_type = self.request.GET.get('parameter_type')
        parameter_id = self.request.GET.get('parameter_id')
        parameter_name = None

        # Get the parameter name if parameter context is provided
        if parameter_type and parameter_id:
            from plans.models import FPIParameter, GPIParameter, PPIProject
            from improve.models import ImprovementProject
            try:
                if parameter_type == 'fpi':
                    param = FPIParameter.objects.get(id=parameter_id)
                    parameter_name = param.sub_head
                elif parameter_type == 'gpi':
                    param = GPIParameter.objects.get(id=parameter_id)
                    parameter_name = param.name
                elif parameter_type == 'ppi':
                    param = PPIProject.objects.get(id=parameter_id)
                    parameter_name = param.name
                elif parameter_type == 'improvement':
                    param = ImprovementProject.objects.get(id=parameter_id)
                    parameter_name = param.name
            except Exception as e:
                print(f"Error fetching parameter name: {e}")

        # Get action items for this meeting (filtered by parameter if provided)
        action_items = meeting.review_action_items.all()
        if parameter_type and parameter_id:
            # Show only actions for this specific parameter
            action_items = action_items.filter(
                parameter_type=parameter_type,
                parameter_id=parameter_id
            )
        else:
            # Show only generic actions (not tied to any parameter)
            action_items = action_items.filter(
                parameter_type__isnull=True,
                parameter_id__isnull=True
            )

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

        # Get teams where the logged-in user is the manager
        available_teams = Team.objects.filter(
            is_active=True,
            manager=self.request.user
        ).order_by('name')

        context.update({
            'meeting': meeting,
            'action_items': action_items,
            'action_summary': action_summary,
            'team_members': team_members,
            'available_teams': available_teams,
            'today': timezone.now().date().strftime('%Y-%m-%d'),
            'parameter_type': parameter_type,
            'parameter_id': parameter_id,
            'parameter_name': parameter_name,
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

            # Get parameter context from request
            parameter_type = request.POST.get('parameter_type')
            parameter_id = request.POST.get('parameter_id')

            if action_text and due_date and assigned_to_id:
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()

                    assigned_to = User.objects.get(id=assigned_to_id)
                    assigned_to_team = None

                    if assigned_to_team_id:
                        assigned_to_team = Team.objects.get(id=assigned_to_team_id)

                    # Create the action item with optional parameter context
                    action_item_data = {
                        'review_meeting': meeting,
                        'action_description': action_text,
                        'priority': priority,
                        'due_date': datetime.strptime(due_date, '%Y-%m-%d').date(),
                        'assigned_to': assigned_to,
                        'assigned_to_team': assigned_to_team,
                        'status': 'pending',
                        'completion_notes': comments,
                        'created_at': timezone.now(),
                        'updated_at': timezone.now()
                    }

                    # Add parameter context if provided
                    if parameter_type and parameter_id:
                        action_item_data['parameter_type'] = parameter_type
                        action_item_data['parameter_id'] = int(parameter_id)

                    ReviewActionItem.objects.create(**action_item_data)

                    # Note: Review action item created successfully
                    # Optional: Could sync to implement.Action later if needed

                except Exception as e:
                    return JsonResponse({'success': False, 'error': str(e)})

        elif action == 'edit':
            # Handle edit action
            action_id = request.POST.get('action_id')
            action_text = request.POST.get('action_description')
            priority = request.POST.get('priority')
            due_date = request.POST.get('due_date')
            assigned_to_id = request.POST.get('assigned_to')
            assigned_to_team_id = request.POST.get('assigned_to_team')
            status = request.POST.get('status')
            completion_notes = request.POST.get('completion_notes', '')

            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()

                action_item = ReviewActionItem.objects.get(id=action_id, review_meeting=meeting)

                # Store old status before updating
                old_status = action_item.status

                # Update fields
                action_item.action_description = action_text
                action_item.priority = priority
                action_item.due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
                action_item.assigned_to = User.objects.get(id=assigned_to_id)
                action_item.status = status

                if assigned_to_team_id:
                    action_item.assigned_to_team = Team.objects.get(id=assigned_to_team_id)
                else:
                    action_item.assigned_to_team = None

                # Set completed_at timestamp if status changed to completed
                if status == 'completed' and old_status != 'completed':
                    action_item.completed_at = timezone.now()
                elif status != 'completed':
                    action_item.completed_at = None

                action_item.save()

                return JsonResponse({'success': True})

            except ReviewActionItem.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Action not found'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        elif action == 'delete':
            item_id = request.POST.get('item_id')
            try:
                item = meeting.review_action_items.get(id=item_id)
                item.delete()
            except ReviewActionItem.DoesNotExist:
                pass

        elif action == 'update_status':
            # Handle status updates (complete/reject)
            action_id = request.POST.get('action_id')
            new_status = request.POST.get('status')
            reason = request.POST.get('reason', '')

            try:
                action_item = ReviewActionItem.objects.get(id=action_id)

                # Update status
                action_item.status = new_status

                # Set completed_at if marking as completed
                if new_status == 'completed':
                    action_item.completed_at = timezone.now()

                # Add reason to completion notes if provided
                if reason:
                    if action_item.completion_notes:
                        action_item.completion_notes += f"\n\nRejection reason: {reason}"
                    else:
                        action_item.completion_notes = f"Rejection reason: {reason}"

                action_item.save()

                return JsonResponse({'success': True})

            except ReviewActionItem.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Action not found'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        elif action == 'reassign':
            # Handle reassignment
            action_id = request.POST.get('action_id')
            assigned_to_id = request.POST.get('assigned_to')
            assigned_to_team_id = request.POST.get('assigned_to_team')
            reassignment_reason = request.POST.get('reassignment_reason', '')

            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()

                action_item = ReviewActionItem.objects.get(id=action_id)

                # Update assigned_to
                action_item.assigned_to = User.objects.get(id=assigned_to_id)

                # Update assigned_to_team if provided
                if assigned_to_team_id:
                    action_item.assigned_to_team = Team.objects.get(id=assigned_to_team_id)

                # Add reassignment note to completion_notes
                if reassignment_reason:
                    reassignment_note = f"\n\nReassigned: {reassignment_reason} (at {timezone.now().strftime('%Y-%m-%d %H:%M')})"
                    if action_item.completion_notes:
                        action_item.completion_notes += reassignment_note
                    else:
                        action_item.completion_notes = reassignment_note.strip()

                action_item.save()

                return JsonResponse({'success': True})

            except ReviewActionItem.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Action not found'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        return JsonResponse({'success': True})


class ParameterActionItemsView(LoginRequiredMixin, TemplateView):
    """Parameter-specific Action Items popup for FPI/GPI/PPI line items"""
    template_name = 'reviews/popups/parameter_action_items.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get parameter type and ID from request
        parameter_type = self.request.GET.get('type', 'fpi')
        parameter_id = self.request.GET.get('id')

        if not parameter_id:
            context.update({
                'meeting': meeting,
                'error': 'Parameter ID not provided',
                'parameter_type': parameter_type,
                'parameter_id': None,
            })
            return context

        # Get action items for this specific parameter
        try:
            action_items = meeting.review_action_items.filter(
                parameter_type=parameter_type,
                parameter_id=parameter_id
            )
        except Exception as e:
            print(f"Error filtering action items: {e}")
            # Fallback to all action items if parameter fields don't exist yet
            action_items = meeting.review_action_items.none()

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

        # Get parameter details based on type
        parameter_name = self.get_parameter_name(parameter_type, parameter_id)

        context.update({
            'meeting': meeting,
            'action_items': action_items,
            'action_summary': action_summary,
            'team_members': team_members,
            'available_teams': available_teams,
            'today': timezone.now().date().strftime('%Y-%m-%d'),
            'parameter_type': parameter_type,
            'parameter_id': parameter_id,
            'parameter_name': parameter_name,
        })
        return context

    def get_parameter_name(self, parameter_type, parameter_id):
        """Get the parameter name based on type and ID"""
        try:
            if parameter_type == 'fpi':
                from plans.models import FPIParameter
                param = FPIParameter.objects.get(id=parameter_id)
                return param.sub_head or 'FPI Parameter'
            elif parameter_type == 'gpi':
                from plans.models import GPIParameter
                param = GPIParameter.objects.get(id=parameter_id)
                return param.name
            elif parameter_type == 'ppi':
                from plans.models import PPIParameter
                param = PPIParameter.objects.get(id=parameter_id)
                return param.name
        except Exception as e:
            print(f"Error getting parameter name: {e}")
            return f"{parameter_type.upper()} Parameter"

    def post(self, request, pk):
        meeting = get_object_or_404(ReviewMeeting, pk=pk)
        action = request.POST.get('action')

        # Get parameter context
        parameter_type = request.POST.get('parameter_type')
        parameter_id = request.POST.get('parameter_id')

        if action == 'add':
            action_text = request.POST.get('action_description')
            priority = request.POST.get('priority')
            due_date = request.POST.get('due_date')
            assigned_to_id = request.POST.get('assigned_to')
            comments = request.POST.get('comments', '')

            if action_text and due_date and assigned_to_id and parameter_type and parameter_id:
                try:
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    assigned_to = User.objects.get(id=assigned_to_id)

                    action_item = ReviewActionItem.objects.create(
                        review_meeting=meeting,
                        action_description=action_text,
                        priority=priority,
                        due_date=due_date,
                        status='pending',
                        completion_notes=comments,
                        assigned_to=assigned_to,
                        parameter_type=parameter_type,
                        parameter_id=parameter_id,
                        created_at=timezone.now(),
                        updated_at=timezone.now()
                    )

                    return JsonResponse({'success': True, 'message': 'Parameter action item created successfully'})

                except Exception as e:
                    return JsonResponse({'success': False, 'error': f'Error creating action item: {str(e)}'})
            else:
                return JsonResponse({'success': False, 'error': 'All required fields must be provided'})

        return JsonResponse({'success': False, 'error': 'Invalid action'})


class ParameterIssuesView(LoginRequiredMixin, TemplateView):
    """Parameter-specific Issues popup for FPI/GPI/PPI line items"""
    template_name = 'reviews/popups/issues.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=kwargs['pk'])

        # Get parameter type and ID from request
        parameter_type = self.request.GET.get('parameter_type')
        parameter_id = self.request.GET.get('parameter_id')
        parameter_name = None

        # Get the parameter name if parameter context is provided
        if parameter_type and parameter_id:
            from plans.models import FPIParameter, GPIParameter, PPIProject
            from improve.models import ImprovementProject
            try:
                if parameter_type == 'fpi':
                    param = FPIParameter.objects.get(id=parameter_id)
                    parameter_name = param.sub_head
                elif parameter_type == 'gpi':
                    param = GPIParameter.objects.get(id=parameter_id)
                    parameter_name = param.name
                elif parameter_type == 'ppi':
                    param = PPIProject.objects.get(id=parameter_id)
                    parameter_name = param.project_name
                elif parameter_type == 'improvement':
                    param = ImprovementProject.objects.get(id=parameter_id)
                    parameter_name = param.name
            except Exception as e:
                print(f"Error fetching parameter name: {e}")

        # Get issues for this parameter
        issues = Issue.objects.filter(team=meeting.team)

        if parameter_type and parameter_id:
            # Filter by parameter type
            if parameter_type == 'fpi':
                issues = issues.filter(fpi_parameter_id=parameter_id)
            elif parameter_type == 'gpi':
                issues = issues.filter(gpi_parameter_id=parameter_id)
            elif parameter_type == 'ppi':
                issues = issues.filter(ppi_project_id=parameter_id)
            elif parameter_type == 'improvement':
                issues = issues.filter(improvement_project_id=parameter_id)

        issues = issues.select_related('reported_by', 'escalated_to_team').prefetch_related('related_actions')

        # Add action counts to each issue
        issues_with_counts = []
        for issue in issues:
            total_actions = issue.related_actions.count()
            completed_actions = issue.related_actions.filter(status='completed').count()
            issue.action_count = f"{completed_actions}/{total_actions}" if total_actions > 0 else "0/0"
            issues_with_counts.append(issue)

        # Calculate issue summary statistics
        issue_summary = {
            'total': issues.count(),
            'high_priority': issues.filter(priority='high').count(),
            'open': issues.filter(status='open').count(),
            'resolved': issues.filter(status='resolved').count(),
        }

        # Get teams where user is a member (for escalation)
        from django.db.models import Q
        user_teams = Team.objects.filter(
            Q(manager=self.request.user) |
            Q(members__member=self.request.user, members__is_active=True),
            is_active=True
        ).distinct().exclude(id=meeting.team.id)

        context.update({
            'meeting': meeting,
            'issues': issues_with_counts,
            'issue_summary': issue_summary,
            'available_teams': user_teams,
            'parameter_type': parameter_type,
            'parameter_id': parameter_id,
            'parameter_name': parameter_name,
            'today': timezone.now().date().strftime('%Y-%m-%d'),
        })
        return context


class SaveFPIDataView(LoginRequiredMixin, TemplateView):
    """AJAX endpoint for saving FPI data changes in review"""

    def update_next_month_goal(self, current_param, new_goal_value, meeting):
        """Update the next month's last_month_goal when current_month_plan is changed"""
        try:
            # This logic only works within the same quarterly plan
            # Since FPI parameters are tied to quarterly plans, and we want to update
            # the same parameter in a future month, this becomes a manual process
            # where the user would need to update the last_month_goal in the next period's entry

            # For now, we'll just note that this value should be carried forward
            # The actual implementation would require:
            # 1. A background job or scheduled task to carry forward values
            # 2. Or a UI mechanism for users to manually update next month's records
            # 3. Or a more complex quarterly plan relationship system

            pass  # Implementation pending - requires business logic clarification

        except Exception as e:
            print(f"Error updating next month goal: {e}")

    def post(self, request, pk):
        meeting = get_object_or_404(ReviewMeeting, pk=pk)

        # Get parameters from request
        data_type = request.POST.get('type')
        param_id = request.POST.get('id')
        field = request.POST.get('field')
        value = request.POST.get('value', '').strip()

        try:
            from plans.models import FPIParameter

            # Get the FPI parameter
            fpi_param = FPIParameter.objects.get(id=param_id)

            # Validate that the parameter belongs to the meeting's team
            if fpi_param.quarterly_plan.team != meeting.team:
                return JsonResponse({
                    'success': False,
                    'error': 'Parameter does not belong to this team'
                })

            # Update the appropriate field
            if field == 'last_month_actual':
                try:
                    fpi_param.last_month_actual = float(value) if value else None
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid number format for last month actual'
                    })
            elif field == 'current_month_plan':
                try:
                    new_value = float(value) if value else None
                    fpi_param.current_month_plan = new_value

                    # When current_month_plan is updated, update the next month's last_month_goal
                    # within the same quarterly plan (if exists)
                    self.update_next_month_goal(fpi_param, new_value, meeting)

                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid number format for current month plan'
                    })
            elif field == 'explanation':
                fpi_param.explanation = value
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid field: {field}'
                })

            # Save the changes
            fpi_param.save()

            return JsonResponse({
                'success': True,
                'message': f'Updated {field} for {fpi_param.sub_head}'
            })

        except FPIParameter.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'FPI parameter not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class SaveGPIDataView(LoginRequiredMixin, TemplateView):
    """AJAX endpoint for saving GPI data changes in review"""

    def post(self, request, pk):
        meeting = get_object_or_404(ReviewMeeting, pk=pk)

        # Get parameters from request
        data_type = request.POST.get('type')
        param_id = request.POST.get('id')
        field = request.POST.get('field')
        value = request.POST.get('value', '').strip()

        try:
            from plans.models import GPIParameter

            # Get the GPI parameter
            gpi_param = GPIParameter.objects.get(id=param_id)

            # Validate that the parameter belongs to the meeting's team
            if gpi_param.quarterly_plan.team != meeting.team:
                return JsonResponse({
                    'success': False,
                    'error': 'Parameter does not belong to this team'
                })

            # Update the appropriate field
            if field == 'last_week_actual':
                try:
                    gpi_param.last_week_actual = float(value) if value else None
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid number format for last week actual'
                    })
            elif field == 'current_week_plan':
                try:
                    new_value = float(value) if value else None
                    gpi_param.current_week_plan = new_value
                    # Update last_week_goal to current value for next week
                    gpi_param.last_week_goal = new_value
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid number format for current week plan'
                    })
            elif field == 'last_month_actual':
                try:
                    gpi_param.last_month_actual = float(value) if value else None
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid number format for last month actual'
                    })
            elif field == 'current_month_plan':
                try:
                    new_value = float(value) if value else None
                    gpi_param.current_month_plan = new_value
                    # Update last_month_goal to current value for next month
                    gpi_param.last_month_goal = new_value
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid number format for current month plan'
                    })
            elif field == 'explanation':
                gpi_param.explanation = value
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid field: {field}'
                })

            # Save the changes
            gpi_param.save()

            return JsonResponse({
                'success': True,
                'message': f'Updated {field} for {gpi_param.name}'
            })

        except GPIParameter.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'GPI parameter not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class UpdateProjectStatusView(LoginRequiredMixin, View):
    """Handle project status updates for PPI and Improvement projects"""

    def post(self, request, pk):
        meeting = get_object_or_404(ReviewMeeting, pk=pk)

        project_id = request.POST.get('project_id')
        project_type = request.POST.get('project_type')
        action = request.POST.get('action')  # complete, undo, hold, resume, drop, activate

        try:
            if project_type == 'PPI':
                from plans.models import PPIProject
                from implement.models import ProjectStatus

                project = PPIProject.objects.get(id=project_id)

                # Get the latest status record
                latest_status_obj = ProjectStatus.objects.filter(
                    project=project
                ).order_by('-updated_at').first()

                # Get previous status (second latest)
                previous_status_obj = ProjectStatus.objects.filter(
                    project=project
                ).order_by('-updated_at')[1:2].first()

                previous_status = previous_status_obj.status if previous_status_obj else 'on_track'

                # Determine new status based on action
                if action == 'complete':
                    new_status = 'completed'
                elif action == 'undo':
                    new_status = previous_status
                elif action == 'hold':
                    new_status = 'on_hold'
                elif action == 'resume':
                    new_status = previous_status
                elif action == 'drop':
                    new_status = 'dropped'
                elif action == 'activate':
                    new_status = previous_status
                else:
                    return JsonResponse({'success': False, 'error': 'Invalid action'})

                # Create new status record
                ProjectStatus.objects.create(
                    project=project,
                    status=new_status,
                    completion_percentage=latest_status_obj.completion_percentage if latest_status_obj else 0,
                    revised_due_date=latest_status_obj.revised_due_date if latest_status_obj else None,
                    challenge='',
                    comments=f'Status changed to {new_status} via review meeting',
                    updated_by=request.user
                )

            elif project_type == 'Improvement':
                from improve.models import ImprovementProject, ImprovementProjectStatus

                project = ImprovementProject.objects.get(id=project_id)

                # Get the latest status record
                latest_status_obj = ImprovementProjectStatus.objects.filter(
                    project=project
                ).order_by('-updated_at').first()

                # Get previous status (second latest)
                previous_status_obj = ImprovementProjectStatus.objects.filter(
                    project=project
                ).order_by('-updated_at')[1:2].first()

                previous_status = previous_status_obj.status if previous_status_obj else 'on_track'

                # Determine new status based on action
                if action == 'complete':
                    new_status = 'completed'
                elif action == 'undo':
                    new_status = previous_status
                elif action == 'hold':
                    new_status = 'on_hold'
                elif action == 'resume':
                    new_status = previous_status
                elif action == 'drop':
                    new_status = 'dropped'
                elif action == 'activate':
                    new_status = previous_status
                else:
                    return JsonResponse({'success': False, 'error': 'Invalid action'})

                # Update project status
                project.status = new_status
                project.save()

                # Create status history record
                ImprovementProjectStatus.objects.create(
                    project=project,
                    status=new_status,
                    completion_percentage=latest_status_obj.completion_percentage if latest_status_obj else 0,
                    revised_due_date=latest_status_obj.revised_due_date if latest_status_obj else None,
                    challenge='',
                    comments=f'Status changed to {new_status} via review meeting',
                    updated_by=request.user
                )
            else:
                return JsonResponse({'success': False, 'error': 'Invalid project type'})

            return JsonResponse({
                'success': True,
                'message': f'Project status updated to {new_status}',
                'new_status': new_status
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class ProjectDetailsView(LoginRequiredMixin, TemplateView):
    """Display project details with weekly task breakdown"""
    template_name = 'reviews/popups/project_details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=self.kwargs['pk'])

        project_id = self.request.GET.get('project_id')
        project_type = self.request.GET.get('project_type')

        from datetime import datetime, timedelta

        # Get project and tasks first
        if project_type == 'PPI':
            from plans.models import PPIProject
            project = PPIProject.objects.get(id=project_id)
            tasks = project.tasks.all()
            # Get quarter start date from the project's quarterly plan
            quarter_start_date = project.quarterly_plan.quarter_start_date if project.quarterly_plan else None
        else:  # Improvement
            from improve.models import ImprovementProject
            project = ImprovementProject.objects.get(id=project_id)
            tasks = project.tasks.all()
            # Get quarter start date from the project's upload (improvement upload)
            quarter_start_date = project.upload.quarter_start_date if project.upload else None

        # Calculate current week based on quarter start date
        today = datetime.now().date()
        if quarter_start_date:
            days_diff = (today - quarter_start_date).days
            current_week = (days_diff // 7) + 1
        else:
            current_week = 1

        # Build weekly task data
        weeks = []
        for week_num in range(1, 14):  # 13 weeks
            week_tasks = list(tasks.filter(week_number=week_num))
            tasks_count = len(week_tasks)
            completed_count = sum(1 for task in week_tasks if task.is_completed)

            # Attach action to each task for status display
            from implement.models import Action
            for task in week_tasks:
                action = Action.objects.filter(
                    ppi_task=task if project_type == 'PPI' else None,
                    improvement_task=task if project_type == 'Improvement' else None
                ).first()
                task.action = action

            # Determine cell style and class (background colors only for past weeks)
            cell_class = ''
            cell_style = ''

            if tasks_count == 0:
                # No tasks - default styling
                cell_class = 'bg-light'
            elif week_num < current_week:
                # Past week
                if completed_count == tasks_count:
                    # All tasks completed - green background
                    cell_style = 'background-color: #90EE90;'
                else:
                    # Incomplete tasks - pink background
                    cell_style = 'background-color: #FFB6C6;'
            elif completed_count == tasks_count:
                # Current/future week with all tasks completed - green background
                cell_style = 'background-color: #90EE90;'

            weeks.append({
                'week_number': week_num,
                'tasks_count': tasks_count,
                'completed_count': completed_count,
                'cell_class': cell_class,
                'cell_style': cell_style,
                'tasks': week_tasks,  # Pass the actual task objects
                'current_week': current_week  # Pass current week for comparison
            })

        context.update({
            'meeting': meeting,
            'meeting_id': meeting.pk,
            'project': project,
            'project_type': project_type,
            'weeks': weeks,
            'current_week': current_week
        })

        return context


class WeekTasksView(LoginRequiredMixin, TemplateView):
    """Display tasks for a specific week of a project"""
    template_name = 'reviews/popups/week_tasks.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=self.kwargs['pk'])

        project_id = self.request.GET.get('project_id')
        project_type = self.request.GET.get('project_type')
        week_number = int(self.request.GET.get('week', 1))

        if project_type == 'PPI':
            from plans.models import PPIProject
            project = PPIProject.objects.get(id=project_id)
            tasks = project.tasks.filter(week_number=week_number)
        else:  # Improvement
            from improve.models import ImprovementProject
            project = ImprovementProject.objects.get(id=project_id)
            tasks = project.tasks.filter(week_number=week_number)

        # Helper function to recursively get all sub-actions with depth level
        def get_nested_sub_actions(action, depth=1):
            """Recursively get all sub-actions with their depth level for tree display"""
            from implement.models import Action
            result = []
            sub_actions = action.sub_actions.all().order_by('created_at')

            for sub_action in sub_actions:
                # Add depth level to sub_action for template rendering
                sub_action.depth_level = depth
                result.append(sub_action)

                # Recursively get sub-actions of this sub-action
                nested = get_nested_sub_actions(sub_action, depth + 1)
                result.extend(nested)

            return result

        # Attach action and all nested sub-actions to each task
        from implement.models import Action
        for task in tasks:
            try:
                # Get the action associated with this task
                action = Action.objects.filter(
                    ppi_task=task if project_type == 'PPI' else None,
                    improvement_task=task if project_type == 'Improvement' else None
                ).first()

                if action:
                    task.action = action
                    # Get all nested sub-actions recursively
                    task.sub_actions = get_nested_sub_actions(action)
                else:
                    task.action = None
                    task.sub_actions = []
            except:
                task.action = None
                task.sub_actions = []

        # Get all action items related to this project from the meeting
        action_items = meeting.review_action_items.filter(
            parameter_type=project_type.lower(),
            parameter_id=project_id
        )

        # Calculate task summary
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(is_completed=True).count()
        pending_tasks = total_tasks - completed_tasks
        completion_percentage = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0

        task_summary = {
            'total': total_tasks,
            'completed': completed_tasks,
            'pending': pending_tasks,
            'completion_percentage': completion_percentage
        }

        context.update({
            'meeting': meeting,
            'project': project,
            'project_type': project_type,
            'week_number': week_number,
            'tasks': tasks,
            'action_items': action_items,
            'task_summary': task_summary
        })

        return context


class FPIDetailsView(LoginRequiredMixin, TemplateView):
    """Display FPI parameter details with financial metrics"""
    template_name = 'reviews/popups/fpi_details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=self.kwargs['pk'])
        
        parameter_id = self.request.GET.get('parameter_id')
        
        from plans.models import FPIParameter, FinancialYear
        parameter = FPIParameter.objects.get(id=parameter_id)
        
        # Get financial year and quarter
        review_date = meeting.review_date.date()
        current_fy = FinancialYear.objects.filter(
            start_date__lte=review_date,
            end_date__gte=review_date
        ).first()
        
        if current_fy:
            # Determine current quarter
            start_date = current_fy.start_date
            months_diff = (review_date.year - start_date.year) * 12 + (review_date.month - start_date.month)
            
            if months_diff < 3:
                current_quarter = '1'
            elif months_diff < 6:
                current_quarter = '2'
            elif months_diff < 9:
                current_quarter = '3'
            else:
                current_quarter = '4'
            
            # Calculate current quarter month (1-3)
            current_month = review_date.month
            quarter_start_month = ((int(current_quarter) - 1) * 3) + current_fy.start_date.month
            if quarter_start_month > 12:
                quarter_start_month -= 12
            current_quarter_month = current_month - quarter_start_month + 1
            if current_quarter_month <= 0:
                current_quarter_month += 12
            current_quarter_month = max(1, min(3, current_quarter_month))
            
            last_quarter_month = current_quarter_month - 1 if current_quarter_month > 1 else 3
            
            # Get milestone data
            milestones = parameter.milestones.all()
            last_month_milestone = milestones.filter(month_number=last_quarter_month).first()
            current_month_milestone = milestones.filter(month_number=current_quarter_month).first()
            
            # Calculate QTD (sum of all months in current quarter up to now)
            qtd_budget = float(sum([float(m.budget_value) for m in milestones.filter(month_number__lte=current_quarter_month)]))
            qtd_actual = float(parameter.last_month_actual or 0)  # This should sum all actuals in quarter

            # Calculate YTD (sum across all quarters up to current)
            # For simplicity, multiply quarter total by number of completed quarters + current quarter progress
            quarter_budget = float(sum([float(m.budget_value) for m in milestones.all()]))
            quarters_completed = int(current_quarter) - 1
            ytd_budget = (quarter_budget * quarters_completed) + qtd_budget
            ytd_actual = qtd_actual  # Simplified - should sum all quarters

            # Year budget is 4 quarters
            year_budget = quarter_budget * 4

            # Prepare details dictionary - ensure all values are float
            details = {
                'last_month_budget': float(last_month_milestone.budget_value) if last_month_milestone else 0.0,
                'last_month_goal': float(parameter.last_month_goal or 0),
                'last_month_actual': float(parameter.last_month_actual or 0),
                'qtd_budget': float(qtd_budget),
                'qtd_actual': float(qtd_actual),
                'ytd_budget': float(ytd_budget),
                'ytd_actual': float(ytd_actual),
                'current_month_budget': float(current_month_milestone.budget_value) if current_month_milestone else 0.0,
                'current_month_goal': float(parameter.current_month_plan or 0),
                'quarter_budget': float(quarter_budget),
                'year_budget': float(year_budget),
            }
            
            # Calculate variances
            details['last_month_variance'] = details['last_month_actual'] - details['last_month_goal']
            details['last_month_variance_percent'] = (details['last_month_variance'] / details['last_month_goal'] * 100) if details['last_month_goal'] else 0
            
            details['qtd_variance'] = details['qtd_actual'] - details['qtd_budget']
            details['qtd_variance_percent'] = (details['qtd_variance'] / details['qtd_budget'] * 100) if details['qtd_budget'] else 0
            
            details['ytd_variance'] = details['ytd_actual'] - details['ytd_budget']
            details['ytd_variance_percent'] = (details['ytd_variance'] / details['ytd_budget'] * 100) if details['ytd_budget'] else 0
            
        else:
            current_quarter = None
            details = {
                'last_month_budget': 0, 'last_month_goal': 0, 'last_month_actual': 0,
                'qtd_budget': 0, 'qtd_actual': 0, 'ytd_budget': 0, 'ytd_actual': 0,
                'current_month_budget': 0, 'current_month_goal': 0,
                'quarter_budget': 0, 'year_budget': 0,
                'last_month_variance': 0, 'last_month_variance_percent': 0,
                'qtd_variance': 0, 'qtd_variance_percent': 0,
                'ytd_variance': 0, 'ytd_variance_percent': 0,
            }
        
        context.update({
            'meeting': meeting,
            'parameter': parameter,
            'details': details,
            'quarter': f"Q{current_quarter}" if current_quarter else "N/A",
            'financial_year': current_fy.year if current_fy else "N/A"
        })
        
        return context


class GPIDetailsView(LoginRequiredMixin, TemplateView):
    """Display GPI parameter details with financial metrics"""

    def get_template_names(self):
        # Determine template based on parameter tracking type
        parameter_id = self.request.GET.get('parameter_id')
        from plans.models import GPIParameter
        parameter = GPIParameter.objects.get(id=parameter_id)

        if parameter.tracking_type == 'weekly':
            return ['reviews/popups/gpi_weekly_details.html']
        else:
            return ['reviews/popups/gpi_details.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        meeting = get_object_or_404(ReviewMeeting, pk=self.kwargs['pk'])

        parameter_id = self.request.GET.get('parameter_id')

        from plans.models import GPIParameter, FinancialYear
        parameter = GPIParameter.objects.get(id=parameter_id)
        
        # Get financial year and quarter
        review_date = meeting.review_date.date()
        current_fy = FinancialYear.objects.filter(
            start_date__lte=review_date,
            end_date__gte=review_date
        ).first()
        
        if current_fy:
            # Determine current quarter
            start_date = current_fy.start_date
            months_diff = (review_date.year - start_date.year) * 12 + (review_date.month - start_date.month)
            
            if months_diff < 3:
                current_quarter = '1'
            elif months_diff < 6:
                current_quarter = '2'
            elif months_diff < 9:
                current_quarter = '3'
            else:
                current_quarter = '4'
            
            milestones = parameter.milestones.all()

            if parameter.tracking_type == 'weekly':
                # Calculate current week within quarter
                from datetime import date
                quarter_start_month = ((int(current_quarter) - 1) * 3) + current_fy.start_date.month
                if quarter_start_month > 12:
                    quarter_start_month -= 12
                    quarter_start_year = current_fy.start_date.year + 1
                else:
                    quarter_start_year = current_fy.start_date.year

                quarter_start = date(quarter_start_year, quarter_start_month, 1)
                days_diff = (review_date - quarter_start).days
                current_week = min(12, max(1, (days_diff // 7) + 1))
                last_week = current_week - 1 if current_week > 1 else 12

                # Get milestone data (for weekly GPI, period_number represents week)
                last_week_milestone = milestones.filter(period_number=last_week).first()
                current_week_milestone = milestones.filter(period_number=current_week).first()

                # Calculate QTD (sum of all weeks in current quarter up to now)
                qtd_budget = float(sum([float(m.budget_value) for m in milestones.filter(period_number__lte=current_week)]))
                qtd_actual = float(parameter.last_week_actual or 0)  # This should sum all actuals in quarter

                # Calculate YTD
                quarter_budget = float(sum([float(m.budget_value) for m in milestones.all()]))
                quarters_completed = int(current_quarter) - 1
                ytd_budget = (quarter_budget * quarters_completed) + qtd_budget
                ytd_actual = qtd_actual

                # Year budget is 4 quarters
                year_budget = quarter_budget * 4

                # Prepare details dictionary - ensure all values are float
                details = {
                    'last_week_budget': float(last_week_milestone.budget_value) if last_week_milestone else 0.0,
                    'last_week_goal': float(parameter.last_week_goal or 0),
                    'last_week_actual': float(parameter.last_week_actual or 0),
                    'qtd_budget': float(qtd_budget),
                    'qtd_actual': float(qtd_actual),
                    'ytd_budget': float(ytd_budget),
                    'ytd_actual': float(ytd_actual),
                    'current_week_budget': float(current_week_milestone.budget_value) if current_week_milestone else 0.0,
                    'current_week_goal': float(parameter.current_week_plan or 0),
                    'quarter_budget': float(quarter_budget),
                    'year_budget': float(year_budget),
                }

                # Calculate variances
                details['last_week_variance'] = details['last_week_actual'] - details['last_week_goal']
                details['last_week_variance_percent'] = (details['last_week_variance'] / details['last_week_goal'] * 100) if details['last_week_goal'] else 0

                details['qtd_variance'] = details['qtd_actual'] - details['qtd_budget']
                details['qtd_variance_percent'] = (details['qtd_variance'] / details['qtd_budget'] * 100) if details['qtd_budget'] else 0

                details['ytd_variance'] = details['ytd_actual'] - details['ytd_budget']
                details['ytd_variance_percent'] = (details['ytd_variance'] / details['ytd_budget'] * 100) if details['ytd_budget'] else 0

                context.update({'current_week': current_week})

            else:  # monthly tracking
                # Calculate current quarter month (1-3)
                current_month = review_date.month
                quarter_start_month = ((int(current_quarter) - 1) * 3) + current_fy.start_date.month
                if quarter_start_month > 12:
                    quarter_start_month -= 12
                current_quarter_month = current_month - quarter_start_month + 1
                if current_quarter_month <= 0:
                    current_quarter_month += 12
                current_quarter_month = max(1, min(3, current_quarter_month))

                last_quarter_month = current_quarter_month - 1 if current_quarter_month > 1 else 3

                # Get milestone data (for monthly GPI, period_number represents month)
                last_month_milestone = milestones.filter(period_number=last_quarter_month).first()
                current_month_milestone = milestones.filter(period_number=current_quarter_month).first()

                # Calculate QTD (sum of all months in current quarter up to now)
                qtd_budget = float(sum([float(m.budget_value) for m in milestones.filter(period_number__lte=current_quarter_month)]))
                qtd_actual = float(parameter.last_month_actual or 0)  # This should sum all actuals in quarter

                # Calculate YTD (sum across all quarters up to current)
                quarter_budget = float(sum([float(m.budget_value) for m in milestones.all()]))
                quarters_completed = int(current_quarter) - 1
                ytd_budget = (quarter_budget * quarters_completed) + qtd_budget
                ytd_actual = qtd_actual  # Simplified - should sum all quarters

                # Year budget is 4 quarters
                year_budget = quarter_budget * 4

                # Prepare details dictionary - ensure all values are float
                details = {
                    'last_month_budget': float(last_month_milestone.budget_value) if last_month_milestone else 0.0,
                    'last_month_goal': float(parameter.last_month_goal or 0),
                    'last_month_actual': float(parameter.last_month_actual or 0),
                    'qtd_budget': float(qtd_budget),
                    'qtd_actual': float(qtd_actual),
                    'ytd_budget': float(ytd_budget),
                    'ytd_actual': float(ytd_actual),
                    'current_month_budget': float(current_month_milestone.budget_value) if current_month_milestone else 0.0,
                    'current_month_goal': float(parameter.current_month_plan or 0),
                    'quarter_budget': float(quarter_budget),
                    'year_budget': float(year_budget),
                }

                # Calculate variances
                details['last_month_variance'] = details['last_month_actual'] - details['last_month_goal']
                details['last_month_variance_percent'] = (details['last_month_variance'] / details['last_month_goal'] * 100) if details['last_month_goal'] else 0

                details['qtd_variance'] = details['qtd_actual'] - details['qtd_budget']
                details['qtd_variance_percent'] = (details['qtd_variance'] / details['qtd_budget'] * 100) if details['qtd_budget'] else 0

                details['ytd_variance'] = details['ytd_actual'] - details['ytd_budget']
                details['ytd_variance_percent'] = (details['ytd_variance'] / details['ytd_budget'] * 100) if details['ytd_budget'] else 0
            
        else:
            current_quarter = None
            details = {
                'last_month_budget': 0, 'last_month_goal': 0, 'last_month_actual': 0,
                'qtd_budget': 0, 'qtd_actual': 0, 'ytd_budget': 0, 'ytd_actual': 0,
                'current_month_budget': 0, 'current_month_goal': 0,
                'quarter_budget': 0, 'year_budget': 0,
                'last_month_variance': 0, 'last_month_variance_percent': 0,
                'qtd_variance': 0, 'qtd_variance_percent': 0,
                'ytd_variance': 0, 'ytd_variance_percent': 0,
            }
        
        context.update({
            'meeting': meeting,
            'parameter': parameter,
            'details': details,
            'quarter': f"Q{current_quarter}" if current_quarter else "N/A",
            'financial_year': current_fy.year if current_fy else "N/A"
        })
        
        return context


@method_decorator(csrf_exempt, name='dispatch')
class UpdateIssueStatusView(LoginRequiredMixin, View):
    """Update issue status with previous status tracking"""
    
    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            issue_id = data.get('issue_id')
            new_status = data.get('status')
            escalated_team_id = data.get('escalated_team_id')
            
            issue = get_object_or_404(Issue, id=issue_id)
            
            # Store previous status before changing
            if new_status in ['resolved', 'on_hold', 'dropped', 'escalated']:
                issue.previous_status = issue.status
            
            # Update status
            issue.status = new_status
            
            # Handle escalation
            if new_status == 'escalated' and escalated_team_id:
                escalated_team = get_object_or_404(Team, id=escalated_team_id)
                issue.escalated_to_team = escalated_team
            
            issue.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Issue status updated to {new_status}',
                'previous_status': issue.previous_status
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    
@method_decorator(csrf_exempt, name='dispatch')
class RevertIssueStatusView(LoginRequiredMixin, View):
    """Revert issue to previous status"""

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            issue_id = data.get('issue_id')

            issue = get_object_or_404(Issue, id=issue_id)

            # Revert to previous status or open if no previous status
            new_status = issue.previous_status if issue.previous_status else 'open'
            issue.status = new_status
            issue.previous_status = ''  # Clear previous status

            # Clear escalation if reverting from escalated
            if issue.escalated_to_team:
                issue.escalated_to_team = None

            issue.save()

            return JsonResponse({
                'success': True,
                'message': f'Issue status reverted to {new_status}',
                'new_status': new_status
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class DeleteActionView(LoginRequiredMixin, View):
    """Delete action item and remove it from associated parameter"""

    def post(self, request, pk):
        try:
            action_id = request.GET.get('action_id')

            # Get the action item
            action = get_object_or_404(ReviewActionItem, id=action_id)

            # Check if user has permission to delete (should be part of the team, team manager, or admin)
            meeting = get_object_or_404(ReviewMeeting, pk=pk)

            # Check if user is a member of the team or the team manager
            from organizations.models import TeamMember
            is_team_member = TeamMember.objects.filter(
                team=meeting.team,
                member=request.user,
                is_active=True
            ).exists()
            is_team_manager = meeting.team.manager == request.user

            if not (is_team_member or is_team_manager or request.user.is_superuser):
                return JsonResponse({
                    'success': False,
                    'error': 'You do not have permission to delete this action'
                }, status=403)

            # Store parameter information before deletion
            parameter_type = action.parameter_type
            parameter_id = action.parameter_id

            # Delete the action
            action.delete()

            # Note: Since ReviewActionItem uses parameter_type and parameter_id
            # to link to parameters, and there's no reverse foreign key,
            # the deletion of the action automatically removes it from the parameter's view.
            # No additional cleanup is needed on the parameter side.

            return JsonResponse({
                'success': True,
                'message': 'Action deleted successfully'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
