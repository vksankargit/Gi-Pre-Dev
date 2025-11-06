from django.db import models
from django.conf import settings
from organizations.models import Team
from plans.models import FinancialYear
import datetime


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
        ordering = ['-uploaded_at']

    @property
    def quarter_start_date(self):
        """
        Calculate the start date of the quarter based on financial year and quarter.
        Returns the Monday of the week that contains the actual quarter start date.
        This ensures weeks run Monday-Sunday.
        """
        fy_start = self.financial_year.start_date

        # Extract quarter number (handle both 'Q1' format and '1' format)
        if self.quarter.startswith('Q'):
            quarter_num = int(self.quarter[1]) - 1  # Q1 -> 0, Q2 -> 1, Q3 -> 2, Q4 -> 3
        else:
            quarter_num = int(self.quarter) - 1  # 1 -> 0, 2 -> 1, 3 -> 2, 4 -> 3

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


class ImprovementUploadHistory(models.Model):
    """Tracks all upload attempts for improvement projects, including re-uploads"""
    improvement_upload = models.ForeignKey(ImprovementUpload, on_delete=models.CASCADE, related_name='upload_history')
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='improve_uploads/')
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
        db_table = 'improve_upload_history'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.improvement_upload.team.name} - {self.improvement_upload.financial_year.year} - {self.improvement_upload.quarter} - {self.uploaded_at}"


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


class ImprovementProjectStatus(models.Model):
    """Status history for improvement projects - identical to ProjectStatus"""
    STATUS_CHOICES = [
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('danger', 'Danger'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]

    project = models.ForeignKey(ImprovementProject, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    revised_due_date = models.DateField(null=True, blank=True)
    challenge = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'improve_project_status'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.project.name} - {self.get_status_display()} ({self.updated_at.strftime('%Y-%m-%d')})"