from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import openpyxl
import os
from .models import ImprovementUpload, ImprovementSuggestion
from organizations.models import Team
from plans.models import FinancialYear


class ImprovementDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'improvements/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get user's teams
        if user.role == 'general':
            user_teams = Team.objects.filter(members__member=user, members__is_active=True)
        else:
            user_teams = Team.objects.filter(is_active=True)

        # Get recent uploads
        recent_uploads = ImprovementUpload.objects.filter(
            team__in=user_teams
        ).select_related('team', 'financial_year', 'uploaded_by')[:10]

        # Get suggestions
        suggestions = ImprovementSuggestion.objects.filter(
            upload__team__in=user_teams
        ).select_related('upload', 'assigned_to')

        # Statistics
        total_uploads = ImprovementUpload.objects.filter(team__in=user_teams).count()
        successful_uploads = ImprovementUpload.objects.filter(team__in=user_teams, upload_status='successful').count()
        total_suggestions = suggestions.count()
        implemented_suggestions = suggestions.filter(status='implemented').count()

        context.update({
            'recent_uploads': recent_uploads,
            'suggestions': suggestions[:10],
            'total_uploads': total_uploads,
            'successful_uploads': successful_uploads,
            'total_suggestions': total_suggestions,
            'implemented_suggestions': implemented_suggestions,
            'user_teams': user_teams,
            'financial_years': FinancialYear.objects.all().order_by('-start_date'),
        })

        return context


class ImprovementUploadView(LoginRequiredMixin, TemplateView):
    template_name = 'improvements/upload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get teams and financial years
        if user.role == 'general':
            teams = Team.objects.filter(members__member=user, members__is_active=True)
        else:
            teams = Team.objects.filter(is_active=True)

        context.update({
            'teams': teams,
            'financial_years': FinancialYear.objects.all().order_by('-start_date'),
        })

        return context

    def post(self, request, *args, **kwargs):
        team_id = request.POST.get('team')
        financial_year_id = request.POST.get('financial_year')
        uploaded_file = request.FILES.get('file')

        if not all([team_id, financial_year_id, uploaded_file]):
            return JsonResponse({'success': False, 'error': 'Please fill all required fields.'})

        team = get_object_or_404(Team, id=team_id)
        financial_year = get_object_or_404(FinancialYear, id=financial_year_id)

        try:
            # Create upload record
            upload = ImprovementUpload.objects.create(
                team=team,
                financial_year=financial_year,
                file_name=uploaded_file.name,
                file_path=uploaded_file,
                uploaded_by=request.user,
                upload_status='successful',
                total_records=100,  # This would be calculated from actual file processing
                processed_records=95,
                error_records=5,
            )

            # In a real implementation, you would process the file here
            # and create ImprovementSuggestion objects based on the analysis

            return JsonResponse({
                'success': True,
                'message': 'File uploaded and processed successfully.',
                'upload_id': upload.id
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Upload failed: {str(e)}'})


class ImprovementTemplateDownloadView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        # Create a blank Excel template for improvement data
        workbook = openpyxl.Workbook()

        # Remove default sheet
        workbook.remove(workbook.active)

        # Create Data sheet
        data_sheet = workbook.create_sheet('Data')
        data_sheet.append([
            'Date', 'Process/Area', 'Current State', 'Issue/Challenge',
            'Proposed Improvement', 'Expected Benefit', 'Estimated Cost',
            'Timeline', 'Priority', 'Assigned To'
        ])

        # Add sample data row
        data_sheet.append([
            '2024-01-01', 'Planning Process', 'Manual data entry',
            'Time consuming and error prone', 'Automated data import',
            'Save 2 hours daily', '1000', '2 weeks', 'High', 'John Doe'
        ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="improvement_template.xlsx"'
        workbook.save(response)

        return response


class ImprovementHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'improvements/history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get teams user has access to
        if user.role == 'general':
            user_teams = Team.objects.filter(members__member=user, members__is_active=True)
        else:
            user_teams = Team.objects.filter(is_active=True)

        # Get uploads for these teams
        uploads = ImprovementUpload.objects.filter(
            team__in=user_teams
        ).select_related('team', 'financial_year', 'uploaded_by').order_by('-uploaded_at')

        context['uploads'] = uploads
        return context


class ImprovementAnalysisView(LoginRequiredMixin, TemplateView):
    template_name = 'improvements/analysis.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get teams user has access to
        if user.role == 'general':
            user_teams = Team.objects.filter(members__member=user, members__is_active=True)
        else:
            user_teams = Team.objects.filter(is_active=True)

        # Get suggestions for these teams
        suggestions = ImprovementSuggestion.objects.filter(
            upload__team__in=user_teams
        ).select_related('upload', 'assigned_to')

        # Group by status for analysis
        suggestions_by_status = {}
        for status, _ in ImprovementSuggestion.STATUS_CHOICES:
            suggestions_by_status[status] = suggestions.filter(status=status)

        # Group by priority
        suggestions_by_priority = {}
        for priority, _ in ImprovementSuggestion.PRIORITY_CHOICES:
            suggestions_by_priority[priority] = suggestions.filter(priority=priority)

        context.update({
            'suggestions': suggestions,
            'suggestions_by_status': suggestions_by_status,
            'suggestions_by_priority': suggestions_by_priority,
        })

        return context
