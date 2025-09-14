from django.db import models
from django.conf import settings
from organizations.models import Team
from plans.models import FPIParameter, GPIParameter, PPIProject


class NumbersTracking(models.Model):
    TRACKING_TYPES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    SOURCE_TYPES = [
        ('fpi', 'FPI'),
        ('gpi', 'GPI'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    source_type = models.CharField(max_length=3, choices=SOURCE_TYPES)
    fpi_parameter = models.ForeignKey(FPIParameter, on_delete=models.CASCADE, null=True, blank=True)
    gpi_parameter = models.ForeignKey(GPIParameter, on_delete=models.CASCADE, null=True, blank=True)
    tracking_type = models.CharField(max_length=10, choices=TRACKING_TYPES)
    
    # For tracking period
    year = models.IntegerField()
    week_number = models.IntegerField(null=True, blank=True)  # 1-52
    month_number = models.IntegerField(null=True, blank=True)  # 1-12
    
    # Data fields
    last_period_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    last_period_plan = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    last_period_actual = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    next_period_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    next_period_plan = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    comments = models.TextField(blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'numbers_tracking'
        
    def __str__(self):
        if self.source_type == 'fpi':
            return f"FPI: {self.fpi_parameter.sub_head}"
        else:
            return f"GPI: {self.gpi_parameter.name}"


class ProjectStatus(models.Model):
    STATUS_CHOICES = [
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('danger', 'Danger'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('dropped', 'Dropped'),
    ]
    
    project = models.ForeignKey(PPIProject, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    revised_due_date = models.DateField(null=True, blank=True)
    challenge = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_status'
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"{self.project.name} - {self.status}"


class Action(models.Model):
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('at_risk', 'At Risk'),
        ('danger', 'Danger'),
        ('done', 'Done'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('ppi', 'PPI Task'),
        ('review', 'Review Meeting'),
        ('issue', 'Issue Resolution'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    ppi_task = models.OneToOneField('plans.PPITask', on_delete=models.CASCADE, null=True, blank=True)
    parent_action = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_actions')
    
    action = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_actions')
    original_due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    revised_due_date = models.DateField(null=True, blank=True)
    challenge = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_actions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'actions'
        ordering = ['original_due_date', '-created_at']
        
    def __str__(self):
        return f"{self.action[:50]}... - {self.assigned_to.get_full_name()}"


class ActionHistory(models.Model):
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=20)
    revised_due_date = models.DateField(null=True, blank=True)
    challenge = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'action_history'
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"{self.action.action[:30]} - {self.status} - {self.updated_at}"


class Issue(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('resolved', 'Resolved'),
        ('on_hold', 'On Hold'),
        ('dropped', 'Dropped'),
        ('escalated', 'Escalated'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    required_by = models.DateField(null=True, blank=True)
    escalated_to_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='escalated_issues')
    
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reported_issues')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'issues'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.team.name}"
        
    @property
    def actions_completed_count(self):
        return self.related_actions.filter(status='completed').count()
        
    @property
    def total_actions_count(self):
        return self.related_actions.count()