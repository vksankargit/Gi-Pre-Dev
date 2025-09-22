from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone
import openpyxl
import os
import datetime
from .models import ImprovementUpload, ImprovementSuggestion
from organizations.models import Team
from plans.models import FinancialYear


class ImprovementDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'improvements/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get user's teams - only teams where user is manager
        if user.role == 'general':
            user_teams = Team.objects.filter(manager=user, is_active=True)
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

        # Get current quarter information
        current_quarter = self._get_current_quarter()

        context.update({
            'recent_uploads': recent_uploads,
            'suggestions': suggestions[:10],
            'total_uploads': total_uploads,
            'successful_uploads': successful_uploads,
            'total_suggestions': total_suggestions,
            'implemented_suggestions': implemented_suggestions,
            'user_teams': user_teams,
            'financial_years': FinancialYear.objects.all().order_by('-start_date'),
            'current_quarter': current_quarter,
        })

        return context

    def _get_current_quarter(self):
        """
        Get current financial year and quarter in FY XX-XX – QX format
        """
        current_date = timezone.now().date()

        # Financial year starts April 1st
        # Determine current financial year
        if current_date.month >= 4:  # April to December = same year FY
            fy_start_year = current_date.year
        else:  # January to March = previous year FY
            fy_start_year = current_date.year - 1

        fy_end_year = fy_start_year + 1

        # Determine current quarter
        if current_date.month >= 4 and current_date.month <= 6:  # April to June
            current_quarter = 1
        elif current_date.month >= 7 and current_date.month <= 9:  # July to September
            current_quarter = 2
        elif current_date.month >= 10 and current_date.month <= 12:  # October to December
            current_quarter = 3
        else:  # January to March (next year)
            current_quarter = 4

        # Format as FY 25-26 – Q2
        fy_str = f'FY {str(fy_start_year)[2:]}-{str(fy_end_year)[2:]}'
        return f'{fy_str} – Q{current_quarter}'


