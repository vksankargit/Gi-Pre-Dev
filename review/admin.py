from django.contrib import admin
from .models import (
    ReviewMeeting, ReviewParticipant, ReviewNote, 
    ReviewDecision, ReviewAction, ReviewIssue
)


@admin.register(ReviewMeeting)
class ReviewMeetingAdmin(admin.ModelAdmin):
    list_display = ('team', 'review_type', 'meeting_date', 'manager', 'created_by', 'created_at')
    list_filter = ('review_type', 'meeting_date', 'created_at')
    search_fields = ('team__name', 'manager__username')
    ordering = ('-meeting_date',)


@admin.register(ReviewParticipant)
class ReviewParticipantAdmin(admin.ModelAdmin):
    list_display = ('review_meeting', 'participant', 'attended')
    list_filter = ('attended', 'review_meeting__review_type', 'review_meeting__meeting_date')
    search_fields = ('participant__username', 'review_meeting__team__name')
    ordering = ('-review_meeting__meeting_date',)


@admin.register(ReviewNote)
class ReviewNoteAdmin(admin.ModelAdmin):
    list_display = ('review_meeting', 'serial_number', 'note_preview', 'created_at')
    list_filter = ('created_at', 'review_meeting__review_type')
    search_fields = ('note', 'review_meeting__team__name')
    ordering = ('review_meeting', 'serial_number')
    
    def note_preview(self, obj):
        return obj.note[:100] + '...' if len(obj.note) > 100 else obj.note
    note_preview.short_description = 'Note'


@admin.register(ReviewDecision)
class ReviewDecisionAdmin(admin.ModelAdmin):
    list_display = ('review_meeting', 'serial_number', 'decision_preview', 'created_at')
    list_filter = ('created_at', 'review_meeting__review_type')
    search_fields = ('decision', 'review_meeting__team__name')
    ordering = ('review_meeting', 'serial_number')
    
    def decision_preview(self, obj):
        return obj.decision[:100] + '...' if len(obj.decision) > 100 else obj.decision
    decision_preview.short_description = 'Decision'


@admin.register(ReviewAction)
class ReviewActionAdmin(admin.ModelAdmin):
    list_display = ('review_meeting', 'action_summary', 'created_at')
    list_filter = ('created_at', 'review_meeting__review_type')
    search_fields = ('action__action', 'review_meeting__team__name')
    ordering = ('-created_at',)
    
    def action_summary(self, obj):
        return obj.action.action[:50] + '...' if len(obj.action.action) > 50 else obj.action.action
    action_summary.short_description = 'Action'


@admin.register(ReviewIssue)
class ReviewIssueAdmin(admin.ModelAdmin):
    list_display = ('review_meeting', 'issue_title', 'created_at')
    list_filter = ('created_at', 'review_meeting__review_type')
    search_fields = ('issue__title', 'review_meeting__team__name')
    ordering = ('-created_at',)
    
    def issue_title(self, obj):
        return obj.issue.title
    issue_title.short_description = 'Issue'