from django.contrib import admin
from .models import ImprovementProject


@admin.register(ImprovementProject)
class ImprovementProjectAdmin(admin.ModelAdmin):
    list_display = ('team', 'financial_year', 'quarter', 'upload_status', 'uploaded_by', 'uploaded_at')
    list_filter = ('upload_status', 'quarter', 'uploaded_at', 'financial_year')
    search_fields = ('team__name', 'file_name')
    ordering = ('-uploaded_at',)