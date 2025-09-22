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

    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='review_action_items')
    action_description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    completion_notes = models.TextField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_actions_assigned')

    class Meta:
        db_table = 'review_action_items'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action_description[:50]} - {self.assigned_to.get_full_name()}"


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
