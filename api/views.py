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
                issue = Issue.objects.create(
                    team=team,
                    title=title,
                    description=description,
                    priority=priority,
                    required_by=required_by_date,
                    reported_by=request.user
                )

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

            # Create the action
            with transaction.atomic():
                action = Action.objects.create(
                    team=team,
                    action=action_text,
                    priority=priority,
                    assigned_to=assigned_user,
                    original_due_date=due_date_parsed,
                    comments=comments,
                    created_by=request.user,
                    source='manual'
                )

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
