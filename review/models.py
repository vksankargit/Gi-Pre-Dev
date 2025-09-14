from django.db import models
from django.conf import settings
from organizations.models import Team


class ReviewMeeting(models.Model):
    REVIEW_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='review_meetings')
    review_type = models.CharField(max_length=10, choices=REVIEW_TYPES)
    meeting_date = models.DateTimeField()
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='managed_meetings')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_meetings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'review_meetings'
        ordering = ['-meeting_date']
        
    def __str__(self):
        return f"{self.team.name} - {self.review_type} - {self.meeting_date.date()}"
        
    @property
    def has_subsequent_review(self):
        """Check if there's a review meeting after this one for the same team"""
        return ReviewMeeting.objects.filter(
            team=self.team,
            meeting_date__gt=self.meeting_date
        ).exists()


class ReviewParticipant(models.Model):
    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='participants')
    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    attended = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'review_participants'
        unique_together = ['review_meeting', 'participant']
        
    def __str__(self):
        return f"{self.participant.get_full_name()} - {self.review_meeting}"


class ReviewNote(models.Model):
    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='notes')
    serial_number = models.IntegerField()
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'review_notes'
        unique_together = ['review_meeting', 'serial_number']
        ordering = ['serial_number']
        
    def __str__(self):
        return f"Note {self.serial_number} - {self.review_meeting}"


class ReviewDecision(models.Model):
    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='decisions')
    serial_number = models.IntegerField()
    decision = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'review_decisions'
        unique_together = ['review_meeting', 'serial_number']
        ordering = ['serial_number']
        
    def __str__(self):
        return f"Decision {self.serial_number} - {self.review_meeting}"


class ReviewAction(models.Model):
    """Actions created during review meetings"""
    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='review_actions')
    action = models.ForeignKey('implement.Action', on_delete=models.CASCADE, related_name='review_meetings')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'review_actions'
        unique_together = ['review_meeting', 'action']
        
    def __str__(self):
        return f"{self.action.action[:50]} - {self.review_meeting}"


class ReviewIssue(models.Model):
    """Issues created during review meetings"""
    review_meeting = models.ForeignKey(ReviewMeeting, on_delete=models.CASCADE, related_name='review_issues')
    issue = models.ForeignKey('implement.Issue', on_delete=models.CASCADE, related_name='review_meetings')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'review_issues'
        unique_together = ['review_meeting', 'issue']
        
    def __str__(self):
        return f"{self.issue.title} - {self.review_meeting}"