from django.db import models
from django.conf import settings
from organizations.models import Team
from plans.models import FinancialYear
from django.utils import timezone


class ReviewMeeting(models.Model):
    REVIEW_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    # Existing database columns - match exactly what's in the DB
    meeting_type = models.CharField(max_length=20, choices=REVIEW_TYPES, null=True, blank=True)
    meeting_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    week_number = models.IntegerField(null=True, blank=True)
    month_number = models.IntegerField(null=True, blank=True)
    quarter_number = models.IntegerField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    key_decisions = models.TextField(null=True, blank=True)
    next_steps = models.TextField(null=True, blank=True)
    agenda = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    finalized_at = models.DateTimeField(null=True, blank=True)
    conducted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conducted_reviews', null=True, blank=True)
    finalized_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='finalized_reviews', null=True, blank=True)
    financial_year = models.ForeignKey('plans.FinancialYear', on_delete=models.CASCADE, null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='review_meetings')

    # New columns that were added in migrations
    review_type = models.CharField(max_length=10, choices=REVIEW_TYPES, null=True, blank=True, default='weekly')
    review_date = models.DateTimeField(null=True, blank=True)
    manager_name = models.CharField(max_length=255, null=True, blank=True, default='')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_reviews', null=True, blank=True)
    is_adhoc = models.BooleanField(default=False, help_text='True if this is an ad-hoc meeting, False if cadence meeting')

    # Many-to-many through existing participants table
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='review_meetings_participated')

    class Meta:
        db_table = 'review_meetings'
        ordering = ['-review_date']

    def __str__(self):
        date_str = self.review_date.strftime('%Y-%m-%d %H:%M') if self.review_date else self.meeting_date.strftime('%Y-%m-%d')
        type_str = self.get_review_type_display() if self.review_type else self.get_meeting_type_display()
        return f"{self.team.name} - {type_str} - {date_str}"


class ReviewNote(models.Model):
    NOTE_TYPES = [
        ('general', 'General'),
        ('action', 'Action'),
        ('decision', 'Decision'),
        ('follow_up', 'Follow Up'),
    ]

    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='review_notes')
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, null=True, blank=True)
    serial_number = models.PositiveIntegerField()
    review_note = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        db_table = 'review_notes'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_note_type_display()} - {self.review_note[:50]}"


class ReviewDecision(models.Model):
    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='decisions')
    serial_number = models.PositiveIntegerField()
    decision = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = 'review_decisions'
        ordering = ['serial_number']
        unique_together = ['review_meeting', 'serial_number']

    def __str__(self):
        return f"Decision {self.serial_number} - {self.decision[:50]}"


class ReviewActionItem(models.Model):
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('dropped', 'Dropped'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    PARAMETER_TYPE_CHOICES = [
        ('fpi', 'FPI'),
        ('gpi', 'GPI'),
        ('ppi', 'PPI'),
        ('issue', 'Issue'),
    ]

    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='review_action_items')
    action = models.TextField(default='')  # Required field in database (NOT NULL)
    action_description = models.TextField(default='', blank=True)  # Alternative description field
    title = models.CharField(max_length=255, null=True, blank=True)  # Title field from schema
    description = models.TextField(null=True, blank=True)  # Description field from schema
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)  # Required (NOT NULL)
    due_date = models.DateField()  # Required (NOT NULL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', null=True, blank=True)
    previous_status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)  # Track previous status for undo/resume/reactivate
    comments = models.TextField(default='', blank=True)  # Required in database (NOT NULL) - use empty string as default
    completion_notes = models.TextField(default='', blank=True)
    notes = models.TextField(null=True, blank=True)  # Notes field from schema
    created_at = models.DateTimeField(auto_now_add=True)  # Required (NOT NULL)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_actions_created')  # Required in database (NOT NULL)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_actions_assigned')  # Required (NOT NULL)
    assigned_to_team = models.ForeignKey('organizations.Team', on_delete=models.CASCADE, related_name='review_actions_team_assigned')  # Required in database (NOT NULL)
    parameter_type = models.CharField(max_length=10, choices=PARAMETER_TYPE_CHOICES, null=True, blank=True)
    parameter_id = models.PositiveIntegerField(null=True, blank=True)
    project_id = models.PositiveIntegerField(null=True, blank=True)  # Project ID field from schema
    week_number = models.PositiveIntegerField(null=True, blank=True)  # Week number field from schema
    month_number = models.PositiveIntegerField(null=True, blank=True)  # Month number field from schema

    class Meta:
        db_table = 'review_action_items'
        ordering = ['-created_at']

    def __str__(self):
        action_text = self.action if self.action else (self.action_description if self.action_description else 'Action')
        assigned_name = self.assigned_to.get_full_name() if self.assigned_to and self.assigned_to.get_full_name() else (self.assigned_to.username if self.assigned_to else 'Unassigned')
        return f"{action_text[:50]} - {assigned_name}"

    def get_parameter_name(self):
        """Get the name of the linked parameter (GPI/PPI/Issue)"""
        if not self.parameter_type or not self.parameter_id:
            return None

        try:
            if self.parameter_type == 'gpi':
                from plans.models import GPIParameter
                param = GPIParameter.objects.get(id=self.parameter_id)
                return param.name
            elif self.parameter_type == 'ppi':
                from plans.models import PPIProject
                param = PPIProject.objects.get(id=self.parameter_id)
                return param.name
            elif self.parameter_type == 'issue':
                from implement.models import Issue
                issue = Issue.objects.get(id=self.parameter_id)
                return f"Issue #{issue.id}: {issue.title}"
        except Exception as e:
            return f"ID: {self.parameter_id}"

        return None


# ReviewCommitment model to match existing database schema
class ReviewCommitment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
        ('cancelled', 'Cancelled'),
    ]

    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='commitments')
    action = models.ForeignKey('implement.Action', on_delete=models.CASCADE, related_name='review_commitments', null=True, blank=True)
    commitment = models.TextField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    committed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_commitments', null=True, blank=True)

    class Meta:
        db_table = 'review_commitments'

    def __str__(self):
        return f"{self.commitment[:50] if self.commitment else 'Commitment'}"
