from django.db import models
from django.conf import settings
from organizations.models import Team
from plans.models import FinancialYear


class ReviewMeeting(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    MEETING_TYPES = [
        ('weekly', 'Weekly Review'),
        ('monthly', 'Monthly Review'),
        ('quarterly', 'Quarterly Review'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='review_meetings')
    financial_year = models.ForeignKey(FinancialYear, on_delete=models.CASCADE)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPES)
    meeting_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Meeting details
    week_number = models.IntegerField(null=True, blank=True)  # For weekly reviews
    month_number = models.IntegerField(null=True, blank=True)  # For monthly reviews
    quarter_number = models.IntegerField(null=True, blank=True)  # For quarterly reviews

    # Meeting logistics
    conducted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conducted_meetings')
    attendees = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='attended_meetings')

    # Meeting outcomes
    summary = models.TextField(blank=True)
    key_decisions = models.TextField(blank=True)
    next_steps = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    finalized_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='finalized_meetings')

    class Meta:
        db_table = 'review_meetings'
        ordering = ['-meeting_date']

    def __str__(self):
        return f"{self.team.name} - {self.get_meeting_type_display()} - {self.meeting_date}"


class Commitment(models.Model):
    COMMITMENT_TYPES = [
        ('fpi', 'FPI Commitment'),
        ('gpi', 'GPI Commitment'),
        ('ppi', 'PPI Commitment'),
        ('other', 'Other Commitment'),
    ]

    STATUS_CHOICES = [
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('behind', 'Behind Schedule'),
        ('completed', 'Completed'),
    ]

    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='commitments')
    commitment_type = models.CharField(max_length=20, choices=COMMITMENT_TYPES)
    description = models.TextField()
    committed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='on_track')
    progress_notes = models.TextField(blank=True)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'review_commitments'

    def __str__(self):
        return f"{self.description[:50]} - {self.committed_by.get_full_name()}"


class ReviewNote(models.Model):
    NOTE_TYPES = [
        ('fpi', 'FPI Note'),
        ('gpi', 'GPI Note'),
        ('ppi', 'PPI Note'),
        ('issue', 'Issue Note'),
        ('general', 'General Note'),
    ]

    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='notes')
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'review_notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_note_type_display()}"


class ActionItem(models.Model):
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
    ]

    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='action_items')
    action_description = models.TextField()
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    completion_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'review_action_items'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action_description[:50]} - {self.assigned_to.get_full_name()}"
