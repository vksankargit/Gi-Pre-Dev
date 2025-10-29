from django.core.management.base import BaseCommand
from django.utils import timezone
from plans.models import GPIParameter, FPIParameter
from datetime import date


class Command(BaseCommand):
    help = 'Weekly rollover: Copy current_week_plan to last_week_goal and current_month_plan to last_month_goal'

    def get_current_week_in_quarter(self, today):
        """Calculate current week number within the quarter (1-13)"""
        month = today.month

        # Determine quarter and month within quarter
        if 4 <= month <= 6:  # Q1: Apr-Jun
            quarter_start_month = 4
            current_quarter = 1
        elif 7 <= month <= 9:  # Q2: Jul-Sep
            quarter_start_month = 7
            current_quarter = 2
        elif 10 <= month <= 12:  # Q3: Oct-Dec
            quarter_start_month = 10
            current_quarter = 3
        else:  # Q4: Jan-Mar
            quarter_start_month = 1
            current_quarter = 4

        # Calculate week number within quarter
        quarter_start = date(today.year if month >= 4 else today.year - 1, quarter_start_month, 1)
        days_diff = (today - quarter_start).days
        week_in_quarter = (days_diff // 7) + 1

        return min(week_in_quarter, 13), current_quarter

    def get_current_month_in_quarter(self, today):
        """Calculate current month number within the quarter (1-3)"""
        month = today.month

        if 4 <= month <= 6:  # Q1: Apr-Jun
            return month - 3
        elif 7 <= month <= 9:  # Q2: Jul-Sep
            return month - 6
        elif 10 <= month <= 12:  # Q3: Oct-Dec
            return month - 9
        else:  # Q4: Jan-Mar
            return month

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting weekly rollover...'))

        today = timezone.now().date()
        current_week_in_quarter, current_quarter = self.get_current_week_in_quarter(today)
        current_month_in_quarter = self.get_current_month_in_quarter(today)

        self.stdout.write(f'Current week in quarter: {current_week_in_quarter}')
        self.stdout.write(f'Current month in quarter: {current_month_in_quarter}')

        # Update all GPI parameters
        gpi_count = 0
        for gpi in GPIParameter.objects.all():
            # Copy current_week_plan to last_week_goal for weekly tracking
            # Skip if it's week 1 of a new quarter (quarter boundary handled by view logic)
            if gpi.tracking_type == 'weekly' and gpi.current_week_plan is not None:
                if current_week_in_quarter > 1:
                    # Within same quarter, copy goal
                    gpi.last_week_goal = gpi.current_week_plan
                else:
                    # Week 1 of new quarter - last_week_goal will be fetched from previous quarter by view
                    # Don't update last_week_goal here
                    pass

                # Always reset current week fields for the new week
                gpi.current_week_plan = None
                gpi.last_week_actual = None
                gpi.save()
                gpi_count += 1

            # Copy current_month_plan to last_month_goal for monthly tracking
            # Only do this at the start of a new month
            elif gpi.tracking_type == 'monthly' and gpi.current_month_plan is not None:
                if today.day <= 7:  # First week of month
                    if current_month_in_quarter > 1:
                        # Within same quarter, copy goal
                        gpi.last_month_goal = gpi.current_month_plan
                    else:
                        # Month 1 of new quarter - last_month_goal will be fetched from previous quarter by view
                        pass

                    # Always reset current month fields for the new month
                    gpi.current_month_plan = None
                    gpi.last_month_actual = None
                    gpi.save()
                    gpi_count += 1

        # Update all FPI parameters (monthly only)
        fpi_count = 0
        if today.day <= 7:  # First week of month
            for fpi in FPIParameter.objects.all():
                if fpi.current_month_plan is not None:
                    if current_month_in_quarter > 1:
                        # Within same quarter, copy goal
                        fpi.last_month_goal = fpi.current_month_plan
                    else:
                        # Month 1 of new quarter - last_month_goal will be fetched from previous quarter by view
                        pass

                    # Always reset current month fields for the new month
                    fpi.current_month_plan = None
                    fpi.last_month_actual = None
                    fpi.save()
                    fpi_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Weekly rollover completed: {gpi_count} GPI parameters and {fpi_count} FPI parameters updated'
        ))
