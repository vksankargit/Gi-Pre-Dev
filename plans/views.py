from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import openpyxl
import os
from .models import AnnualPlan, QuarterlyPlan, FinancialYear
from organizations.models import Team


class PlanDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'plans/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get teams where user is manager or can access based on role
        if user.role == 'general':
            managed_teams = Team.objects.filter(manager=user, is_active=True)
        else:
            # Admin/coordinator can see all teams
            managed_teams = Team.objects.filter(is_active=True)

        # Get financial years
        financial_years = FinancialYear.objects.all().order_by('-start_date')

        context.update({
            'managed_teams': managed_teams,
            'financial_years': financial_years,
        })

        return context


class AnnualPlanUploadView(LoginRequiredMixin, TemplateView):
    template_name = 'plans/annual_upload.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get teams and financial years
        managed_teams = Team.objects.filter(manager=user, is_active=True)
        financial_years = FinancialYear.objects.all().order_by('-start_date')
        
        context.update({
            'managed_teams': managed_teams,
            'financial_years': financial_years,
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        team_id = request.POST.get('team')
        financial_year_id = request.POST.get('financial_year')
        uploaded_file = request.FILES.get('file')
        
        if not all([team_id, financial_year_id, uploaded_file]):
            messages.error(request, 'Please fill all required fields.')
            return self.get(request, *args, **kwargs)
        
        team = get_object_or_404(Team, id=team_id, manager=request.user)
        financial_year = get_object_or_404(FinancialYear, id=financial_year_id)
        
        # Process and save the annual plan
        try:
            annual_plan, created = AnnualPlan.objects.update_or_create(
                team=team,
                financial_year=financial_year,
                defaults={
                    'file_name': uploaded_file.name,
                    'file_path': uploaded_file,
                    'upload_status': 'successful',
                    'uploaded_by': request.user,
                    'error_log': ''
                }
            )
            
            messages.success(request, 'Annual plan uploaded successfully.')
            
        except Exception as e:
            messages.error(request, f'Error uploading file: {str(e)}')
        
        return redirect('plans:annual_upload')


class AnnualPlanTemplateDownloadView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        # Create a blank Excel template for annual plan
        workbook = openpyxl.Workbook()
        
        # Remove default sheet
        workbook.remove(workbook.active)
        
        # Create FPI sheet
        fpi_sheet = workbook.create_sheet('FPI')
        fpi_sheet.append(['Parameter Type', 'Sub Head', 'Annual Goal', 'Q1', 'Q2', 'Q3', 'Q4'])
        
        # Create GPI sheet
        gpi_sheet = workbook.create_sheet('GPI')
        gpi_sheet.append(['Goal & Progress Indicator', 'Unit of Measure', 'Tracking Type', 'Annual Goal', 'Q1', 'Q2', 'Q3', 'Q4'])
        
        # Create PPI sheet
        ppi_sheet = workbook.create_sheet('PPI')
        ppi_sheet.append(['Project Name', 'Completion Criteria', 'Start Date', 'End Date'])
        
        # Save to response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="annual_plan_template.xlsx"'
        workbook.save(response)
        
        return response


class QuarterlyPlanUploadView(LoginRequiredMixin, TemplateView):
    template_name = 'plans/quarterly_upload.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get teams and financial years
        managed_teams = Team.objects.filter(manager=user, is_active=True)
        financial_years = FinancialYear.objects.all().order_by('-start_date')
        
        quarters = [('Q1', 'Q1'), ('Q2', 'Q2'), ('Q3', 'Q3'), ('Q4', 'Q4')]
        
        context.update({
            'managed_teams': managed_teams,
            'financial_years': financial_years,
            'quarters': quarters,
        })
        
        return context


class QuarterlyPlanTemplateDownloadView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        # Create a blank Excel template for quarterly plan
        workbook = openpyxl.Workbook()
        
        # Remove default sheet
        workbook.remove(workbook.active)
        
        # Create sheets
        sheets_data = {
            'FPI': ['Parameter Type', 'Sub Head', 'Responsibility', 'Quarter Goal', 'Month 1', 'Month 2', 'Month 3'],
            'GPI-M': ['Goal & Progress Indicator', 'Unit of Measure', 'Responsibility', 'Quarter Goal', 'Month 1', 'Month 2', 'Month 3'],
            'GPI-W': ['Goal & Progress Indicator', 'Unit of Measure', 'Responsibility', 'Quarter Goal'] + [f'Week {i}' for i in range(1, 14)],
            'PPI': ['Project Name', 'Completion Criteria', 'Responsibility', 'Start Date', 'End Date'] + [f'Week {i}' for i in range(1, 14)]
        }
        
        for sheet_name, headers in sheets_data.items():
            sheet = workbook.create_sheet(sheet_name)
            sheet.append(headers)
        
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="quarterly_plan_template.xlsx"'
        workbook.save(response)
        
        return response


class AnnualPlanHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'plans/annual_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get plans for teams managed by user
        plans = AnnualPlan.objects.filter(
            team__manager=user
        ).select_related('team', 'financial_year', 'uploaded_by').order_by('-uploaded_at')
        
        context['plans'] = plans
        return context


class QuarterlyPlanHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'plans/quarterly_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get plans for teams managed by user
        plans = QuarterlyPlan.objects.filter(
            team__manager=user
        ).select_related('team', 'financial_year', 'uploaded_by').order_by('-uploaded_at')
        
        context['plans'] = plans
        return context


class PlanFileDownloadView(LoginRequiredMixin, TemplateView):
    def get(self, request, plan_id, plan_type):
        user = request.user
        
        if plan_type == 'annual':
            plan = get_object_or_404(AnnualPlan, id=plan_id, team__manager=user)
            file_path = plan.file_path
        else:
            plan = get_object_or_404(QuarterlyPlan, id=plan_id, team__manager=user)
            file_path = plan.file_path
        
        if file_path and os.path.exists(file_path.path):
            response = HttpResponse(
                file_path.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{plan.file_name}"'
            return response
        
        messages.error(request, 'File not found.')
        return redirect('plans:dashboard')


class PlanErrorLogView(LoginRequiredMixin, TemplateView):
    def get(self, request, plan_id, plan_type):
        user = request.user
        
        if plan_type == 'annual':
            plan = get_object_or_404(AnnualPlan, id=plan_id, team__manager=user)
        else:
            plan = get_object_or_404(QuarterlyPlan, id=plan_id, team__manager=user)
        
        if plan.upload_status == 'failed' and plan.error_log:
            response = HttpResponse(plan.error_log, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="error_log_{plan_id}.txt"'
            return response
        
        messages.error(request, 'No error log available.')
        return redirect('plans:dashboard')