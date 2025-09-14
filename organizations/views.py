from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from .models import Organization, OrganizationCoordinator, Team, TeamMember
from .forms import OrganizationForm, TeamForm
from .email_service import CoordinatorEmailService
from accounts.models import User


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'admin'


class CoordinatorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ['admin', 'coordinator']


class OrganizationListView(AdminRequiredMixin, ListView):
    model = Organization
    template_name = 'organizations/organization_list.html'
    context_object_name = 'organizations'
    ordering = ['name']


class OrganizationCreateView(AdminRequiredMixin, CreateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/organization_form.html'
    success_url = reverse_lazy('organizations:list')

    def form_valid(self, form):
        messages.success(self.request, 'Organization created successfully.')
        return super().form_valid(form)


class OrganizationEditView(AdminRequiredMixin, UpdateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/organization_form.html'
    success_url = reverse_lazy('organizations:list')

    def form_valid(self, form):
        messages.success(self.request, 'Organization updated successfully.')
        return super().form_valid(form)


class OrganizationToggleStatusView(AdminRequiredMixin, TemplateView):
    def post(self, request, pk):
        organization = get_object_or_404(Organization, pk=pk)
        organization.is_active = not organization.is_active
        organization.save()
        status = 'activated' if organization.is_active else 'deactivated'
        messages.success(request, f'Organization {status} successfully.')
        return redirect('organizations:list')


class OrganizationCoordinatorsView(AdminRequiredMixin, TemplateView):
    template_name = 'organizations/organization_coordinators.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = get_object_or_404(Organization, pk=kwargs['pk'])
        context['organization'] = organization
        context['coordinators'] = organization.coordinators.all()
        return context


class UserListView(CoordinatorRequiredMixin, ListView):
    model = User
    template_name = 'organizations/user_list.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        return User.objects.filter(role='general').order_by('username')


class UserCreateView(CoordinatorRequiredMixin, CreateView):
    model = User
    template_name = 'organizations/user_form.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'mobile_number']
    success_url = reverse_lazy('organizations:users')
    
    def form_valid(self, form):
        form.instance.role = 'general'
        form.instance.set_password('changeme123')  # Default password
        messages.success(self.request, 'User created successfully with default password "changeme123".')
        return super().form_valid(form)


class UserEditView(CoordinatorRequiredMixin, UpdateView):
    model = User
    template_name = 'organizations/user_form.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'mobile_number']
    success_url = reverse_lazy('organizations:users')
    
    def form_valid(self, form):
        messages.success(self.request, 'User updated successfully.')
        return super().form_valid(form)


class UserToggleStatusView(CoordinatorRequiredMixin, TemplateView):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk, role='general')
        user.is_active = not user.is_active
        user.save()
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {status} successfully.')
        return redirect('organizations:users')


class TeamListView(CoordinatorRequiredMixin, ListView):
    model = Team
    template_name = 'organizations/team_list.html'
    context_object_name = 'teams'
    ordering = ['organization', 'name']


class TeamCreateView(CoordinatorRequiredMixin, CreateView):
    model = Team
    form_class = TeamForm
    template_name = 'organizations/team_form.html'
    success_url = reverse_lazy('organizations:teams')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Team created successfully.')
        return super().form_valid(form)


class TeamEditView(CoordinatorRequiredMixin, UpdateView):
    model = Team
    form_class = TeamForm
    template_name = 'organizations/team_form.html'
    success_url = reverse_lazy('organizations:teams')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Team updated successfully.')
        return super().form_valid(form)


class TeamToggleStatusView(CoordinatorRequiredMixin, TemplateView):
    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        team.is_active = not team.is_active
        team.save()
        status = 'activated' if team.is_active else 'deactivated'
        messages.success(request, f'Team {status} successfully.')
        return redirect('organizations:teams')


class TeamMembersView(CoordinatorRequiredMixin, TemplateView):
    template_name = 'organizations/team_members.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = get_object_or_404(Team, pk=kwargs['pk'])
        context['team'] = team
        context['members'] = team.members.all()
        return context


# AJAX Views for Coordinator Management
@method_decorator(csrf_exempt, name='dispatch')
class AddCoordinatorView(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            organization_id = data.get('organization_id')
            name = data.get('name', '').strip()
            mobile = data.get('mobile', '').strip()
            email = data.get('email', '').strip()

            if not all([organization_id, name, email]):
                return JsonResponse({
                    'success': False,
                    'error': 'Organization ID, name, and email are required.'
                })

            # Check if email already exists
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'A user with this email already exists.'
                })

            # Get organization
            organization = get_object_or_404(Organization, id=organization_id)

            # Create coordinator user
            first_name, last_name = (name.split(' ', 1) + [''])[:2]
            coordinator = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                mobile_number=mobile,
                role='coordinator',
                password='changeme123'  # Default password
            )

            # Create organization coordinator relationship
            org_coordinator = OrganizationCoordinator.objects.create(
                organization=organization,
                coordinator=coordinator
            )

            # Send welcome email
            email_sent = CoordinatorEmailService.send_welcome_email(
                coordinator=coordinator,
                organization=organization,
                request=request
            )

            return JsonResponse({
                'success': True,
                'coordinator': {
                    'id': org_coordinator.id,
                    'name': coordinator.get_full_name() or coordinator.username,
                    'email': coordinator.email,
                    'mobile': coordinator.mobile_number or '-',
                    'is_active': org_coordinator.is_active
                },
                'email_sent': email_sent
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class GetCoordinatorView(AdminRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        try:
            org_coordinator = get_object_or_404(OrganizationCoordinator, id=pk)
            coordinator = org_coordinator.coordinator

            return JsonResponse({
                'success': True,
                'coordinator': {
                    'id': org_coordinator.id,
                    'name': coordinator.get_full_name() or coordinator.username,
                    'email': coordinator.email,
                    'mobile': coordinator.mobile_number or '',
                    'is_active': org_coordinator.is_active
                }
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class EditCoordinatorView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            data = json.loads(request.body)
            name = data.get('name', '').strip()
            mobile = data.get('mobile', '').strip()
            email = data.get('email', '').strip()

            if not all([name, email]):
                return JsonResponse({
                    'success': False,
                    'error': 'Name and email are required.'
                })

            # Get coordinator relationship
            org_coordinator = get_object_or_404(OrganizationCoordinator, id=pk)
            coordinator = org_coordinator.coordinator

            # Check if email already exists for other users
            if User.objects.filter(email=email).exclude(id=coordinator.id).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'A user with this email already exists.'
                })

            # Update coordinator user
            first_name, last_name = (name.split(' ', 1) + [''])[:2]
            coordinator.username = email
            coordinator.email = email
            coordinator.first_name = first_name
            coordinator.last_name = last_name
            coordinator.mobile_number = mobile
            coordinator.save()

            # Send update notification email
            email_sent = CoordinatorEmailService.send_update_notification(
                coordinator=coordinator,
                organization=org_coordinator.organization,
                request=request
            )

            return JsonResponse({
                'success': True,
                'coordinator': {
                    'id': org_coordinator.id,
                    'name': coordinator.get_full_name() or coordinator.username,
                    'email': coordinator.email,
                    'mobile': coordinator.mobile_number or '-',
                    'is_active': org_coordinator.is_active
                },
                'email_sent': email_sent
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class GetUsersView(CoordinatorRequiredMixin, View):
    def get(self, request, organization_id, *args, **kwargs):
        try:
            organization = get_object_or_404(Organization, id=organization_id)

            # Get general users - for now we'll return all general users
            # In a full implementation, you'd filter by organization membership
            users = User.objects.filter(role='general', is_active=True)

            users_data = [
                {
                    'id': user.id,
                    'name': user.get_full_name() or user.username,
                    'email': user.email
                }
                for user in users
            ]

            return JsonResponse({
                'success': True,
                'users': users_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class ToggleCoordinatorView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            org_coordinator = get_object_or_404(OrganizationCoordinator, id=pk)
            org_coordinator.is_active = not org_coordinator.is_active
            org_coordinator.save()

            return JsonResponse({
                'success': True,
                'is_active': org_coordinator.is_active,
                'status': 'Active' if org_coordinator.is_active else 'Inactive'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })