from django.db import models
from django.conf import settings
from organizations.models import Team
from plans.models import FinancialYear


class ImprovementUpload(models.Model):
    STATUS_CHOICES = [
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('processing', 'Processing'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='improvement_uploads')
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='improvements/')
    upload_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    error_log = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Analysis results
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    error_records = models.IntegerField(default=0)

    class Meta:
        db_table = 'improvement_uploads'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.team.name} - {self.file_name} - {self.uploaded_at.date()}"


class ImprovementSuggestion(models.Model):
    PRIORITY_CHOICES = [
        ('high', 'High Impact'),
        ('medium', 'Medium Impact'),
        ('low', 'Low Impact'),
    ]

    STATUS_CHOICES = [
        ('identified', 'Identified'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('implemented', 'Implemented'),
        ('rejected', 'Rejected'),
    ]

    upload = models.ForeignKey(ImprovementUpload, on_delete=models.CASCADE, related_name='suggestions')
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)  # e.g., 'Process', 'Technology', 'Resource'
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='identified')

    # Impact estimation
    estimated_savings = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    estimated_effort = models.CharField(max_length=100, blank=True)  # e.g., '2 weeks', '1 month'

    # Assignment
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    target_completion_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'improvement_suggestions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.priority}"
