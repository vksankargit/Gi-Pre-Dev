"""
URL configuration for pre_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from accounts.utils import get_effective_user
from django.utils import timezone
from django.db.models import Q, Count, Sum, Case, When, IntegerField, DecimalField, F, Value
from django.db.models.functions import Coalesce
import datetime

@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_effective_user(self.request)
        context['user'] = user

        # Add dashboard data for general users
        if user.role == 'general':
            context.update(self.get_general_user_dashboard_data(user))

        return context

    def get_general_user_dashboard_data(self, user):
        """Get dashboard data for general users"""
        from organizations.models import Team
        from plans.models import QuarterlyPlan, GPIParameter, PPIProject
        from implement.models import Action, ProjectStatus, NumbersTracking
        from improve.models import ImprovementProject, ImprovementProjectStatus
        from reviews.models import ReviewMeeting

        data = {}
        current_date = timezone.now().date()
        current_datetime = timezone.now()

        # Get teams managed by user
        managed_teams = Team.objects.filter(manager=user, is_active=True)

        # Get current week number and financial year info
        current_week = current_date.isocalendar()[1]
        if current_date.month >= 4:
            fy_start_year = current_date.year
        else:
            fy_start_year = current_date.year - 1

        # Team Performance Summary (for managers)
        if managed_teams.exists():
            team_performance = []

            for team in managed_teams:
                # Get current quarter plan
                current_quarter = self._get_current_quarter(current_date)
                quarterly_plan = QuarterlyPlan.objects.filter(
                    team=team,
                    financial_year__start_date__year=fy_start_year,
                    quarter=current_quarter
                ).first()

                if quarterly_plan:
                    # FPI Performance (budget vs actual tracking)
                    fpi_params = FPIParameter.objects.filter(quarterly_plan=quarterly_plan)
                    fpi_total = fpi_params.count()
                    fpi_on_track = fpi_params.filter(
                        last_month_actual__lte=F('last_month_goal') * 1.1,  # Within 10%
                        last_month_actual__gte=F('last_month_goal') * 0.9
                    ).count() if fpi_total > 0 else 0

                    # GPI Performance (weekly/monthly tracking)
                    gpi_params = GPIParameter.objects.filter(quarterly_plan=quarterly_plan)
                    gpi_total = gpi_params.count()
                    # Simplified: count parameters that have recent tracking data
                    gpi_tracked = NumbersTracking.objects.filter(
                        team=team,
                        source_type='gpi',
                        gpi_parameter__in=gpi_params,
                        updated_at__gte=current_datetime - datetime.timedelta(days=14)
                    ).values('gpi_parameter').distinct().count()

                    # PPI Performance (project completion)
                    ppi_projects = PPIProject.objects.filter(quarterly_plan=quarterly_plan)
                    ppi_total = ppi_projects.count()
                    ppi_completed = ProjectStatus.objects.filter(
                        project__in=ppi_projects,
                        status__in=['completed']
                    ).values('project').distinct().count()
                    ppi_on_track = ProjectStatus.objects.filter(
                        project__in=ppi_projects,
                        status='on_track'
                    ).values('project').distinct().count()
                    ppi_at_risk = ProjectStatus.objects.filter(
                        project__in=ppi_projects,
                        status__in=['at_risk', 'danger']
                    ).values('project').distinct().count()

                    team_performance.append({
                        'team_name': team.name,
                        'quarter': f'{current_quarter}',
                        'fpi': {
                            'total': fpi_total,
                            'on_track': fpi_on_track,
                            'percentage': round((fpi_on_track / fpi_total * 100) if fpi_total > 0 else 0, 1)
                        },
                        'gpi': {
                            'total': gpi_total,
                            'tracked': gpi_tracked,
                            'percentage': round((gpi_tracked / gpi_total * 100) if gpi_total > 0 else 0, 1)
                        },
                        'ppi': {
                            'total': ppi_total,
                            'completed': ppi_completed,
                            'on_track': ppi_on_track,
                            'at_risk': ppi_at_risk,
                            'percentage': round((ppi_completed / ppi_total * 100) if ppi_total > 0 else 0, 1)
                        }
                    })

            data['team_performance'] = team_performance

        # Upcoming Review Meetings (for all users)
        upcoming_reviews = ReviewMeeting.objects.filter(
            Q(team__manager=user) | Q(team__members__member=user),
            meeting_date__gte=current_date,
            meeting_date__lte=current_date + datetime.timedelta(days=30)
        ).select_related('team', 'financial_year').distinct().order_by('meeting_date')[:5]

        data['upcoming_reviews'] = upcoming_reviews

        # Projects Assigned to User
        # PPI Projects
        ppi_assigned = PPIProject.objects.filter(
            responsible_user=user
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year')

        # Get latest status for each project
        ppi_projects_data = []
        for project in ppi_assigned:
            latest_status = ProjectStatus.objects.filter(project=project).first()
            ppi_projects_data.append({
                'project': project,
                'status': latest_status,
                'type': 'PPI'
            })

        # Improvement Projects
        improvement_assigned = ImprovementProject.objects.filter(
            responsible_user=user
        ).select_related('upload__team', 'upload__financial_year')

        for project in improvement_assigned:
            latest_status = ImprovementProjectStatus.objects.filter(project=project).first()
            ppi_projects_data.append({
                'project': project,
                'status': latest_status,
                'type': 'Improvement'
            })

        data['assigned_projects'] = ppi_projects_data

        # My To Do - Actions (Overdue and Current Week)
        # Get overdue actions (checking both original and revised due dates)
        overdue_actions = Action.objects.filter(
            assigned_to=user,
            status__in=['not_started', 'in_progress', 'at_risk']
        ).select_related('ppi_task', 'improvement_task', 'ppi_project', 'improvement_project')

        # Filter overdue in Python since we need to check revised_due_date first
        overdue_actions = [
            action for action in overdue_actions
            if (action.revised_due_date or action.original_due_date) < current_date
        ]
        overdue_actions.sort(key=lambda x: x.revised_due_date or x.original_due_date)

        # Get current week actions
        week_start = current_date - datetime.timedelta(days=current_date.weekday())
        week_end = week_start + datetime.timedelta(days=6)

        current_week_actions = Action.objects.filter(
            assigned_to=user,
            status__in=['not_started', 'in_progress', 'at_risk']
        ).select_related('ppi_task', 'improvement_task', 'ppi_project', 'improvement_project')

        # Filter current week in Python
        current_week_actions = [
            action for action in current_week_actions
            if week_start <= (action.revised_due_date or action.original_due_date) <= week_end
        ]
        current_week_actions.sort(key=lambda x: x.revised_due_date or x.original_due_date)

        data['overdue_actions'] = overdue_actions
        data['current_week_actions'] = current_week_actions
        data['current_week_number'] = current_week

        return data

    def _get_current_quarter(self, current_date):
        """Determine current quarter based on date"""
        if current_date.month >= 4:
            fy_start_year = current_date.year
        else:
            fy_start_year = current_date.year - 1

        fy_start = datetime.date(fy_start_year, 4, 1)

        if fy_start <= current_date <= datetime.date(fy_start_year, 6, 30):
            return 'Q1'
        elif datetime.date(fy_start_year, 7, 1) <= current_date <= datetime.date(fy_start_year, 9, 30):
            return 'Q2'
        elif datetime.date(fy_start_year, 10, 1) <= current_date <= datetime.date(fy_start_year, 12, 31):
            return 'Q3'
        else:
            return 'Q4'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', DashboardView.as_view(), name='dashboard'),
    path('accounts/', include('accounts.urls')),
    path('organizations/', include('organizations.urls')),
    path('plans/', include('plans.urls')),
    path('implement/', include('implement.urls')),
    path('review/', include('reviews.urls')),
    path('improve/', include('improve.urls')),
    path('api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)