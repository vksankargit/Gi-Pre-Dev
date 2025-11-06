from django.contrib import admin
from .models import (
    FinancialYear, AnnualPlan, QuarterlyPlan,
    FPIParameter, GPIParameter, PPIProject, PPITask,
    GPIMilestone, FPIMilestone, AnnualFPIParameter,
    AnnualGPIParameter, AnnualPPIProject
)


@admin.register(FinancialYear)
class FinancialYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'start_date', 'end_date')
    ordering = ('-start_date',)


@admin.register(AnnualPlan)
class AnnualPlanAdmin(admin.ModelAdmin):
    list_display = ('team', 'financial_year', 'upload_status', 'uploaded_by', 'uploaded_at')
    list_filter = ('upload_status', 'uploaded_at', 'financial_year')
    search_fields = ('team__name', 'file_name')
    ordering = ('-uploaded_at',)


@admin.register(QuarterlyPlan)
class QuarterlyPlanAdmin(admin.ModelAdmin):
    list_display = ('team', 'financial_year', 'quarter', 'upload_status', 'uploaded_by', 'uploaded_at')
    list_filter = ('upload_status', 'quarter', 'uploaded_at', 'financial_year')
    search_fields = ('team__name', 'file_name')
    ordering = ('-uploaded_at',)


@admin.register(FPIParameter)
class FPIParameterAdmin(admin.ModelAdmin):
    list_display = ('sub_head', 'main_head', 'quarterly_plan', 'responsible_user', 'quarter_goal')
    list_filter = ('main_head', 'quarterly_plan__financial_year', 'quarterly_plan__quarter')
    search_fields = ('sub_head', 'quarterly_plan__team__name')
    ordering = ('quarterly_plan', 'main_head', 'sub_head')


@admin.register(GPIParameter)
class GPIParameterAdmin(admin.ModelAdmin):
    list_display = ('name', 'tracking_type', 'indicator_type', 'quarterly_plan', 'responsible_user', 'quarter_goal')
    list_filter = ('tracking_type', 'indicator_type', 'quarterly_plan__financial_year', 'quarterly_plan__quarter')
    search_fields = ('name', 'quarterly_plan__team__name')
    ordering = ('quarterly_plan', 'tracking_type', 'name')


@admin.register(PPIProject)
class PPIProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'quarterly_plan', 'responsible_user', 'start_date', 'end_date')
    list_filter = ('quarterly_plan__financial_year', 'quarterly_plan__quarter', 'start_date', 'end_date')
    search_fields = ('name', 'quarterly_plan__team__name')
    ordering = ('quarterly_plan', 'start_date', 'name')


@admin.register(PPITask)
class PPITaskAdmin(admin.ModelAdmin):
    list_display = ('project', 'week_number', 'assigned_to', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'week_number', 'project__quarterly_plan__financial_year')
    search_fields = ('task_description', 'project__name', 'assigned_to__username')
    ordering = ('project', 'week_number')


@admin.register(GPIMilestone)
class GPIMilestoneAdmin(admin.ModelAdmin):
    list_display = ('gpi_parameter', 'period_number', 'budget_value')
    list_filter = ('gpi_parameter__tracking_type', 'gpi_parameter__quarterly_plan__financial_year')
    search_fields = ('gpi_parameter__name',)
    ordering = ('gpi_parameter', 'period_number')


@admin.register(FPIMilestone)
class FPIMilestoneAdmin(admin.ModelAdmin):
    list_display = ('fpi_parameter', 'month_number', 'budget_value')
    list_filter = ('fpi_parameter__quarterly_plan__financial_year', 'month_number')
    search_fields = ('fpi_parameter__sub_head',)
    ordering = ('fpi_parameter', 'month_number')


@admin.register(AnnualFPIParameter)
class AnnualFPIParameterAdmin(admin.ModelAdmin):
    list_display = ('sub_head', 'main_head', 'annual_plan', 'responsible_user', 'annual_goal')
    list_filter = ('main_head', 'annual_plan__financial_year')
    search_fields = ('sub_head', 'annual_plan__team__name')
    ordering = ('annual_plan', 'main_head', 'sub_head')


@admin.register(AnnualGPIParameter)
class AnnualGPIParameterAdmin(admin.ModelAdmin):
    list_display = ('name', 'tracking_type', 'indicator_type', 'annual_plan', 'responsible_user', 'annual_goal')
    list_filter = ('tracking_type', 'indicator_type', 'annual_plan__financial_year')
    search_fields = ('name', 'annual_plan__team__name')
    ordering = ('annual_plan', 'tracking_type', 'name')


@admin.register(AnnualPPIProject)
class AnnualPPIProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'annual_plan', 'responsible_user')
    list_filter = ('annual_plan__financial_year',)
    search_fields = ('name', 'annual_plan__team__name')
    ordering = ('annual_plan', 'name')