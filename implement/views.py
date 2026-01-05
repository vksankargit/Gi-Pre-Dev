from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView, FormView, CreateView, UpdateView, View, RedirectView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from django.db.models import Q
from .models import ProjectStatus, Action, Issue, ActionHistory
from plans.models import PPIProject, GPIParameter, GPIMilestone, PPITask, FinancialYear
from improve.models import ImprovementProject, ImprovementTask
from organizations.models import Team, TeamMember
from accounts.utils import get_effective_user
from reviews.models import ReviewMeeting


class ImplementDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/dashboard.html'
    
    def get_context_data(self, **kwargs):
        from datetime import date, datetime, timedelta
        import calendar

        context = super().get_context_data(**kwargs)
        user = get_effective_user(self.request)

        # Get current date and calculate week info as per PRD format
        today = date.today()

        # Calculate current week number (ISO week number)
        year, week_num, weekday = today.isocalendar()

        # Calculate week start and end dates
        week_start = today - timedelta(days=weekday-1)  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday

        # Format as "Week 19 – 20-Jul-25 to 26-Jul-25"
        current_week_display = f"Week {week_num} – {week_start.strftime('%d-%b-%y')} to {week_end.strftime('%d-%b-%y')}"

        # Get current month name
        current_month = calendar.month_name[today.month]

        # Calculate current quarter for filtering
        now = timezone.now()
        current_month_num = now.month

        # Determine quarter based on month (financial year starts April 1)
        if 4 <= current_month_num <= 6:
            current_quarter_num = 1
            fy_start_year = now.year
        elif 7 <= current_month_num <= 9:
            current_quarter_num = 2
            fy_start_year = now.year
        elif 10 <= current_month_num <= 12:
            current_quarter_num = 3
            fy_start_year = now.year
        else:  # Jan-Mar
            current_quarter_num = 4
            fy_start_year = now.year - 1

        # Format the financial year string to match database format (e.g., "FY 25-26")
        fy_end_year = fy_start_year + 1
        current_fy_string = f"FY {fy_start_year % 100:02d}-{fy_end_year % 100:02d}"
        current_financial_year = FinancialYear.objects.filter(year=current_fy_string).first()

        # Calculate current week number within quarter (for My Numbers tracking)
        # Quarter start month mapping
        quarter_start_months = {1: 4, 2: 7, 3: 10, 4: 1}  # Apr, Jul, Oct, Jan
        quarter_start_month = quarter_start_months[current_quarter_num]

        # Calculate quarter start date
        if current_quarter_num == 4:  # Jan-Mar quarter
            quarter_start_year = fy_start_year + 1  # Next calendar year
        else:
            quarter_start_year = fy_start_year

        # Start from the 1st of the quarter month
        month_first_day = date(quarter_start_year, quarter_start_month, 1)

        # Find the Monday on or before the 1st of the quarter month
        # This ensures we get the first Monday of the quarter week system
        # weekday() returns 0=Monday, 6=Sunday
        if month_first_day.weekday() == 0:
            # First day is Monday
            quarter_start_date = month_first_day
        else:
            # Go back to the previous Monday
            days_back_to_monday = month_first_day.weekday()
            quarter_start_date = month_first_day - timedelta(days=days_back_to_monday)

        # Calculate which week of the quarter we're in
        days_into_quarter = (today - quarter_start_date).days
        current_week_in_quarter = (days_into_quarter // 7) + 1  # Week 1-13

        # Week selection for historical data viewing
        # Get selected week from request (default to current week)
        selected_week = int(self.request.GET.get('week', current_week_in_quarter))
        # Ensure selected week is within valid range (1 to current week)
        selected_week = max(1, min(selected_week, current_week_in_quarter))

        # Generate list of available weeks with date ranges (1 to current week)
        available_weeks_with_dates = []
        for week_num in range(1, current_week_in_quarter + 1):
            # Calculate week start date (Monday of that week)
            week_start = quarter_start_date + timedelta(days=(week_num - 1) * 7)
            week_end = week_start + timedelta(days=6)  # Sunday

            # Calculate ISO week number for this week
            iso_year, iso_week_num, iso_weekday = week_start.isocalendar()

            # Format: "Week 43 (01-Oct-25 to 07-Oct-25)"
            week_display = f"Week {iso_week_num} ({week_start.strftime('%d-%b-%y')} to {week_end.strftime('%d-%b-%y')})"
            available_weeks_with_dates.append({
                'number': week_num,  # Keep quarter week number for internal use
                'display': week_display
            })

        # Debug: Print week selection info
        print(f"DEBUG Week Selection: current_week={current_week_in_quarter}, selected_week={selected_week}, total_weeks={len(available_weeks_with_dates)}")

        # Check if selected week is locked (based on weekly review completion)
        # A week is locked if a weekly review has been completed for that week or any later week
        from plans.models import GPIWeeklyRecord
        is_week_locked = False
        latest_locked_week = 0

        # Check for any weekly review meetings that have been completed
        # If a review for week N is done, weeks 1 to N are locked
        weekly_reviews = ReviewMeeting.objects.filter(
            review_type='weekly',
            quarter_number=current_quarter_num,
            financial_year=current_financial_year,
            status='completed',
            week_number__isnull=False  # Exclude None values
        ).order_by('-week_number')

        if weekly_reviews.exists():
            latest_locked_week = weekly_reviews.first().week_number
            is_week_locked = selected_week <= latest_locked_week

        # Calculate current month number within quarter (1-3)
        current_month_in_quarter = ((current_month_num - quarter_start_month) % 12) // 1 + 1
        if current_month_in_quarter > 3:
            current_month_in_quarter = ((current_month_num - quarter_start_month + 12) % 12) // 1 + 1

        # Month selection for historical data viewing
        # Get selected month from request (default to current month)
        selected_month = int(self.request.GET.get('month', current_month_in_quarter))
        # Ensure selected month is within valid range (1 to current month in quarter)
        selected_month = max(1, min(selected_month, current_month_in_quarter))

        # Generate list of available months with date ranges (1 to current month)
        available_months_with_dates = []
        for month_num in range(1, current_month_in_quarter + 1):
            # Calculate the actual calendar month
            actual_month_num = ((quarter_start_month + month_num - 2) % 12) + 1
            if actual_month_num < quarter_start_month and current_quarter_num != 4:
                actual_year = quarter_start_year + 1
            elif actual_month_num < 4 and current_quarter_num == 4:
                actual_year = quarter_start_year
            else:
                actual_year = quarter_start_year

            # Get month name and calculate first and last day of month
            month_start = date(actual_year, actual_month_num, 1)
            # Get last day of month
            if actual_month_num == 12:
                month_end = date(actual_year, 12, 31)
            else:
                next_month = date(actual_year if actual_month_num < 12 else actual_year + 1,
                                 (actual_month_num % 12) + 1, 1)
                month_end = next_month - timedelta(days=1)

            # Format: "October (01-Oct-25 to 31-Oct-25)"
            month_name = calendar.month_name[actual_month_num]
            month_display = f"{month_name} ({month_start.strftime('%d-%b-%y')} to {month_end.strftime('%d-%b-%y')})"
            available_months_with_dates.append({
                'number': month_num,  # Keep quarter month number for internal use
                'display': month_display
            })

        # Check if selected month is locked (based on monthly review completion)
        is_month_locked = False
        latest_locked_month = 0

        # Check for any monthly review meetings that have been completed
        monthly_reviews = ReviewMeeting.objects.filter(
            review_type='monthly',
            quarter_number=current_quarter_num,
            financial_year=current_financial_year,
            status='completed',
            month_number__isnull=False  # Exclude None values
        ).order_by('-month_number')

        if monthly_reviews.exists():
            latest_locked_month = monthly_reviews.first().month_number
            is_month_locked = selected_month <= latest_locked_month

        # Get user's teams (where user is a member OR manager)
        user_member_teams = user.team_memberships.filter(is_active=True).values_list('team_id', flat=True)
        user_managed_teams = user.managed_teams.filter(is_active=True).values_list('id', flat=True)
        user_teams = list(user_member_teams) + list(user_managed_teams)

        # Separate managed teams from member-only teams
        managed_team_ids = list(user_managed_teams)
        member_only_team_ids = list(user_member_teams)

        # Debug logging commented out to avoid Unicode encoding issues
        # print(f"DEBUG Dashboard: User={user.username}, managed_teams={managed_team_ids}, member_teams={member_only_team_ids}")

        # Get Weekly Numbers from GPI Parameters - filter by current quarter
        # Show ALL parameters from teams where user is manager or member
        weekly_numbers = GPIParameter.objects.filter(
            Q(quarterly_plan__team_id__in=managed_team_ids) |  # All parameters from managed teams
            Q(quarterly_plan__team_id__in=member_only_team_ids),  # All parameters from member teams
            tracking_type='weekly',
            quarterly_plan__quarter=current_quarter_num,
            quarterly_plan__financial_year=current_financial_year
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year', 'responsible_user', 'assigned_team').prefetch_related('milestones', 'weekly_records') if current_financial_year else GPIParameter.objects.none()

        # Debug logging commented out to avoid Unicode encoding issues with special characters (₹, etc.)
        # print(f"DEBUG: Showing {weekly_numbers.count()} weekly parameters")
        # for param in weekly_numbers:
        #     print(f"   - {param.name} (team: {param.quarterly_plan.team.name}, responsible: {param.responsible_user.username})")

        # Get Monthly Numbers from GPI Parameters - filter by current quarter
        # Show ALL parameters from teams where user is manager or member
        # FPI has been removed from the system

        monthly_gpi = GPIParameter.objects.filter(
            Q(quarterly_plan__team_id__in=managed_team_ids) |  # All parameters from managed teams
            Q(quarterly_plan__team_id__in=member_only_team_ids),  # All parameters from member teams
            tracking_type='monthly',
            quarterly_plan__quarter=current_quarter_num,
            quarterly_plan__financial_year=current_financial_year
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year', 'responsible_user', 'assigned_team').prefetch_related('milestones') if current_financial_year else GPIParameter.objects.none()

        # Convert querysets to lists and combine monthly numbers
        monthly_numbers = list(monthly_gpi)

        # Get summary statistics (exclude carry_forward actions)
        # Show counts from user's teams OR where user is assigned/responsible
        context.update({
            'my_actions_count': Action.objects.filter(
                Q(team_id__in=user_teams) | Q(assigned_to=user),
                status__in=['not_started', 'in_progress', 'at_risk', 'danger']
            ).exclude(status='carry_forward').count(),
            'my_projects_count': PPIProject.objects.filter(
                Q(quarterly_plan__team_id__in=user_teams) | Q(responsible_user=user)
            ).count() + ImprovementProject.objects.filter(
                Q(upload__team_id__in=user_teams) | Q(responsible_user=user)
            ).count(),
            'pending_numbers': weekly_numbers.count() + monthly_gpi.count(),
            'today': today,
            'current_week_display': current_week_display,
            'current_month': current_month,
            'current_week_num': week_num,
            'current_year': year,
            'current_week_in_quarter': current_week_in_quarter,
            'current_month_in_quarter': current_month_in_quarter,
        })


        # Actions (exclude carry_forward actions)
        # Calculate date ranges for My To Do filtering
        current_week_start = today - timedelta(days=today.weekday())  # Monday
        current_week_end = current_week_start + timedelta(days=6)  # Sunday
        next_week_start = current_week_end + timedelta(days=1)  # Next Monday
        next_week_end = next_week_start + timedelta(days=6)  # Next Sunday

        # Get filter parameter from request (default: overdue,current_week)
        filter_param = self.request.GET.get('due_date_filter', 'overdue,current_week')
        filters = [f.strip() for f in filter_param.split(',') if f.strip()]

        # Get all regular actions first
        # Show actions from user's teams OR where user is assigned
        all_regular_actions = Action.objects.filter(
            Q(team_id__in=user_teams) | Q(assigned_to=user)
        ).exclude(
            status='carry_forward'
        ).select_related('team', 'created_by', 'assigned_to').prefetch_related('assigned_to__team_memberships__team')

        # Apply filtering for regular actions
        if filters:
            filter_query = Q()

            if 'overdue' in filters:
                # Overdue: due date before today and not completed
                filter_query |= Q(original_due_date__lt=today) & ~Q(status__in=['completed', 'done'])

            if 'current_week' in filters:
                # Current week: due date between current week start and end
                filter_query |= Q(original_due_date__gte=current_week_start, original_due_date__lte=current_week_end)

            if 'next_week' in filters:
                # Next week: due date between next week start and end
                filter_query |= Q(original_due_date__gte=next_week_start, original_due_date__lte=next_week_end)

            if 'later' in filters:
                # Later: due date after next week end
                filter_query |= Q(original_due_date__gt=next_week_end)

            regular_actions = all_regular_actions.filter(filter_query)
        else:
            # No filters selected, show all actions
            regular_actions = all_regular_actions

        # Get Review Action Items (from parameter actions in Issue Log, GPI, FPI, PPI)
        # Show review actions from user's teams OR where user is assigned
        from reviews.models import ReviewActionItem
        all_review_actions = ReviewActionItem.objects.filter(
            Q(assigned_to_team_id__in=user_teams) | Q(assigned_to=user)
        ).select_related(
            'assigned_to_team', 'review_meeting', 'assigned_to'
        ).prefetch_related('assigned_to__team_memberships__team')

        # Apply filtering for review actions
        if filters:
            review_filter_query = Q()

            if 'overdue' in filters:
                # Overdue: due date before today and not completed
                review_filter_query |= Q(due_date__lt=today) & ~Q(status='completed')

            if 'current_week' in filters:
                # Current week: due date between current week start and end
                review_filter_query |= Q(due_date__gte=current_week_start, due_date__lte=current_week_end)

            if 'next_week' in filters:
                # Next week: due date between next week start and end
                review_filter_query |= Q(due_date__gte=next_week_start, due_date__lte=next_week_end)

            if 'later' in filters:
                # Later: due date after next week end
                review_filter_query |= Q(due_date__gt=next_week_end)

            review_actions = all_review_actions.filter(review_filter_query)
        else:
            review_actions = all_review_actions

        # Normalize both types of actions into a unified format for the template
        combined_actions = []

        # Add regular actions with a wrapper to normalize field names
        for action in regular_actions:
            action.action_type = 'regular'  # Mark as regular action
            # Add next assignee in reassignment chain
            action.next_assignee = action.get_next_assignee_in_chain(user)
            # Add permission flags based on reassignment hierarchy
            action.can_edit = action.can_edit_action(user)
            action.can_reassign = action.can_reassign_action(user)
            action.can_create_sub = action.can_create_sub_items(user)
            # Add sub-action count for rejection validation
            action.has_sub_actions = action.sub_actions.exists()
            combined_actions.append(action)

        # Add review actions with field mapping
        for review_action in review_actions:
            # Create a wrapper object to match the Action model's interface
            class ReviewActionWrapper:
                def __init__(self, review_action):
                    self.id = review_action.id
                    self.action = review_action.action_description  # Map to 'action' field
                    self.action_type = 'review'  # Mark as review action
                    self.team = review_action.assigned_to_team
                    self.priority = review_action.priority
                    self.assigned_to = review_action.assigned_to
                    self.original_due_date = review_action.due_date  # Map to 'original_due_date'
                    self.status = review_action.status
                    self.revised_due_date = None  # Review actions don't have revised due dates
                    self.comments = review_action.completion_notes
                    self.ppi_task = None
                    self.improvement_task = None
                    self.source_display = 'Review'

                    # Add source information based on parameter_type
                    if review_action.parameter_type:
                        self.source = 'review'
                        param_name = review_action.get_parameter_name()
                        if param_name:
                            self.source_detail = param_name
                        else:
                            self.source_detail = f"{review_action.parameter_type.upper()} #{review_action.parameter_id}"
                    else:
                        self.source = 'review'
                        self.source_detail = f"Meeting #{review_action.review_meeting.id}"

                def get_source_display(self):
                    return self.source_display

                def get_priority_display(self):
                    priority_dict = dict(ReviewActionItem.PRIORITY_CHOICES)
                    return priority_dict.get(self.priority, self.priority)

                def get_status_display(self):
                    # Map review action statuses to regular action statuses for display
                    status_map = {
                        'pending': 'Pending',
                        'in_progress': 'On Track',
                        'completed': 'Completed',
                        'cancelled': 'Cancelled',
                    }
                    return status_map.get(self.status, self.status.title())

            combined_actions.append(ReviewActionWrapper(review_action))

        # Sort all actions by due date (oldest first) and created date (newest first as tiebreaker)
        # Handle None values: put items with no due date at the end, and use 0 for None ids
        from datetime import date
        combined_actions.sort(key=lambda x: (
            x.original_due_date if x.original_due_date is not None else date.max,
            -(x.id if x.id is not None else 0)
        ))

        actions = combined_actions
        # Actions are filtered and ready to be passed to template

        # Enhance weekly numbers with budget data and weekly records
        enhanced_weekly_numbers = []
        for gpi in weekly_numbers:
            # Load weekly record for selected week
            weekly_record = gpi.weekly_records.filter(week_number=selected_week).first()

            # If no record exists, create a new one (not saved yet)
            if not weekly_record:
                weekly_record = GPIWeeklyRecord(
                    gpi_parameter=gpi,
                    week_number=selected_week,
                    week_goal=None,
                    week_actual=None,
                    explanation='',
                    is_locked=is_week_locked
                )

            # Attach weekly record data to GPI parameter for display
            gpi.current_week_plan = weekly_record.week_goal
            gpi.last_week_actual = None  # Will be set below
            gpi.explanation = weekly_record.explanation
            gpi.is_locked = weekly_record.is_locked or is_week_locked

            # Get budget for selected week
            selected_week_milestone = gpi.milestones.filter(period_number=selected_week).first()
            gpi.current_week_budget = selected_week_milestone.budget_value if selected_week_milestone else 0

            # Handle last week data
            if selected_week > 1:
                # Last week is in the same quarter
                last_week_number = selected_week - 1
                last_week_milestone = gpi.milestones.filter(period_number=last_week_number).first()
                gpi.last_week_budget = last_week_milestone.budget_value if last_week_milestone else 0

                # Get last week's record for goal and actual
                last_week_record = gpi.weekly_records.filter(week_number=last_week_number).first()
                if last_week_record:
                    gpi.last_week_goal = last_week_record.week_goal if last_week_record.week_goal else 0
                    gpi.last_week_actual = last_week_record.week_actual if last_week_record.week_actual else 0
                else:
                    gpi.last_week_goal = 0
                    gpi.last_week_actual = 0
            else:
                # Week 1: Last week is in previous quarter (week 13)
                previous_quarter_num = current_quarter_num - 1 if current_quarter_num > 1 else 4

                # Determine FY for previous quarter
                if current_quarter_num == 1:
                    prev_fy_start_year = fy_start_year - 1
                    prev_fy_end_year = prev_fy_start_year + 1
                    prev_fy_string = f"FY {prev_fy_start_year % 100:02d}-{prev_fy_end_year % 100:02d}"
                    prev_financial_year = FinancialYear.objects.filter(year=prev_fy_string).first()
                else:
                    prev_financial_year = current_financial_year

                # Get GPI parameter from previous quarter
                if prev_financial_year:
                    prev_quarter_gpi = GPIParameter.objects.filter(
                        quarterly_plan__team=gpi.quarterly_plan.team,
                        quarterly_plan__quarter=previous_quarter_num,
                        quarterly_plan__financial_year=prev_financial_year,
                        name=gpi.name,
                        tracking_type='weekly'
                    ).first()

                    if prev_quarter_gpi:
                        # Get week 13 budget from previous quarter
                        last_week_milestone = prev_quarter_gpi.milestones.filter(period_number=13).first()
                        gpi.last_week_budget = last_week_milestone.budget_value if last_week_milestone else 0

                        # Get week 13 record from previous quarter
                        prev_quarter_record = prev_quarter_gpi.weekly_records.filter(week_number=13).first()
                        if prev_quarter_record:
                            gpi.last_week_goal = prev_quarter_record.week_goal if prev_quarter_record.week_goal else 0
                            gpi.last_week_actual = prev_quarter_record.week_actual if prev_quarter_record.week_actual else 0
                        else:
                            gpi.last_week_goal = 0
                            gpi.last_week_actual = 0
                    else:
                        gpi.last_week_budget = 0
                        gpi.last_week_goal = 0
                        gpi.last_week_actual = 0
                else:
                    gpi.last_week_budget = 0
                    gpi.last_week_goal = 0
                    gpi.last_week_actual = 0

            # Add permission flags for the current user
            gpi.is_manager = gpi.quarterly_plan.team_id in managed_team_ids
            gpi.is_responsible_user = gpi.responsible_user == user
            gpi.is_team_member = gpi.quarterly_plan.team_id in member_only_team_ids
            gpi.can_edit_numbers = gpi.is_responsible_user and not gpi.is_locked
            gpi.can_create_actions_issues = gpi.is_responsible_user and not gpi.is_locked
            gpi.can_reassign = gpi.is_manager

            enhanced_weekly_numbers.append(gpi)

        # Enhance monthly numbers with budget data
        month_num = timezone.now().month
        last_month = month_num - 1 if month_num > 1 else 12
        next_month = month_num + 1 if month_num < 12 else 1

        # Calculate quarterly month numbers (1-3 within quarter)
        # For financial year: Q1=Apr-Jun, Q2=Jul-Sep, Q3=Oct-Dec, Q4=Jan-Mar
        # current_month_in_quarter is already calculated above (1-3)

        enhanced_monthly_numbers = []
        for param in monthly_numbers:
            # FPI has been removed - only GPI parameters now

            # Handle quarter boundary: if current month is first month of quarter, last month is in previous quarter
            if current_month_in_quarter > 1:
                # Last month is in the same quarter
                last_quarter_month = current_month_in_quarter - 1

                # Get GPI milestone values (for monthly GPI, use period_number as month)
                last_month_milestone = param.milestones.filter(period_number=last_quarter_month).first()
                current_month_milestone = param.milestones.filter(period_number=current_month_in_quarter).first()

                param.last_month_budget = last_month_milestone.budget_value if last_month_milestone else 0
                param.current_month_budget = current_month_milestone.budget_value if current_month_milestone else 0

                # For last_month_goal within same quarter, use the stored value from monthly_rollover
                # This was set by the rollover command copying previous month's current_month_plan
                if not param.last_month_goal:
                    param.last_month_goal = 0
            else:
                # Last month is in the previous quarter (month 3 of previous quarter)
                # Get previous quarter's plan
                previous_quarter_num = current_quarter_num - 1 if current_quarter_num > 1 else 4

                # Determine FY for previous quarter
                if current_quarter_num == 1:
                    # Q1, so previous Q4 is from previous FY
                    prev_fy_start_year = fy_start_year - 1
                    prev_fy_end_year = prev_fy_start_year + 1
                    prev_fy_string = f"FY {prev_fy_start_year % 100:02d}-{prev_fy_end_year % 100:02d}"
                    prev_financial_year = FinancialYear.objects.filter(year=prev_fy_string).first()
                else:
                    # Previous quarter is in same FY
                    prev_financial_year = current_financial_year

                # Get parameter from previous quarter
                if prev_financial_year:
                    # Get GPI parameter from previous quarter by matching name
                    prev_quarter_param = GPIParameter.objects.filter(
                        quarterly_plan__team=param.quarterly_plan.team,
                        quarterly_plan__quarter=previous_quarter_num,
                        quarterly_plan__financial_year=prev_financial_year,
                        name=param.name,
                        tracking_type='monthly'
                    ).first()

                    if prev_quarter_param:
                        # Get month 3 budget from previous quarter (using period_number)
                        last_month_milestone = prev_quarter_param.milestones.filter(period_number=3).first()
                        param.last_month_budget = last_month_milestone.budget_value if last_month_milestone else 0

                        # Get month 3 goal (current_month_plan) from previous quarter
                        param.last_month_goal = prev_quarter_param.current_month_plan if prev_quarter_param.current_month_plan else 0
                    else:
                        param.last_month_budget = 0
                        param.last_month_goal = 0
                else:
                    param.last_month_budget = 0
                    param.last_month_goal = 0

                # Current month budget from current quarter (month 1)
                current_month_milestone = param.milestones.filter(period_number=1).first()

                param.current_month_budget = current_month_milestone.budget_value if current_month_milestone else 0

            # Set is_locked for monthly parameters
            param.is_locked = is_month_locked

            # Add permission flags for the current user
            param.is_manager = param.quarterly_plan.team_id in managed_team_ids
            param.is_responsible_user = param.responsible_user == user
            param.is_team_member = param.quarterly_plan.team_id in member_only_team_ids
            param.can_edit_numbers = param.is_responsible_user and not param.is_locked
            param.can_create_actions_issues = param.is_responsible_user and not param.is_locked
            param.can_reassign = param.is_manager

            enhanced_monthly_numbers.append(param)

        # Get teams where user is manager (for reassignment dropdown)
        from organizations.models import Team
        user_teams = Team.objects.filter(manager=user)

        # Calculate current quarter display using already calculated values
        quarter = f"Q{current_quarter_num}"
        current_quarter_display = f"{quarter} of FY {fy_start_year:02d}–{fy_end_year:02d}"

        # Calculate previous quarter display
        previous_quarter_num = current_quarter_num - 1 if current_quarter_num > 1 else 4
        if current_quarter_num == 1:
            # Previous quarter is Q4 of previous FY
            prev_fy_start_year = fy_start_year - 1
            prev_fy_end_year = fy_start_year
            previous_quarter_display = f"Q{previous_quarter_num} of FY {prev_fy_start_year:02d}–{prev_fy_end_year:02d}"
        else:
            # Previous quarter is in same FY
            previous_quarter_display = f"Q{previous_quarter_num} of FY {fy_start_year:02d}–{fy_end_year:02d}"

        # Get both PPI projects and Improvement projects
        ppi_projects = []
        improvement_projects = []

        if current_financial_year:
            # Use current_quarter_num which is already calculated
            # Show ALL projects from teams where user is manager or member
            ppi_projects = PPIProject.objects.filter(
                Q(quarterly_plan__team_id__in=managed_team_ids) |  # All projects from managed teams
                Q(quarterly_plan__team_id__in=member_only_team_ids),  # All projects from member teams
                quarterly_plan__quarter=current_quarter_num,
                quarterly_plan__financial_year=current_financial_year
            ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year', 'responsible_user').prefetch_related('status_history', 'responsible_user__team_memberships__team')

            # Get improvement projects for the same quarter and financial year
            # Show ALL projects from teams where user is manager or member
            improvement_projects = ImprovementProject.objects.filter(
                Q(upload__team_id__in=managed_team_ids) |  # All projects from managed teams
                Q(upload__team_id__in=member_only_team_ids),  # All projects from member teams
                upload__quarter=quarter,
                upload__financial_year=current_financial_year
            ).select_related('upload__team', 'upload__financial_year', 'responsible_user').prefetch_related('tasks', 'responsible_user__team_memberships__team')
        else:
            # Fallback if no financial year found - show all projects
            ppi_projects = PPIProject.objects.filter(
                Q(quarterly_plan__team_id__in=managed_team_ids) |
                Q(quarterly_plan__team_id__in=member_only_team_ids)
            ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year', 'responsible_user').prefetch_related('status_history', 'responsible_user__team_memberships__team')

            improvement_projects = ImprovementProject.objects.filter(
                Q(upload__team_id__in=managed_team_ids) |
                Q(upload__team_id__in=member_only_team_ids)
            ).select_related('upload__team', 'upload__financial_year', 'responsible_user').prefetch_related('tasks', 'responsible_user__team_memberships__team')

        # Combine and enhance all projects
        enhanced_projects = []

        # Process PPI projects
        for project in ppi_projects:
            # Use the completion_percentage property which calculates based on completed weeks
            # Note: project.completion_percentage is a @property that returns an integer (0-100)
            # based on: (# of weeks with completed activities / # of weeks with planned activities) * 100

            # Add project type identifier
            project.project_type = 'PPI'

            # Add permission flags for the current user
            project.is_manager = project.quarterly_plan.team_id in managed_team_ids
            project.is_responsible_user = project.responsible_user == user
            project.is_team_member = project.quarterly_plan.team_id in member_only_team_ids
            project.can_create_actions_issues = project.is_responsible_user
            project.can_edit = project.is_responsible_user
            project.can_mark_done = project.is_responsible_user
            project.can_reassign = project.is_manager  # Only managers can reassign

            enhanced_projects.append(project)

        # Process improvement projects - adapt them to PPI project interface
        for imp_project in improvement_projects:
            # Create a wrapper class to make improvement project compatible with template
            class ProjectWrapper:
                def __init__(self, improvement_project):
                    self.id = improvement_project.id
                    self.pk = improvement_project.pk  # Add pk for template compatibility
                    self.name = improvement_project.name
                    self.completion_criteria = improvement_project.completion_criteria
                    self.responsible_user = improvement_project.responsible_user
                    self.start_date = improvement_project.start_date
                    self.end_date = improvement_project.end_date
                    self.steps = improvement_project.steps
                    self.status = improvement_project.status  # Copy the current status
                    self.project_type = 'Improvement'
                    self.tracking_type = improvement_project.tracking_type  # Add tracking type for filtering

                    # Create a quarterly_plan-like object for template compatibility
                    class TeamWrapper:
                        def __init__(self, team):
                            self.id = team.id
                            self.name = team.name

                    class QuarterlyPlanWrapper:
                        def __init__(self, upload):
                            self.team = TeamWrapper(upload.team)

                            # Extract FY and quarter from the quarter string "FY 25-26 – Q2"
                            quarter_str = upload.quarter

                            # Extract financial year from quarter string
                            # Handle different separator characters (–, -, �)
                            fy_part = None
                            if 'FY' in quarter_str:
                                # Try different separators
                                for separator in ['–', '-', '�']:
                                    if separator in quarter_str:
                                        fy_part = quarter_str.split(separator)[0].strip()  # Get "FY 25-26"
                                        break

                            if fy_part:
                                # Create a mock financial year object for display
                                class FinancialYearWrapper:
                                    def __init__(self, year_str):
                                        self.year = year_str

                                self.financial_year = FinancialYearWrapper(fy_part)
                            else:
                                # Fallback to actual upload financial year
                                self.financial_year = upload.financial_year

                            # Extract quarter number
                            if 'Q' in quarter_str:
                                # Find the Q and extract what follows
                                q_index = quarter_str.find('Q')
                                if q_index != -1:
                                    quarter_part = quarter_str[q_index:q_index+2]  # Get "Q2"
                                    self.quarter = quarter_part.replace("Q", "")  # Convert "Q2" to "2"
                                else:
                                    self.quarter = "1"  # Fallback
                            else:
                                self.quarter = "1"  # Fallback

                    self.quarterly_plan = QuarterlyPlanWrapper(improvement_project.upload)

                    # Also add upload for direct access
                    self.upload = improvement_project.upload

                    # Make tasks accessible
                    self.tasks = improvement_project.tasks

                    # Use the completion_percentage property from the model which calculates based on completed weeks
                    # Note: improvement_project.completion_percentage is a @property that returns an integer (0-100)
                    # based on: (# of weeks with completed activities / # of weeks with planned activities) * 100
                    self.completion_percentage = improvement_project.completion_percentage

                    # Add permission flags for the current user
                    self.is_manager = improvement_project.upload.team_id in managed_team_ids
                    self.is_responsible_user = improvement_project.responsible_user == user
                    self.is_team_member = improvement_project.upload.team_id in member_only_team_ids
                    self.can_create_actions_issues = self.is_responsible_user
                    self.can_edit = self.is_responsible_user
                    self.can_mark_done = self.is_responsible_user
                    self.can_reassign = self.is_manager  # Only managers can reassign

                def get_status_display(self):
                    """Method to provide human-readable status like Django models"""
                    status_dict = dict(ImprovementProject.STATUS_CHOICES)
                    return status_dict.get(self.status, self.status)

            enhanced_projects.append(ProjectWrapper(imp_project))

        # Check for saved review meetings to determine if data entry should be disabled
        # Get all teams for the user's parameters
        user_teams_for_params = set()
        for param in weekly_numbers:
            user_teams_for_params.add(param.quarterly_plan.team.id)
        for param in enhanced_monthly_numbers:
            if hasattr(param, 'quarterly_plan'):
                user_teams_for_params.add(param.quarterly_plan.team.id)

        # Check weekly review meetings for current week
        weekly_review_locked = {}
        for team_id in user_teams_for_params:
            # Check if a weekly review meeting exists for current week (any status except 'cancelled')
            # Once a review meeting is created, data entry should be locked
            review_exists = ReviewMeeting.objects.filter(
                team_id=team_id,
                financial_year=current_financial_year,
                meeting_type='weekly',
                week_number=current_week_in_quarter
            ).exclude(status='cancelled').exists()
            weekly_review_locked[team_id] = review_exists

        # Check monthly review meetings for current month
        monthly_review_locked = {}
        for team_id in user_teams_for_params:
            # Check if a monthly review meeting exists for current month (any status except 'cancelled')
            review_exists = ReviewMeeting.objects.filter(
                team_id=team_id,
                financial_year=current_financial_year,
                meeting_type='monthly',
                month_number=current_month_in_quarter
            ).exclude(status='cancelled').exists()
            monthly_review_locked[team_id] = review_exists

        # Add locked status to each parameter
        for param in enhanced_weekly_numbers:
            param.is_locked = weekly_review_locked.get(param.quarterly_plan.team.id, False)

        for param in enhanced_monthly_numbers:
            if hasattr(param, 'quarterly_plan'):
                param.is_locked = monthly_review_locked.get(param.quarterly_plan.team.id, False)
            else:
                param.is_locked = False

        context.update({
            'weekly_numbers': enhanced_weekly_numbers,
            'monthly_numbers': enhanced_monthly_numbers,
            'projects': enhanced_projects,
            'actions': actions,
            'user_teams': user_teams,
            'current_user_id': user.id,
            'current_quarter_num': current_quarter_num,
            'current_quarter_display': current_quarter_display,
            'previous_quarter_display': previous_quarter_display,
            'current_week_start': current_week_start,
            'current_week_end': current_week_end,
            'next_week_start': next_week_start,
            'next_week_end': next_week_end,
            'selected_filters': filters,
            # Week selection variables
            'current_week_in_quarter': current_week_in_quarter,
            'selected_week': selected_week,
            'available_weeks_with_dates': available_weeks_with_dates,
            'is_week_locked': is_week_locked,
            # Month selection variables
            'current_month_in_quarter': current_month_in_quarter,
            'selected_month': selected_month,
            'available_months_with_dates': available_months_with_dates,
            'is_month_locked': is_month_locked,
        })

        return context


class MyNumbersView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/my_numbers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_effective_user(self.request)

        # Get teams where user is manager or member
        from organizations.models import Team, TeamMember
        from django.db.models import Q

        # Get team IDs where user is manager
        managed_team_ids = Team.objects.filter(
            manager=user,
            is_active=True
        ).values_list('id', flat=True)

        # Get team IDs where user is member
        member_team_ids = TeamMember.objects.filter(
            member=user,
            is_active=True
        ).values_list('team_id', flat=True)

        # Combine both lists
        accessible_team_ids = list(set(list(managed_team_ids) + list(member_team_ids)))

        # Get current week/month numbers from quarterly plans of accessible teams
        weekly_numbers_qs = GPIParameter.objects.filter(
            quarterly_plan__team_id__in=accessible_team_ids,
            tracking_type='weekly'
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year').prefetch_related('milestones')

        # Add model_type to weekly numbers
        weekly_numbers = []
        for gpi in weekly_numbers_qs:
            gpi.model_type = 'gpi'
            weekly_numbers.append(gpi)

        # Get Monthly Numbers from FPI and GPI Parameters from accessible teams
        monthly_fpi = FPIParameter.objects.filter(
            quarterly_plan__team_id__in=accessible_team_ids
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year').prefetch_related('milestones')

        monthly_gpi = GPIParameter.objects.filter(
            quarterly_plan__team_id__in=accessible_team_ids,
            tracking_type='monthly'
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year').prefetch_related('milestones')

        # Convert querysets to lists and add model type indicators
        monthly_numbers = []

        # Add FPI parameters with type indicator
        for fpi in monthly_fpi:
            fpi.model_type = 'fpi'
            monthly_numbers.append(fpi)

        # Add GPI parameters with type indicator
        for gpi in monthly_gpi:
            gpi.model_type = 'gpi'
            monthly_numbers.append(gpi)

        # Calculate current week and month information
        from datetime import date, timedelta
        today = date.today()

        # Get current financial year and quarter
        current_financial_year = FinancialYear.objects.filter(
            start_date__lte=today,
            end_date__gte=today
        ).first()

        if not current_financial_year:
            # No active financial year found
            context.update({
                'weekly_numbers': weekly_numbers,
                'monthly_numbers': monthly_numbers,
                'error': 'No active financial year found'
            })
            return context

        # Determine current quarter
        fy_start_date = current_financial_year.start_date
        fy_start_year = fy_start_date.year
        days_into_fy = (today - fy_start_date).days
        current_quarter_num = (days_into_fy // 91) + 1  # Rough quarter calculation
        if current_quarter_num > 4:
            current_quarter_num = 4

        current_month_num = today.month

        # Calculate quarter start date
        quarter_start_months = {1: 4, 2: 7, 3: 10, 4: 1}  # Apr, Jul, Oct, Jan
        quarter_start_month = quarter_start_months[current_quarter_num]

        if current_quarter_num == 4:  # Jan-Mar quarter
            quarter_start_year = fy_start_year + 1
        else:
            quarter_start_year = fy_start_year

        month_first_day = date(quarter_start_year, quarter_start_month, 1)

        # Find the Monday on or before the 1st of the quarter month
        if month_first_day.weekday() == 0:
            quarter_start_date = month_first_day
        else:
            days_back_to_monday = month_first_day.weekday()
            quarter_start_date = month_first_day - timedelta(days=days_back_to_monday)

        # Calculate which week of the quarter we're in
        days_into_quarter = (today - quarter_start_date).days
        current_week_in_quarter = (days_into_quarter // 7) + 1  # Week 1-13

        # Week selection for historical data viewing
        selected_week = int(self.request.GET.get('week', current_week_in_quarter))
        selected_week = max(1, min(selected_week, current_week_in_quarter))

        # Generate list of available weeks with date ranges
        available_weeks_with_dates = []
        for week_num in range(1, current_week_in_quarter + 1):
            week_start = quarter_start_date + timedelta(days=(week_num - 1) * 7)
            week_end = week_start + timedelta(days=6)
            iso_year, iso_week_num, iso_weekday = week_start.isocalendar()
            week_display = f"Week {iso_week_num} ({week_start.strftime('%d-%b-%y')} to {week_end.strftime('%d-%b-%y')})"
            available_weeks_with_dates.append({
                'number': week_num,
                'display': week_display
            })

        # Calculate current month number within quarter (1-3)
        current_month_in_quarter = ((current_month_num - quarter_start_month) % 12) // 1 + 1
        if current_month_in_quarter > 3:
            current_month_in_quarter = ((current_month_num - quarter_start_month + 12) % 12) // 1 + 1

        # Month selection
        selected_month = int(self.request.GET.get('month', current_month_in_quarter))
        selected_month = max(1, min(selected_month, current_month_in_quarter))

        # Generate list of available months with date ranges
        available_months_with_dates = []
        for month_num in range(1, current_month_in_quarter + 1):
            month_offset = month_num - 1
            month_value = quarter_start_month + month_offset
            if month_value > 12:
                month_value -= 12
                month_year = quarter_start_year + 1
            else:
                month_year = quarter_start_year

            month_start = date(month_year, month_value, 1)
            # Get last day of month
            if month_value == 12:
                month_end = date(month_year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(month_year, month_value + 1, 1) - timedelta(days=1)

            month_display = f"Month {month_num} ({month_start.strftime('%b %Y')})"
            available_months_with_dates.append({
                'number': month_num,
                'display': month_display
            })

        context.update({
            'weekly_numbers': weekly_numbers,
            'monthly_numbers': monthly_numbers,
            'current_week_in_quarter': current_week_in_quarter,
            'selected_week': selected_week,
            'available_weeks_with_dates': available_weeks_with_dates,
            'current_month_in_quarter': current_month_in_quarter,
            'selected_month': selected_month,
            'available_months_with_dates': available_months_with_dates,
            'current_quarter': f'Q{current_quarter_num}',
            'current_financial_year': current_financial_year,
        })

        return context


class SaveNumberView(LoginRequiredMixin, TemplateView):
    def post(self, request):
        try:
            from plans.models import GPIWeeklyRecord, GPIMonthlyRecord

            # Handle both parameter naming conventions
            data_type = request.POST.get('type') or request.POST.get('param_type')  # 'gpi' or 'fpi'
            param_id = request.POST.get('id') or request.POST.get('param_id')
            field = request.POST.get('field')
            value = request.POST.get('value', '').strip()
            week_number = request.POST.get('week_number')  # For weekly tracking

            # Determine if this is a numeric or text field
            numeric_fields = ['last_week_actual', 'last_week_goal', 'current_week_plan', 'last_month_actual', 'last_month_goal', 'current_month_plan']
            text_fields = ['explanation']

            if field in numeric_fields:
                # Handle numeric fields
                if value == '':
                    value = None
                else:
                    try:
                        value = float(value)
                    except ValueError:
                        return JsonResponse({'success': False, 'error': 'Invalid numeric value'})
            elif field in text_fields:
                # Handle text fields - keep as string
                pass
            else:
                return JsonResponse({'success': False, 'error': f'Unknown field: {field}'})

            if data_type == 'gpi':
                # Get the parameter - allow if user is responsible OR if user manages the team
                from django.db.models import Q
                from organizations.models import Team

                # Get teams managed by this user
                user_managed_teams = Team.objects.filter(manager=request.user).values_list('id', flat=True)

                # Allow access if user is responsible OR parameter is from a managed team
                param = get_object_or_404(
                    GPIParameter,
                    Q(id=param_id) & (
                        Q(responsible_user=request.user) |
                        Q(quarterly_plan__team_id__in=user_managed_teams)
                    )
                )

                # Handle weekly tracking - save to GPIWeeklyRecord
                if field in ['current_week_plan', 'last_week_actual', 'explanation'] and week_number:
                    week_number = int(week_number)
                    print(f"DEBUG: Saving {field}={value} for GPI param {param_id}, current week={week_number}")

                    # For last_week_actual, we need to save to the PREVIOUS week's record
                    if field == 'last_week_actual':
                        # Save to previous week's record
                        save_week_number = week_number - 1
                        print(f"DEBUG: last_week_actual - saving to week {save_week_number}")
                        if save_week_number < 1:
                            # If we're in week 1, last week is week 13 of previous quarter
                            # For now, just return error - this case needs special handling
                            print(f"DEBUG: Cannot save to week {save_week_number} - returning error")
                            return JsonResponse({'success': False, 'error': 'Cannot edit previous quarter data from here'})
                    else:
                        save_week_number = week_number
                        print(f"DEBUG: Saving to week {save_week_number}")

                    # Check if week is locked
                    # TODO: Add lock checking logic here

                    # Get or create weekly record
                    weekly_record, created = GPIWeeklyRecord.objects.get_or_create(
                        gpi_parameter=param,
                        week_number=save_week_number,
                        defaults={'week_goal': None, 'week_actual': None, 'explanation': ''}
                    )
                    print(f"DEBUG: Weekly record {'created' if created else 'found'}: GPI {param.id}, Week {save_week_number}, is_locked={weekly_record.is_locked}")

                    # Map field names to record field names
                    if field == 'current_week_plan':
                        weekly_record.week_goal = value
                    elif field == 'last_week_actual':
                        weekly_record.week_actual = value
                    elif field == 'explanation':
                        weekly_record.explanation = value

                    weekly_record.save()
                    print(f"GPI Weekly Save: {field}={value} for param {param_id}, week {save_week_number}")

                # Handle monthly tracking - save to GPIMonthlyRecord
                elif field in ['last_month_actual', 'last_month_goal', 'current_month_plan', 'explanation']:
                    # For now, keep old behavior for monthly (will enhance later)
                    old_value = getattr(param, field, 'NOT_SET')
                    setattr(param, field, value)
                    param.save()
                    new_value = getattr(param, field, 'NOT_SET')
                    print(f"GPI Monthly Save: {field} changed from '{old_value}' to '{new_value}' for param {param_id}")
                else:
                    return JsonResponse({'success': False, 'error': f'Invalid field for GPI: {field}'})

            elif data_type == 'fpi':
                # Get the parameter - allow if user is responsible OR if user manages the team
                from django.db.models import Q
                from organizations.models import Team

                # Get teams managed by this user
                user_managed_teams = Team.objects.filter(manager=request.user).values_list('id', flat=True)

                # Allow access if user is responsible OR parameter is from a managed team
                param = get_object_or_404(
                    Q(id=param_id) & (
                        Q(responsible_user=request.user) |
                        Q(quarterly_plan__team_id__in=user_managed_teams)
                    )
                )
                # FPI is monthly only - keep old behavior for now
                if field in ['last_month_actual', 'last_month_goal', 'current_month_plan', 'explanation']:
                    old_value = getattr(param, field, 'NOT_SET')
                    setattr(param, field, value)
                    param.save()
                    new_value = getattr(param, field, 'NOT_SET')
                    print(f"FPI Save: {field} changed from '{old_value}' to '{new_value}' for param {param_id}")
                else:
                    return JsonResponse({'success': False, 'error': f'Invalid field for FPI: {field}'})

            else:
                # Debug: Show what was received with more details
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid type received: "{data_type}" (type: {type(data_type)}). Expected "gpi" or "fpi". All POST data: {dict(request.POST)}'
                })

            return JsonResponse({
                'success': True,
                'debug': f'Saved {field}={value} to {data_type} parameter {param_id}'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class ReassignParameterView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            param_id = request.POST.get('param_id')
            param_type = request.POST.get('param_type')
            member_id = request.POST.get('member_id')
            team_id = request.POST.get('team_id')

            if not all([param_id, param_type, member_id]):
                return JsonResponse({'success': False, 'error': 'Missing required parameters'})

            # Get the new responsible user
            from django.contrib.auth import get_user_model
            from organizations.models import Team
            User = get_user_model()
            new_user = get_object_or_404(User, id=member_id)

            # Get the team if provided
            assigned_team = None
            if team_id:
                assigned_team = get_object_or_404(Team, id=team_id)

            if param_type == 'gpi':
                param = get_object_or_404(GPIParameter, id=param_id)
                # Check if user has permission (is responsible user OR is team manager OR is member of the team)
                user_teams = list(request.user.team_memberships.filter(is_active=True).values_list('team_id', flat=True))
                user_managed_teams = list(request.user.managed_teams.filter(is_active=True).values_list('id', flat=True))
                all_user_teams = user_teams + user_managed_teams

                if param.responsible_user != request.user and param.quarterly_plan.team_id not in all_user_teams:
                    return JsonResponse({'success': False, 'error': 'You do not have permission to reassign this parameter'})

                param.responsible_user = new_user
                param.assigned_team = assigned_team
                param.save()
            elif param_type == 'fpi':
                param = get_object_or_404(id=param_id)
                # Check if user has permission (is responsible user OR is team manager OR is member of the team)
                user_teams = list(request.user.team_memberships.filter(is_active=True).values_list('team_id', flat=True))
                user_managed_teams = list(request.user.managed_teams.filter(is_active=True).values_list('id', flat=True))
                all_user_teams = user_teams + user_managed_teams

                if param.responsible_user != request.user and param.quarterly_plan.team_id not in all_user_teams:
                    return JsonResponse({'success': False, 'error': 'You do not have permission to reassign this parameter'})

                param.responsible_user = new_user
                param.assigned_team = assigned_team
                param.save()
            else:
                return JsonResponse({'success': False, 'error': 'Invalid parameter type'})

            return JsonResponse({
                'success': True,
                'message': f'Parameter successfully reassigned to {new_user.get_full_name()}'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class ReassignTaskView(LoginRequiredMixin, View):
    def post(self, request):
        import sys
        sys.stderr.write("=" * 80 + "\n")
        sys.stderr.write("REASSIGN TASK VIEW POST METHOD CALLED\n")
        sys.stderr.write("=" * 80 + "\n")
        sys.stderr.flush()

        import logging
        logger = logging.getLogger(__name__)

        try:
            task_id = request.POST.get('entity_id')
            member_id = request.POST.get('member_id')

            sys.stderr.write(f"task_id={task_id}, member_id={member_id}, user={request.user.get_full_name()}\n")
            sys.stderr.flush()

            logger.info(f"=== REASSIGN TASK START === task_id={task_id}, member_id={member_id}, user={request.user.get_full_name()}")

            if not all([task_id, member_id]):
                logger.error("Missing required parameters")
                return JsonResponse({'success': False, 'error': 'Missing required parameters'})

            # Get the new responsible user
            from django.contrib.auth import get_user_model
            User = get_user_model()
            new_user = get_object_or_404(User, id=member_id)
            logger.info(f"New user found: {new_user.get_full_name()} (ID: {new_user.id})")

            # Get the task and ensure only the project owner can reassign
            from plans.models import PPITask
            task = get_object_or_404(PPITask, id=task_id)
            logger.info(f"Task found: {task.id}, currently assigned to: {task.assigned_to.get_full_name() if task.assigned_to else 'None'} (ID: {task.assigned_to.id if task.assigned_to else 'None'})")

            # Check if the current user is the project owner
            if task.project.responsible_user != request.user:
                logger.error(f"Permission denied: user {request.user.get_full_name()} is not project owner")
                return JsonResponse({'success': False, 'error': 'Only project owner can reassign tasks'})

            # Reassign the task
            old_assignee = task.assigned_to
            task.assigned_to = new_user
            task.save()
            logger.info(f"Task {task.id} saved with new assignee: {new_user.get_full_name()}")

            # Verify the save
            task.refresh_from_db()
            logger.info(f"Task {task.id} after refresh: assigned_to={task.assigned_to.get_full_name()} (ID: {task.assigned_to.id})")

            # Get or create the corresponding Action for this task
            try:
                action = Action.objects.get(ppi_task=task)
                logger.info(f"Found existing action {action.id} for task {task.id}, currently assigned to: {action.assigned_to.get_full_name()} (ID: {action.assigned_to.id})")

                # Update the existing action
                action.assigned_to = new_user
                action.team = task.project.quarterly_plan.team
                action.save()
                logger.info(f"Action {action.id} saved with new assignee")

                # Verify the save
                action.refresh_from_db()
                logger.info(f"Action {action.id} after refresh: assigned_to={action.assigned_to.get_full_name()} (ID: {action.assigned_to.id})")

                # Create history entry
                ActionHistory.objects.create(
                    action=action,
                    status=action.status,
                    comments=f"Task reassigned from {old_assignee.get_full_name()} to {new_user.get_full_name()}",
                    updated_by=request.user
                )
                logger.info(f"Created ActionHistory entry for action {action.id}")
            except Action.DoesNotExist:
                logger.info(f"No existing action found for task {task.id}, creating new one")
                # Create a new action for this task
                action = Action.objects.create(
                    team=task.project.quarterly_plan.team,
                    source='ppi',
                    ppi_task=task,
                    action=f"Week {task.week_number}: {task.task_description}",
                    priority='medium',
                    assigned_to=new_user,
                    original_due_date=task.project.end_date if task.project.end_date else timezone.now().date(),
                    created_by=request.user
                )
                logger.info(f"Created new action {action.id} for task {task.id}")

            logger.info(f"=== REASSIGN TASK SUCCESS === Task {task.id} reassigned to {new_user.get_full_name()}")
            return JsonResponse({
                'success': True,
                'message': f'Task successfully reassigned to {new_user.get_full_name()}'
            })

        except Exception as e:
            logger.exception(f"=== REASSIGN TASK ERROR === {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})


class ParameterCommentsView(LoginRequiredMixin, View):
    def get(self, request, param_id):
        try:
            param_type = request.GET.get('type', 'gpi')

            if param_type == 'gpi':
                param = get_object_or_404(GPIParameter, id=param_id)
                parameter_name = param.name
                comments = param.explanation or ""
            elif param_type == 'fpi':
                param = get_object_or_404(id=param_id)
                parameter_name = param.sub_head or param.main_head
                comments = param.explanation or ""
            else:
                return JsonResponse({'success': False, 'error': 'Invalid parameter type'})

            # Check if user has access to this parameter
            if param.responsible_user != request.user:
                # Allow viewing if user is in the same team
                if not (hasattr(param, 'quarterly_plan') and
                       param.quarterly_plan.team.members.filter(id=request.user.id).exists()):
                    return JsonResponse({'success': False, 'error': 'Access denied'})

            return JsonResponse({
                'success': True,
                'parameter_name': parameter_name,
                'comments': comments
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class MyProjectsView(LoginRequiredMixin, RedirectView):
    """Redirect to dashboard with My Projects tab active"""

    def get_redirect_url(self, *args, **kwargs):
        return reverse('implement:dashboard') + '#my-projects'


class MyTodoView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/my_todo.html'
    # Added due date filter: Overdue, Current Week, Next Week, Later
    def get_context_data(self, **kwargs):
        from django.db.models import Q
        from datetime import date, timedelta
        from reviews.models import ReviewActionItem
        context = super().get_context_data(**kwargs)
        user = get_effective_user(self.request)

        # Calculate date ranges for filtering
        today = date.today()

        # Current week: Monday to Sunday of this week
        current_week_start = today - timedelta(days=today.weekday())  # Monday
        current_week_end = current_week_start + timedelta(days=6)  # Sunday

        # Next week: Monday to Sunday of next week
        next_week_start = current_week_end + timedelta(days=1)  # Next Monday
        next_week_end = next_week_start + timedelta(days=6)  # Next Sunday

        # Get filter parameter from request (default: overdue,current_week)
        filter_param = self.request.GET.get('due_date_filter', 'overdue,current_week')
        filters = [f.strip() for f in filter_param.split(',') if f.strip()]

        # Get regular actions assigned to user OR created by user OR owned via project
        # This includes:
        # 1. Actions assigned to the user
        # 2. Actions created by the user (delegated tasks)
        # 3. Actions linked to PPI tasks where user owns the project
        # Use .distinct() to avoid duplicates when an action matches multiple conditions
        # Exclude carry_forward actions from the todo list
        all_regular_actions = Action.objects.filter(
            Q(assigned_to=user) |
            Q(created_by=user) |
            Q(ppi_task__project__responsible_user=user) |
            Q(improvement_task__project__responsible_user=user)
        ).exclude(
            status='carry_forward'
        ).select_related(
            'team', 'created_by', 'assigned_to', 'ppi_task__project', 'improvement_task__project'
        ).distinct()

        # Apply filtering for regular actions
        if filters:
            filter_query = Q()

            if 'overdue' in filters:
                # Overdue: due date before today and not completed
                filter_query |= Q(original_due_date__lt=today) & ~Q(status__in=['completed', 'done'])

            if 'current_week' in filters:
                # Current week: due date between current week start and end
                filter_query |= Q(original_due_date__gte=current_week_start, original_due_date__lte=current_week_end)

            if 'next_week' in filters:
                # Next week: due date between next week start and end
                filter_query |= Q(original_due_date__gte=next_week_start, original_due_date__lte=next_week_end)

            if 'later' in filters:
                # Later: due date after next week end
                filter_query |= Q(original_due_date__gt=next_week_end)

            regular_actions = all_regular_actions.filter(filter_query)
        else:
            # No filters selected, show all actions
            regular_actions = all_regular_actions

        # Get Review Action Items (from parameter actions in Issue Log, GPI, FPI, PPI)
        all_review_actions = ReviewActionItem.objects.filter(
            assigned_to=user
        ).select_related(
            'assigned_to_team', 'review_meeting', 'assigned_to'
        )

        # Apply filtering for review actions
        if filters:
            review_filter_query = Q()

            if 'overdue' in filters:
                # Overdue: due date before today and not completed
                review_filter_query |= Q(due_date__lt=today) & ~Q(status='completed')

            if 'current_week' in filters:
                # Current week: due date between current week start and end
                review_filter_query |= Q(due_date__gte=current_week_start, due_date__lte=current_week_end)

            if 'next_week' in filters:
                # Next week: due date between next week start and end
                review_filter_query |= Q(due_date__gte=next_week_start, due_date__lte=next_week_end)

            if 'later' in filters:
                # Later: due date after next week end
                review_filter_query |= Q(due_date__gt=next_week_end)

            review_actions = all_review_actions.filter(review_filter_query)
        else:
            review_actions = all_review_actions

        # Normalize both types of actions into a unified format for the template
        combined_actions = []

        # Add regular actions with a wrapper to normalize field names
        for action in regular_actions:
            action.action_type = 'regular'  # Mark as regular action
            action.original_due_date_display = action.original_due_date
            combined_actions.append(action)

        # Add review actions with field mapping
        for review_action in review_actions:
            # Create a wrapper object to match the Action model's interface
            class ReviewActionWrapper:
                def __init__(self, review_action):
                    self.id = review_action.id
                    self.action = review_action.action_description  # Map to 'action' field
                    self.action_type = 'review'  # Mark as review action
                    self.team = review_action.assigned_to_team
                    self.priority = review_action.priority
                    self.assigned_to = review_action.assigned_to
                    self.original_due_date = review_action.due_date  # Map to 'original_due_date'
                    self.original_due_date_display = review_action.due_date
                    self.status = review_action.status
                    self.revised_due_date = None  # Review actions don't have revised due dates
                    self.comments = review_action.completion_notes
                    self.ppi_task = None
                    self.improvement_task = None

                    # Add source information based on parameter_type
                    if review_action.parameter_type:
                        self.source = 'review'
                        self.source_display = f"Review - {review_action.parameter_type.upper()}"
                        # Get the parameter name for display
                        param_name = review_action.get_parameter_name()
                        if param_name:
                            self.source_detail = param_name
                        else:
                            self.source_detail = f"{review_action.parameter_type.upper()} #{review_action.parameter_id}"
                    else:
                        self.source = 'review'
                        self.source_display = 'Review Meeting'
                        self.source_detail = f"Meeting #{review_action.review_meeting.id}"

                def get_source_display(self):
                    return self.source_display

                def get_priority_display(self):
                    priority_dict = dict(ReviewActionItem.PRIORITY_CHOICES)
                    return priority_dict.get(self.priority, self.priority)

                def get_status_display(self):
                    # Map review action statuses to regular action statuses for display
                    status_map = {
                        'pending': 'Pending',
                        'in_progress': 'On Track',
                        'completed': 'Completed',
                        'cancelled': 'Cancelled',
                    }
                    return status_map.get(self.status, self.status.title())

            combined_actions.append(ReviewActionWrapper(review_action))

        # Sort all actions by due date (oldest first) and created date (newest first as tiebreaker)
        combined_actions.sort(key=lambda x: (
            x.original_due_date if x.original_due_date is not None else date.max,
            -(x.id if x.id is not None else 0)
        ))

        context.update({
            'actions': combined_actions,
            'today': today,
            'current_week_start': current_week_start,
            'current_week_end': current_week_end,
            'next_week_start': next_week_start,
            'next_week_end': next_week_end,
            'selected_filters': filters,
        })

        return context


class ActionCreateView(LoginRequiredMixin, CreateView):
    model = Action
    template_name = 'implement/action_form.html'
    fields = ['action', 'priority', 'assigned_to', 'original_due_date', 'comments']
    success_url = reverse_lazy('implement:my_todo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Get available users for assignment
        context['available_users'] = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # Set team based on user's team membership
        user_teams = self.request.user.team_memberships.filter(is_active=True)
        if user_teams.exists():
            form.instance.team = user_teams.first().team

        messages.success(self.request, 'Action created successfully.')
        return super().form_valid(form)


class ActionEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        """Render the action edit modal form (this will be called via AJAX)"""
        # get_object_or_404 already handles DoesNotExist and raises Http404
        action = get_object_or_404(Action, pk=pk)

        # Check if user has permission to edit this action based on reassignment hierarchy
        # Only the final assignee can edit the action
        if not action.can_edit_action(request.user):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("You don't have permission to edit this action. Only the final assignee can edit.")

        try:
            # Get the latest history entry if available
            latest_history = action.history.first()

            context = {
                'object': action,
                'latest_history': latest_history,
                'status_choices': Action.STATUS_CHOICES,
            }

            return render(request, 'implement/action_edit_modal.html', context)
        except Exception as e:
            from django.http import HttpResponseServerError
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in ActionEditView.get for action {pk}: {str(e)}")
            return HttpResponseServerError(f"Error loading action edit form: {str(e)}")

    def post(self, request, pk):
        """Handle the modal form submission"""
        action = get_object_or_404(Action, pk=pk)

        # Check if user has permission to edit this action based on reassignment hierarchy
        # Only the final assignee can edit the action
        if not action.can_edit_action(request.user):
            return JsonResponse({
                'success': False,
                'error': "You don't have permission to edit this action. Only the final assignee can edit."
            })

        try:
            status = request.POST.get('status')
            revised_due_date = request.POST.get('revised_due_date')
            challenge = request.POST.get('challenge', '')
            comments = request.POST.get('comments', '')
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error processing request: {str(e)}'
            })

        # Validate required fields based on status (according to PRD)
        if status == 'at_risk' and not challenge:
            return JsonResponse({
                'success': False,
                'error': 'Challenge field is required for At Risk status.'
            })
        elif status == 'danger' and (not challenge or not revised_due_date):
            return JsonResponse({
                'success': False,
                'error': 'Challenge and Revised Due Date are required for Danger status.'
            })

        # Update action fields
        action.status = status
        action.challenge = challenge
        action.comments = comments

        # Convert revised_due_date string to date object if provided
        if revised_due_date:
            try:
                from datetime import datetime
                action.revised_due_date = datetime.strptime(revised_due_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid date format for revised due date.'
                })
        else:
            action.revised_due_date = None

        action.save()

        # Create history entry
        ActionHistory.objects.create(
            action=action,
            status=status,
            revised_due_date=action.revised_due_date,
            challenge=challenge,
            comments=comments,
            updated_by=request.user
        )

        return JsonResponse({'success': True})


class ActionReassignView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/action_reassign.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        action = get_object_or_404(Action, pk=kwargs['pk'])

        # Get teams where the logged-in user is the manager
        teams = Team.objects.filter(manager=self.request.user, is_active=True)

        context.update({
            'action': action,
            'teams': teams,
        })

        return context

    def post(self, request, pk):
        """Handle action reassignment with hierarchy management"""
        import logging
        from django.db import transaction
        logger = logging.getLogger(__name__)

        action = get_object_or_404(Action, pk=pk)
        logger.info(f"Reassigning action {pk}. Current assignee: {action.assigned_to.get_full_name()} (ID: {action.assigned_to.id})")

        # Check if user has permission to reassign this action
        # Only users in the reassignment chain (but not the final assignee) can reassign
        if not action.can_reassign_action(request.user):
            logger.error(f"User {request.user.get_full_name()} does not have permission to reassign action {pk}")
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to reassign this action. Only users in the reassignment chain (not the final assignee) can reassign.'
            })

        team_id = request.POST.get('team')
        assigned_to_id = request.POST.get('assigned_to')
        reassignment_reason = request.POST.get('reassignment_reason', '')
        notify_assignee = request.POST.get('notify_assignee') == 'on'

        logger.info(f"POST data - team_id: {team_id}, assigned_to_id: {assigned_to_id}")
        logger.info(f"All POST data: {dict(request.POST)}")

        # Validate required fields
        if not team_id or not assigned_to_id:
            logger.error("Missing required fields")
            return JsonResponse({
                'success': False,
                'error': 'Team and assignee are required'
            })

        try:
            from organizations.models import Team
            from django.contrib.auth import get_user_model
            from .models import ActionReassignment
            User = get_user_model()

            new_team = get_object_or_404(Team, pk=team_id)
            new_assignee = get_object_or_404(User, pk=assigned_to_id)

            logger.info(f"New team: {new_team.name} (ID: {new_team.id})")
            logger.info(f"New assignee: {new_assignee.get_full_name()} (ID: {new_assignee.id})")

            with transaction.atomic():
                # Get the current assignee before reassignment
                current_assignee = action.assigned_to

                # Get all existing reassignments for this action
                existing_reassignments = ActionReassignment.objects.filter(
                    action=action
                ).order_by('sequence_number')

                # Find the position of the current user in the chain
                current_user_position = None
                for reassignment in existing_reassignments:
                    if reassignment.reassigned_to == request.user:
                        current_user_position = reassignment.sequence_number
                        break

                # If no reassignments exist yet, this is the first one
                if not existing_reassignments.exists():
                    # Add the original assignee as the first person in the hierarchy
                    ActionReassignment.objects.create(
                        action=action,
                        reassigned_from=action.created_by,
                        reassigned_to=current_assignee,
                        reassignment_reason="Original assignee",
                        sequence_number=1
                    )
                    logger.info(f"Created first reassignment record for original assignee: {current_assignee.get_full_name()}")
                    next_sequence = 2
                else:
                    # If user is in the chain, delete all reassignments after them
                    if current_user_position is not None:
                        # Delete all reassignments after the current user's position
                        ActionReassignment.objects.filter(
                            action=action,
                            sequence_number__gt=current_user_position
                        ).delete()

                        # Get incomplete actions of users who were removed from the chain
                        # and delete them along with their sub-actions
                        removed_reassignments = existing_reassignments.filter(
                            sequence_number__gt=current_user_position
                        )
                        for removed_reassignment in removed_reassignments:
                            removed_user = removed_reassignment.reassigned_to
                            # Delete incomplete actions assigned to removed users
                            Action.objects.filter(
                                parent_action=action,
                                assigned_to=removed_user,
                                status__in=['not_started', 'in_progress', 'at_risk', 'danger', 'overdue', 'on_hold']
                            ).delete()

                        next_sequence = current_user_position + 1
                    else:
                        # User is not in the chain, add to the end
                        next_sequence = existing_reassignments.last().sequence_number + 1

                # Create new reassignment record
                ActionReassignment.objects.create(
                    action=action,
                    reassigned_from=request.user,
                    reassigned_to=new_assignee,
                    reassignment_reason=reassignment_reason,
                    sequence_number=next_sequence
                )

                # Update the action
                action.team = new_team
                action.assigned_to = new_assignee
                action.save()

                logger.info(f"Action saved. New assignee: {action.assigned_to.get_full_name()} (ID: {action.assigned_to.id})")

                # Create history entry for reassignment
                from .models import ActionHistory
                ActionHistory.objects.create(
                    action=action,
                    status=action.status,  # Keep current status
                    comments=f"Reassigned to {new_assignee.get_full_name()} in {new_team.name}. {reassignment_reason}".strip(),
                    updated_by=request.user
                )

                logger.info("Reassignment completed successfully")

            return JsonResponse({
                'success': True,
                'message': 'Action reassigned successfully. All incomplete actions from removed assignees have been deleted.'
            })

        except Exception as e:
            logger.error(f"Error during reassignment: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class ActionToggleCompleteView(LoginRequiredMixin, TemplateView):
    def post(self, request, pk):
        from django.utils import timezone
        action = get_object_or_404(Action, pk=pk)

        if action.status == 'completed':
            action.status = 'in_progress'  # or previous status

            # If this action is linked to a PPI task, mark it as incomplete
            if action.ppi_task:
                action.ppi_task.is_completed = False
                action.ppi_task.completed_at = None
                action.ppi_task.save()

            # If this action is linked to an Improvement task, mark it as incomplete
            if action.improvement_task:
                action.improvement_task.is_completed = False
                action.improvement_task.completed_at = None
                action.improvement_task.save()
        else:
            action.status = 'completed'

            # If this action is linked to a PPI task, mark it as complete
            if action.ppi_task:
                action.ppi_task.is_completed = True
                action.ppi_task.completed_at = timezone.now()
                action.ppi_task.save()

            # If this action is linked to an Improvement task, mark it as complete
            if action.improvement_task:
                action.improvement_task.is_completed = True
                action.improvement_task.completed_at = timezone.now()
                action.improvement_task.save()

        action.save()

        # Return JSON for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'message': 'Action status updated.',
                'new_status': action.status
            })

        # Regular form submission - redirect with message
        messages.success(request, 'Action status updated.')
        return redirect('implement:my_todo')


class ToggleActionStatusView(LoginRequiredMixin, View):
    """Toggle action status for Implement screen actions (Mark Complete/Undo, On-Hold/Resume, Drop/Mark Active)"""

    def post(self, request):
        from django.http import JsonResponse
        from django.db import transaction

        action_id = request.POST.get('action_id')
        new_status = request.POST.get('new_status')

        if not action_id or not new_status:
            return JsonResponse({'success': False, 'error': 'Missing required parameters'})

        try:
            action = Action.objects.get(id=action_id)

            # Verify user is assigned to this action
            if action.assigned_to != request.user:
                return JsonResponse({'success': False, 'error': 'You are not assigned to this action'})

            # Verify action is from Implement screen (source = 'manual')
            if action.source != 'manual':
                return JsonResponse({'success': False, 'error': 'Can only toggle status for Implement screen actions'})

            # Verify action is not linked to PPI or Improvement tasks
            if action.ppi_task or action.improvement_task:
                return JsonResponse({'success': False, 'error': 'Cannot toggle status for PPI/Improvement task actions'})

            with transaction.atomic():
                if new_status == 'completed':
                    # Mark Complete: Save current status and change to completed
                    action.previous_status = action.status
                    action.status = 'completed'

                elif new_status == 'undo':
                    # Undo: Revert to previous status
                    if action.previous_status:
                        action.status = action.previous_status
                        action.previous_status = ''
                    else:
                        action.status = 'not_started'

                elif new_status == 'on_hold':
                    # On-Hold: Save current status and change to on_hold
                    action.previous_status = action.status
                    action.status = 'on_hold'

                elif new_status == 'resume':
                    # Resume: Revert to previous status
                    if action.previous_status:
                        action.status = action.previous_status
                        action.previous_status = ''
                    else:
                        action.status = 'not_started'

                elif new_status == 'dropped':
                    # Drop: Save current status and change to dropped
                    action.previous_status = action.status
                    action.status = 'dropped'

                elif new_status == 'activate':
                    # Mark Active: Revert to previous status
                    if action.previous_status:
                        action.status = action.previous_status
                        action.previous_status = ''
                    else:
                        action.status = 'not_started'
                else:
                    return JsonResponse({'success': False, 'error': 'Invalid status'})

                action.save()

                # Create history record
                ActionHistory.objects.create(
                    action=action,
                    status=action.status,
                    revised_due_date=action.revised_due_date,
                    challenge=action.challenge,
                    comments=f'Status toggled to {action.get_status_display()}',
                    updated_by=request.user
                )

            return JsonResponse({'success': True, 'message': 'Action status updated successfully'})

        except Action.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Action not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class ActionRejectView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/action_reject.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        action = get_object_or_404(Action, pk=kwargs['pk'])

        # Check if action can be rejected (must be done/completed/rejected and no sub-actions)
        can_reject = (action.status in ['done', 'completed', 'rejected']) and not action.sub_actions.exists()

        context['action'] = action
        context['can_reject'] = can_reject
        return context

    def post(self, request, pk):
        action = get_object_or_404(Action, pk=pk)

        # Validate that action can be rejected
        if action.status not in ['done', 'completed', 'rejected']:
            return JsonResponse({
                'success': False,
                'error': 'Action can only be rejected if it is Done or Completed.'
            })

        if action.sub_actions.exists():
            return JsonResponse({
                'success': False,
                'error': 'Action cannot be rejected because it has sub-actions.'
            })

        rejection_reason = request.POST.get('rejection_reason', '')

        # Store previous status before changing to rejected
        if action.status != 'rejected':
            action.previous_status = action.status

        action.status = 'rejected'
        action.rejection_reason = rejection_reason
        action.save()

        # Create history entry
        from .models import ActionHistory
        ActionHistory.objects.create(
            action=action,
            status='rejected',
            comments=f"Action marked as rejected. Reason: {rejection_reason}",
            updated_by=request.user
        )

        # Return JSON for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'message': 'Action rejected and reopened.',
                'rejection_reason': rejection_reason
            })

        # Regular form submission - redirect with message
        messages.success(request, 'Action rejected and reopened.')
        return redirect('implement:dashboard')


class ActionHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/action_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        action = get_object_or_404(Action, pk=kwargs['pk'])
        
        context.update({
            'action': action,
            'history': action.history.all().order_by('-updated_at'),
        })
        
        return context


class SubActionView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/sub_actions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parent_action = get_object_or_404(Action, pk=kwargs['pk'])

        # Get teams where logged-in user is manager
        available_teams = Team.objects.filter(manager=self.request.user, is_active=True)

        # Calculate progress stats
        sub_actions = parent_action.sub_actions.all()
        completed_count = sub_actions.filter(status='completed').count()
        in_progress_count = sub_actions.filter(status='in_progress').count()
        pending_count = sub_actions.exclude(status__in=['completed', 'in_progress']).count()

        context.update({
            'parent_action': parent_action,
            'sub_actions': sub_actions,
            'available_teams': available_teams,
            'completed_count': completed_count,
            'in_progress_count': in_progress_count,
            'pending_count': pending_count,
            'today': timezone.now().date(),
        })

        return context


class SubActionCreateView(LoginRequiredMixin, View):
    def post(self, request):
        """Create a new sub-action"""
        parent_action_id = request.POST.get('parent_action_id')
        team_id = request.POST.get('team')
        action_text = request.POST.get('action')
        priority = request.POST.get('priority')
        assigned_to_id = request.POST.get('assigned_to')
        original_due_date = request.POST.get('original_due_date')
        comments = request.POST.get('comments', '')

        # Validate required fields
        if not all([parent_action_id, team_id, action_text, assigned_to_id, original_due_date]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'})

        try:
            parent_action = get_object_or_404(Action, pk=parent_action_id)
            selected_team = get_object_or_404(Team, pk=team_id)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            assigned_user = get_object_or_404(User, pk=assigned_to_id)

            # Verify that the logged-in user is the manager of the selected team
            if selected_team.manager != request.user:
                return JsonResponse({'success': False, 'error': 'You can only assign to teams you manage'})

            # Verify that the assigned user is either a member of the selected team OR the team manager
            is_team_member = selected_team.members.filter(member=assigned_user, is_active=True).exists()
            is_team_manager = selected_team.manager == assigned_user

            if not (is_team_member or is_team_manager):
                return JsonResponse({'success': False, 'error': 'Selected user is not a member of the selected team'})

            # Convert date string to date object
            from datetime import datetime
            due_date = datetime.strptime(original_due_date, '%Y-%m-%d').date()

            # Create sub-action
            sub_action = Action.objects.create(
                team=selected_team,
                source='manual',
                parent_action=parent_action,
                action=action_text,
                priority=priority or 'medium',
                assigned_to=assigned_user,
                original_due_date=due_date,
                status='not_started',
                comments=comments,
                created_by=request.user
            )

            return JsonResponse({'success': True, 'sub_action_id': sub_action.id})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class SubActionDetailsView(LoginRequiredMixin, View):
    def get(self, request, pk):
        """Get sub-action details for editing"""
        try:
            sub_action = get_object_or_404(Action, pk=pk)

            data = {
                'action': sub_action.action,
                'priority': sub_action.priority,
                'original_due_date': sub_action.original_due_date.strftime('%Y-%m-%d'),
                'assigned_to': sub_action.assigned_to.id,
                'team': sub_action.team.id,
                'comments': sub_action.comments or '',
                'status': sub_action.status,
            }

            return JsonResponse(data)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class SubActionUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        """Update an existing sub-action"""
        try:
            sub_action = get_object_or_404(Action, pk=pk)

            # Update fields
            sub_action.action = request.POST.get('action', sub_action.action)
            sub_action.priority = request.POST.get('priority', sub_action.priority)
            sub_action.comments = request.POST.get('comments', sub_action.comments)

            # Update team if provided
            team_id = request.POST.get('team')
            if team_id:
                selected_team = get_object_or_404(Team, pk=team_id)

                # Verify that the logged-in user is the manager of the selected team
                if selected_team.manager != request.user:
                    return JsonResponse({'success': False, 'error': 'You can only assign to teams you manage'})

                sub_action.team = selected_team

            # Update assigned user if provided
            assigned_to_id = request.POST.get('assigned_to')
            if assigned_to_id:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                assigned_user = get_object_or_404(User, pk=assigned_to_id)

                # Verify that the assigned user is either a member of the selected team OR the team manager
                is_team_member = sub_action.team.members.filter(member=assigned_user, is_active=True).exists()
                is_team_manager = sub_action.team.manager == assigned_user

                if not (is_team_member or is_team_manager):
                    return JsonResponse({'success': False, 'error': 'Selected user is not a member of the selected team'})

                sub_action.assigned_to = assigned_user

            # Update due date if provided
            original_due_date = request.POST.get('original_due_date')
            if original_due_date:
                from datetime import datetime
                sub_action.original_due_date = datetime.strptime(original_due_date, '%Y-%m-%d').date()

            sub_action.save()

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class SubActionDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        """Delete a sub-action"""
        try:
            sub_action = get_object_or_404(Action, pk=pk)
            sub_action.delete()

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class IssueCreateView(LoginRequiredMixin, CreateView):
    model = Issue
    template_name = 'implement/issue_form.html'
    fields = ['title', 'description', 'priority', 'required_by']
    success_url = reverse_lazy('implement:dashboard')
    
    def form_valid(self, form):
        form.instance.reported_by = self.request.user
        # Set team based on user's team membership
        user_teams = self.request.user.team_memberships.filter(is_active=True)
        if user_teams.exists():
            form.instance.team = user_teams.first().team
        
        messages.success(self.request, 'Issue created successfully.')
        return super().form_valid(form)


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = PPIProject
    template_name = 'implement/project_form.html'
    fields = ['name', 'completion_criteria', 'start_date', 'end_date']
    success_url = reverse_lazy('implement:my_projects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = True
        return context

    def form_valid(self, form):
        form.instance.responsible_user = self.request.user
        # Set quarterly plan based on user's team - this is a simplified approach
        # In a real implementation, you'd allow user to select the quarterly plan
        from plans.models import QuarterlyPlan
        quarterly_plans = QuarterlyPlan.objects.filter(
            team__members__user=self.request.user,
            team__members__is_active=True
        ).distinct().first()

        if quarterly_plans:
            form.instance.quarterly_plan = quarterly_plans

        messages.success(self.request, 'Project created successfully.')
        return super().form_valid(form)


class ImprovementProjectEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        """Render the improvement project edit modal form (this will be called via AJAX)"""
        project = get_object_or_404(ImprovementProject, pk=pk)

        # Check if user has permission to edit this project
        if project.responsible_user != request.user:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("You don't have permission to edit this project.")

        context = {
            'object': project,
            'status_choices': ImprovementProject.STATUS_CHOICES,
        }

        return render(request, 'implement/unified_project_form.html', context)

    def post(self, request, pk):
        """Handle the modal form submission for improvement project"""
        project = get_object_or_404(ImprovementProject, pk=pk)

        # Check if user has permission to edit this project
        if project.responsible_user != request.user:
            return JsonResponse({
                'success': False,
                'error': "You don't have permission to edit this project."
            })

        status = request.POST.get('status')
        revised_due_date = request.POST.get('revised_due_date')
        challenge = request.POST.get('challenge', '')
        comments = request.POST.get('comments', '')

        # Validate required fields based on status
        if status == 'at_risk' and not challenge:
            return JsonResponse({
                'success': False,
                'error': 'Challenge field is required for At Risk status.'
            })
        elif status == 'danger' and (not challenge or not revised_due_date):
            return JsonResponse({
                'success': False,
                'error': 'Challenge and Revised Due Date are required for Danger status.'
            })

        try:
            # Import the new status model
            from improve.models import ImprovementProjectStatus

            # Create a new status history entry
            revised_due_date_obj = None
            if revised_due_date:
                from datetime import datetime
                revised_due_date_obj = datetime.strptime(revised_due_date, '%Y-%m-%d').date()

            ImprovementProjectStatus.objects.create(
                project=project,
                status=status,
                completion_percentage=0,  # You might want to add this field to the form later
                revised_due_date=revised_due_date_obj,
                challenge=challenge,
                comments=comments,
                updated_by=request.user
            )

            # Also update the project's current status for consistency
            project.status = status
            project.save()

            # Log the status update (similar to how PPI projects work)
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'Improvement project {project.pk} status updated to {status} by user {request.user.pk}')

            return JsonResponse({'success': True, 'message': 'Improvement project updated successfully.'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class ProjectEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        """Render the project edit modal form (this will be called via AJAX)"""
        project = get_object_or_404(PPIProject, pk=pk)

        # Get the latest status if available
        latest_status = project.status_history.first()

        context = {
            'object': project,
            'latest_status': latest_status,
            'status_choices': ProjectStatus.STATUS_CHOICES,
        }

        return render(request, 'implement/unified_project_form.html', context)

    def post(self, request, pk):
        """Handle the modal form submission"""
        project = get_object_or_404(PPIProject, pk=pk)

        status = request.POST.get('status')
        revised_due_date = request.POST.get('revised_due_date')
        challenge = request.POST.get('challenge', '')
        comments = request.POST.get('comments', '')

        # Validate required fields based on status
        if status == 'at_risk' and not challenge:
            return JsonResponse({
                'success': False,
                'error': 'Challenge field is required for At Risk status.'
            })
        elif status == 'danger' and (not challenge or not revised_due_date):
            return JsonResponse({
                'success': False,
                'error': 'Challenge and Revised Due Date are required for Danger status.'
            })

        # Create new status history entry
        try:
            ProjectStatus.objects.create(
                project=project,
                status=status,
                completion_percentage=0,  # Default to 0 as per model
                revised_due_date=revised_due_date if revised_due_date else None,
                challenge=challenge,
                comments=comments,
                updated_by=request.user
            )

            messages.success(request, 'Project status updated successfully.')
            return JsonResponse({'success': True, 'message': 'Project updated successfully.'})

        except Exception as e:
            messages.error(request, f'Error updating project: {str(e)}')
            return JsonResponse({'success': False, 'error': str(e)})


class ProjectReassignView(LoginRequiredMixin, View):
    template_name = 'implement/project_reassign.html'

    def get_project(self, pk):
        """Get project from either PPIProject or ImprovementProject"""
        try:
            return get_object_or_404(PPIProject, pk=pk)
        except:
            return get_object_or_404(ImprovementProject, pk=pk)

    def get(self, request, pk):
        project = self.get_project(pk)
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Get teams where the logged-in user is a manager
        available_teams = Team.objects.filter(
            manager=request.user,
            is_active=True
        ).order_by('name')

        context = {
            'project': project,
            'available_teams': available_teams,
        }

        return render(request, self.template_name, context)

    def post(self, request, pk):
        project = self.get_project(pk)

        new_responsible_user_id = request.POST.get('responsible_user')
        team_id = request.POST.get('team')
        reassignment_reason = request.POST.get('reassignment_reason', '')
        handover_notes = request.POST.get('handover_notes', '')
        notify_assignee = request.POST.get('notify_assignee') == 'on'
        transfer_tasks = request.POST.get('transfer_tasks') == 'on'

        if not new_responsible_user_id:
            return JsonResponse({
                'success': False,
                'error': 'Please select a user to reassign the project to.'
            })

        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            new_responsible_user = User.objects.get(id=new_responsible_user_id)

            # Update project responsibility
            old_responsible_user = project.responsible_user
            project.responsible_user = new_responsible_user
            project.save()

            # Transfer related tasks if requested
            if transfer_tasks:
                project.tasks.update(assigned_to=new_responsible_user)

            # Create a log entry or notification if needed
            # TODO: Add notification system

            messages.success(request, f'Project successfully reassigned to {new_responsible_user.get_full_name()}.')
            return JsonResponse({'success': True, 'message': 'Project reassigned successfully.'})

        except User.DoesNotExist:
            messages.error(request, 'Selected user not found.')
            return JsonResponse({'success': False, 'error': 'Selected user not found.'})
        except Exception as e:
            messages.error(request, f'Error reassigning project: {str(e)}')
            return JsonResponse({'success': False, 'error': str(e)})


class GetTeamMembersView(LoginRequiredMixin, View):
    def get(self, request):
        team_id = request.GET.get('team_id')
        if not team_id:
            return JsonResponse({'success': False, 'error': 'Team ID required'})

        try:
            team = get_object_or_404(Team, id=team_id)

            # Check if user is a manager of this team
            if team.manager != request.user:
                return JsonResponse({'success': False, 'error': 'Access denied'})

            # Get active team members (through TeamMember model)
            team_members = team.members.filter(is_active=True)

            members_data = [
                {
                    'id': team_member.member.id,
                    'name': team_member.member.get_full_name(),
                    'email': team_member.member.email
                }
                for team_member in team_members
                if team_member.member.is_active
            ]

            # Add team manager to the members list if not already included
            manager_ids = [member['id'] for member in members_data]
            if team.manager.id not in manager_ids and team.manager.is_active:
                members_data.insert(0, {  # Insert at beginning
                    'id': team.manager.id,
                    'name': team.manager.get_full_name() + ' (Manager)',
                    'email': team.manager.email
                })

            return JsonResponse({'success': True, 'members': members_data})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class ProjectToggleCompleteView(LoginRequiredMixin, TemplateView):
    def post(self, request, pk):
        project = get_object_or_404(PPIProject, pk=pk)
        
        # Create or update project status
        status, created = ProjectStatus.objects.get_or_create(
            project=project,
            defaults={
                'status': 'completed',
                'completion_percentage': 100.00,
                'updated_by': request.user
            }
        )
        
        if not created:
            if status.status == 'completed':
                status.status = 'on_track'
                status.completion_percentage = 0.00
            else:
                status.status = 'completed'
                status.completion_percentage = 100.00
            status.updated_by = request.user
            status.save()
        
        messages.success(request, 'Project status updated.')
        return redirect('implement:my_projects')


class ProjectHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/unified_project_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Try to get either PPI or Improvement project
        project_id = kwargs['pk']
        project = None

        try:
            project = get_object_or_404(PPIProject, pk=project_id)
        except:
            project = get_object_or_404(ImprovementProject, pk=project_id)

        # Calculate completed tasks count
        completed_tasks_count = project.tasks.filter(is_completed=True).count() if hasattr(project, 'tasks') and project.tasks.exists() else 0
        total_tasks_count = project.tasks.count() if hasattr(project, 'tasks') else 0

        context.update({
            'project': project,
            'history': project.status_history.all().order_by('-updated_at'),
            'completed_tasks_count': completed_tasks_count,
            'total_tasks_count': total_tasks_count,
        })

        return context


class ProjectDetailsView(LoginRequiredMixin, TemplateView):
    """Display project details with weekly task breakdown"""
    template_name = 'implement/popups/project_details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        project_id = self.kwargs['pk']
        project_type = self.request.GET.get('project_type', 'PPI')

        from datetime import datetime, timedelta

        # Get current week based on quarter start date
        today = datetime.now().date()

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
            for task in week_tasks:
                action = Action.objects.filter(
                    ppi_task=task if project_type == 'PPI' else None,
                    improvement_task=task if project_type == 'Improvement' else None
                ).first()
                task.action = action

            # Determine cell style and class (background only for completed/overdue weeks)
            cell_class = ''
            cell_style = ''

            if tasks_count == 0:
                # No tasks - default styling
                cell_class = 'bg-light'
            elif completed_count == tasks_count:
                # All tasks completed - green background
                cell_style = 'background-color: #90EE90;'
            elif week_num < current_week:
                # Past week with incomplete tasks - light red background
                cell_style = 'background-color: #FFB6C6;'

            weeks.append({
                'week_number': week_num,
                'tasks': week_tasks,
                'tasks_count': tasks_count,
                'completed_count': completed_count,
                'cell_class': cell_class,
                'cell_style': cell_style,
            })

        # Adapt project object to match review template expectations
        # Add aliases for field names that differ between models
        project.project_name = project.name
        project.original_due_date = project.end_date

        context.update({
            'project': project,
            'project_type': project_type,
            'weeks': weeks,
            'current_week': current_week,
        })

        return context


class WeekTasksView(LoginRequiredMixin, TemplateView):
    """Display tasks for a specific week of a project"""
    template_name = 'implement/popups/week_tasks.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        project_id = self.kwargs['pk']
        project_type = self.request.GET.get('project_type', 'PPI')
        week_number = int(self.request.GET.get('week'))

        from datetime import datetime

        # Get current week based on quarter start date
        today = datetime.now().date()

        if project_type == 'PPI':
            from plans.models import PPIProject
            project = PPIProject.objects.get(id=project_id)
            # Get quarter start date from the project's quarterly plan
            quarter_start_date = project.quarterly_plan.quarter_start_date if project.quarterly_plan else None
        else:  # Improvement
            from improve.models import ImprovementProject
            project = ImprovementProject.objects.get(id=project_id)
            # Get quarter start date from the project's upload (improvement upload)
            quarter_start_date = project.upload.quarter_start_date if project.upload else None

        # Calculate current week based on quarter start date
        if quarter_start_date:
            days_diff = (today - quarter_start_date).days
            current_week = (days_diff // 7) + 1
        else:
            current_week = 1

        # Get tasks for this week with their related actions and sub-actions
        tasks = project.tasks.filter(week_number=week_number).order_by('id')

        # Helper function to recursively get all sub-actions with depth level
        def get_nested_sub_actions(action, depth=1):
            """Recursively get all sub-actions with their depth level for tree display"""
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

        # Adapt project object to match template expectations
        project.project_name = project.name

        context.update({
            'project': project,
            'project_type': project_type,
            'week_number': week_number,
            'tasks': tasks,
            'current_week': current_week,
            'task_summary': task_summary,
        })

        return context


class TaskHistoryView(LoginRequiredMixin, View):
    def get(self, request, task_id):
        print(f"=== TaskHistoryView GET request ===")
        print(f"task_id: {task_id}")
        print(f"user: {request.user}")
        print(f"authenticated: {request.user.is_authenticated}")

        try:
            task = get_object_or_404(PPITask, pk=task_id)
            print(f"Found task: {task}")
        except Exception as e:
            print(f"Error getting task: {e}")
            return JsonResponse({'error': f'Task not found: {e}'}, status=404)

        # Get the associated action for this task
        try:
            action = Action.objects.get(ppi_task=task)
            action_history = action.history.all().order_by('-updated_at')

            # Get sub-actions
            sub_actions = action.sub_actions.all().order_by('-created_at')

            # Compile comprehensive history data
            history_data = []

            # Add action history entries
            for entry in action_history:
                history_data.append({
                    'type': 'status_update',
                    'timestamp': entry.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'date': entry.updated_at.strftime('%b %d, %Y'),
                    'time': entry.updated_at.strftime('%H:%M'),
                    'status': entry.status,
                    'status_display': entry.status.replace('_', ' ').title(),
                    'revised_due_date': entry.revised_due_date.strftime('%b %d, %Y') if entry.revised_due_date else None,
                    'challenge': entry.challenge,
                    'comments': entry.comments,
                    'updated_by': entry.updated_by.get_full_name(),
                })

            # Add sub-action creation entries
            for sub_action in sub_actions:
                history_data.append({
                    'type': 'sub_action_created',
                    'timestamp': sub_action.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'date': sub_action.created_at.strftime('%b %d, %Y'),
                    'time': sub_action.created_at.strftime('%H:%M'),
                    'sub_action_text': sub_action.action[:100] + '...' if len(sub_action.action) > 100 else sub_action.action,
                    'created_by': sub_action.assigned_to.get_full_name(),
                })

            # Sort all history by timestamp (newest first)
            history_data.sort(key=lambda x: x['timestamp'], reverse=True)

        except Action.DoesNotExist:
            action = None
            history_data = []

        # Return JSON response
        response_data = {
            'task': {
                'id': task.id,
                'description': task.task_description,
                'week_number': task.week_number,
                'assigned_to': task.assigned_to.get_full_name(),
                'project_name': task.project.name,
                'is_completed': task.is_completed,
            },
            'action': {
                'id': action.id,
                'text': action.action,
                'status': action.status,
                'priority': action.priority,
            } if action else None,
            'history': history_data,
        }

        return JsonResponse(response_data)