class ImprovementUploadView(LoginRequiredMixin, TemplateView):
    template_name = 'improvements/upload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get teams and financial years - only teams where user is manager
        if user.role == 'general':
            teams = Team.objects.filter(manager=user, is_active=True)
        else:
            teams = Team.objects.filter(is_active=True)

        context.update({
            'teams': teams,
            'financial_years': FinancialYear.objects.all().order_by('-start_date'),
        })

        return context

    def post(self, request, *args, **kwargs):
        team_id = request.POST.get('team')
        quarter = request.POST.get('quarter')
        uploaded_file = request.FILES.get('file')

        if not all([team_id, quarter, uploaded_file]):
            return JsonResponse({'success': False, 'error': 'Please fill all required fields.'})

        team = get_object_or_404(Team, id=team_id)

        # Get current financial year based on the quarter
        current_financial_year = self._get_current_financial_year()

        try:
            # Create upload record with initial processing status
            upload = ImprovementUpload.objects.create(
                team=team,
                financial_year=current_financial_year,
                file_name=uploaded_file.name,
                file_path=uploaded_file,
                uploaded_by=request.user,
                upload_status='processing',
                total_records=0,
                processed_records=0,
                error_records=0,
            )

            # Process the Excel file
            total_records, processed_records, error_records, errors = self._process_excel_file(uploaded_file, upload)

            # Update upload record with processing results
            upload.total_records = total_records
            upload.processed_records = processed_records
            upload.error_records = error_records
            upload.upload_status = 'successful' if error_records == 0 else 'failed'
            if errors:
                upload.error_log = '\n'.join(errors)
            upload.save()

            # Return appropriate response based on errors
            if error_records > 0:
                return JsonResponse({
                    'success': False,
                    'error': f'File uploaded but processing failed. Total: {total_records}, Processed: {processed_records}, Errors: {error_records}',
                    'upload_id': upload.id,
                    'total_records': total_records,
                    'processed_records': processed_records,
                    'error_records': error_records
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': f'File uploaded and processed successfully. Total: {total_records}, Processed: {processed_records}, Errors: {error_records}',
                    'upload_id': upload.id,
                    'total_records': total_records,
                    'processed_records': processed_records,
                    'error_records': error_records
                })

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Upload failed: {str(e)}'})

    def _get_current_financial_year(self):
        """
        Get the current financial year object
        """
        current_date = timezone.now().date()

        # Financial year starts April 1st
        if current_date.month >= 4:  # April to December = same year FY
            fy_start_year = current_date.year
        else:  # January to March = previous year FY
            fy_start_year = current_date.year - 1

        # Try to get the financial year, create if it doesn't exist
        try:
            financial_year = FinancialYear.objects.get(
                start_date__year=fy_start_year,
                start_date__month=4,
                start_date__day=1
            )
        except FinancialYear.DoesNotExist:
            # Create the financial year if it doesn't exist
            start_date = datetime.date(fy_start_year, 4, 1)
            end_date = datetime.date(fy_start_year + 1, 3, 31)
            financial_year = FinancialYear.objects.create(
                year=f'FY {str(fy_start_year)[2:]}-{str(fy_start_year + 1)[2:]}',
                start_date=start_date,
                end_date=end_date
            )

        return financial_year

    def _process_excel_file(self, uploaded_file, upload):
        """
        Process the uploaded Excel file and create improvement suggestions.
        Returns: (total_records, processed_records, error_records, errors)
        """
        total_records = 0
        processed_records = 0
        error_records = 0
        errors = []

        try:
            # Load the workbook
            workbook = openpyxl.load_workbook(uploaded_file)
            worksheet = workbook.active

            # Expected columns based on template
            expected_headers = [
                'Date', 'Process/Area', 'Current State', 'Issue/Challenge',
                'Proposed Improvement', 'Expected Benefit', 'Estimated Cost',
                'Timeline', 'Priority', 'Assigned To'
            ]

            # Get headers from first row
            headers = []
            for cell in worksheet[1]:
                headers.append(cell.value)

            # Validate headers
            missing_headers = set(expected_headers) - set(headers)
            if missing_headers:
                errors.append(f"Missing required headers: {', '.join(missing_headers)}")
                return 0, 0, 1, errors

            # Process data rows (skip header row)
            for row_num, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
                total_records += 1

                try:
                    # Skip empty rows
                    if not any(row):
                        continue

                    # Extract data from row
                    row_data = dict(zip(headers, row))

                    # Validate required fields
                    required_fields = ['Process/Area', 'Issue/Challenge', 'Proposed Improvement']
                    missing_fields = [field for field in required_fields if not row_data.get(field)]

                    if missing_fields:
                        errors.append(f"Row {row_num}: Missing required fields: {', '.join(missing_fields)}")
                        error_records += 1
                        continue

                    # Parse priority
                    priority_mapping = {
                        'high': 'high',
                        'medium': 'medium',
                        'low': 'low',
                        'high impact': 'high',
                        'medium impact': 'medium',
                        'low impact': 'low'
                    }
                    priority = 'medium'  # default
                    if row_data.get('Priority'):
                        priority = priority_mapping.get(str(row_data['Priority']).lower(), 'medium')

                    # Parse estimated cost
                    estimated_savings = None
                    if row_data.get('Estimated Cost'):
                        try:
                            # Remove currency symbols and convert to decimal
                            cost_str = str(row_data['Estimated Cost']).replace('$', '').replace(',', '')
                            estimated_savings = float(cost_str) if cost_str.replace('.', '').isdigit() else None
                        except (ValueError, TypeError):
                            pass

                    # Create improvement suggestion
                    title = f"{row_data.get('Process/Area', 'Unknown')} Improvement"
                    description = f"Current State: {row_data.get('Current State', 'Not specified')}\n"
                    description += f"Issue/Challenge: {row_data.get('Issue/Challenge', '')}\n"
                    description += f"Proposed Improvement: {row_data.get('Proposed Improvement', '')}\n"
                    if row_data.get('Expected Benefit'):
                        description += f"Expected Benefit: {row_data.get('Expected Benefit')}\n"
                    if row_data.get('Timeline'):
                        description += f"Timeline: {row_data.get('Timeline')}"

                    ImprovementSuggestion.objects.create(
                        upload=upload,
                        title=title[:255],  # Truncate to fit field length
                        description=description,
                        category=row_data.get('Process/Area', 'General')[:100],
                        priority=priority,
                        status='identified',
                        estimated_savings=estimated_savings,
                        estimated_effort=str(row_data.get('Timeline', ''))[:100] if row_data.get('Timeline') else ''
                    )

                    processed_records += 1

                except Exception as row_error:
                    errors.append(f"Row {row_num}: Error processing data - {str(row_error)}")
                    error_records += 1

        except Exception as file_error:
            errors.append(f"File processing error: {str(file_error)}")
            return 0, 0, 1, errors

        return total_records, processed_records, error_records, errors


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
            user_teams = Team.objects.filter(manager=user, is_active=True)
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
            user_teams = Team.objects.filter(manager=user, is_active=True)
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
