from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
import json
from datetime import datetime

from organizations.models import Team, TeamMember
from implement.models import Issue, Action


class UserTeamsAPIView(LoginRequiredMixin, View):
    """API to get teams where user is a manager (for Add Action popup)"""

    def get(self, request):
        user = request.user
        teams = []

        # Get teams where user is a manager
        managed_teams = Team.objects.filter(manager=user, is_active=True)
        for team in managed_teams:
            teams.append({
                'id': team.id,
                'name': team.name,
                'role': 'Manager'
            })

        # Sort teams by name
        teams.sort(key=lambda x: x['name'])

        return JsonResponse({
            'success': True,
            'teams': teams
        })


class IssueTeamsAPIView(LoginRequiredMixin, View):
    """API to get teams where user is a manager or member (for Create Issue popup)"""

    def get(self, request):
        user = request.user
        teams = []
        team_ids_seen = set()

        # Get teams where user is a manager
        managed_teams = Team.objects.filter(manager=user, is_active=True)
        for team in managed_teams:
            teams.append({
                'id': team.id,
                'name': team.name,
                'role': 'Manager'
            })
            team_ids_seen.add(team.id)

        # Get teams where user is a member
        member_teams = TeamMember.objects.filter(
            member=user,
            is_active=True,
            team__is_active=True
        ).select_related('team')

        for membership in member_teams:
            # Only add if not already added as manager
            if membership.team.id not in team_ids_seen:
                teams.append({
                    'id': membership.team.id,
                    'name': membership.team.name,
                    'role': 'Member'
                })
                team_ids_seen.add(membership.team.id)

        # Sort teams by name
        teams.sort(key=lambda x: x['name'])

        return JsonResponse({
            'success': True,
            'teams': teams
        })


class TeamMembersAPIView(LoginRequiredMixin, View):
    """API to get members of a specific team"""

    def get(self, request, team_id):
        user = request.user

        try:
            # Check if user has access to this team
            team = Team.objects.get(id=team_id)

            # Check if user is manager or a team member
            is_manager = team.manager == user
            user_membership = TeamMember.objects.filter(
                member=user,
                team=team,
                is_active=True
            ).first()

            if not is_manager and not user_membership:
                return JsonResponse({
                    'success': False,
                    'error': 'You do not have access to this team'
                })

            members = []

            # If user is manager, show all team members + self
            if is_manager:
                team_members = TeamMember.objects.filter(
                    team=team,
                    is_active=True
                ).select_related('member')

                for membership in team_members:
                    members.append({
                        'id': membership.member.id,
                        'name': membership.member.get_full_name(),
                        'email': membership.member.email,
                        'is_self': membership.member == user
                    })

                # Add self if not already in the list (manager)
                if not any(m['is_self'] for m in members):
                    members.append({
                        'id': user.id,
                        'name': user.get_full_name(),
                        'email': user.email,
                        'is_self': True
                    })
            else:
                # If user is just a member, only show self
                members.append({
                    'id': user.id,
                    'name': user.get_full_name(),
                    'email': user.email,
                    'is_self': True
                })

            return JsonResponse({
                'success': True,
                'members': members
            })

        except Team.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Team not found'
            })


