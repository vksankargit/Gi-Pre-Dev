from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.http import HttpResponse
import openpyxl
import os
from .models import ImprovementProject
from plans.models import FinancialYear
from organizations.models import Team


class ImproveDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'improve/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get teams where user is manager
        managed_teams = Team.objects.filter(manager=user, is_active=True)
        
        # Get recent improvement projects
        recent_projects = ImprovementProject.objects.filter(
            team__in=managed_teams
        ).select_related('team', 'financial_year', 'uploaded_by').order_by('-uploaded_at')[:10]
        
        context.update({
            'managed_teams': managed_teams,
            'recent_projects': recent_projects,
        })
        
        return context


class ImprovementProjectUploadView(LoginRequiredMixin, TemplateView):
    template_name = 'improve/upload.html'
    
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
    
    def post(self, request, *args, **kwargs):
        team_id = request.POST.get('team')
        financial_year_id = request.POST.get('financial_year')
        quarter = request.POST.get('quarter')
        uploaded_file = request.FILES.get('file')
        
        if not all([team_id, financial_year_id, quarter, uploaded_file]):
            messages.error(request, 'Please fill all required fields.')
            return self.get(request, *args, **kwargs)
        
        # Validate file type
        if not uploaded_file.name.endswith('.xlsx'):
            messages.error(request, 'Please upload an Excel (.xlsx) file.')
            return self.get(request, *args, **kwargs)
        
        team = get_object_or_404(Team, id=team_id, manager=request.user)
        financial_year = get_object_or_404(FinancialYear, id=financial_year_id)
        
        try:
            # Create or update improvement project
            improvement_project, created = ImprovementProject.objects.update_or_create(
                team=team,
                financial_year=financial_year,
                quarter=quarter,
                defaults={
                    'file_name': uploaded_file.name,
                    'file_path': uploaded_file,
                    'upload_status': 'successful',
                    'uploaded_by': request.user,
                    'error_log': ''
                }
            )
            
            action = 'created' if created else 'updated'
            messages.success(request, f'Improvement project {action} successfully.')
            
        except Exception as e:
            # Log error and mark as failed
            ImprovementProject.objects.update_or_create(
                team=team,
                financial_year=financial_year,
                quarter=quarter,
                defaults={
                    'file_name': uploaded_file.name,
                    'file_path': uploaded_file,
                    'upload_status': 'failed',
                    'uploaded_by': request.user,
                    'error_log': str(e)
                }
            )
            messages.error(request, f'Error uploading file: {str(e)}')
        
        return redirect('improve:upload')


class ImprovementProjectTemplateDownloadView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        # Create a blank Excel template for improvement projects
        workbook = openpyxl.Workbook()
        
        # Remove default sheet and create improvement projects sheet
        workbook.remove(workbook.active)
        sheet = workbook.create_sheet('Improvement Projects')
        
        # Add headers
        headers = [
            'Project Name',
            'Description', 
            'Category',
            'Priority',
            'Expected Benefits',
            'Resource Requirements',
            'Timeline',
            'Success Metrics',
            'Owner',
            'Status'
        ]
        sheet.append(headers)
        
        # Add some example data/instructions
        example_row = [
            'Example Project',
            'Describe the improvement project',
            'Process/Technology/Training',
            'High/Medium/Low',
            'Expected benefits and outcomes',
            'Required resources',
            'Start - End dates',
            'How success will be measured',
            'Project owner email',
            'Planned/In Progress/Completed'
        ]
        sheet.append(example_row)
        
        # Style the header row
        for cell in sheet[1]:
            cell.font = openpyxl.styles.Font(bold=True)
            cell.fill = openpyxl.styles.PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        # Adjust column widths
        for column in sheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            sheet.column_dimensions[column_letter].width = adjusted_width
        
        # Save to response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="improvement_projects_template.xlsx"'
        workbook.save(response)
        
        return response


class ImprovementProjectHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'improve/history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get improvement projects for teams managed by user
        team_filter = self.request.GET.get('team', 'all')
        
        projects = ImprovementProject.objects.filter(
            team__manager=user
        ).select_related('team', 'financial_year', 'uploaded_by').order_by('-uploaded_at')
        
        if team_filter != 'all':
            try:
                team_id = int(team_filter)
                projects = projects.filter(team_id=team_id)
            except (ValueError, TypeError):
                pass
        
        # Get teams for filter dropdown
        managed_teams = Team.objects.filter(manager=user, is_active=True)
        
        context.update({
            'projects': projects,
            'managed_teams': managed_teams,
            'selected_team': team_filter,
        })
        
        return context


class ImprovementProjectFileDownloadView(LoginRequiredMixin, TemplateView):
    def get(self, request, project_id):
        user = request.user
        
        project = get_object_or_404(
            ImprovementProject, 
            id=project_id, 
            team__manager=user
        )
        
        if project.file_path and os.path.exists(project.file_path.path):
            response = HttpResponse(
                project.file_path.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{project.file_name}"'
            return response
        
        messages.error(request, 'File not found.')
        return redirect('improve:history')


class ImprovementProjectErrorLogView(LoginRequiredMixin, TemplateView):
    def get(self, request, project_id):
        user = request.user
        
        project = get_object_or_404(
            ImprovementProject, 
            id=project_id, 
            team__manager=user
        )
        
        if project.upload_status == 'failed' and project.error_log:
            response = HttpResponse(project.error_log, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="error_log_{project_id}.txt"'
            return response
        
        messages.error(request, 'No error log available.')
        return redirect('improve:history')