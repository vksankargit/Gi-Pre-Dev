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
from accounts.utils import get_effective_user


class ImproveDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'improve/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_effective_user(self.request)

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

        # Get current quarter information (both display and value formats)
        current_quarter_display, current_quarter_value = self._get_current_quarter()

        context.update({
            'recent_uploads': recent_uploads,
            'total_uploads': total_uploads,
            'successful_uploads': successful_uploads,
            'total_suggestions': total_projects,  # Projects instead of suggestions
            'implemented_suggestions': completed_projects,  # Completed instead of implemented
            'user_teams': user_teams,
            'financial_years': FinancialYear.objects.all().order_by('-start_date'),
            'current_quarter': current_quarter_display,
            'current_quarter_value': current_quarter_value,
        })

        return context

    def _get_current_quarter(self):
        """
        Get current financial year and quarter in both display and value formats
        Returns: (display_format, value_format) e.g., ("FY 25-26 – Q3", "2025_3")
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
        display_format = f'{fy_str} – Q{current_quarter}'
        value_format = f'{fy_start_year}_{current_quarter}'
        return display_format, value_format


class ImprovementProjectUploadView(LoginRequiredMixin, TemplateView):
    template_name = 'improve/upload.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get teams and financial years
        if user.role == 'general':
            managed_teams = Team.objects.filter(manager=user, is_active=True)
        else:
            # For coordinators and admins, show all teams
            managed_teams = Team.objects.filter(is_active=True)

        # Generate current quarter option only (unlike Quarterly Plan which shows current and next)
        current_date = timezone.now().date()
        quarters = self._get_current_quarter_option(current_date)

        # Debug: Log what we're sending to template
        print(f"DEBUG get_context_data: quarters = {quarters}")

        context.update({
            'managed_teams': managed_teams,
            'quarters': quarters,
        })

        return context

    def _get_current_quarter_option(self, current_date):
        """
        Generate current quarter option in FY XX-XX – QX format based on current date
        Only shows current quarter (unlike Quarterly Plan which shows current and next)
        """
        # Financial year starts April 1st
        # Determine current financial year
        if current_date.month >= 4:  # April to December = same year FY
            fy_start_year = current_date.year
        else:  # January to March = previous year FY
            fy_start_year = current_date.year - 1

        fy_end_year = fy_start_year + 1
        fy_start = datetime.date(fy_start_year, 4, 1)

        # Determine current quarter
        if fy_start <= current_date <= datetime.date(fy_start_year, 6, 30):
            current_quarter = 1
        elif datetime.date(fy_start_year, 7, 1) <= current_date <= datetime.date(fy_start_year, 9, 30):
            current_quarter = 2
        elif datetime.date(fy_start_year, 10, 1) <= current_date <= datetime.date(fy_start_year, 12, 31):
            current_quarter = 3
        else:  # Jan 1 to Mar 31 of next year
            current_quarter = 4

        quarters = []
        current_fy_str = f'FY {str(fy_start_year)[2:]}-{str(fy_end_year)[2:]}'
        quarters.append((f'{fy_start_year}_{current_quarter}', f'{current_fy_str} – Q{current_quarter}'))

        return quarters
    
    def post(self, request, *args, **kwargs):
        team_id = request.POST.get('team')
        quarter_id = request.POST.get('quarter')
        uploaded_file = request.FILES.get('file')

        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Debug: Log what we received
        print(f"DEBUG: Received quarter_id = '{quarter_id}'")
        print(f"DEBUG: POST data = {request.POST}")

        if not all([team_id, quarter_id, uploaded_file]):
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

        # Parse quarter information (format: "year_quarter", e.g., "2025_3")
        try:
            if '_' in quarter_id:
                # New format: "2025_3"
                year_str, quarter_str = quarter_id.split('_')
                financial_year_start = int(year_str)
                quarter_num = int(quarter_str)
            else:
                # Fallback: Handle unexpected format - extract quarter number and current FY year
                error_msg = f'Received unexpected quarter format: "{quarter_id}". Please refresh the page (Ctrl+F5) and try again.'
                print(f"DEBUG: Unexpected quarter format: {quarter_id}")
                if is_ajax:
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return self.get(request, *args, **kwargs)

            # Validate quarter number
            if quarter_num not in [1, 2, 3, 4]:
                raise ValueError("Invalid quarter number")

            # Get or create the financial year
            try:
                financial_year = FinancialYear.objects.get(
                    start_date__year=financial_year_start,
                    start_date__month=4,
                    start_date__day=1
                )
            except FinancialYear.DoesNotExist:
                # Create the financial year if it doesn't exist
                start_date = datetime.date(financial_year_start, 4, 1)
                end_date = datetime.date(financial_year_start + 1, 3, 31)
                financial_year = FinancialYear.objects.create(
                    year=f'FY {str(financial_year_start)[2:]}-{str(financial_year_start + 1)[2:]}',
                    start_date=start_date,
                    end_date=end_date
                )

            # Convert quarter number to Q format
            quarter = f'Q{quarter_num}'

        except (ValueError, AttributeError) as e:
            error_msg = f'Invalid quarter format: {quarter_id}. Expected format: "YYYY_Q" (e.g., "2025_3"). Error: {str(e)}'
            print(f"DEBUG: Error parsing quarter_id: {e}")
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return self.get(request, *args, **kwargs)

        try:
            # Allow team access based on user role
            if request.user.role == 'general':
                team = get_object_or_404(Team, id=team_id, manager=request.user, is_active=True)
            else:
                # For coordinators and admins, allow access to any active team
                team = get_object_or_404(Team, id=team_id, is_active=True)
        except:
            error_msg = 'Invalid team selection.'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg})
            messages.error(request, error_msg)
            return self.get(request, *args, **kwargs)

        try:
            # Always create a new improvement upload (multiple uploads allowed per quarter)
            improvement_upload = ImprovementUpload.objects.create(
                team=team,
                financial_year=financial_year,
                quarter=quarter,
                file_name=uploaded_file.name,
                file_path=uploaded_file,
                upload_status='processing',
                uploaded_by=request.user,
                error_log='',
                total_records=0,
                processed_records=0,
                error_records=0
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

                # Create history record for failed upload
                from improve.models import ImprovementUploadHistory
                ImprovementUploadHistory.objects.create(
                    improvement_upload=improvement_upload,
                    file_name=uploaded_file.name,
                    file_path=improvement_upload.file_path,
                    upload_status='failed',
                    error_log=improvement_upload.error_log,
                    uploaded_by=request.user,
                    total_records=improvement_upload.total_records,
                    processed_records=improvement_upload.processed_records,
                    error_records=improvement_upload.error_records
                )

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

                # Create history record for successful upload
                from improve.models import ImprovementUploadHistory
                ImprovementUploadHistory.objects.create(
                    improvement_upload=improvement_upload,
                    file_name=uploaded_file.name,
                    file_path=improvement_upload.file_path,
                    upload_status='successful',
                    error_log='',
                    uploaded_by=request.user,
                    total_records=improvement_upload.total_records,
                    processed_records=improvement_upload.processed_records,
                    error_records=0
                )

                success_message = f'Improvement plan uploaded and processed successfully. Total: {improvement_upload.total_records}, Processed: {improvement_upload.processed_records}, Errors: {improvement_upload.error_records}'

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

            # Process PPI-style sheet (assume first sheet or named 'PPI' or 'Improvements')
            if 'PPI' in workbook.sheetnames:
                sheet = workbook['PPI']
            elif 'Improvements' in workbook.sheetnames:
                sheet = workbook['Improvements']
            else:
                sheet = workbook.active

            # First pass: Extract all project names from the uploaded file
            project_names_in_file = []
            for row_num, row in enumerate(sheet.iter_rows(min_row=5, values_only=True), start=5):
                if not any(row):  # Skip empty rows
                    continue

                if len(row) < 2:
                    continue

                project_name = row[1]  # Project name is in column B (index 1)

                # Skip rows without project name or with header-like content
                if not project_name or project_name == 'None' or str(project_name).strip() == 'Project Name':
                    continue

                project_names_in_file.append(str(project_name).strip())

            # Check for duplicates across all existing improvement projects for the same team/quarter/year
            if project_names_in_file:
                # Get ALL existing project names for the same team, financial year, and quarter
                # Exclude the current upload since it was just created and has no projects yet
                existing_project_names = list(ImprovementProject.objects.filter(
                    upload__team=improvement_upload.team,
                    upload__financial_year=improvement_upload.financial_year,
                    upload__quarter=improvement_upload.quarter
                ).exclude(upload=improvement_upload).values_list('name', flat=True))

                # Find duplicates
                duplicates = [name for name in project_names_in_file if name in existing_project_names]

                if duplicates:
                    # Return error and don't import anything
                    duplicate_list = ', '.join(f'"{name}"' for name in duplicates[:5])
                    if len(duplicates) > 5:
                        duplicate_list += f' and {len(duplicates) - 5} more'
                    errors.append(f"Duplicate project names found: {duplicate_list}. These projects already exist for {improvement_upload.team.name} - {improvement_upload.financial_year.year} {improvement_upload.quarter}. Please remove duplicates from the file and try again.")
                    return errors

            # Don't delete any existing projects - we're adding new ones to the quarter

            # Process improvement projects using PPI format
            project_errors = self._process_improvement_sheet(sheet, improvement_upload, User)
            errors.extend(project_errors)

            # Count records processed
            total_records = max(0, len(list(sheet.iter_rows(min_row=5, values_only=True))) - sum(1 for row in sheet.iter_rows(min_row=5, values_only=True) if not any(row)))
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
        """Process improvement sheet using PPI format: ['', 'Project Name', 'Completion Criteria', 'Responsibility', 'Start Date', 'End Date', 'Steps', 'W1 Budget', 'W2 Budget', ...]"""
        errors = []

        # Row 2: Title "PROJECT PROGRESS INDICATORS"
        # Row 3: Empty
        # Row 4: Headers
        # Row 5+: Data rows
        for row_num, row in enumerate(sheet.iter_rows(min_row=5, values_only=True), start=5):
            if not any(row):  # Skip empty rows
                continue

            try:
                # Format: ['', 'Project Name', 'Completion Criteria', 'Responsibility', 'Start Date', 'End Date', 'Steps', 'W1 Budget', 'W2 Budget', ...]
                if len(row) < 6:
                    continue

                _, project_name, completion_criteria, responsibility, start_date, end_date = row[:6]
                steps = row[6] if len(row) > 6 else ''

                # Skip rows without project name or with header-like content
                if not project_name or project_name == 'None' or str(project_name).strip() == 'Project Name':
                    continue

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

                # Process weekly tasks starting from column 8 (W1 Budget)
                week_task_errors = self._process_weekly_improvement_tasks(improvement_project, row, row_num, User)
                errors.extend(week_task_errors)

            except Exception as e:
                errors.append(f"Improvements Row {row_num}: {str(e)}")

        return errors

    def _process_weekly_improvement_tasks(self, improvement_project, row, row_num, User):
        """Process weekly tasks from improvement row and create ImprovementTask records"""
        errors = []

        try:
            # Weekly tasks start from column 8 (index 7) - W1 Budget, W2 Budget, W3 Budget, ...
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

                        # Calculate due date for this week based on quarter start date
                        quarter_start = improvement_project.upload.quarter_start_date
                        week_due_date = quarter_start + datetime.timedelta(weeks=week_num-1, days=6)

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
        # Serve the actual IMPROVE template file from the project root
        template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'IMPROVE - Template.xlsx')

        if os.path.exists(template_path):
            with open(template_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename="IMPROVE - Template.xlsx"'
                return response
        else:
            messages.error(request, 'Template file not found.')
            return redirect('improve:dashboard')


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


class IndividualImprovementProjectHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'improve/project_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(ImprovementProject, pk=kwargs['pk'])

        # Calculate completed tasks count
        completed_tasks_count = project.tasks.filter(is_completed=True).count() if hasattr(project, 'tasks') and project.tasks.exists() else 0
        total_tasks_count = project.tasks.count() if hasattr(project, 'tasks') else 0

        context.update({
            'project': project,
            'history': project.status_history.all().order_by('-updated_at'),  # Now we have real status history
            'completed_tasks_count': completed_tasks_count,
            'total_tasks_count': total_tasks_count,
        })

        return context