@method_decorator(csrf_exempt, name='dispatch')
class CreateIssueAPIView(LoginRequiredMixin, View):
    """API to create a new issue"""

    def post(self, request):
        try:
            # Get form data
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            priority = request.POST.get('priority', 'medium')
            required_by = request.POST.get('required_by', '').strip()
            team_id = request.POST.get('team', '').strip()

            # Get parameter linking data (for My Numbers issues)
            parameter_type = request.POST.get('parameter_type', '').strip()
            parameter_id = request.POST.get('parameter_id', '').strip()

            # Get project linking data (for My Projects issues)
            project_id = request.POST.get('project_id', '').strip()
            project_type = request.POST.get('project_type', '').strip()

            # Get action linking data (for Action issues)
            action_id = request.POST.get('action_id', '').strip()

            # Get week/month tracking data (for My Numbers)
            week_number = request.POST.get('week_number', '').strip()
            month_number = request.POST.get('month_number', '').strip()

            # Validation
            if not title:
                return JsonResponse({
                    'success': False,
                    'error': 'Issue title is required'
                })

            if not team_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Please select a team'
                })

            # Check if user has access to the team
            try:
                team = Team.objects.get(id=team_id)

                # Check if user is manager or a team member
                is_manager = team.manager == request.user
                user_membership = TeamMember.objects.filter(
                    member=request.user,
                    team=team,
                    is_active=True
                ).first()

                if not is_manager and not user_membership:
                    return JsonResponse({
                        'success': False,
                        'error': 'You do not have access to this team'
                    })
            except Team.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid team selected'
                })

            # Parse required_by date
            required_by_date = None
            if required_by:
                try:
                    required_by_date = datetime.strptime(required_by, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid date format'
                    })

            # Create the issue
            with transaction.atomic():
                issue_data = {
                    'team': team,
                    'title': title,
                    'description': description,
                    'priority': priority,
                    'required_by': required_by_date,
                    'reported_by': request.user
                }

                # Link to parameter if provided
                if parameter_type and parameter_id:
                    from plans.models import GPIParameter, FPIParameter

                    if parameter_type == 'gpi':
                        try:
                            gpi_param = GPIParameter.objects.get(id=parameter_id)
                            issue_data['gpi_parameter'] = gpi_param
                        except GPIParameter.DoesNotExist:
                            pass  # Silently ignore if parameter not found
                    elif parameter_type == 'fpi':
                        try:
                            fpi_param = FPIParameter.objects.get(id=parameter_id)
                            issue_data['fpi_parameter'] = fpi_param
                        except FPIParameter.DoesNotExist:
                            pass  # Silently ignore if parameter not found

                # Link to project if provided
                if project_id and project_type:
                    if project_type == 'PPI':
                        from plans.models import PPIProject
                        try:
                            ppi_project = PPIProject.objects.get(id=project_id)
                            issue_data['ppi_project'] = ppi_project
                        except PPIProject.DoesNotExist:
                            pass
                    elif project_type == 'Improvement':
                        from improve.models import ImprovementProject
                        try:
                            improvement_project = ImprovementProject.objects.get(id=project_id)
                            issue_data['improvement_project'] = improvement_project
                        except ImprovementProject.DoesNotExist:
                            pass

                # Link to action if provided
                if action_id:
                    try:
                        action = Action.objects.get(id=action_id)
                        issue_data['action'] = action
                    except Action.DoesNotExist:
                        pass

                # Add week/month tracking for My Numbers
                if week_number:
                    issue_data['week_number'] = int(week_number)
                if month_number:
                    issue_data['month_number'] = int(month_number)

                issue = Issue.objects.create(**issue_data)

            return JsonResponse({
                'success': True,
                'message': 'Issue created successfully',
                'issue_id': issue.id
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error creating issue: {str(e)}'
            })


@method_decorator(csrf_exempt, name='dispatch')
class TeamMembersForReassignAPIView(LoginRequiredMixin, View):
    """API to get all members of a team for reassignment purposes"""

    def get(self, request, team_id):
        try:
            team = Team.objects.get(id=team_id, is_active=True)

            members = []

            # Get all team members
            team_members = TeamMember.objects.filter(
                team=team,
                is_active=True
            ).select_related('member')

            for membership in team_members:
                members.append({
                    'id': membership.member.id,
                    'name': membership.member.get_full_name(),
                    'email': membership.member.email
                })

            # Add manager if not already in list
            manager_in_list = any(m['id'] == team.manager.id for m in members)
            if not manager_in_list:
                members.append({
                    'id': team.manager.id,
                    'name': team.manager.get_full_name(),
                    'email': team.manager.email
                })

            # Sort by name
            members.sort(key=lambda x: x['name'])

            return JsonResponse({
                'success': True,
                'members': members
            })

        except Team.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Team not found'
            })


