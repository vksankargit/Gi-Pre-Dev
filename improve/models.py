from django.db import models
from django.conf import settings
from organizations.models import Team
from plans.models import FinancialYear


class ImprovementProject(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='improvement_projects')
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    quarter = models.CharField(max_length=2, choices=[('Q1', 'Q1'), ('Q2', 'Q2'), ('Q3', 'Q3'), ('Q4', 'Q4')])
    file_name = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='improvement_projects/')
    upload_status = models.CharField(max_length=20, choices=[('successful', 'Successful'), ('failed', 'Failed')])
    error_log = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'improvement_projects'
        unique_together = ['team', 'financial_year', 'quarter']
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return f"{self.team.name} - {self.financial_year.year} - {self.quarter}"