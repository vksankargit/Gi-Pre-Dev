from django.db import models
from django.conf import settings
from organizations.models import Team
import datetime


class FinancialYear(models.Model):
    year = models.CharField(max_length=10, unique=True)  # e.g., "FY 25-26"
    start_date = models.DateField()
    end_date = models.DateField()
    
    class Meta:
        db_table = 'financial_years'
        ordering = ['-start_date']
        
    def __str__(self):
        return self.year


class AnnualPlan(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='annual_plans')
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='annual_plans/')
    upload_status = models.CharField(max_length=20, choices=[('successful', 'Successful'), ('failed', 'Failed')])
    error_log = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'annual_plans'
        unique_together = ['team', 'financial_year']
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.team.name} - {self.financial_year.year}"


class AnnualPlanUploadHistory(models.Model):
    """Tracks all upload attempts for annual plans, including re-uploads"""
    annual_plan = models.ForeignKey(AnnualPlan, on_delete=models.CASCADE, related_name='upload_history')
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='annual_plans/')
    upload_status = models.CharField(max_length=20, choices=[
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('processing', 'Processing')
    ])
    error_log = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    error_records = models.IntegerField(default=0)

    class Meta:
        db_table = 'annual_plan_upload_history'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.annual_plan.team.name} - {self.annual_plan.financial_year.year} - {self.uploaded_at}"


class QuarterlyPlan(models.Model):
    QUARTERS = [
        ('Q1', 'Q1'),
        ('Q2', 'Q2'),
        ('Q3', 'Q3'),
        ('Q4', 'Q4'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='quarterly_plans')
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    quarter = models.CharField(max_length=2, choices=QUARTERS)
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='quarterly_plans/')
    upload_status = models.CharField(max_length=20, choices=[('successful', 'Successful'), ('failed', 'Failed')])
    error_log = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'quarterly_plans'
        unique_together = ['team', 'financial_year', 'quarter']
        ordering = ['-uploaded_at']
        
    @property
    def quarter_start_date(self):
        """
        Calculate the start date of the quarter based on financial year and quarter.
        Returns the Monday of the week that contains the actual quarter start date.
        This ensures weeks run Monday-Sunday.
        """
        fy_start = self.financial_year.start_date

        # Extract quarter number (handle both 'Q1' format and integer format)
        if isinstance(self.quarter, int):
            quarter_num = self.quarter - 1  # 1 -> 0, 2 -> 1, 3 -> 2, 4 -> 3
        elif str(self.quarter).startswith('Q'):
            quarter_num = int(str(self.quarter)[1]) - 1  # Q1 -> 0, Q2 -> 1, Q3 -> 2, Q4 -> 3
        else:
            quarter_num = int(self.quarter) - 1  # '1' -> 0, '2' -> 1, '3' -> 2, '4' -> 3

        # Each quarter is 3 months
        months_offset = quarter_num * 3

        # Calculate the actual quarter start date
        month = fy_start.month + months_offset
        year = fy_start.year

        # Handle year rollover
        while month > 12:
            month -= 12
            year += 1

        actual_quarter_start = datetime.date(year, month, fy_start.day)

        # Find the Monday of the week containing this date
        # weekday() returns 0 for Monday, 6 for Sunday
        days_since_monday = actual_quarter_start.weekday()
        week_start_monday = actual_quarter_start - datetime.timedelta(days=days_since_monday)

        return week_start_monday

    def __str__(self):
        return f"{self.team.name} - {self.financial_year.year} - {self.quarter}"


class QuarterlyPlanUploadHistory(models.Model):
    """Tracks all upload attempts for quarterly plans, including re-uploads"""
    quarterly_plan = models.ForeignKey(QuarterlyPlan, on_delete=models.CASCADE, related_name='upload_history')
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='quarterly_plans/')
    upload_status = models.CharField(max_length=20, choices=[
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('processing', 'Processing')
    ])
    error_log = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    error_records = models.IntegerField(default=0)

    class Meta:
        db_table = 'quarterly_plan_upload_history'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.quarterly_plan.team.name} - {self.quarterly_plan.financial_year.year} - {self.quarterly_plan.quarter} - {self.uploaded_at}"


class FPIParameter(models.Model):
    MAIN_HEADS = [
        ('revenue', 'Revenue'),
        ('variable_cost', 'Variable Cost'),
        ('operating_expenses', 'Operating Expenses'),
        ('other_expenses', 'Other Expenses'),
    ]

    quarterly_plan = models.ForeignKey(QuarterlyPlan, on_delete=models.CASCADE, related_name='fpi_parameters')
    main_head = models.CharField(max_length=20, choices=MAIN_HEADS)
    sub_head = models.CharField(max_length=255)
    responsible_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    assigned_team = models.ForeignKey('organizations.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_fpi_parameters', help_text="Team selected during reassignment")
    annual_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q1_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q2_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q3_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q4_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    ytd_till_last_quarter = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    quarter_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    quarter_goal = models.DecimalField(max_digits=15, decimal_places=2)
    month1_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    month2_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    month3_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Actual and Plan fields for data entry
    last_month_actual = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    last_month_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Previous month's current_month_plan value")
    current_month_plan = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    explanation = models.TextField(blank=True)

    class Meta:
        db_table = 'fpi_parameters'
        unique_together = ['quarterly_plan', 'sub_head']

    def __str__(self):
        return f"{self.sub_head} - {self.quarterly_plan}"