class CreateActionAPIView(LoginRequiredMixin, View):
    """API to create a new action"""

    def post(self, request):
        try:
            # Get form data
            action_text = request.POST.get('action', '').strip()
            priority = request.POST.get('priority', 'medium')
            due_date = request.POST.get('due_date', '').strip()
            team_id = request.POST.get('team', '').strip()
            assigned_to_id = request.POST.get('assigned_to', '').strip()
            comments = request.POST.get('comments', '').strip()

            # Get parameter linking data (for My Numbers actions)
            parameter_type = request.POST.get('parameter_type', '').strip()
            parameter_id = request.POST.get('parameter_id', '').strip()

            # Get project linking data (for My Projects actions)
            project_id = request.POST.get('project_id', '').strip()
            project_type = request.POST.get('project_type', '').strip()

            # Get week/month tracking data (for My Numbers)
            week_number = request.POST.get('week_number', '').strip()
            month_number = request.POST.get('month_number', '').strip()

            # Validation
            if not action_text:
                return JsonResponse({
                    'success': False,
                    'error': 'Action is required'
                })

            if not team_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Please select a team'
                })

            if not assigned_to_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Please select a member'
                })

            # Check if user has access to the team
            try:
                team = Team.objects.get(id=team_id)

                # Check if user is manager or a team member
                is_manager = team.manager == request.user
                user_membership = TeamMember.objects.filter(
                    member=request.user,
                    team=team,
                    is_active=True
                ).first()

                if not is_manager and not user_membership:
                    return JsonResponse({
                        'success': False,
                        'error': 'You do not have access to this team'
                    })
            except Team.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid team selected'
                })

            # Check if assigned user is valid
            try:
                from accounts.models import User
                assigned_user = User.objects.get(id=assigned_to_id)

                # Check if assigned user is a member of the team
                assigned_membership = TeamMember.objects.filter(
                    member=assigned_user,
                    team=team,
                    is_active=True
                ).first()

                if not assigned_membership and assigned_user != request.user:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid team member selected'
                    })

            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid user selected'
                })

            # Parse due date
            due_date_parsed = None
            if due_date:
                try:
                    due_date_parsed = datetime.strptime(due_date, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid date format'
                    })
            else:
                # Set default due date to 7 days from now
                from datetime import date, timedelta
                due_date_parsed = date.today() + timedelta(days=7)

            # Check if this is a sub-action
            parent_action_id = request.POST.get('parent_action_id', '').strip()
            parent_action = None
            if parent_action_id:
                try:
                    parent_action = Action.objects.get(id=parent_action_id)
                except Action.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid parent action'
                    })

            # Create the action
            with transaction.atomic():
                action_data = {
                    'team': team,
                    'action': action_text,
                    'priority': priority,
                    'assigned_to': assigned_user,
                    'original_due_date': due_date_parsed,
                    'comments': comments,
                    'created_by': request.user,
                    'source': 'manual',
                    'parent_action': parent_action  # Set parent action if provided
                }

                # Link to parameter if provided
                if parameter_type and parameter_id:
                    from plans.models import GPIParameter, FPIParameter

                    if parameter_type == 'gpi':
                        try:
                            gpi_param = GPIParameter.objects.get(id=parameter_id)
                            action_data['gpi_parameter'] = gpi_param
                        except GPIParameter.DoesNotExist:
                            pass  # Silently ignore if parameter not found
                    elif parameter_type == 'fpi':
                        try:
                            fpi_param = FPIParameter.objects.get(id=parameter_id)
                            action_data['fpi_parameter'] = fpi_param
                        except FPIParameter.DoesNotExist:
                            pass  # Silently ignore if parameter not found

                # Link to project if provided
                if project_id and project_type:
                    if project_type == 'PPI':
                        from plans.models import PPIProject
                        try:
                            ppi_project = PPIProject.objects.get(id=project_id)
                            action_data['ppi_project'] = ppi_project
                        except PPIProject.DoesNotExist:
                            pass
                    elif project_type == 'Improvement':
                        from improve.models import ImprovementProject
                        try:
                            improvement_project = ImprovementProject.objects.get(id=project_id)
                            action_data['improvement_project'] = improvement_project
                        except ImprovementProject.DoesNotExist:
                            pass

                # Add week/month tracking for My Numbers
                if week_number:
                    action_data['week_number'] = int(week_number)
                if month_number:
                    action_data['month_number'] = int(month_number)

                action = Action.objects.create(**action_data)

            return JsonResponse({
                'success': True,
                'message': 'Action created successfully',
                'action_id': action.id
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error creating action: {str(e)}'
            })


class ParameterActionsAPIView(LoginRequiredMixin, View):
    """API to get actions for a specific parameter (GPI or FPI)"""

    def get(self, request):
        parameter_type = request.GET.get('parameter_type')  # 'gpi' or 'fpi'
        parameter_id = request.GET.get('parameter_id')
        week_number = request.GET.get('week_number')
        month_number = request.GET.get('month_number')

        if not parameter_type or not parameter_id:
            return JsonResponse({
                'success': False,
                'message': 'Missing parameter_type or parameter_id'
            })

        try:
            from plans.models import GPIParameter, FPIParameter

            # Get the parameter and its actions
            if parameter_type == 'gpi':
                parameter = GPIParameter.objects.select_related('quarterly_plan__team').get(id=parameter_id)
                actions = Action.objects.filter(gpi_parameter=parameter).select_related('assigned_to')

                # Filter by week/month if provided
                if week_number:
                    actions = actions.filter(week_number=int(week_number))
                if month_number:
                    actions = actions.filter(month_number=int(month_number))

                parameter_name = parameter.name
            elif parameter_type == 'fpi':
                parameter = FPIParameter.objects.select_related('quarterly_plan__team').get(id=parameter_id)
                actions = Action.objects.filter(fpi_parameter=parameter).select_related('assigned_to')

                # Filter by month if provided (FPI is monthly)
                if month_number:
                    actions = actions.filter(month_number=int(month_number))

                parameter_name = parameter.sub_head
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid parameter_type. Must be "gpi" or "fpi"'
                })

            # Format actions for response
            actions_data = []
            for action in actions:
                # Use revised_due_date if available, otherwise original_due_date
                due_date = action.revised_due_date if action.revised_due_date else action.original_due_date

                actions_data.append({
                    'id': action.id,
                    'description': action.action,  # Field is called 'action', not 'description'
                    'assigned_to_name': action.assigned_to.get_full_name() or action.assigned_to.username,
                    'due_date': due_date.strftime('%Y-%m-%d') if due_date else None,
                    'status': action.status,
                    'status_display': action.get_status_display(),
                    'priority': action.priority,
                    'priority_display': action.get_priority_display()
                })

            return JsonResponse({
                'success': True,
                'actions': actions_data,
                'parameter_name': parameter_name
            })

        except (GPIParameter.DoesNotExist, FPIParameter.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': 'Parameter not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error fetching actions: {str(e)}'
            })


