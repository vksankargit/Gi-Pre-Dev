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
from .models import Organization, OrganizationCoordinator, Team, TeamMember, TeamMeetingType
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_organizations_count'] = Organization.objects.filter(is_active=True).count()
        return context


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
        if self.request.user.role == 'coordinator':
            # Show only users from organizations this coordinator manages
            from .models import OrganizationCoordinator
            coordinator_orgs = OrganizationCoordinator.objects.filter(
                coordinator=self.request.user,
                is_active=True
            ).values_list('organization', flat=True)
            return User.objects.filter(
                role='general',
                organization__in=coordinator_orgs
            ).select_related('organization').order_by('organization__name', 'username')
        else:
            # Admins can see all general users
            return User.objects.filter(role='general').select_related('organization').order_by('organization__name', 'username')


class UserCreateView(CoordinatorRequiredMixin, CreateView):
    model = User
    template_name = 'organizations/user_form.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'mobile_number', 'organization']
    success_url = reverse_lazy('organizations:users')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter organizations based on user role
        if self.request.user.role == 'coordinator':
            # Show only organizations this coordinator manages
            from .models import OrganizationCoordinator
            coordinator_orgs = OrganizationCoordinator.objects.filter(
                coordinator=self.request.user,
                is_active=True
            ).values_list('organization', flat=True)
            form.fields['organization'].queryset = Organization.objects.filter(
                id__in=coordinator_orgs,
                is_active=True
            )
        else:
            # Admins can see all active organizations
            form.fields['organization'].queryset = Organization.objects.filter(is_active=True)

        form.fields['organization'].required = True
        return form

    def form_valid(self, form):
        form.instance.role = 'general'
        form.instance.set_password('changeme123')  # Default password
        messages.success(self.request, 'User created successfully with default password "changeme123".')
        return super().form_valid(form)


class UserEditView(CoordinatorRequiredMixin, UpdateView):
    model = User
    template_name = 'organizations/user_form.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'mobile_number', 'organization']
    success_url = reverse_lazy('organizations:users')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter organizations based on user role
        if self.request.user.role == 'coordinator':
            # Show only organizations this coordinator manages
            from .models import OrganizationCoordinator
            coordinator_orgs = OrganizationCoordinator.objects.filter(
                coordinator=self.request.user,
                is_active=True
            ).values_list('organization', flat=True)
            form.fields['organization'].queryset = Organization.objects.filter(
                id__in=coordinator_orgs,
                is_active=True
            )
        else:
            # Admins can see all active organizations
            form.fields['organization'].queryset = Organization.objects.filter(is_active=True)

        form.fields['organization'].required = True
        return form

    def get_queryset(self):
        # Users can only edit users from their managed organizations (for coordinators)
        if self.request.user.role == 'coordinator':
            from .models import OrganizationCoordinator
            coordinator_orgs = OrganizationCoordinator.objects.filter(
                coordinator=self.request.user,
                is_active=True
            ).values_list('organization', flat=True)
            return User.objects.filter(role='general', organization__in=coordinator_orgs)
        else:
            return User.objects.filter(role='general')

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
        import sys
        sys.stderr.write("DEBUG: TeamCreateView form_valid called - form is valid!\n")
        sys.stderr.flush()
        messages.success(self.request, 'Team Meeting created successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        import sys
        sys.stderr.write("DEBUG: TeamCreateView form_invalid called - validation failed!\n")
        sys.stderr.write(f"DEBUG: Form errors: {form.errors}\n")
        sys.stderr.write(f"DEBUG: Form data: {form.data}\n")
        for field_name, field in form.fields.items():
            if field_name in form.errors:
                sys.stderr.write(f"DEBUG: Field '{field_name}' error: {form.errors[field_name]}\n")
        sys.stderr.flush()
        return super().form_invalid(form)


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
        messages.success(self.request, 'Team Meeting updated successfully.')
        return super().form_valid(form)


class TeamToggleStatusView(CoordinatorRequiredMixin, TemplateView):
    def post(self, request, pk):
        team = get_object_or_404(Team, pk=pk)
        team.is_active = not team.is_active
        team.save()
        status = 'activated' if team.is_active else 'deactivated'
        messages.success(request, f'Team Meeting {status} successfully.')
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
            coordinator_type = data.get('type', 'new')  # 'existing' or 'new'

            if not organization_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Organization ID is required.'
                })

            # Get organization
            organization = get_object_or_404(Organization, id=organization_id)

            if coordinator_type == 'existing':
                # Handle existing coordinator assignment
                coordinator_id = data.get('coordinator_id')
                if not coordinator_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Coordinator ID is required for existing coordinator.'
                    })

                # Get the existing coordinator
                coordinator = get_object_or_404(User, id=coordinator_id, role='coordinator')

                # Check if already assigned to this organization
                if OrganizationCoordinator.objects.filter(
                    organization=organization,
                    coordinator=coordinator
                ).exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'This coordinator is already assigned to this organization.'
                    })

                # Create organization coordinator relationship
                org_coordinator = OrganizationCoordinator.objects.create(
                    organization=organization,
                    coordinator=coordinator
                )

                email_sent = False  # No welcome email for existing coordinators

            else:
                # Handle new coordinator creation
                name = data.get('name', '').strip()
                mobile = data.get('mobile', '').strip()
                email = data.get('email', '').strip()

                if not all([name, email]):
                    return JsonResponse({
                        'success': False,
                        'error': 'Name and email are required for new coordinator.'
                    })

                # Check if email already exists
                if User.objects.filter(email=email).exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'A user with this email already exists.'
                    })

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

                # Send welcome email for new coordinators
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
                'email_sent': email_sent,
                'type': coordinator_type
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

            # Filter users by the selected organization
            users = User.objects.filter(
                role='general',
                is_active=True,
                organization=organization
            )

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