class GPIParameter(models.Model):
    TRACKING_TYPES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    INDICATOR_TYPES = [
        ('outcome', 'Outcome'),
        ('activity', 'Activity'),
    ]

    CUMULATION_TYPES = [
        ('sum', 'Sum'),
        ('average', 'Average'),
        ('na', 'NA'),
    ]

    quarterly_plan = models.ForeignKey(QuarterlyPlan, on_delete=models.CASCADE, related_name='gpi_parameters')
    name = models.CharField(max_length=255)
    cumulation_type = models.CharField(max_length=10, choices=CUMULATION_TYPES, default='na')
    unit_of_measure = models.CharField(max_length=50, blank=True)
    tracking_type = models.CharField(max_length=10, choices=TRACKING_TYPES)
    indicator_type = models.CharField(max_length=10, choices=INDICATOR_TYPES)
    responsible_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    assigned_team = models.ForeignKey('organizations.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_gpi_parameters', help_text="Team selected during reassignment")
    annual_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q1_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q2_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q3_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q4_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    ytd_till_last_quarter = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    quarter_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    quarter_goal = models.DecimalField(max_digits=15, decimal_places=2)

    # Actual and Plan fields for data entry
    last_week_actual = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    last_week_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Previous week's current_week_plan value")
    current_week_plan = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    last_month_actual = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    last_month_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Previous month's current_month_plan value")
    current_month_plan = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    explanation = models.TextField(blank=True)

    class Meta:
        db_table = 'gpi_parameters'
        unique_together = ['quarterly_plan', 'name']

    def __str__(self):
        return f"{self.name} - {self.quarterly_plan}"


