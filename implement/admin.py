from django.contrib import admin
from .models import (
    NumbersTracking, ProjectStatus, Action, ActionHistory, Issue
)


@admin.register(NumbersTracking)
class NumbersTrackingAdmin(admin.ModelAdmin):
    list_display = ('team', 'source_type', 'tracking_type', 'year', 'week_number', 'month_number', 'assigned_to', 'updated_at')
    list_filter = ('source_type', 'tracking_type', 'year', 'team')
    search_fields = ('team__name', 'assigned_to__username')
    ordering = ('-updated_at',)


@admin.register(ProjectStatus)
class ProjectStatusAdmin(admin.ModelAdmin):
    list_display = ('project', 'status', 'completion_percentage', 'updated_by', 'updated_at')
    list_filter = ('status', 'updated_at', 'project__quarterly_plan__financial_year')
    search_fields = ('project__name', 'updated_by__username')
    ordering = ('-updated_at',)


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('action_summary', 'team', 'priority', 'assigned_to', 'status', 'original_due_date', 'created_at')
    list_filter = ('priority', 'status', 'source', 'created_at', 'original_due_date')
    search_fields = ('action', 'assigned_to__username', 'team__name')
    ordering = ('-created_at',)
    
    def action_summary(self, obj):
        return obj.action[:50] + '...' if len(obj.action) > 50 else obj.action
    action_summary.short_description = 'Action'


@admin.register(ActionHistory)
class ActionHistoryAdmin(admin.ModelAdmin):
    list_display = ('action_summary', 'status', 'updated_by', 'updated_at')
    list_filter = ('status', 'updated_at')
    search_fields = ('action__action', 'updated_by__username')
    ordering = ('-updated_at',)
    
    def action_summary(self, obj):
        return obj.action.action[:50] + '...' if len(obj.action.action) > 50 else obj.action.action
    action_summary.short_description = 'Action'


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'team', 'priority', 'status', 'reported_by', 'required_by', 'created_at')
    list_filter = ('priority', 'status', 'created_at', 'required_by')
    search_fields = ('title', 'description', 'team__name', 'reported_by__username')
    ordering = ('-created_at',)