from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import NumbersTracking, ProjectStatus, Action, Issue
from plans.models import PPIProject
from organizations.models import Team


class ImplementDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        from datetime import date

        # Get summary statistics
        context.update({
            'my_actions_count': Action.objects.filter(assigned_to=user, status__in=['not_started', 'in_progress', 'at_risk', 'danger']).count(),
            'my_projects_count': PPIProject.objects.filter(responsible_user=user).count(),
            'pending_numbers': NumbersTracking.objects.filter(assigned_to=user).count(),
            'today': date.today(),
        })

        # Get data for tabs
        # Weekly numbers
        weekly_numbers = NumbersTracking.objects.filter(
            assigned_to=user,
            tracking_type='weekly'
        ).select_related('team', 'fpi_parameter', 'gpi_parameter')

        # Monthly numbers
        monthly_numbers = NumbersTracking.objects.filter(
            assigned_to=user,
            tracking_type='monthly'
        ).select_related('team', 'fpi_parameter', 'gpi_parameter')

        # Projects
        projects = PPIProject.objects.filter(
            responsible_user=user
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year').prefetch_related('status_history')

        # Actions
        actions = Action.objects.filter(
            assigned_to=user
        ).select_related('team', 'created_by').order_by('original_due_date', '-created_at')

        context.update({
            'weekly_numbers': weekly_numbers,
            'monthly_numbers': monthly_numbers,
            'projects': projects,
            'actions': actions,
        })

        return context


class MyNumbersView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/my_numbers.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get current week/month numbers
        weekly_numbers = NumbersTracking.objects.filter(
            assigned_to=user,
            tracking_type='weekly'
        ).select_related('team', 'fpi_parameter', 'gpi_parameter')
        
        monthly_numbers = NumbersTracking.objects.filter(
            assigned_to=user,
            tracking_type='monthly'
        ).select_related('team', 'fpi_parameter', 'gpi_parameter')
        
        context.update({
            'weekly_numbers': weekly_numbers,
            'monthly_numbers': monthly_numbers,
        })
        
        return context


class MyProjectsView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/my_projects.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get projects where user is responsible or has assigned tasks
        projects = PPIProject.objects.filter(
            responsible_user=user
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year')
        
        context['projects'] = projects
        return context


class MyTodoView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/my_todo.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get actions assigned to user
        actions = Action.objects.filter(
            assigned_to=user
        ).select_related('team', 'created_by').order_by('original_due_date', '-created_at')
        
        context['actions'] = actions
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


class ActionEditView(LoginRequiredMixin, UpdateView):
    model = Action
    template_name = 'implement/action_form.html'
    fields = ['action', 'priority', 'status', 'revised_due_date', 'challenge', 'comments']
    success_url = reverse_lazy('implement:my_todo')
    
    def form_valid(self, form):
        messages.success(self.request, 'Action updated successfully.')
        return super().form_valid(form)


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
        
        context.update({
            'parent_action': parent_action,
            'sub_actions': parent_action.sub_actions.all(),
        })
        
        return context


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
    fields = ['name', 'completion_criteria', 'start_date', 'due_date']
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


class ProjectEditView(LoginRequiredMixin, UpdateView):
    model = PPIProject
    template_name = 'implement/project_form.html'
    fields = ['name', 'completion_criteria', 'due_date']
    success_url = reverse_lazy('implement:my_projects')

    def form_valid(self, form):
        messages.success(self.request, 'Project updated successfully.')
        return super().form_valid(form)


class ProjectReassignView(LoginRequiredMixin, TemplateView):
    template_name = 'implement/project_reassign.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(PPIProject, pk=kwargs['pk'])
        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Get available users for assignment
        context['available_users'] = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        context['project'] = project
        return context


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
        
        context.update({
            'project': project,
            'history': project.status_history.all().order_by('-updated_at'),
        })
        
        return context