class PPIProject(models.Model):
    STATUS_CHOICES = [
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('danger', 'Danger'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]

    quarterly_plan = models.ForeignKey(QuarterlyPlan, on_delete=models.CASCADE, related_name='ppi_projects')
    name = models.CharField(max_length=255)
    completion_criteria = models.TextField()
    responsible_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    annual_goal = models.CharField(max_length=255, blank=True)
    q1_budget = models.CharField(max_length=255, blank=True)
    q2_budget = models.CharField(max_length=255, blank=True)
    q3_budget = models.CharField(max_length=255, blank=True)
    q4_budget = models.CharField(max_length=255, blank=True)
    steps = models.TextField(blank=True)  # General steps description
    explanation = models.TextField(blank=True)

    class Meta:
        db_table = 'ppi_projects'
        unique_together = ['quarterly_plan', 'name']

    def __str__(self):
        return f"{self.name} - {self.quarterly_plan}"

    @property
    def completion_percentage(self):
        """
        Calculate completion percentage based on completed weeks vs total planned weeks.
        Formula: (# of weeks with completed activities / # of weeks with planned activities) * 100
        Returns integer percentage (0-100).
        """
        # Get all tasks for this project
        all_tasks = self.tasks.all()

        if not all_tasks.exists():
            return 0

        # Get unique week numbers that have tasks
        weeks_with_tasks = all_tasks.values_list('week_number', flat=True).distinct()
        total_weeks = len(weeks_with_tasks)

        if total_weeks == 0:
            return 0

        # Count weeks where all tasks are completed
        completed_weeks = 0
        for week_num in weeks_with_tasks:
            week_tasks = all_tasks.filter(week_number=week_num)
            if week_tasks.filter(is_completed=True).count() == week_tasks.count():
                completed_weeks += 1

        # Calculate percentage and round to integer
        percentage = (completed_weeks / total_weeks) * 100
        return round(percentage)


class PPITask(models.Model):
    project = models.ForeignKey(PPIProject, on_delete=models.CASCADE, related_name='tasks')
    task_description = models.TextField()
    week_number = models.IntegerField()  # Week 1-13 within quarter
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ppi_tasks'
        
    def __str__(self):
        return f"Week {self.week_number}: {self.task_description[:50]}"



class GPIMilestone(models.Model):
    """Stores weekly or monthly milestone values for GPI parameters"""
    gpi_parameter = models.ForeignKey(GPIParameter, on_delete=models.CASCADE, related_name='milestones')
    period_number = models.IntegerField()  # Week 1-13 or Month 1-3 depending on tracking_type
    budget_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        db_table = 'gpi_milestones'
        unique_together = ['gpi_parameter', 'period_number']

    def __str__(self):
        period_type = "Week" if self.gpi_parameter.tracking_type == 'weekly' else "Month"
        return f"{self.gpi_parameter.name} - {period_type} {self.period_number}"


class FPIMilestone(models.Model):
    """Stores monthly milestone values for FPI parameters"""
    fpi_parameter = models.ForeignKey(FPIParameter, on_delete=models.CASCADE, related_name='milestones')
    month_number = models.IntegerField()  # Month 1-3 within quarter
    budget_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        db_table = 'fpi_milestones'
        unique_together = ['fpi_parameter', 'month_number']

    def __str__(self):
        return f"{self.fpi_parameter.sub_head} - Month {self.month_number}"


# Historical weekly/monthly data tracking models
class GPIWeeklyRecord(models.Model):
    """Stores historical weekly data for GPI parameters"""
    gpi_parameter = models.ForeignKey(GPIParameter, on_delete=models.CASCADE, related_name='weekly_records')
    week_number = models.IntegerField()  # Week 1-13 within quarter
    week_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Goal entered for this week")
    week_actual = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Actual achieved for this week")
    explanation = models.TextField(blank=True)
    is_locked = models.BooleanField(default=False, help_text="Locked after weekly review is completed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gpi_weekly_records'
        unique_together = ['gpi_parameter', 'week_number']
        ordering = ['week_number']

    def __str__(self):
        return f"{self.gpi_parameter.name} - Week {self.week_number}"


class FPIMonthlyRecord(models.Model):
    """Stores historical monthly data for FPI parameters"""
    fpi_parameter = models.ForeignKey(FPIParameter, on_delete=models.CASCADE, related_name='monthly_records')
    month_number = models.IntegerField()  # Month 1-3 within quarter
    month_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Goal entered for this month")
    month_actual = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Actual achieved for this month")
    explanation = models.TextField(blank=True)
    is_locked = models.BooleanField(default=False, help_text="Locked after monthly review is completed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fpi_monthly_records'
        unique_together = ['fpi_parameter', 'month_number']
        ordering = ['month_number']

    def __str__(self):
        return f"{self.fpi_parameter.sub_head} - Month {self.month_number}"


class GPIMonthlyRecord(models.Model):
    """Stores historical monthly data for monthly-tracked GPI parameters"""
    gpi_parameter = models.ForeignKey(GPIParameter, on_delete=models.CASCADE, related_name='monthly_records')
    month_number = models.IntegerField()  # Month 1-3 within quarter
    month_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Goal entered for this month")
    month_actual = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Actual achieved for this month")
    explanation = models.TextField(blank=True)
    is_locked = models.BooleanField(default=False, help_text="Locked after monthly review is completed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'gpi_monthly_records'
        unique_together = ['gpi_parameter', 'month_number']
        ordering = ['month_number']

    def __str__(self):
        return f"{self.gpi_parameter.name} - Month {self.month_number}"


# Annual Plan models
class AnnualFPIParameter(models.Model):
    """FPI parameters from Annual Plan"""
    MAIN_HEADS = [
        ('revenue', 'Revenue'),
        ('variable_cost', 'Variable Cost'),
        ('operating_expenses', 'Operating Expenses'),
        ('other_expenses', 'Other Expenses'),
    ]

    annual_plan = models.ForeignKey(AnnualPlan, on_delete=models.CASCADE, related_name='fpi_parameters')
    main_head = models.CharField(max_length=20, choices=MAIN_HEADS)
    sub_head = models.CharField(max_length=255)
    responsible_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    annual_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q1_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q2_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q3_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q4_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    explanation = models.TextField(blank=True)

    class Meta:
        db_table = 'annual_fpi_parameters'
        unique_together = ['annual_plan', 'sub_head']

    def __str__(self):
        return f"{self.sub_head} - {self.annual_plan}"


class AnnualGPIParameter(models.Model):
    """GPI parameters from Annual Plan"""
    TRACKING_TYPES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    INDICATOR_TYPES = [
        ('outcome', 'Outcome'),
        ('activity', 'Activity'),
    ]

    CUMULATION_TYPES = [
        ('sum', 'Sum'),
        ('average', 'Average'),
        ('na', 'NA'),
    ]

    annual_plan = models.ForeignKey(AnnualPlan, on_delete=models.CASCADE, related_name='gpi_parameters')
    name = models.CharField(max_length=255)
    cumulation_type = models.CharField(max_length=10, choices=CUMULATION_TYPES, default='na')
    indicator_type = models.CharField(max_length=10, choices=INDICATOR_TYPES)
    tracking_type = models.CharField(max_length=10, choices=TRACKING_TYPES)
    responsible_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    annual_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q1_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q2_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q3_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    q4_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'annual_gpi_parameters'
        unique_together = ['annual_plan', 'name']

    def __str__(self):
        return f"{self.name} - {self.annual_plan}"


class AnnualPPIProject(models.Model):
    """PPI projects from Annual Plan"""
    annual_plan = models.ForeignKey(AnnualPlan, on_delete=models.CASCADE, related_name='ppi_projects')
    name = models.CharField(max_length=255)
    completion_criteria = models.TextField(blank=True)
    responsible_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    annual_goal = models.TextField(blank=True)
    q1_goal = models.TextField(blank=True)
    q2_goal = models.TextField(blank=True)
    q3_goal = models.TextField(blank=True)
    q4_goal = models.TextField(blank=True)

    class Meta:
        db_table = 'annual_ppi_projects'
        unique_together = ['annual_plan', 'name']

    def __str__(self):
        return f"{self.name} - {self.annual_plan}"