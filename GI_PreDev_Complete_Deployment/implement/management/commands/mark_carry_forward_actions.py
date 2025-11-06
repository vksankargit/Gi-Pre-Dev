from django.core.management.base import BaseCommand
from django.utils import timezone
from implement.models import Action
from plans.models import QuarterlyPlan, FinancialYear
from improve.models import ImprovementUpload


class Command(BaseCommand):
    help = 'Mark past quarter PPI and Improvement actions as carry forward'

    def handle(self, *args, **options):
        now = timezone.now()
        current_month = now.month

        # Determine current quarter based on month (financial year starts April 1)
        if 4 <= current_month <= 6:
            current_quarter_num = 1
            fy_start_year = now.year
        elif 7 <= current_month <= 9:
            current_quarter_num = 2
            fy_start_year = now.year
        elif 10 <= current_month <= 12:
            current_quarter_num = 3
            fy_start_year = now.year
        else:  # Jan-Mar
            current_quarter_num = 4
            fy_start_year = now.year - 1

        # Format the financial year string
        fy_end_year = fy_start_year + 1
        current_fy_string = f"FY {fy_start_year % 100:02d}-{fy_end_year % 100:02d}"
        current_financial_year = FinancialYear.objects.filter(year=current_fy_string).first()

        if not current_financial_year:
            self.stdout.write(self.style.ERROR(f'Financial year {current_fy_string} not found'))
            return

        self.stdout.write(f'Current Quarter: Q{current_quarter_num} of {current_fy_string}')

        # Get all current quarter quarterly plans
        current_quarter_plans = QuarterlyPlan.objects.filter(
            quarter=current_quarter_num,
            financial_year=current_financial_year
        )

        self.stdout.write(f'Found {current_quarter_plans.count()} current quarter plans')

        # Mark PPI actions from past quarters as carry forward
        # Include rejected status as well
        ppi_actions_updated = 0
        ppi_actions = Action.objects.filter(
            source='ppi',
            ppi_task__isnull=False,
            status__in=['not_started', 'in_progress', 'at_risk', 'danger', 'overdue', 'rejected']
        ).select_related('ppi_task__project__quarterly_plan')

        for action in ppi_actions:
            quarterly_plan = action.ppi_task.project.quarterly_plan

            # Check if this action belongs to a past quarter
            # Compare as strings since quarter is stored as string in database
            if (quarterly_plan.financial_year != current_financial_year or
                str(quarterly_plan.quarter) != str(current_quarter_num)):
                action.status = 'carry_forward'
                action.save()
                ppi_actions_updated += 1
                self.stdout.write(f'  Marked PPI action {action.id} as carry forward (Q{quarterly_plan.quarter} {quarterly_plan.financial_year.year})')

        # Mark Improvement actions from past quarters as carry forward
        # Include rejected status as well
        improvement_actions_updated = 0
        improvement_actions = Action.objects.filter(
            source='improvement',
            improvement_task__isnull=False,
            status__in=['not_started', 'in_progress', 'at_risk', 'danger', 'overdue', 'rejected']
        ).select_related('improvement_task__project__upload')

        for action in improvement_actions:
            upload = action.improvement_task.project.upload

            # Check if this action belongs to current quarter
            # The upload.quarter contains both FY and quarter like "FY 25-26 – Q2"
            is_current_quarter = (
                f'Q{current_quarter_num}' in upload.quarter and
                current_fy_string in upload.quarter
            )

            if not is_current_quarter:
                action.status = 'carry_forward'
                action.save()
                improvement_actions_updated += 1
                self.stdout.write(f'  Marked Improvement action {action.id} as carry forward ({upload.quarter})')

        self.stdout.write(self.style.SUCCESS(
            f'Successfully marked {ppi_actions_updated} PPI actions and {improvement_actions_updated} Improvement actions as carry forward'
        ))
