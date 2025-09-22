from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
import openpyxl
import os
import datetime
from django.contrib.auth import get_user_model
from .models import ImprovementUpload, ImprovementProject, ImprovementTask
from plans.models import FinancialYear
from organizations.models import Team


class ImproveDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'improve/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get user's teams - only teams where user is manager
        if user.role == 'general':
            user_teams = Team.objects.filter(manager=user, is_active=True)
        else:
            user_teams = Team.objects.filter(is_active=True)

        # Get recent improvement uploads
        recent_uploads = ImprovementUpload.objects.filter(
            team__in=user_teams
        ).select_related('team', 'financial_year', 'uploaded_by').order_by('-uploaded_at')[:10]

        # Statistics
        total_uploads = ImprovementUpload.objects.filter(team__in=user_teams).count()
        successful_uploads = ImprovementUpload.objects.filter(team__in=user_teams, upload_status='successful').count()

        # For improve app, projects replace suggestions
        total_projects = ImprovementProject.objects.filter(upload__team__in=user_teams).count()
        completed_projects = ImprovementProject.objects.filter(upload__team__in=user_teams, status='completed').count()

        # Get current quarter information
        current_quarter = self._get_current_quarter()

        context.update({
            'recent_uploads': recent_uploads,
            'total_uploads': total_uploads,
            'successful_uploads': successful_uploads,
            'total_suggestions': total_projects,  # Projects instead of suggestions
            'implemented_suggestions': completed_projects,  # Completed instead of implemented
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

        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if not all([team_id, financial_year_id, quarter, uploaded_file]):
            error_msg = 'Please fill all required fields.'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return self.get(request, *args, **kwargs)

        # Validate file type
        if not uploaded_file.name.endswith(('.xlsx', '.xls')):
            error_msg = 'Please upload an Excel (.xlsx or .xls) file.'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return self.get(request, *args, **kwargs)

        try:
            team = get_object_or_404(Team, id=team_id, manager=request.user)
            financial_year = get_object_or_404(FinancialYear, id=financial_year_id)
        except:
            error_msg = 'Invalid team or financial year selection.'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return self.get(request, *args, **kwargs)

        try:
            # Create or update improvement upload
            improvement_upload, created = ImprovementUpload.objects.update_or_create(
                team=team,
                financial_year=financial_year,
                quarter=quarter,
                defaults={
                    'file_name': uploaded_file.name,
                    'file_path': uploaded_file,
                    'upload_status': 'processing',
                    'uploaded_by': request.user,
                    'error_log': '',
                    'total_records': 0,
                    'processed_records': 0,
                    'error_records': 0,
                }
            )

            # Process the Excel file using PPI-style processing
            processing_errors = self._process_improvement_excel_file(improvement_upload, uploaded_file)

            # Refresh the upload object to get updated statistics
            improvement_upload.refresh_from_db()

            # Determine success/failure based on both processing errors and error records
            has_errors = bool(processing_errors) or improvement_upload.error_records > 0

            if has_errors:
                improvement_upload.upload_status = 'failed'
                improvement_upload.error_log = '\n'.join(processing_errors) if processing_errors else 'Processing errors occurred'
                improvement_upload.save()

                if processing_errors:
                    error_message = f'File uploaded but processing failed: {"; ".join(processing_errors[:3])}'
                    if len(processing_errors) > 3:
                        error_message += f' and {len(processing_errors) - 3} more errors.'
                else:
                    error_message = f'File uploaded but processing failed. Total: {improvement_upload.total_records}, Processed: {improvement_upload.processed_records}, Errors: {improvement_upload.error_records}'

                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_message})
                messages.error(request, error_message)
            else:
                improvement_upload.upload_status = 'successful'
                improvement_upload.save()
                action = 'created' if created else 'updated'
                success_message = f'Improvement plan {action} and processed successfully. Total: {improvement_upload.total_records}, Processed: {improvement_upload.processed_records}, Errors: {improvement_upload.error_records}'

                if is_ajax:
                    return JsonResponse({'success': True, 'message': success_message})
                messages.success(request, success_message)

        except Exception as e:
            # Log error and mark as failed
            try:
                ImprovementUpload.objects.update_or_create(
                    team=team,
                    financial_year=financial_year,
                    quarter=quarter,
                    defaults={
                        'file_name': uploaded_file.name,
                        'file_path': uploaded_file,
                        'upload_status': 'failed',
                        'uploaded_by': request.user,
                        'error_log': str(e),
                        'total_records': 0,
                        'processed_records': 0,
                        'error_records': 1,
                    }
                )
            except:
                pass

            error_msg = f'Error uploading file: {str(e)}'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)

        if is_ajax:
            return JsonResponse({'success': False, 'error': 'Unknown error occurred'})
        return redirect('improve:upload')

    def _process_improvement_excel_file(self, improvement_upload, uploaded_file):
        """
        Process the uploaded Excel file using PPI-style processing.
        Returns a list of error messages (empty if successful).
        """
        errors = []
        User = get_user_model()
        total_records = 0
        processed_records = 0
        error_records = 0

        try:
            # Load the Excel workbook
            workbook = openpyxl.load_workbook(uploaded_file, data_only=True)

            # Clear existing projects for this upload
            ImprovementProject.objects.filter(upload=improvement_upload).delete()

            # Process PPI-style sheet (assume first sheet or named 'Improvements')
            if 'Improvements' in workbook.sheetnames:
                sheet = workbook['Improvements']
            else:
                sheet = workbook.active

            # Process improvement projects using PPI format
            project_errors = self._process_improvement_sheet(sheet, improvement_upload, User)
            errors.extend(project_errors)

            # Count records processed
            total_records = max(0, len(list(sheet.iter_rows(min_row=7, values_only=True))) - sum(1 for row in sheet.iter_rows(min_row=7, values_only=True) if not any(row)))
            processed_records = ImprovementProject.objects.filter(upload=improvement_upload).count()
            error_records = len(errors)

            # Update statistics
            improvement_upload.total_records = total_records
            improvement_upload.processed_records = processed_records
            improvement_upload.error_records = error_records
            improvement_upload.save()

        except Exception as e:
            errors.append(f"Error reading Excel file: {str(e)}")

        return errors

    def _process_improvement_sheet(self, sheet, improvement_upload, User):
        """Process improvement sheet using PPI format: ['', 'Project Name', 'Completion Criteria', 'Responsibility', 'Start Date', 'End Date', 'Steps', 'W1', 'W2', ...]"""
        errors = []

        # Header is at row 6, data starts at row 7 (like PPI)
        for row_num, row in enumerate(sheet.iter_rows(min_row=7, values_only=True), start=7):
            if not any(row):  # Skip empty rows
                continue

            try:
                # Format: ['', 'Project Name', 'Completion Criteria', 'Responsibility', 'Start Date', 'End Date', 'Steps', 'W1', 'W2', ...]
                if len(row) < 6:
                    continue

                _, project_name, completion_criteria, responsibility, start_date, end_date = row[:6]
                steps = row[6] if len(row) > 6 else ''

                if not project_name or project_name == 'None':
                    continue  # Skip rows without project name

                # Find responsible user by email
                responsible_user = None
                if responsibility:
                    try:
                        responsible_user = User.objects.get(email__iexact=responsibility.strip())
                    except User.DoesNotExist:
                        try:
                            responsible_user = User.objects.get(username__iexact=responsibility.strip())
                        except User.DoesNotExist:
                            errors.append(f"Improvements Row {row_num}: User '{responsibility}' not found")
                            continue

                # Parse dates
                parsed_start_date = None
                parsed_end_date = None

                if start_date:
                    if isinstance(start_date, datetime.datetime):
                        parsed_start_date = start_date.date()
                    elif isinstance(start_date, datetime.date):
                        parsed_start_date = start_date
                    else:
                        try:
                            parsed_start_date = datetime.datetime.strptime(str(start_date), '%Y-%m-%d').date()
                        except:
                            errors.append(f"Improvements Row {row_num}: Invalid start date format")
                            continue

                if end_date:
                    if isinstance(end_date, datetime.datetime):
                        parsed_end_date = end_date.date()
                    elif isinstance(end_date, datetime.date):
                        parsed_end_date = end_date
                    else:
                        try:
                            parsed_end_date = datetime.datetime.strptime(str(end_date), '%Y-%m-%d').date()
                        except:
                            errors.append(f"Improvements Row {row_num}: Invalid end date format")
                            continue

                # Create improvement project
                improvement_project = ImprovementProject.objects.create(
                    upload=improvement_upload,
                    name=str(project_name).strip(),
                    completion_criteria=str(completion_criteria).strip() if completion_criteria else '',
                    responsible_user=responsible_user,
                    start_date=parsed_start_date or datetime.date.today(),
                    end_date=parsed_end_date or datetime.date.today(),
                    steps=str(steps).strip() if steps else ''
                )

                # Process weekly tasks starting from column 8 (W1)
                week_task_errors = self._process_weekly_improvement_tasks(improvement_project, row, row_num, User)
                errors.extend(week_task_errors)

            except Exception as e:
                errors.append(f"Improvements Row {row_num}: {str(e)}")

        return errors

    def _process_weekly_improvement_tasks(self, improvement_project, row, row_num, User):
        """Process weekly tasks from improvement row and create ImprovementTask records"""
        errors = []

        try:
            # Weekly tasks start from column 8 (index 7) - W1, W2, W3, ...
            for week_num in range(1, 14):  # Up to 13 weeks per quarter
                task_column_index = 6 + week_num  # W1 is at index 7, W2 at 8, etc.

                if task_column_index < len(row):
                    task_description = row[task_column_index]

                    if task_description and str(task_description).strip() and str(task_description).strip() != 'None':
                        # Parse task description for assigned user (format: "Task description @user@email.com")
                        task_text = str(task_description).strip()
                        assigned_user = improvement_project.responsible_user  # Default to project responsible user

                        # Check if task has specific user assignment
                        if '@' in task_text:
                            parts = task_text.split('@')
                            if len(parts) >= 2:
                                task_text = parts[0].strip()
                                user_email = parts[-1].strip()
                                try:
                                    assigned_user = User.objects.get(email__iexact=user_email)
                                except User.DoesNotExist:
                                    errors.append(f"Improvements Row {row_num}, Week {week_num}: User '{user_email}' not found")
                                    continue

                        # Create the improvement task
                        improvement_task = ImprovementTask.objects.create(
                            project=improvement_project,
                            task_description=task_text,
                            week_number=week_num,
                            assigned_to=assigned_user
                        )

                        # Calculate due date for this week
                        # Assume quarter starts from project start_date
                        week_due_date = improvement_project.start_date + datetime.timedelta(weeks=week_num-1, days=6)

                        # Create corresponding Action
                        from implement.models import Action
                        Action.objects.create(
                            team=improvement_project.upload.team,
                            source='improvement',
                            improvement_task=improvement_task,
                            action=f"[Week {week_num}] {task_text}",
                            priority='medium',
                            assigned_to=assigned_user,
                            original_due_date=week_due_date,
                            status='not_started',
                            created_by=assigned_user,
                            comments=f"From Improvement project: {improvement_project.name}"
                        )

        except Exception as e:
            errors.append(f"Improvements Row {row_num}: Error processing weekly tasks - {str(e)}")

        return errors