class ParameterIssuesAPIView(LoginRequiredMixin, View):
    """API to get issues for a specific parameter (GPI or FPI)"""

    def get(self, request):
        parameter_type = request.GET.get('parameter_type')  # 'gpi' or 'fpi'
        parameter_id = request.GET.get('parameter_id')
        week_number = request.GET.get('week_number')
        month_number = request.GET.get('month_number')

        if not parameter_type or not parameter_id:
            return JsonResponse({
                'success': False,
                'message': 'Missing parameter_type or parameter_id'
            })

        try:
            from plans.models import GPIParameter, FPIParameter

            # Get the parameter and its issues
            if parameter_type == 'gpi':
                parameter = GPIParameter.objects.select_related('quarterly_plan__team').get(id=parameter_id)
                issues = Issue.objects.filter(gpi_parameter=parameter).select_related('team', 'reported_by')

                # Filter by week/month if provided
                if week_number:
                    issues = issues.filter(week_number=int(week_number))
                if month_number:
                    issues = issues.filter(month_number=int(month_number))

                parameter_name = parameter.name
            elif parameter_type == 'fpi':
                parameter = FPIParameter.objects.select_related('quarterly_plan__team').get(id=parameter_id)
                issues = Issue.objects.filter(fpi_parameter=parameter).select_related('team', 'reported_by')

                # Filter by month if provided (FPI is monthly)
                if month_number:
                    issues = issues.filter(month_number=int(month_number))

                parameter_name = parameter.sub_head
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid parameter_type. Must be "gpi" or "fpi"'
                })

            # Format issues for response
            issues_data = []
            for issue in issues:
                issues_data.append({
                    'id': issue.id,
                    'title': issue.title,
                    'description': issue.description,
                    'priority': issue.priority,
                    'priority_display': issue.get_priority_display(),
                    'required_by': issue.required_by.strftime('%Y-%m-%d') if issue.required_by else None,
                    'team_name': issue.team.name,
                    'status': issue.status,
                    'status_display': issue.get_status_display()
                })

            return JsonResponse({
                'success': True,
                'issues': issues_data,
                'parameter_name': parameter_name
            })

        except (GPIParameter.DoesNotExist, FPIParameter.DoesNotExist):
            return JsonResponse({
                'success': False,
                'message': 'Parameter not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error fetching issues: {str(e)}'
            })


class ProjectActionsAPIView(LoginRequiredMixin, View):
    def get(self, request):
        project_id = request.GET.get('project_id')
        project_type = request.GET.get('project_type')

        if not project_id or not project_type:
            return JsonResponse({
                'success': False,
                'error': 'Missing project_id or project_type'
            })

        try:
            if project_type == 'PPI':
                from plans.models import PPIProject
                project = PPIProject.objects.get(id=project_id)
                actions = Action.objects.filter(ppi_project=project).select_related('assigned_to', 'team')
            elif project_type == 'Improvement':
                from improve.models import ImprovementProject
                project = ImprovementProject.objects.get(id=project_id)
                actions = Action.objects.filter(improvement_project=project).select_related('assigned_to', 'team')
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid project type'
                })

            actions_data = []
            for action in actions:
                actions_data.append({
                    'id': action.id,
                    'action': action.action,
                    'priority': action.priority,
                    'priority_display': action.get_priority_display(),
                    'assigned_to_name': action.assigned_to.get_full_name() if action.assigned_to else 'Unassigned',
                    'original_due_date': action.original_due_date.strftime('%Y-%m-%d') if action.original_due_date else None,
                    'status': action.status,
                    'status_display': action.get_status_display()
                })

            return JsonResponse({
                'success': True,
                'actions': actions_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error fetching actions: {str(e)}'
            })


