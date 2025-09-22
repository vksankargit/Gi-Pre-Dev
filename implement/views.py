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
from plans.models import PPIProject, FPIParameter, GPIParameter, GPIMilestone, FPIMilestone, PPITask, FinancialYear
from improve.models import ImprovementProject, ImprovementTask
from organizations.models import Team, TeamMember


class ImplementDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/dashboard.html'
    
    def get_context_data(self, **kwargs):
        from datetime import date, datetime, timedelta
        import calendar

        context = super().get_context_data(**kwargs)
        user = self.request.user

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

        # Get Weekly Numbers from GPI Parameters
        weekly_numbers = GPIParameter.objects.filter(
            responsible_user=user,
            tracking_type='weekly'
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year').prefetch_related('milestones')

        # Get Monthly Numbers from FPI and GPI Parameters
        monthly_fpi = FPIParameter.objects.filter(
            responsible_user=user
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year').prefetch_related('milestones')

        monthly_gpi = GPIParameter.objects.filter(
            responsible_user=user,
            tracking_type='monthly'
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year').prefetch_related('milestones')

        # Convert querysets to lists and combine monthly numbers
        monthly_numbers = list(monthly_fpi) + list(monthly_gpi)

        # Get summary statistics
        context.update({
            'my_actions_count': Action.objects.filter(assigned_to=user, status__in=['not_started', 'in_progress', 'at_risk', 'danger']).count(),
            'my_projects_count': PPIProject.objects.filter(responsible_user=user).count() + ImprovementProject.objects.filter(responsible_user=user).count(),
            'pending_numbers': weekly_numbers.count() + monthly_fpi.count() + monthly_gpi.count(),
            'today': today,
            'current_week_display': current_week_display,
            'current_month': current_month,
            'current_week_num': week_num,
            'current_year': year,
        })


        # Actions
        actions = Action.objects.filter(
            assigned_to=user
        ).select_related('team', 'created_by').order_by('original_due_date', '-created_at')

        # Debug: Log the actions being sent to template
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"ImplementDashboardView for user {user}: Found {actions.count()} actions")
        for action in actions[:10]:  # Log first 10 actions
            logger.info(f"  Action {action.id}: {action.action[:50]}")

        # Enhance weekly numbers with budget data
        enhanced_weekly_numbers = []
        for gpi in weekly_numbers:
            # Calculate which Excel week corresponds to current calendar weeks
            # Week 37 = W11, Week 38 = W12 (assuming quarter starts at week 27)

            current_excel_week = week_num - 26  # Convert calendar week to Excel week (W1 = week 27)
            last_excel_week = current_excel_week - 1

            # Get milestone values for last week and current week
            last_week_milestone = gpi.milestones.filter(period_number=last_excel_week).first()
            current_week_milestone = gpi.milestones.filter(period_number=current_excel_week).first()

            # Add budget values to the GPI object
            gpi.last_week_budget = last_week_milestone.budget_value if last_week_milestone else 0
            gpi.current_week_budget = current_week_milestone.budget_value if current_week_milestone else 0

            enhanced_weekly_numbers.append(gpi)

        # Enhance monthly numbers with budget data
        current_month = timezone.now().month
        last_month = current_month - 1 if current_month > 1 else 12
        next_month = current_month + 1 if current_month < 12 else 1

        # Calculate quarterly month numbers (1-3 within quarter)
        quarter_start_month = ((current_month - 1) // 3) * 3 + 1  # Jan=1, Apr=4, Jul=7, Oct=10
        current_quarter_month = current_month - quarter_start_month + 1  # 1-3
        last_quarter_month = current_quarter_month - 1 if current_quarter_month > 1 else 3

        enhanced_monthly_numbers = []
        for param in monthly_numbers:
            # Check if this is FPI or GPI parameter
            if hasattr(param, 'main_head'):  # FPI parameter
                # Get FPI milestone values
                last_month_milestone = param.milestones.filter(month_number=last_quarter_month).first()
                current_month_milestone = param.milestones.filter(month_number=current_quarter_month).first()
            else:  # GPI parameter
                # Get GPI milestone values (for monthly GPI, use period_number as month)
                last_month_milestone = param.milestones.filter(period_number=last_quarter_month).first()
                current_month_milestone = param.milestones.filter(period_number=current_quarter_month).first()

            # Add budget values to the parameter object
            param.last_month_budget = last_month_milestone.budget_value if last_month_milestone else 0
            param.current_month_budget = current_month_milestone.budget_value if current_month_milestone else 0

            enhanced_monthly_numbers.append(param)

        # Get teams where user is manager (for reassignment dropdown)
        from organizations.models import Team
        user_teams = Team.objects.filter(manager=user)

        # Calculate current quarter display
        now = timezone.now()
        current_year = now.year
        current_month = now.month

        # Determine quarter based on month (financial year starts April 1)
        if 4 <= current_month <= 6:
            quarter = "Q1"
            fy_start = current_year
        elif 7 <= current_month <= 9:
            quarter = "Q2"
            fy_start = current_year
        elif 10 <= current_month <= 12:
            quarter = "Q3"
            fy_start = current_year
        else:  # Jan-Mar
            quarter = "Q4"
            fy_start = current_year - 1

        fy_end = fy_start + 1
        current_quarter_display = f"{quarter} of FY {fy_start:02d}–{fy_end:02d}"

        # Filter projects by current quarter and financial year
        from plans.models import FinancialYear
        # Format the financial year string to match database format (e.g., "FY 25-26")
        # Use last 2 digits of the year
        fy_string = f"FY {fy_start % 100:02d}-{fy_end % 100:02d}"
        current_fy = FinancialYear.objects.filter(year=fy_string).first()

        # Get both PPI projects and Improvement projects
        ppi_projects = []
        improvement_projects = []

        if current_fy:
            # Convert quarter format from "Q1" to "1" to match database format
            quarter_number = quarter.replace("Q", "")
            ppi_projects = PPIProject.objects.filter(
                responsible_user=user,
                quarterly_plan__quarter=quarter_number,
                quarterly_plan__financial_year=current_fy
            ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year').prefetch_related('status_history')

            # Get improvement projects for the same quarter and financial year
            # Search by quarter string which contains both FY and quarter like "FY 25-26 – Q2"
            improvement_projects = ImprovementProject.objects.filter(
                responsible_user=user,
                upload__quarter__icontains=quarter
            ).filter(
                upload__quarter__icontains=fy_string
            ).select_related('upload__team', 'upload__financial_year').prefetch_related('tasks')
        else:
            # Fallback if no financial year found - show all projects
            ppi_projects = PPIProject.objects.filter(
                responsible_user=user
            ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year').prefetch_related('status_history')

            improvement_projects = ImprovementProject.objects.filter(
                responsible_user=user
            ).select_related('upload__team', 'upload__financial_year').prefetch_related('tasks')

        # Combine and enhance all projects
        enhanced_projects = []

        # Process PPI projects
        for project in ppi_projects:
            # Calculate completion percentage based on project tasks
            if hasattr(project, 'tasks') and project.tasks.exists():
                total_tasks = project.tasks.count()
                completed_tasks = project.tasks.filter(is_completed=True).count()
                project.completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            else:
                # Use status_history if available
                latest_status = project.status_history.first() if hasattr(project, 'status_history') else None
                if latest_status and hasattr(latest_status, 'completion_percentage'):
                    project.completion_percentage = latest_status.completion_percentage
                else:
                    project.completion_percentage = 0

            # Add project type identifier
            project.project_type = 'PPI'
            enhanced_projects.append(project)

        # Process improvement projects - adapt them to PPI project interface
        for imp_project in improvement_projects:
            # Create a wrapper class to make improvement project compatible with template
            class ProjectWrapper:
                def __init__(self, improvement_project):
                    self.id = improvement_project.id
                    self.name = improvement_project.name
                    self.completion_criteria = improvement_project.completion_criteria
                    self.responsible_user = improvement_project.responsible_user
                    self.start_date = improvement_project.start_date
                    self.end_date = improvement_project.end_date
                    self.steps = improvement_project.steps
                    self.project_type = 'Improvement'

                    # Create a quarterly_plan-like object for template compatibility
                    class TeamWrapper:
                        def __init__(self, team):
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

                    # Make tasks accessible
                    self.tasks = improvement_project.tasks

                    # Calculate completion percentage
                    if improvement_project.tasks.exists():
                        total_tasks = improvement_project.tasks.count()
                        completed_tasks = improvement_project.tasks.filter(is_completed=True).count()
                        self.completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                    else:
                        self.completion_percentage = 0

            enhanced_projects.append(ProjectWrapper(imp_project))

        context.update({
            'weekly_numbers': enhanced_weekly_numbers,
            'monthly_numbers': enhanced_monthly_numbers,
            'projects': enhanced_projects,
            'actions': actions,
            'user_teams': user_teams,
            'current_quarter_display': current_quarter_display,
        })

        return context


class MyNumbersView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/my_numbers.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get current week/month numbers
        weekly_numbers_qs = GPIParameter.objects.filter(
            responsible_user=user,
            tracking_type='weekly'
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year').prefetch_related('milestones')

        # Add model_type to weekly numbers
        weekly_numbers = []
        for gpi in weekly_numbers_qs:
            gpi.model_type = 'gpi'
            weekly_numbers.append(gpi)

        # Get Monthly Numbers from FPI and GPI Parameters
        monthly_fpi = FPIParameter.objects.filter(
            responsible_user=user
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year').prefetch_related('milestones')

        monthly_gpi = GPIParameter.objects.filter(
            responsible_user=user,
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

        # Debug: Print what we're sending to template
        print(f"=== MyNumbersView DEBUG ===")
        print(f"Weekly numbers count: {len(weekly_numbers)}")
        for gpi in weekly_numbers:
            print(f"  {gpi.name}: last_week_actual={gpi.last_week_actual}, current_week_plan={gpi.current_week_plan}")

        print(f"Monthly numbers count: {len(monthly_numbers)}")
        for param in monthly_numbers[:3]:  # Show first 3 to avoid too much output
            if hasattr(param, 'sub_head'):
                name = param.sub_head
            else:
                name = param.name
            print(f"  {name}: last_month_actual={param.last_month_actual}, current_month_plan={param.current_month_plan}")

        context.update({
            'weekly_numbers': weekly_numbers,
            'monthly_numbers': monthly_numbers,
        })

        return context


class SaveNumberView(LoginRequiredMixin, TemplateView):
    def post(self, request):
        try:
            # Handle both parameter naming conventions
            data_type = request.POST.get('type') or request.POST.get('param_type')  # 'gpi' or 'fpi'
            param_id = request.POST.get('id') or request.POST.get('param_id')
            field = request.POST.get('field')
            value = request.POST.get('value', '').strip()

            # Determine if this is a numeric or text field
            numeric_fields = ['last_week_actual', 'current_week_plan', 'last_month_actual', 'current_month_plan']
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
                param = get_object_or_404(GPIParameter, id=param_id, responsible_user=request.user)
                if field in ['last_week_actual', 'current_week_plan', 'last_month_actual', 'current_month_plan', 'explanation']:
                    old_value = getattr(param, field, 'NOT_SET')
                    setattr(param, field, value)
                    param.save()
                    new_value = getattr(param, field, 'NOT_SET')
                    print(f"GPI Save: {field} changed from '{old_value}' to '{new_value}' for param {param_id}")
                else:
                    return JsonResponse({'success': False, 'error': f'Invalid field for GPI: {field}'})

            elif data_type == 'fpi':
                param = get_object_or_404(FPIParameter, id=param_id, responsible_user=request.user)
                if field in ['last_month_actual', 'current_month_plan', 'explanation']:
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

            if not all([param_id, param_type, member_id]):
                return JsonResponse({'success': False, 'error': 'Missing required parameters'})

            # Get the new responsible user
            from django.contrib.auth import get_user_model
            User = get_user_model()
            new_user = get_object_or_404(User, id=member_id)

            if param_type == 'gpi':
                param = get_object_or_404(GPIParameter, id=param_id, responsible_user=request.user)
                param.responsible_user = new_user
                param.save()
            elif param_type == 'fpi':
                param = get_object_or_404(FPIParameter, id=param_id, responsible_user=request.user)
                param.responsible_user = new_user
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
        try:
            task_id = request.POST.get('entity_id')
            member_id = request.POST.get('member_id')

            if not all([task_id, member_id]):
                return JsonResponse({'success': False, 'error': 'Missing required parameters'})

            # Get the new responsible user
            from django.contrib.auth import get_user_model
            User = get_user_model()
            new_user = get_object_or_404(User, id=member_id)

            # Get the task and ensure only the project owner can reassign
            from plans.models import PPITask
            task = get_object_or_404(PPITask, id=task_id)

            # Check if the current user is the project owner
            if task.project.responsible_user != request.user:
                return JsonResponse({'success': False, 'error': 'Only project owner can reassign tasks'})

            # Reassign the task
            task.assigned_to = new_user
            task.save()

            return JsonResponse({
                'success': True,
                'message': f'Task successfully reassigned to {new_user.get_full_name()}'
            })

        except Exception as e:
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
                param = get_object_or_404(FPIParameter, id=param_id)
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get actions assigned to user
        actions = Action.objects.filter(
            assigned_to=user
        ).select_related('team', 'created_by').order_by('original_due_date', '-created_at')

        # Debug: Log the actions being sent to template
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"MyTodoView for user {user}: Found {actions.count()} actions")
        for action in actions[:10]:  # Log first 10 actions
            logger.info(f"  Action {action.id}: {action.action[:50]}")

        context.update({
            'actions': actions,
            'today': timezone.now().date(),
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

        # Check if user has permission to edit this action
        # User can edit if they are assigned to it or they are the creator
        if action.assigned_to != request.user and action.created_by != request.user:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("You don't have permission to edit this action.")

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

        # Check if user has permission to edit this action
        if action.assigned_to != request.user and action.created_by != request.user:
            return JsonResponse({
                'success': False,
                'error': "You don't have permission to edit this action."
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
        
        # Get available teams and members
        teams = Team.objects.filter(is_active=True)
        
        context.update({
            'action': action,
            'teams': teams,
        })
        
        return context


class ActionToggleCompleteView(LoginRequiredMixin, TemplateView):
    def post(self, request, pk):
        action = get_object_or_404(Action, pk=pk)
        
        if action.status == 'completed':
            action.status = 'in_progress'  # or previous status
        else:
            action.status = 'completed'
        
        action.save()
        messages.success(request, 'Action status updated.')
        return redirect('implement:my_todo')


class ActionRejectView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/action_reject.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        action = get_object_or_404(Action, pk=kwargs['pk'])
        context['action'] = action
        return context
    
    def post(self, request, pk):
        action = get_object_or_404(Action, pk=pk)
        rejection_reason = request.POST.get('rejection_reason', '')
        
        action.status = 'rejected'
        action.rejection_reason = rejection_reason
        action.save()
        
        messages.success(request, 'Action rejected.')
        return redirect('implement:my_todo')


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

        return render(request, 'implement/project_form.html', context)

    def post(self, request, pk):
        """Handle the modal form submission"""
        project = get_object_or_404(PPIProject, pk=pk)

        status = request.POST.get('status')
        revised_due_date = request.POST.get('revised_due_date')
        challenge = request.POST.get('challenge', '')
        comments = request.POST.get('comments', '')

        # Validate required fields based on status
        if status == 'at_risk' and not challenge:
            messages.error(request, 'Challenge field is required for At Risk status.')
            return redirect('implement:project_edit', pk=pk)
        elif status == 'danger' and (not challenge or not revised_due_date):
            messages.error(request, 'Challenge and Revised Due Date are required for Danger status.')
            return redirect('implement:project_edit', pk=pk)

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

    def get(self, request, pk):
        project = get_object_or_404(PPIProject, pk=pk)
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
        project = get_object_or_404(PPIProject, pk=pk)

        new_responsible_user_id = request.POST.get('responsible_user')
        team_id = request.POST.get('team')
        reassignment_reason = request.POST.get('reassignment_reason', '')
        handover_notes = request.POST.get('handover_notes', '')
        notify_assignee = request.POST.get('notify_assignee') == 'on'
        transfer_tasks = request.POST.get('transfer_tasks') == 'on'

        if not new_responsible_user_id:
            messages.error(request, 'Please select a user to reassign the project to.')
            return redirect('implement:project_reassign', pk=pk)

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
    template_name = 'implement/project_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(PPIProject, pk=kwargs['pk'])

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