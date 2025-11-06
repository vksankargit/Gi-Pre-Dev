from django.contrib import admin
from .models import ImprovementUpload, ImprovementProject, ImprovementTask, ImprovementProjectStatus


@admin.register(ImprovementUpload)
class ImprovementUploadAdmin(admin.ModelAdmin):
    list_display = ('team', 'financial_year', 'quarter', 'upload_status', 'uploaded_by', 'uploaded_at')
    list_filter = ('upload_status', 'quarter', 'uploaded_at', 'financial_year')
    search_fields = ('team__name', 'file_name')
    ordering = ('-uploaded_at',)


@admin.register(ImprovementProject)
class ImprovementProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'responsible_user', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('name', 'completion_criteria')
    ordering = ('name',)


@admin.register(ImprovementTask)
class ImprovementTaskAdmin(admin.ModelAdmin):
    list_display = ('project', 'week_number', 'task_description', 'assigned_to', 'is_completed')
    list_filter = ('is_completed', 'week_number')
    search_fields = ('task_description', 'project__name')
    ordering = ('project', 'week_number')


@admin.register(ImprovementProjectStatus)
class ImprovementProjectStatusAdmin(admin.ModelAdmin):
    list_display = ('project', 'status', 'completion_percentage', 'updated_by', 'updated_at')
    list_filter = ('status', 'updated_at')
    search_fields = ('project__name', 'challenge', 'comments')
    ordering = ('-updated_at',)
    readonly_fields = ('updated_at',)