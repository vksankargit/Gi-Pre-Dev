from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.db import models
from django.db.models import Q
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

            # Get quarter tracking data (for My Projects)
            quarter_number = request.POST.get('quarter_number', '').strip()

            # Get review meeting ID (for review location issues)
            meeting_id = request.POST.get('meeting_id', '').strip()

            # Debug logging commented out to avoid Unicode encoding issues
            # print(f"DEBUG CREATE ISSUE: Title='{title}', Team={team_id}, ParamType={parameter_type}, ParamID={parameter_id}, Week={week_number}, Month={month_number}")

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
                    from plans.models import GPIParameter

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

                # Add quarter tracking for My Projects
                if quarter_number:
                    issue_data['quarter_number'] = int(quarter_number)

                # Link to review meeting if provided
                if meeting_id:
                    from reviews.models import ReviewMeeting
                    try:
                        review_meeting = ReviewMeeting.objects.get(id=meeting_id)
                        issue_data['review_meeting'] = review_meeting
                    except ReviewMeeting.DoesNotExist:
                        pass  # Silently ignore if meeting not found

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

            # Get quarter tracking data (for My Projects)
            quarter_number = request.POST.get('quarter_number', '').strip()

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
                    from plans.models import GPIParameter

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

                # Add quarter tracking for My Projects
                if quarter_number:
                    action_data['quarter_number'] = int(quarter_number)

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
        parameter_type = request.GET.get('parameter_type')  # 'gpi', 'fpi', or 'screen'
        parameter_id = request.GET.get('parameter_id')
        week_number = request.GET.get('week_number')
        month_number = request.GET.get('month_number')

        # Handle screen-level actions (no specific parameter)
        if parameter_type == 'screen' or parameter_id == 'null' or not parameter_id:
            try:
                from organizations.models import TeamMember

                # Get user's teams
                user_teams = list(Team.objects.filter(
                    Q(manager=request.user) |
                    Q(members__member=request.user, members__is_active=True)
                ).values_list('id', flat=True))

                # Get all screen-level actions (no parameter link) for user's teams
                actions = Action.objects.filter(
                    gpi_parameter__isnull=True,
                    ppi_project__isnull=True,
                    improvement_project__isnull=True,
                    team_id__in=user_teams
                ).select_related('assigned_to', 'team')

                # Filter by week/month if provided
                if week_number:
                    actions = actions.filter(week_number=int(week_number))
                if month_number:
                    actions = actions.filter(month_number=int(month_number))

                parameter_name = f"Screen-level Actions (Week {week_number})" if week_number else f"Screen-level Actions (Month {month_number})"

                # Format actions for response
                actions_data = []
                for action in actions:
                    # Use revised_due_date if available, otherwise original_due_date
                    due_date = action.revised_due_date if action.revised_due_date else action.original_due_date

                    # Format assigned to with team name
                    assigned_to_display = f"{action.team.name} - {action.assigned_to.get_full_name() or action.assigned_to.username}" if action.team else (action.assigned_to.get_full_name() or action.assigned_to.username)

                    actions_data.append({
                        'id': action.id,
                        'description': action.action,
                        'assigned_to_name': assigned_to_display,
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

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error fetching screen-level actions: {str(e)}'
                })

        if not parameter_type or not parameter_id:
            return JsonResponse({
                'success': False,
                'message': 'Missing parameter_type or parameter_id'
            })

        try:
            from plans.models import GPIParameter

            # Get the parameter and its actions
            if parameter_type == 'gpi':
                parameter = GPIParameter.objects.select_related('quarterly_plan__team').get(id=parameter_id)
                actions = Action.objects.filter(gpi_parameter=parameter).select_related('assigned_to', 'team')

                # Filter by week/month if provided
                if week_number:
                    actions = actions.filter(week_number=int(week_number))
                if month_number:
                    actions = actions.filter(month_number=int(month_number))

                parameter_name = parameter.name
            elif parameter_type == 'fpi':
                parameter = FPIParameter.objects.select_related('quarterly_plan__team').get(id=parameter_id)
                actions = Action.objects.filter(fpi_parameter=parameter).select_related('assigned_to', 'team')

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

                # Format assigned to with team name
                assigned_to_display = f"{action.team.name} - {action.assigned_to.get_full_name() or action.assigned_to.username}" if action.team else (action.assigned_to.get_full_name() or action.assigned_to.username)

                actions_data.append({
                    'id': action.id,
                    'description': action.action,  # Field is called 'action', not 'description'
                    'assigned_to_name': assigned_to_display,
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

        except (GPIParameter.DoesNotExist.DoesNotExist):
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
        parameter_type = request.GET.get('parameter_type')  # 'gpi', 'fpi', or 'screen'
        parameter_id = request.GET.get('parameter_id')
        week_number = request.GET.get('week_number')
        month_number = request.GET.get('month_number')

        # Handle screen-level issues (no specific parameter)
        if parameter_type == 'screen' or parameter_id == 'null' or not parameter_id:
            try:
                from organizations.models import TeamMember

                # Get user's teams
                user_teams = list(Team.objects.filter(
                    Q(manager=request.user) |
                    Q(members__member=request.user, members__is_active=True)
                ).values_list('id', flat=True))

                # Get all screen-level issues (no parameter link) for user's teams
                issues = Issue.objects.filter(
                    gpi_parameter__isnull=True,
                    ppi_project__isnull=True,
                    improvement_project__isnull=True,
                    action__isnull=True,
                    team_id__in=user_teams
                ).select_related('team', 'reported_by')

                # Filter by week/month if provided
                if week_number:
                    issues = issues.filter(week_number=int(week_number))
                if month_number:
                    issues = issues.filter(month_number=int(month_number))

                parameter_name = f"Screen-level Issues (Week {week_number})" if week_number else f"Screen-level Issues (Month {month_number})"

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
                        'team_name': issue.team.name if issue.team else 'Unassigned',
                        'status': issue.status,
                        'status_display': issue.get_status_display()
                    })

                return JsonResponse({
                    'success': True,
                    'issues': issues_data,
                    'parameter_name': parameter_name
                })

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error fetching screen-level issues: {str(e)}'
                })

        if not parameter_type or not parameter_id:
            return JsonResponse({
                'success': False,
                'message': 'Missing parameter_type or parameter_id'
            })

        try:
            from plans.models import GPIParameter

            # Get the parameter and its issues
            if parameter_type == 'gpi':
                parameter = GPIParameter.objects.select_related('quarterly_plan__team').get(id=parameter_id)

                # Get user's teams
                from organizations.models import TeamMember
                user_teams = list(Team.objects.filter(
                    Q(manager=request.user) |
                    Q(members__member=request.user, members__is_active=True)
                ).values_list('id', flat=True))

                # Debug logging commented out
                # print(f"DEBUG: User {request.user.username} belongs to teams: {user_teams}")

                # Filter issues to only show those from user's teams
                issues = Issue.objects.filter(
                    gpi_parameter=parameter,
                    team_id__in=user_teams
                ).select_related('team', 'reported_by')
                # print(f"DEBUG: Found {issues.count()} total issues for GPI {parameter_id} in user's teams")

                # Debug: Print ALL issues BEFORE week/month filtering
                # for issue in issues:
                #     print(f"DEBUG BEFORE FILTER: Issue #{issue.id}: '{issue.title}', Team: {issue.team.name}, Week: {issue.week_number}")

                # Filter by week/month if provided
                if week_number:
                    issues = issues.filter(week_number=int(week_number))
                    # print(f"DEBUG: After week filter ({week_number}): {issues.count()} issues")
                if month_number:
                    issues = issues.filter(month_number=int(month_number))
                    # print(f"DEBUG: After month filter ({month_number}): {issues.count()} issues")

                # Debug: Print all issues with their details
                # for issue in issues:
                #     print(f"DEBUG: Issue #{issue.id}: {issue.title}, Team: {issue.team.name}, Week: {issue.week_number}, Status: {issue.status}")

                parameter_name = parameter.name
            elif parameter_type == 'fpi':
                parameter = FPIParameter.objects.select_related('quarterly_plan__team').get(id=parameter_id)

                # Get user's teams
                from organizations.models import TeamMember
                user_teams = list(Team.objects.filter(
                    Q(manager=request.user) |
                    Q(members__member=request.user, members__is_active=True)
                ).values_list('id', flat=True))

                # Filter issues to only show those from user's teams
                issues = Issue.objects.filter(
                    fpi_parameter=parameter,
                    team_id__in=user_teams
                ).select_related('team', 'reported_by')

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

        except (GPIParameter.DoesNotExist.DoesNotExist):
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
                # Format assigned to with team name
                if action.assigned_to:
                    assigned_to_display = f"{action.team.name} - {action.assigned_to.get_full_name()}" if action.team else action.assigned_to.get_full_name()
                else:
                    assigned_to_display = 'Unassigned'

                actions_data.append({
                    'id': action.id,
                    'action': action.action,
                    'priority': action.priority,
                    'priority_display': action.get_priority_display(),
                    'assigned_to_name': assigned_to_display,
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
                # Format assigned to with team name
                if action.assigned_to:
                    assigned_to_display = f"{action.team.name} - {action.assigned_to.get_full_name()}" if action.team else action.assigned_to.get_full_name()
                else:
                    assigned_to_display = 'Unassigned'

                actions_data.append({
                    'id': action.id,
                    'action': action.action,
                    'priority': action.priority,
                    'priority_display': action.get_priority_display(),
                    'assigned_to_name': assigned_to_display,
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

class AvailablePeriodsAPIView(LoginRequiredMixin, View):
    """API endpoint to get available periods (weeks/months/quarters/years) for a team"""

    def get(self, request):
        from django.utils import timezone
        from reviews.models import ReviewMeeting
        from plans.models import FinancialYear
        from datetime import datetime, timedelta
        import calendar

        team_id = request.GET.get('team_id')
        period_type = request.GET.get('period_type')  # 'week', 'month', 'quarter', 'year'

        try:
            team = Team.objects.get(id=team_id)

            # Get the last review for this team
            last_review = ReviewMeeting.objects.filter(
                team=team,
                is_adhoc=False
            ).order_by('-review_date').first()

            periods = []
            today = timezone.now().date()

            # Get current financial year
            current_fy = FinancialYear.objects.filter(
                start_date__lte=today,
                end_date__gte=today
            ).first()

            if period_type == 'week':
                # Use ISO week numbers
                # Get the current ISO week number
                current_iso_week = today.isocalendar()[1]
                current_year = today.isocalendar()[0]

                # Get last review's ISO week if available
                last_iso_week = None
                if last_review and last_review.review_date:
                    last_review_date = last_review.review_date.date() if hasattr(last_review.review_date, 'date') else last_review.review_date
                    last_iso_week = last_review_date.isocalendar()[1]
                    last_year = last_review_date.isocalendar()[0]

                    # If last review was in a different year, start from week 1 of current year
                    if last_year != current_year:
                        last_iso_week = 0

                # Start from week after last review, or a reasonable range (last 13 weeks - one quarter)
                if last_iso_week is None:
                    # No last review - show last 13 weeks
                    start_week = max(1, current_iso_week - 12)
                else:
                    # Has last review - start from next week after last review
                    start_week = last_iso_week + 1

                # Ensure start_week doesn't exceed current_iso_week
                # If it does, show at least the current week
                if start_week > current_iso_week:
                    start_week = current_iso_week

                # Generate weeks from start_week to current week
                for iso_week in range(start_week, current_iso_week + 1):
                    # Calculate the Monday of this ISO week
                    # ISO weeks start on Monday
                    import datetime
                    week_start = datetime.datetime.strptime(f'{current_year}-W{iso_week:02d}-1', '%G-W%V-%u').date()
                    week_end = week_start + timedelta(days=6)

                    periods.append({
                        'number': iso_week,
                        'date_range': f'{week_start.strftime("%d-%b")} to {week_end.strftime("%d-%b")}'
                    })

            elif period_type == 'month':
                # Get current month and quarter
                if current_fy:
                    months_from_start = ((today.year - current_fy.start_date.year) * 12 +
                                        (today.month - current_fy.start_date.month))
                    current_quarter = (months_from_start // 3) + 1
                    month_in_quarter = (months_from_start % 3) + 1

                    start_month = 1
                    if last_review and last_review.month_number:
                        start_month = last_review.month_number + 1

                    # Generate months up to current month in quarter
                    for month_num in range(start_month, month_in_quarter + 1):
                        # Calculate actual calendar month
                        months_offset = ((current_quarter - 1) * 3) + (month_num - 1)
                        actual_month = current_fy.start_date.month + months_offset
                        actual_year = current_fy.start_date.year + (actual_month - 1) // 12
                        actual_month = ((actual_month - 1) % 12) + 1

                        month_name = calendar.month_abbr[actual_month]
                        year_short = str(actual_year)[2:]

                        periods.append({
                            'number': month_num,
                            'name': f'{month_name}-{year_short}'
                        })

            elif period_type == 'quarter':
                # All quarters
                periods = [
                    {'number': 1, 'name': 'Q1 (Apr-Jun)'},
                    {'number': 2, 'name': 'Q2 (Jul-Sep)'},
                    {'number': 3, 'name': 'Q3 (Oct-Dec)'},
                    {'number': 4, 'name': 'Q4 (Jan-Mar)'}
                ]

            elif period_type == 'year':
                # Generate financial years
                current_year = timezone.now().year
                for year in range(current_year - 2, current_year + 3):
                    periods.append({
                        'number': year,
                        'name': f'FY {year % 100:02d}-{(year + 1) % 100:02d}'
                    })

            return JsonResponse({
                'success': True,
                'periods': periods
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class CheckPendingReviewsAPIView(LoginRequiredMixin, View):
    """API endpoint to check if there are pending reviews before a selected date"""
    
    def get(self, request):
        from django.utils import timezone
        from reviews.models import ReviewMeeting
        from datetime import datetime
        
        team_id = request.GET.get('team_id')
        selected_date_str = request.GET.get('date')
        
        try:
            team = Team.objects.get(id=team_id)
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            today = timezone.now().date()
            
            # Check if there are reviews with status 'scheduled' before the selected date
            pending_reviews = ReviewMeeting.objects.filter(
                team=team,
                review_date__lt=selected_date,
                review_date__gte=today,
                status='scheduled'
            ).count()
            
            if pending_reviews > 0:
                return JsonResponse({
                    'success': True,
                    'has_pending': True,
                    'message': f'There are {pending_reviews} pending review(s) before this date. Consider completing them first.'
                })
            else:
                return JsonResponse({
                    'success': True,
                    'has_pending': False
                })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class GPIAvailablePeriodsAPIView(LoginRequiredMixin, View):
    """API endpoint to get available periods (weeks/months) for GPI tab
    Shows periods from current quarter and previous quarter"""

    def get(self, request):
        from django.utils import timezone
        from reviews.models import ReviewMeeting
        from plans.models import FinancialYear
        from datetime import datetime, timedelta
        import calendar

        meeting_id = request.GET.get('meeting_id')
        team_id = request.GET.get('team_id')
        period_type = request.GET.get('period_type')  # 'week' or 'month'

        try:
            team = Team.objects.get(id=team_id)
            meeting = ReviewMeeting.objects.get(id=meeting_id)

            review_date = meeting.review_date.date() if hasattr(meeting.review_date, 'date') else meeting.review_date

            # Get current financial year
            current_fy = FinancialYear.objects.filter(
                start_date__lte=review_date,
                end_date__gte=review_date
            ).first()

            if not current_fy:
                return JsonResponse({
                    'success': False,
                    'error': 'No financial year found for review date'
                }, status=400)

            periods = []

            if period_type == 'week':
                # Use ISO week numbers
                # Get the review week number
                review_week = meeting.week_number if meeting.week_number else review_date.isocalendar()[1]

                # Generate weeks: last 13 weeks up to and including the review week
                # This gives us roughly the current and previous quarter
                weeks_to_show = 13

                for i in range(weeks_to_show - 1, -1, -1):
                    # Calculate the date for this week (going backwards from review_date)
                    week_date = review_date - timedelta(weeks=i)
                    iso_year, iso_week, iso_day = week_date.isocalendar()

                    # Get Monday of that ISO week
                    # Calculate the Monday of the ISO week
                    week_monday = week_date - timedelta(days=iso_day - 1)
                    week_sunday = week_monday + timedelta(days=6)

                    periods.append({
                        'number': iso_week,
                        'date_range': f'{week_monday.strftime("%d-%b-%y")} to {week_sunday.strftime("%d-%b-%y")}',
                        'year': iso_year
                    })

            elif period_type == 'month':
                # Determine current quarter based on review date
                months_from_start = ((review_date.year - current_fy.start_date.year) * 12 +
                                    (review_date.month - current_fy.start_date.month))
                current_quarter = min(4, max(1, (months_from_start // 3) + 1))
                month_in_quarter = (months_from_start % 3) + 1

                # Previous quarter months (3 months)
                prev_quarter = current_quarter - 1 if current_quarter > 1 else 4
                for month_num in range(1, 4):  # 3 months in previous quarter
                    months_offset = ((prev_quarter - 1) * 3) + (month_num - 1)
                    actual_month = current_fy.start_date.month + months_offset
                    actual_year = current_fy.start_date.year + (actual_month - 1) // 12
                    actual_month = ((actual_month - 1) % 12) + 1

                    month_name = calendar.month_name[actual_month]

                    periods.append({
                        'number': month_num,
                        'name': f'{month_name} {actual_year}',
                        'quarter': prev_quarter
                    })

                # Current quarter months (up to review month)
                for month_num in range(1, month_in_quarter + 1):
                    months_offset = ((current_quarter - 1) * 3) + (month_num - 1)
                    actual_month = current_fy.start_date.month + months_offset
                    actual_year = current_fy.start_date.year + (actual_month - 1) // 12
                    actual_month = ((actual_month - 1) % 12) + 1

                    month_name = calendar.month_name[actual_month]

                    periods.append({
                        'number': month_num + 3,  # Offset by previous quarter months
                        'name': f'{month_name} {actual_year}',
                        'quarter': current_quarter
                    })

            return JsonResponse({
                'success': True,
                'periods': periods
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class PPIAvailableQuartersAPIView(LoginRequiredMixin, View):
    """API endpoint to get available quarters for PPI tab (previous + current quarter)"""

    def get(self, request):
        try:
            meeting_id = request.GET.get('meeting_id')
            team_id = request.GET.get('team_id')

            if not meeting_id or not team_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing meeting_id or team_id'
                }, status=400)

            # Get the review meeting
            from reviews.models import ReviewMeeting
            meeting = ReviewMeeting.objects.get(pk=meeting_id)
            review_date = meeting.review_date.date()

            # Get current financial year
            from plans.models import FinancialYear
            financial_year = FinancialYear.objects.filter(
                start_date__lte=review_date,
                end_date__gte=review_date
            ).first()

            if not financial_year:
                return JsonResponse({
                    'success': False,
                    'error': 'No financial year found'
                }, status=404)

            # Calculate current quarter
            months_from_fy_start = ((review_date.year - financial_year.start_date.year) * 12 +
                                    (review_date.month - financial_year.start_date.month))
            current_quarter = min(4, max(1, (months_from_fy_start // 3) + 1))

            # Build quarters list (previous quarter + current quarter)
            quarters = []

            # Add previous quarter if exists
            if current_quarter > 1:
                prev_quarter = current_quarter - 1
                quarters.append({
                    'number': prev_quarter,
                    'display_name': f'Q{prev_quarter} of {financial_year.year}',
                    'is_current': False
                })

            # Add current quarter
            quarters.append({
                'number': current_quarter,
                'display_name': f'Q{current_quarter} of {financial_year.year}',
                'is_current': True
            })

            return JsonResponse({
                'success': True,
                'quarters': quarters,
                'current_quarter': current_quarter
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class PPIDataAPIView(LoginRequiredMixin, View):
    """API endpoint to get PPI project data for a specific quarter and tracking type"""

    def get(self, request):
        try:
            meeting_id = request.GET.get('meeting_id')
            team_id = request.GET.get('team_id')
            quarter = int(request.GET.get('quarter', 1))
            tracking_type = request.GET.get('tracking_type', 'weekly')

            if not meeting_id or not team_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required parameters'
                }, status=400)

            # Get the review meeting
            from reviews.models import ReviewMeeting
            from organizations.models import Team
            meeting = ReviewMeeting.objects.get(pk=meeting_id)
            team = Team.objects.get(pk=team_id)
            review_date = meeting.review_date.date()

            # Get current financial year
            from plans.models import FinancialYear, QuarterlyPlan
            financial_year = FinancialYear.objects.filter(
                start_date__lte=review_date,
                end_date__gte=review_date
            ).first()

            if not financial_year:
                return JsonResponse({
                    'success': False,
                    'error': 'No financial year found'
                }, status=404)

            # Calculate current quarter
            months_from_fy_start = ((review_date.year - financial_year.start_date.year) * 12 +
                                    (review_date.month - financial_year.start_date.month))
            current_quarter = min(4, max(1, (months_from_fy_start // 3) + 1))

            # Check if the selected quarter is the current quarter (for editability)
            is_current_quarter = (quarter == current_quarter)

            # Get PPI projects for the quarter with the specified tracking type
            # We need to combine projects from TWO sources:
            # 1. PPIProject (from plans app - quarterly plan)
            # 2. ImprovementProject (from improve app - uploaded files)
            from plans.models import PPIProject, QuarterlyPlan
            from improve.models import ImprovementProject

            project_data = []

            # SOURCE 1: Get PPIProjects from QuarterlyPlan
            quarterly_plan = QuarterlyPlan.objects.filter(
                financial_year=financial_year,
                quarter=quarter,
                team=team
            ).first()

            if quarterly_plan:
                ppi_projects = PPIProject.objects.filter(
                    quarterly_plan=quarterly_plan,
                    tracking_type=tracking_type
                ).select_related('responsible_user', 'quarterly_plan')

                # Process PPIProjects
                for project in ppi_projects:
                    # Calculate completion percentage and task counts
                    from implement.models import Action
                    all_tasks = Action.objects.filter(ppi_project=project)
                    total_tasks = all_tasks.count()
                    completed_tasks = all_tasks.filter(status='completed').count()
                    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                    all_tasks_completed = (completed_tasks == total_tasks) if total_tasks > 0 else False

                    # Get latest status from NumbersTracking
                    from implement.models import NumbersTracking
                    latest_tracking = NumbersTracking.objects.filter(
                        ppi_project=project
                    ).order_by('-week_number', '-id').first()

                    status = latest_tracking.status if latest_tracking else 'on_track'
                    status_display = dict(PPIProject.STATUS_CHOICES).get(status, 'Not Set')

                    project_data.append({
                        'id': f'ppi_{project.id}',  # Prefix to differentiate sources
                        'source': 'quarterly_plan',
                        'project_name': project.name,
                        'completion_criteria': project.completion_criteria or '',
                        'original_due_date': project.start_date.strftime('%b %d, %Y') if project.start_date else None,
                        'revised_due_date': project.end_date.strftime('%b %d, %Y') if project.end_date else None,
                        'completion_percentage': round(completion_percentage, 1),
                        'status': status,
                        'status_display': status_display,
                        'assigned_to': project.responsible_user.get_full_name() if project.responsible_user else None,
                        'total_tasks': total_tasks,
                        'completed_tasks': completed_tasks,
                        'all_tasks_completed': all_tasks_completed
                    })

            # SOURCE 2: Get ImprovementProjects from uploaded files
            quarter_str = f'Q{quarter}'
            improvement_projects = ImprovementProject.objects.filter(
                upload__financial_year=financial_year,
                upload__quarter=quarter_str,
                upload__team=team,
                tracking_type=tracking_type
            ).select_related('responsible_user', 'upload')

            # Process ImprovementProjects
            for project in improvement_projects:
                # Calculate completion percentage and task counts
                from implement.models import Action
                all_tasks = Action.objects.filter(improvement_project=project)
                total_tasks = all_tasks.count()
                completed_tasks = all_tasks.filter(status='completed').count()
                completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                all_tasks_completed = (completed_tasks == total_tasks) if total_tasks > 0 else False

                # ImprovementProjects use their own status field (no NumbersTracking)
                status = project.status
                # Use ImprovementProject STATUS_CHOICES for display
                status_display = dict(ImprovementProject.STATUS_CHOICES).get(status, 'Not Set')

                project_data.append({
                    'id': f'improve_{project.id}',  # Prefix to differentiate sources
                    'source': 'improve_upload',
                    'project_name': project.name,
                    'completion_criteria': project.completion_criteria or '',
                    'original_due_date': project.start_date.strftime('%b %d, %Y') if project.start_date else None,
                    'revised_due_date': project.end_date.strftime('%b %d, %Y') if project.end_date else None,
                    'completion_percentage': round(completion_percentage, 1),
                    'status': status,
                    'status_display': status_display,
                    'assigned_to': project.responsible_user.get_full_name() if project.responsible_user else None,
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'all_tasks_completed': all_tasks_completed
                })

            return JsonResponse({
                'success': True,
                'projects': project_data,
                'is_current_quarter': is_current_quarter
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class UnifiedIssuesAPIView(LoginRequiredMixin, View):
    """API endpoint to get issues based on unified context from any location in the application"""

    def get(self, request):
        try:
            # Extract context parameters
            location = request.GET.get('location')  # 'implement' or 'review'
            level = request.GET.get('level')  # 'screen' or 'item'
            screen = request.GET.get('screen')  # 'my_numbers', 'my_projects', 'my_todo'
            period = request.GET.get('period')  # 'weekly', 'monthly', 'quarterly', 'yearly', 'adhoc'
            period_number = request.GET.get('period_number')  # week/month/quarter number
            item_type = request.GET.get('item_type')  # 'gpi', 'ppi', 'action'
            item_id = request.GET.get('item_id')  # ID of the item
            team_id = request.GET.get('team_id')  # Team ID
            meeting_id = request.GET.get('meeting_id')  # Review meeting ID

            # Debug logging
            print(f"\n{'='*80}")
            print(f"DEBUG UNIFIED ISSUES API:")
            print(f"  location={location}")
            print(f"  level={level}")
            print(f"  screen={screen}")
            print(f"  period={period}")
            print(f"  period_number={period_number}")
            print(f"  meeting_id={meeting_id}")
            print(f"  item_type={item_type}")
            print(f"  item_id={item_id}")
            print(f"  team_id={team_id}")
            print(f"{'='*80}\n")

            # Start with base query - get issues for teams where user is manager or member
            user = request.user
            team_ids = set()

            # Get teams where user is a manager
            managed_teams = Team.objects.filter(manager=user, is_active=True)
            team_ids.update(managed_teams.values_list('id', flat=True))

            # Get teams where user is a member
            member_teams = TeamMember.objects.filter(member=user).values_list('team_id', flat=True)
            team_ids.update(member_teams)

            # Base query for issues
            issues_query = Issue.objects.filter(team_id__in=team_ids)

            # Apply filters based on context
            if team_id:
                issues_query = issues_query.filter(team_id=team_id)

            # Filter by parameter linking if item-level
            if level == 'item' and item_type and item_id:
                if item_type == 'gpi':
                    issues_query = issues_query.filter(gpi_parameter_id=item_id)
                elif item_type == 'ppi':
                    issues_query = issues_query.filter(ppi_project_id=item_id)
                elif item_type == 'improvement':
                    issues_query = issues_query.filter(improvement_project_id=item_id)
                elif item_type == 'action':
                    issues_query = issues_query.filter(action_id=item_id)

            # Filter by period if screen-level
            if level == 'screen' and period:
                if period == 'weekly' and period_number:
                    # For Review location, filter by review_meeting_id if provided
                    if location == 'review' and meeting_id:
                        issues_query = issues_query.filter(
                            review_meeting_id=meeting_id,
                            gpi_parameter__isnull=True,
                            ppi_project__isnull=True,
                            improvement_project__isnull=True,
                            action__isnull=True
                        )
                    else:
                        # For Implement location, filter by week_number and exclude review meeting issues
                        issues_query = issues_query.filter(
                            week_number=period_number,
                            review_meeting__isnull=True
                        )
                elif period == 'monthly' and period_number:
                    # For Review location, filter by review_meeting_id if provided
                    if location == 'review' and meeting_id:
                        issues_query = issues_query.filter(
                            review_meeting_id=meeting_id,
                            gpi_parameter__isnull=True,
                            ppi_project__isnull=True,
                            improvement_project__isnull=True,
                            action__isnull=True
                        )
                    else:
                        # For Implement location, filter by month_number and exclude review meeting issues
                        issues_query = issues_query.filter(
                            month_number=period_number,
                            review_meeting__isnull=True
                        )
                elif period == 'quarterly' and period_number:
                    # For quarterly, exclude review meeting issues
                    issues_query = issues_query.filter(
                        quarter_number=period_number,
                        review_meeting__isnull=True
                    )
                elif period == 'manual':
                    # Manual issues: not linked to any period or parameter or review meeting
                    issues_query = issues_query.filter(
                        week_number__isnull=True,
                        month_number__isnull=True,
                        quarter_number__isnull=True,
                        gpi_parameter__isnull=True,
                        ppi_project__isnull=True,
                        improvement_project__isnull=True,
                        action__isnull=True,
                        review_meeting__isnull=True
                    )

            # Order by created date (newest first)
            issues_query = issues_query.order_by('-created_at')

            # Debug: Print the query and results
            print(f"QUERY FILTER CONDITIONS:")
            print(f"  Final query count: {issues_query.count()}")
            if issues_query.exists():
                print(f"  Issue IDs: {list(issues_query.values_list('id', flat=True))}")
                print(f"  Issue review_meeting_ids: {list(issues_query.values_list('review_meeting_id', flat=True))}")
                print(f"  Issue week_numbers: {list(issues_query.values_list('week_number', flat=True))}")
            print(f"{'='*80}\n")

            # Build response data
            issues_data = []
            for issue in issues_query:
                issues_data.append({
                    'id': issue.id,
                    'title': issue.title,
                    'description': issue.description or '',
                    'priority': issue.priority or '',
                    'priority_display': issue.get_priority_display() if issue.priority else '',
                    'issue_type': issue.issue_type,
                    'issue_type_display': issue.get_issue_type_display(),
                    'status': issue.status,
                    'status_display': issue.get_status_display(),
                    'required_by': issue.required_by.isoformat() if issue.required_by else None,
                    'reported_by_name': issue.reported_by.get_full_name() if issue.reported_by else 'Unknown',
                    'team_name': issue.team.name if issue.team else 'N/A',
                    'created_at': issue.created_at.isoformat() if issue.created_at else None
                })

            return JsonResponse({
                'success': True,
                'issues': issues_data,
                'count': len(issues_data)
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