class ImprovementProjectTemplateDownloadView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        # Create a blank Excel template for improvement projects using PPI format
        workbook = openpyxl.Workbook()

        # Remove default sheet and create improvements sheet
        workbook.remove(workbook.active)
        sheet = workbook.create_sheet('Improvements')

        # Add header structure matching PPI format
        # Row 1-5: Instructions/headers
        sheet.append(['Improvement Projects Template - Use PPI Format'])
        sheet.append(['Instructions: Fill in project details starting from row 7'])
        sheet.append(['Format: Project Name | Completion Criteria | Responsibility (email) | Start Date | End Date | Steps | W1 | W2 | ... | W13'])
        sheet.append([])  # Empty row
        sheet.append([])  # Empty row

        # Row 6: Headers (like PPI)
        headers = ['', 'Project Name', 'Completion Criteria for the quarter', 'Responsibility', 'Start Date', 'End Date', 'Steps']
        # Add weekly columns W1 through W13
        headers.extend([f'W{i}' for i in range(1, 14)])
        sheet.append(headers)

        # Row 7: Example data
        example_row = [
            '',  # Empty first column like PPI
            'Process Optimization',
            'Reduce processing time by 30% for quarterly reports',
            'user@example.com',
            '2024-01-01',
            '2024-03-31',
            'Analyze current process, identify bottlenecks, implement automation'
        ]
        # Add example weekly tasks
        example_tasks = [
            'Analysis phase @user@example.com',
            'Requirements gathering',
            'Design new process',
            'Development start',
            'Testing phase',
            'User training',
            'Pilot rollout',
            'Full deployment',
            'Monitor results',
            'Optimize further',
            'Documentation',
            'Final review',
            'Completion report'
        ]
        example_row.extend(example_tasks)
        sheet.append(example_row)

        # Style the header row (row 6)
        for cell in sheet[6]:
            if cell.value:
                cell.font = openpyxl.styles.Font(bold=True)
                cell.fill = openpyxl.styles.PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")

        # Style the instruction rows
        for row in range(1, 4):
            for cell in sheet[row]:
                if cell.value:
                    cell.font = openpyxl.styles.Font(italic=True)

        # Adjust column widths
        column_widths = [5, 25, 40, 20, 12, 12, 30] + [15] * 13  # Weekly columns
        for idx, width in enumerate(column_widths, 1):
            sheet.column_dimensions[openpyxl.utils.get_column_letter(idx)].width = width

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
        
        # Get improvement uploads for teams managed by user
        team_filter = self.request.GET.get('team', 'all')

        uploads = ImprovementUpload.objects.filter(
            team__manager=user
        ).select_related('team', 'financial_year', 'uploaded_by').order_by('-uploaded_at')

        if team_filter != 'all':
            try:
                team_id = int(team_filter)
                uploads = uploads.filter(team_id=team_id)
            except (ValueError, TypeError):
                pass
        
        # Get teams for filter dropdown
        managed_teams = Team.objects.filter(manager=user, is_active=True)
        
        context.update({
            'uploads': uploads,
            'managed_teams': managed_teams,
            'selected_team': team_filter,
        })
        
        return context


class ImprovementProjectFileDownloadView(LoginRequiredMixin, TemplateView):
    def get(self, request, project_id):
        user = request.user
        
        upload = get_object_or_404(
            ImprovementUpload,
            id=project_id,
            team__manager=user
        )
        
        if upload.file_path and os.path.exists(upload.file_path.path):
            response = HttpResponse(
                upload.file_path.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{upload.file_name}"'
            return response
        
        messages.error(request, 'File not found.')
        return redirect('improve:history')


class ImprovementProjectErrorLogView(LoginRequiredMixin, TemplateView):
    def get(self, request, project_id):
        user = request.user
        
        upload = get_object_or_404(
            ImprovementUpload,
            id=project_id,
            team__manager=user
        )
        
        if upload.upload_status == 'failed' and upload.error_log:
            response = HttpResponse(upload.error_log, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="error_log_{project_id}.txt"'
            return response
        
        messages.error(request, 'No error log available.')
        return redirect('improve:history')