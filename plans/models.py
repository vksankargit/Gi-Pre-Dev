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
    quarter_goal = models.DecimalField(max_digits=15, decimal_places=2)
    month1_budget = models.DecimalField(max_digits=15, decimal_places=2)
    month2_budget = models.DecimalField(max_digits=15, decimal_places=2)
    month3_budget = models.DecimalField(max_digits=15, decimal_places=2)
    
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
    unit_of_measure = models.CharField(max_length=50)
    tracking_type = models.CharField(max_length=10, choices=TRACKING_TYPES)
    indicator_type = models.CharField(max_length=10, choices=INDICATOR_TYPES)
    responsible_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quarter_goal = models.DecimalField(max_digits=15, decimal_places=2)
    
    class Meta:
        db_table = 'gpi_parameters'
        unique_together = ['quarterly_plan', 'name']
        
    def __str__(self):
        return f"{self.name} - {self.quarterly_plan}"


class PPIProject(models.Model):
    quarterly_plan = models.ForeignKey(QuarterlyPlan, on_delete=models.CASCADE, related_name='ppi_projects')
    name = models.CharField(max_length=255)
    completion_criteria = models.TextField()
    responsible_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_date = models.DateField()
    due_date = models.DateField()
    
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