@method_decorator(csrf_exempt, name='dispatch')
class RemoveCoordinatorView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            org_coordinator = get_object_or_404(OrganizationCoordinator, id=pk)
            coordinator_name = org_coordinator.coordinator.get_full_name() or org_coordinator.coordinator.username
            organization_name = org_coordinator.organization.name

            # Delete the coordinator relationship
            org_coordinator.delete()

            return JsonResponse({
                'success': True,
                'message': f'{coordinator_name} has been removed from {organization_name}.'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class GetAvailableCoordinatorsView(AdminRequiredMixin, View):
    def get(self, request, organization_id, *args, **kwargs):
        try:
            organization = get_object_or_404(Organization, id=organization_id)

            # Get all coordinators who are not already assigned to this organization
            assigned_coordinator_ids = OrganizationCoordinator.objects.filter(
                organization=organization
            ).values_list('coordinator_id', flat=True)

            available_coordinators = User.objects.filter(
                role='coordinator',
                is_active=True
            ).exclude(id__in=assigned_coordinator_ids)

            coordinators_data = [
                {
                    'id': coord.id,
                    'name': coord.get_full_name() or coord.username,
                    'email': coord.email,
                    'mobile': coord.mobile_number or ''
                }
                for coord in available_coordinators
            ]

            return JsonResponse({
                'success': True,
                'coordinators': coordinators_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

@method_decorator(csrf_exempt, name='dispatch')
class GetMeetingTypesView(CoordinatorRequiredMixin, View):
    """AJAX view to get meeting types for a specific organization"""

    def get(self, request, organization_id, *args, **kwargs):
        try:
            organization = get_object_or_404(Organization, id=organization_id)

            # Get all active meeting types for this organization
            meeting_types = TeamMeetingType.objects.filter(
                organization=organization,
                is_active=True
            ).order_by('name')

            meeting_types_data = [
                {
                    'id': mt.id,
                    'name': mt.name
                }
                for mt in meeting_types
            ]

            return JsonResponse({
                'success': True,
                'meeting_types': meeting_types_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(csrf_exempt, name='dispatch')
class CreateMeetingTypeView(CoordinatorRequiredMixin, View):
    """AJAX view to create a new meeting type"""

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            organization_id = data.get('organization_id')
            name = data.get('name', '').strip()

            if not organization_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Organization ID is required.'
                })

            if not name:
                return JsonResponse({
                    'success': False,
                    'error': 'Meeting type name is required.'
                })

            # Get organization
            organization = get_object_or_404(Organization, id=organization_id)

            # Check if meeting type already exists for this organization
            existing_type = TeamMeetingType.objects.filter(
                organization=organization,
                name__iexact=name
            ).first()

            if existing_type:
                if existing_type.is_active:
                    return JsonResponse({
                        'success': False,
                        'error': 'A meeting type with this name already exists for this organization.'
                    })
                else:
                    # Reactivate if it was deactivated
                    existing_type.is_active = True
                    existing_type.save()
                    return JsonResponse({
                        'success': True,
                        'meeting_type': {
                            'id': existing_type.id,
                            'name': existing_type.name
                        }
                    })

            # Create new meeting type
            meeting_type = TeamMeetingType.objects.create(
                organization=organization,
                name=name
            )

            return JsonResponse({
                'success': True,
                'meeting_type': {
                    'id': meeting_type.id,
                    'name': meeting_type.name
                }
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
class GetTeamMembersView(View):
    """AJAX view to get team members for reassignment dropdown"""

    def get(self, request, team_id, *args, **kwargs):
        try:
            # Verify the user has access to this team (must be manager)
            team = get_object_or_404(Team, id=team_id, manager=request.user)

            # Get team members including the manager
            members_data = []

            # Add team manager
            members_data.append({
                'id': team.manager.id,
                'name': team.manager.get_full_name() or team.manager.username,
                'is_manager': True
            })

            # Add team members
            for team_member in team.members.filter(is_active=True):
                members_data.append({
                    'id': team_member.member.id,
                    'name': team_member.member.get_full_name() or team_member.member.username,
                    'is_manager': False
                })

            return JsonResponse({
                'success': True,
                'members': members_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

