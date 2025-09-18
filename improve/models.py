from django.db import models
from django.conf import settings
from organizations.models import Team
from plans.models import FinancialYear


class ImprovementUpload(models.Model):
    """File upload record for improvement projects - similar to QuarterlyPlan"""
    STATUS_CHOICES = [
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('processing', 'Processing'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='improve_uploads')
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE, related_name='improve_uploads')
    quarter = models.CharField(max_length=2, choices=[('Q1', 'Q1'), ('Q2', 'Q2'), ('Q3', 'Q3'), ('Q4', 'Q4')])
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='improve_uploads/')
    upload_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    error_log = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='improve_uploads')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Processing statistics
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    error_records = models.IntegerField(default=0)

    class Meta:
        db_table = 'improve_uploads'
        unique_together = ['team', 'financial_year', 'quarter']
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.team.name} - {self.financial_year.year} - {self.quarter}"


class ImprovementProject(models.Model):
    """Individual improvement projects from PPI-like structure"""
    STATUS_CHOICES = [
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('danger', 'Danger'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]

    upload = models.ForeignKey(ImprovementUpload, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    completion_criteria = models.TextField()
    responsible_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    steps = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='on_track')

    class Meta:
        db_table = 'improve_projects'
        unique_together = ['upload', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.upload}"


class ImprovementTask(models.Model):
    """Weekly tasks for improvement projects - identical to PPITask"""
    project = models.ForeignKey(ImprovementProject, on_delete=models.CASCADE, related_name='tasks')
    task_description = models.TextField()
    week_number = models.IntegerField()  # Week 1-13 within quarter
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'improve_tasks'

    def __str__(self):
        return f"Week {self.week_number}: {self.task_description[:50]}"