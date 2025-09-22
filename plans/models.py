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
        
    def __str__(self):
        return f"{self.team.name} - {self.financial_year.year} - {self.quarter}"


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
    annual_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    ytd_till_last_quarter = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    quarter_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    quarter_goal = models.DecimalField(max_digits=15, decimal_places=2)
    month1_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    month2_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    month3_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Actual and Plan fields for data entry
    last_month_actual = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
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
        ('goal', 'Goal'),
        ('progress', 'Progress'),
    ]

    quarterly_plan = models.ForeignKey(QuarterlyPlan, on_delete=models.CASCADE, related_name='gpi_parameters')
    name = models.CharField(max_length=255)
    unit_of_measure = models.CharField(max_length=50, blank=True)
    tracking_type = models.CharField(max_length=10, choices=TRACKING_TYPES)
    indicator_type = models.CharField(max_length=10, choices=INDICATOR_TYPES)
    responsible_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    annual_goal = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    ytd_till_last_quarter = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    quarter_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    quarter_goal = models.DecimalField(max_digits=15, decimal_places=2)

    # Actual and Plan fields for data entry
    last_week_actual = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    current_week_plan = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    last_month_actual = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
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
    steps = models.TextField(blank=True)  # General steps description
    explanation = models.TextField(blank=True)

    class Meta:
        db_table = 'ppi_projects'
        unique_together = ['quarterly_plan', 'name']

    def __str__(self):
        return f"{self.name} - {self.quarterly_plan}"


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
    period_number = models.IntegerField()  # Week 1-12 or Month 1-3 depending on tracking_type
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
        ('goal', 'Goal'),
        ('progress', 'Progress'),
    ]

    annual_plan = models.ForeignKey(AnnualPlan, on_delete=models.CASCADE, related_name='gpi_parameters')
    name = models.CharField(max_length=255)
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
    responsible_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
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