class ProjectIssuesAPIView(LoginRequiredMixin, View):
    def get(self, request):
        project_id = request.GET.get('project_id')
        project_type = request.GET.get('project_type')

        if not project_id or not project_type:
            return JsonResponse({
                'success': False,
                'error': 'Missing project_id or project_type'
            })

        try:
            if project_type == 'PPI':
                from plans.models import PPIProject
                project = PPIProject.objects.get(id=project_id)
                issues = Issue.objects.filter(ppi_project=project).select_related('team', 'reported_by')
            elif project_type == 'Improvement':
                from improve.models import ImprovementProject
                project = ImprovementProject.objects.get(id=project_id)
                issues = Issue.objects.filter(improvement_project=project).select_related('team', 'reported_by')
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid project type'
                })

            issues_data = []
            for issue in issues:
                issues_data.append({
                    'id': issue.id,
                    'title': issue.title,
                    'description': issue.description,
                    'priority': issue.priority,
                    'priority_display': issue.get_priority_display(),
                    'required_by': issue.required_by.strftime('%Y-%m-%d') if issue.required_by else None,
                    'team_name': issue.team.name if issue.team else 'Unassigned',
                    'status': issue.status,
                    'status_display': issue.get_status_display()
                })

            return JsonResponse({
                'success': True,
                'issues': issues_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error fetching issues: {str(e)}'
            })


class ActionActionsAPIView(LoginRequiredMixin, View):
    def get(self, request):
        action_id = request.GET.get('action_id')

        if not action_id:
            return JsonResponse({
                'success': False,
                'error': 'Missing action_id'
            })

        try:
            parent_action = Action.objects.get(id=action_id)
            # Fetch actions that have this action as parent_action
            actions = Action.objects.filter(parent_action=parent_action).select_related('assigned_to', 'team')

            actions_data = []
            for action in actions:
                actions_data.append({
                    'id': action.id,
                    'action': action.action,
                    'priority': action.priority,
                    'priority_display': action.get_priority_display(),
                    'assigned_to_name': action.assigned_to.get_full_name() if action.assigned_to else 'Unassigned',
                    'original_due_date': action.original_due_date.strftime('%Y-%m-%d') if action.original_due_date else None,
                    'status': action.status,
                    'status_display': action.get_status_display()
                })

            return JsonResponse({
                'success': True,
                'actions': actions_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error fetching actions: {str(e)}'
            })


class ActionIssuesAPIView(LoginRequiredMixin, View):
    def get(self, request):
        action_id = request.GET.get('action_id')

        if not action_id:
            return JsonResponse({
                'success': False,
                'error': 'Missing action_id'
            })

        try:
            action = Action.objects.get(id=action_id)
            issues = Issue.objects.filter(action=action).select_related('team', 'reported_by')

            issues_data = []
            for issue in issues:
                issues_data.append({
                    'id': issue.id,
                    'title': issue.title,
                    'description': issue.description,
                    'priority': issue.priority,
                    'priority_display': issue.get_priority_display(),
                    'required_by': issue.required_by.strftime('%Y-%m-%d') if issue.required_by else None,
                    'team_name': issue.team.name if issue.team else 'Unassigned',
                    'status': issue.status,
                    'status_display': issue.get_status_display()
                })

            return JsonResponse({
                'success': True,
                'issues': issues_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error fetching issues: {str(e)}'
            })


class ActionActionsAPIView(LoginRequiredMixin, View):
    def get(self, request):
        action_id = request.GET.get('action_id')

        if not action_id:
            return JsonResponse({
                'success': False,
                'error': 'Missing action_id'
            })

        try:
            parent_action = Action.objects.get(id=action_id)
            # Fetch actions that have this action as parent_action
            actions = Action.objects.filter(parent_action=parent_action).select_related('assigned_to', 'team')

            actions_data = []
            for action in actions:
                actions_data.append({
                    'id': action.id,
                    'action': action.action,
                    'priority': action.priority,
                    'priority_display': action.get_priority_display(),
                    'assigned_to_name': action.assigned_to.get_full_name() if action.assigned_to else 'Unassigned',
                    'original_due_date': action.original_due_date.strftime('%Y-%m-%d') if action.original_due_date else None,
                    'status': action.status,
                    'status_display': action.get_status_display()
                })

            return JsonResponse({
                'success': True,
                'actions': actions_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error fetching actions: {str(e)}'
            })
