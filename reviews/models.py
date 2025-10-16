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
    meeting_type = models.CharField(max_length=20, choices=REVIEW_TYPES)
    meeting_date = models.DateField()
    status = models.CharField(max_length=20)
    week_number = models.IntegerField(null=True, blank=True)
    month_number = models.IntegerField(null=True, blank=True)
    quarter_number = models.IntegerField(null=True, blank=True)
    summary = models.TextField()
    key_decisions = models.TextField()
    next_steps = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    finalized_at = models.DateTimeField(null=True, blank=True)
    conducted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conducted_reviews')
    finalized_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='finalized_reviews', null=True, blank=True)
    financial_year = models.ForeignKey('plans.FinancialYear', on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='review_meetings')

    # New columns that were added in migrations
    review_type = models.CharField(max_length=10, choices=REVIEW_TYPES, null=True, blank=True, default='weekly')
    review_date = models.DateTimeField(null=True, blank=True)
    manager_name = models.CharField(max_length=255, null=True, blank=True, default='')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_reviews', null=True, blank=True)

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
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        db_table = 'review_notes'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_note_type_display()} - {self.title[:50]}"


class ReviewDecision(models.Model):
    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='decisions')
    serial_number = models.PositiveIntegerField()
    decision = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

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
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PARAMETER_TYPE_CHOICES = [
        ('fpi', 'FPI'),
        ('gpi', 'GPI'),
        ('ppi', 'PPI'),
    ]

    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='review_action_items')
    action_description = models.TextField(default='')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completion_notes = models.TextField(default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_actions_assigned')
    assigned_to_team = models.ForeignKey('organizations.Team', on_delete=models.CASCADE, related_name='review_actions_team_assigned', null=True, blank=True)
    parameter_type = models.CharField(max_length=10, choices=PARAMETER_TYPE_CHOICES, null=True, blank=True)
    parameter_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'review_action_items'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action_description[:50]} - {self.assigned_to.get_full_name()}"

    def get_parameter_name(self):
        """Get the name of the linked parameter (FPI/GPI/PPI)"""
        if not self.parameter_type or not self.parameter_id:
            return None

        try:
            if self.parameter_type == 'fpi':
                from plans.models import FPIParameter
                param = FPIParameter.objects.get(id=self.parameter_id)
                # FPI uses main_head and sub_head combination
                if param.sub_head:
                    return f"{param.main_head} - {param.sub_head}"
                return param.main_head
            elif self.parameter_type == 'gpi':
                from plans.models import GPIParameter
                param = GPIParameter.objects.get(id=self.parameter_id)
                return param.name
            elif self.parameter_type == 'ppi':
                from plans.models import PPIProject
                param = PPIProject.objects.get(id=self.parameter_id)
                return param.name
        except Exception as e:
            return f"ID: {self.parameter_id}"

        return None


# ReviewCommitment model to match existing database schema
class ReviewCommitment(models.Model):
    COMMITMENT_TYPES = [
        ('action', 'Action'),
        ('improvement', 'Improvement'),
        ('follow_up', 'Follow Up'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
        ('cancelled', 'Cancelled'),
    ]

    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='commitments')
    commitment_type = models.CharField(max_length=20, choices=COMMITMENT_TYPES)
    description = models.TextField()
    target_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    progress_notes = models.TextField()
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    committed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_commitments')

    class Meta:
        db_table = 'review_commitments'

    def __str__(self):
        return f"{self.get_commitment_type_display()} - {self.description[:50]}"
