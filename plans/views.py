from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone
import openpyxl
import os
import datetime
from .models import AnnualPlan, QuarterlyPlan, FinancialYear, FPIParameter, GPIParameter, PPIProject, PPITask, FPIMilestone, GPIMilestone
from organizations.models import Team
from django.contrib.auth import get_user_model


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

        # Get current and next financial years only
        current_date = timezone.now().date()

        # Calculate financial year boundaries
        # FY starts April 1st - determine current FY and next FY dates
        if current_date.month >= 4:  # April to December = same year FY
            current_fy_start = datetime.date(current_date.year, 4, 1)
            next_fy_start = datetime.date(current_date.year + 1, 4, 1)
        else:  # January to March = previous year FY
            current_fy_start = datetime.date(current_date.year - 1, 4, 1)
            next_fy_start = datetime.date(current_date.year, 4, 1)

        # Include current and next financial year only
        financial_years = FinancialYear.objects.filter(
            start_date__gte=current_fy_start,
            start_date__lt=next_fy_start + datetime.timedelta(days=365)  # Include next FY
        ).order_by('start_date')

        # Generate current and next quarter options as per PRD
        quarters = self._get_quarter_options(current_date)

        context.update({
            'managed_teams': managed_teams,
            'financial_years': financial_years,
            'quarters': quarters,
        })

        return context

    def _get_quarter_options(self, current_date):
        """
        Generate quarter options in FY XX-XX – QX format based on current date
        Per PRD: Q1-Q3 shows current and next, Q4 shows current and next FY Q1
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

        if current_quarter <= 3:  # Q1-Q3: show current and next in same FY
            current_fy_str = f'FY {str(fy_start_year)[2:]}-{str(fy_end_year)[2:]}'
            quarters.append((f'{fy_start_year}_{current_quarter}', f'{current_fy_str} – Q{current_quarter}'))
            quarters.append((f'{fy_start_year}_{current_quarter + 1}', f'{current_fy_str} – Q{current_quarter + 1}'))
        else:  # Q4: show current Q4 and next FY Q1
            current_fy_str = f'FY {str(fy_start_year)[2:]}-{str(fy_end_year)[2:]}'
            next_fy_str = f'FY {str(fy_end_year)[2:]}-{str(fy_end_year + 1)[2:]}'
            quarters.append((f'{fy_start_year}_{current_quarter}', f'{current_fy_str} – Q{current_quarter}'))
            quarters.append((f'{fy_end_year}_1', f'{next_fy_str} – Q1'))

        return quarters


class AnnualPlanUploadView(LoginRequiredMixin, TemplateView):
    template_name = 'plans/annual_upload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get teams and current/next financial years
        managed_teams = Team.objects.filter(manager=user, is_active=True)
        current_date = timezone.now().date()

        # Calculate financial year boundaries
        # FY starts April 1st - determine current FY and next FY dates
        if current_date.month >= 4:  # April to December = same year FY
            current_fy_start = datetime.date(current_date.year, 4, 1)
            next_fy_start = datetime.date(current_date.year + 1, 4, 1)
        else:  # January to March = previous year FY
            current_fy_start = datetime.date(current_date.year - 1, 4, 1)
            next_fy_start = datetime.date(current_date.year, 4, 1)

        # Include current and next financial year only
        financial_years = FinancialYear.objects.filter(
            start_date__gte=current_fy_start,
            start_date__lt=next_fy_start + datetime.timedelta(days=365)  # Include next FY
        ).order_by('start_date')

        context.update({
            'managed_teams': managed_teams,
            'financial_years': financial_years,
        })

        return context

    def post(self, request, *args, **kwargs):
        # Check if this is an AJAX request - since the JavaScript uses fetch() API,
        # we'll check for multiple indicators that this is an AJAX request
        is_ajax = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest' or
            'application/json' in request.headers.get('accept', '') or
            # If called from our upload form JS, we can assume it's AJAX
            request.META.get('HTTP_SEC_FETCH_MODE') == 'cors' or
            # The form is posted via fetch() so let's detect that
            True  # For now, always return JSON since this endpoint is only used by JavaScript
        )

        # Get parameters with correct names (JS sends team_id/plan_year_id)
        team_id = request.POST.get('team_id') or request.POST.get('team')
        financial_year_id = request.POST.get('plan_year_id') or request.POST.get('financial_year')
        uploaded_file = request.FILES.get('file')

        # Validation
        if not all([team_id, financial_year_id, uploaded_file]):
            error_message = 'Please fill all required fields.'
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': error_message
                })
            else:
                messages.error(request, error_message)
                return redirect('plans:dashboard')

        # Verify team access
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            error_message = 'Invalid team selected.'
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': error_message
                })
            else:
                messages.error(request, error_message)
                return redirect('plans:dashboard')

        # Check if user has access to this team (manager or member)
        if team.manager != request.user:
            # Check if user is a team member
            from organizations.models import TeamMember
            team_membership = TeamMember.objects.filter(
                member=request.user,
                team=team,
                is_active=True
            ).first()

            if not team_membership:
                error_message = 'You do not have access to this team.'
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error': error_message
                    })
                else:
                    messages.error(request, error_message)
                    return redirect('plans:dashboard')

        # Get financial year
        try:
            financial_year = FinancialYear.objects.get(id=financial_year_id)
        except FinancialYear.DoesNotExist:
            error_message = 'Invalid financial year selected.'
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': error_message
                })
            else:
                messages.error(request, error_message)
                return redirect('plans:dashboard')

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

            success_message = 'Annual plan uploaded successfully.'
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': success_message
                })
            else:
                messages.success(request, success_message)
                return redirect('plans:annual_upload')

        except Exception as e:
            error_message = f'Error uploading file: {str(e)}'
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': error_message
                })
            else:
                messages.error(request, error_message)
                return redirect('plans:dashboard')


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

        # Get teams and current/next financial years
        managed_teams = Team.objects.filter(manager=user, is_active=True)
        current_date = timezone.now().date()

        # Calculate financial year boundaries
        # FY starts April 1st - determine current FY and next FY dates
        if current_date.month >= 4:  # April to December = same year FY
            current_fy_start = datetime.date(current_date.year, 4, 1)
            next_fy_start = datetime.date(current_date.year + 1, 4, 1)
        else:  # January to March = previous year FY
            current_fy_start = datetime.date(current_date.year - 1, 4, 1)
            next_fy_start = datetime.date(current_date.year, 4, 1)

        # Include current and next financial year only
        financial_years = FinancialYear.objects.filter(
            start_date__gte=current_fy_start,
            start_date__lt=next_fy_start + datetime.timedelta(days=365)  # Include next FY
        ).order_by('start_date')
        
        # Generate current and next quarter options as per PRD
        quarters = self._get_quarter_options(current_date)
        
        context.update({
            'managed_teams': managed_teams,
            'financial_years': financial_years,
            'quarters': quarters,
        })
        
        return context

    def _get_quarter_options(self, current_date):
        """
        Generate quarter options in FY XX-XX – QX format based on current date
        Per PRD: Q1-Q3 shows current and next, Q4 shows current and next FY Q1
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

        if current_quarter <= 3:  # Q1-Q3: show current and next in same FY
            current_fy_str = f'FY {str(fy_start_year)[2:]}-{str(fy_end_year)[2:]}'
            quarters.append((f'{fy_start_year}_{current_quarter}', f'{current_fy_str} – Q{current_quarter}'))
            quarters.append((f'{fy_start_year}_{current_quarter + 1}', f'{current_fy_str} – Q{current_quarter + 1}'))
        else:  # Q4: show current Q4 and next FY Q1
            current_fy_str = f'FY {str(fy_start_year)[2:]}-{str(fy_end_year)[2:]}'
            next_fy_str = f'FY {str(fy_end_year)[2:]}-{str(fy_end_year + 1)[2:]}'
            quarters.append((f'{fy_start_year}_{current_quarter}', f'{current_fy_str} – Q{current_quarter}'))
            quarters.append((f'{fy_end_year}_1', f'{next_fy_str} – Q1'))

        return quarters

    def post(self, request, *args, **kwargs):
        # Check if this is an AJAX request - similar to annual upload
        is_ajax = True  # Always return JSON since this endpoint is only used by JavaScript

        # Get parameters (JS sends team_id/quarter_id)
        team_id = request.POST.get('team_id') or request.POST.get('team')
        quarter_id = request.POST.get('quarter_id') or request.POST.get('quarter')
        uploaded_file = request.FILES.get('file')

        # Validation
        if not all([team_id, quarter_id, uploaded_file]):
            error_message = 'Please fill all required fields.'
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': error_message
                })
            else:
                messages.error(request, error_message)
                return redirect('plans:dashboard')

        # Verify team access
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            error_message = 'Invalid team selected.'
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': error_message
                })
            else:
                messages.error(request, error_message)
                return redirect('plans:dashboard')

        # Check if user has access to this team (manager or member)
        if team.manager != request.user:
            # Check if user is a team member
            from organizations.models import TeamMember
            team_membership = TeamMember.objects.filter(
                member=request.user,
                team=team,
                is_active=True
            ).first()

            if not team_membership:
                error_message = 'You do not have access to this team.'
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error': error_message
                    })
                else:
                    messages.error(request, error_message)
                    return redirect('plans:dashboard')

        # Parse quarter information (format: "year_quarter", e.g., "2025_2")
        try:
            year_str, quarter_str = quarter_id.split('_')
            financial_year_start = int(year_str)
            quarter_num = int(quarter_str)

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
        except (ValueError, AttributeError):
            error_message = 'Invalid quarter selected.'
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': error_message
                })
            else:
                messages.error(request, error_message)
                return redirect('plans:dashboard')

        # Process and save the quarterly plan
        try:
            quarterly_plan, created = QuarterlyPlan.objects.update_or_create(
                team=team,
                financial_year=financial_year,
                quarter=quarter_num,
                defaults={
                    'file_name': uploaded_file.name,
                    'file_path': uploaded_file,
                    'upload_status': 'processing',
                    'uploaded_by': request.user,
                    'error_log': ''
                }
            )

            # Process the Excel file to create FPI, GPI, and PPI records
            processing_errors = self._process_quarterly_excel_file(quarterly_plan, uploaded_file)

            if processing_errors:
                quarterly_plan.upload_status = 'failed'
                quarterly_plan.error_log = '\n'.join(processing_errors)
                quarterly_plan.save()

                error_message = f'File uploaded but processing failed: {"; ".join(processing_errors[:3])}'
                if len(processing_errors) > 3:
                    error_message += f' and {len(processing_errors) - 3} more errors.'

                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error': error_message,
                        'errors': processing_errors
                    })
                else:
                    messages.error(request, error_message)
                    return redirect('plans:dashboard')
            else:
                quarterly_plan.upload_status = 'successful'
                quarterly_plan.save()

                success_message = 'Quarterly plan uploaded and processed successfully.'
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': success_message
                    })
                else:
                    messages.success(request, success_message)
                    return redirect('plans:dashboard')

        except Exception as e:
            error_message = f'Error uploading file: {str(e)}'
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'error': error_message
                })
            else:
                messages.error(request, error_message)
                return redirect('plans:dashboard')

    def _process_quarterly_excel_file(self, quarterly_plan, uploaded_file):
        """
        Process the uploaded Excel file to create FPI, GPI, and PPI records.
        Returns a list of error messages (empty if successful).
        """
        errors = []
        User = get_user_model()

        try:
            # Load the Excel workbook
            workbook = openpyxl.load_workbook(uploaded_file, data_only=True)

            # Clear existing records for this quarterly plan
            FPIParameter.objects.filter(quarterly_plan=quarterly_plan).delete()
            GPIParameter.objects.filter(quarterly_plan=quarterly_plan).delete()
            PPIProject.objects.filter(quarterly_plan=quarterly_plan).delete()

            # Process FPI sheet
            if 'FPI' in workbook.sheetnames:
                fpi_errors = self._process_fpi_sheet(workbook['FPI'], quarterly_plan, User)
                errors.extend(fpi_errors)
            else:
                errors.append("Missing FPI sheet in uploaded file")

            # Process GPI-M sheet
            if 'GPI-M' in workbook.sheetnames:
                gpi_m_errors = self._process_gpi_sheet(workbook['GPI-M'], quarterly_plan, User, 'monthly')
                errors.extend(gpi_m_errors)
            else:
                errors.append("Missing GPI-M sheet in uploaded file")

            # Process GPI-W sheet
            if 'GPI-W' in workbook.sheetnames:
                gpi_w_errors = self._process_gpi_sheet(workbook['GPI-W'], quarterly_plan, User, 'weekly')
                errors.extend(gpi_w_errors)
            else:
                errors.append("Missing GPI-W sheet in uploaded file")

            # Process PPI sheet
            if 'PPI' in workbook.sheetnames:
                ppi_errors = self._process_ppi_sheet(workbook['PPI'], quarterly_plan, User)
                errors.extend(ppi_errors)
            else:
                errors.append("Missing PPI sheet in uploaded file")

        except Exception as e:
            errors.append(f"Error reading Excel file: {str(e)}")

        return errors

    def _process_fpi_sheet(self, sheet, quarterly_plan, User):
        """Process FPI sheet with full monthly milestone extraction"""
        errors = []

        # Header is at row 4, data starts at row 5
        for row_num, row in enumerate(sheet.iter_rows(min_row=5, values_only=True), start=5):
            if not any(row):  # Skip empty rows
                continue

            try:
                # Actual format: ['', 'Main Head', 'Sub-head', 'Responsibility', 'Annual Goal', 'YTD till last Qtr', 'Next Qtr Budget', 'Next Qtr Goal', 'M1', 'M2', 'M3', ...]
                if len(row) < 8:
                    continue

                main_head = row[1] if len(row) > 1 else ''
                sub_head = row[2] if len(row) > 2 else ''
                responsibility = row[3] if len(row) > 3 else ''
                quarter_goal = row[7] if len(row) > 7 else 0  # Next Qtr Goal

                if not sub_head or str(sub_head).strip() == 'None' or str(sub_head).strip() == '':
                    continue  # Skip rows without sub_head

                # Find responsible user by email
                responsible_user = None
                if responsibility and str(responsibility).strip():
                    responsibility_clean = str(responsibility).strip()
                    try:
                        responsible_user = User.objects.get(email__iexact=responsibility_clean)
                    except User.DoesNotExist:
                        try:
                            responsible_user = User.objects.get(username__iexact=responsibility_clean)
                        except User.DoesNotExist:
                            # Show available users for debugging
                            available_emails = list(User.objects.values_list('email', flat=True))
                            errors.append(f"FPI Row {row_num}: User '{responsibility_clean}' not found. Available emails: {available_emails}")
                            continue

                # Map main head to model field
                main_head_mapping = {
                    'revenues': 'revenue',
                    'revenue': 'revenue',
                    'total revenue': 'revenue',
                    'cogs (variable cost)': 'variable_cost',
                    'variable cost': 'variable_cost',
                    'operating expenses': 'operating_expenses',
                    'other expenses': 'other_expenses'
                }
                main_head_value = main_head_mapping.get(str(main_head).lower().strip(), 'revenue')

                # Extract monthly budget values for the legacy fields
                # M1, M2, M3 are at indices 8, 9, 10
                month1_budget = 0
                month2_budget = 0
                month3_budget = 0

                if len(row) > 8:  # M1
                    try:
                        month1_budget = float(row[8]) if row[8] else 0
                    except (ValueError, TypeError):
                        pass

                if len(row) > 9:  # M2
                    try:
                        month2_budget = float(row[9]) if row[9] else 0
                    except (ValueError, TypeError):
                        pass

                if len(row) > 10:  # M3
                    try:
                        month3_budget = float(row[10]) if row[10] else 0
                    except (ValueError, TypeError):
                        pass

                # Create FPI parameter
                fpi_parameter = FPIParameter.objects.create(
                    quarterly_plan=quarterly_plan,
                    main_head=main_head_value,
                    sub_head=str(sub_head).strip(),
                    responsible_user=responsible_user,
                    quarter_goal=float(quarter_goal) if quarter_goal else 0,
                    month1_budget=month1_budget,
                    month2_budget=month2_budget,
                    month3_budget=month3_budget
                )

                # Create FPI milestone records for each month
                # M1, M2, M3 are at indices 8, 9, 10
                for month_num in range(1, 4):  # Month 1-3
                    col_index = 7 + month_num  # M1 is at index 8, so 7 + 1 = 8
                    if col_index < len(row) and row[col_index] is not None:
                        try:
                            month_value = float(row[col_index])
                            if month_value != 0:  # Only create milestone if value is non-zero
                                FPIMilestone.objects.create(
                                    fpi_parameter=fpi_parameter,
                                    month_number=month_num,
                                    budget_value=month_value
                                )
                        except (ValueError, TypeError):
                            pass  # Skip invalid values

            except Exception as e:
                errors.append(f"FPI Row {row_num}: {str(e)}")

        return errors

    def _process_gpi_sheet(self, sheet, quarterly_plan, User, tracking_type):
        """Process GPI sheet with full weekly/monthly milestone extraction"""
        errors = []

        # Header is at row 6, data starts at row 7
        for row_num, row in enumerate(sheet.iter_rows(min_row=7, values_only=True), start=7):
            if not any(row):  # Skip empty rows
                continue

            try:
                # Actual format: ['', 'Goal & Progress Indicators', 'Indicator Type (Goal / Progress)', 'Responsibility', 'Annual Goal', 'YTD till last quarter', 'Next Quarter Budget', 'Next Quarter Goal', 'W1/M1', 'W2/M2', ...]
                if len(row) < 8:
                    continue

                name = row[1] if len(row) > 1 else ''
                indicator_type = row[2] if len(row) > 2 else ''
                responsibility = row[3] if len(row) > 3 else ''
                quarter_goal = row[7] if len(row) > 7 else 0  # Next Quarter Goal

                if not name or str(name).strip() == 'None' or str(name).strip() == '':
                    continue  # Skip rows without name

                # Find responsible user by email
                responsible_user = None
                if responsibility and str(responsibility).strip():
                    responsibility_clean = str(responsibility).strip()
                    try:
                        responsible_user = User.objects.get(email__iexact=responsibility_clean)
                    except User.DoesNotExist:
                        try:
                            responsible_user = User.objects.get(username__iexact=responsibility_clean)
                        except User.DoesNotExist:
                            # Show available users for debugging
                            available_emails = list(User.objects.values_list('email', flat=True))
                            errors.append(f"GPI-{tracking_type[0].upper()} Row {row_num}: User '{responsibility_clean}' not found. Available emails: {available_emails}")
                            continue

                # Map indicator type
                indicator_type_value = 'goal' if str(indicator_type).lower().strip() == 'goal' else 'progress'

                # Create GPI parameter
                gpi_parameter = GPIParameter.objects.create(
                    quarterly_plan=quarterly_plan,
                    name=str(name).strip(),
                    unit_of_measure='',  # Unit of measure not present in this format
                    tracking_type=tracking_type,
                    indicator_type=indicator_type_value,
                    responsible_user=responsible_user,
                    quarter_goal=float(quarter_goal) if quarter_goal else 0
                )

                # Extract weekly/monthly milestone data
                # W1/M1 starts at index 8 (after Next Quarter Goal)
                if tracking_type == 'weekly':
                    # Process W1-W13 columns (starting from index 8)
                    for week_num in range(1, 14):  # W1 to W13
                        col_index = 7 + week_num  # W1 is at index 8, so 7 + 1 = 8
                        if col_index < len(row) and row[col_index] is not None:
                            try:
                                week_value = float(row[col_index])
                                if week_value != 0:  # Only create milestone if value is non-zero
                                    GPIMilestone.objects.create(
                                        gpi_parameter=gpi_parameter,
                                        period_number=week_num,
                                        budget_value=week_value
                                    )
                            except (ValueError, TypeError):
                                pass  # Skip invalid values

                elif tracking_type == 'monthly':
                    # Process M1-M3 columns (starting from index 8)
                    for month_num in range(1, 4):  # Month 1 to Month 3
                        col_index = 7 + month_num  # M1 is at index 8, so 7 + 1 = 8
                        if col_index < len(row) and row[col_index] is not None:
                            try:
                                month_value = float(row[col_index])
                                if month_value != 0:  # Only create milestone if value is non-zero
                                    GPIMilestone.objects.create(
                                        gpi_parameter=gpi_parameter,
                                        period_number=month_num,
                                        budget_value=month_value
                                    )
                            except (ValueError, TypeError):
                                pass  # Skip invalid values

            except Exception as e:
                errors.append(f"GPI-{tracking_type[0].upper()} Row {row_num}: {str(e)}")

        return errors

    def _process_ppi_sheet(self, sheet, quarterly_plan, User):
        """Process PPI sheet: ['Project Name', 'Completion Criteria for the quarter', 'Responsibility', 'Start Date', 'End Date', 'Steps', 'W1', 'W2', ...]"""
        errors = []

        # Header is at row 6, data starts at row 7
        for row_num, row in enumerate(sheet.iter_rows(min_row=7, values_only=True), start=7):
            if not any(row):  # Skip empty rows
                continue

            try:
                # Format: ['', 'Project Name', 'Completion Criteria for the quarter', 'Responsibility', 'Start Date', 'End Date', 'Steps', 'W1', 'W2', ...]
                _, project_name, completion_criteria, responsibility, start_date, end_date = row[:6]

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
                            errors.append(f"PPI Row {row_num}: User '{responsibility}' not found")
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
                            errors.append(f"PPI Row {row_num}: Invalid start date format")
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
                            errors.append(f"PPI Row {row_num}: Invalid end date format")
                            continue

                # Create PPI project
                ppi_project = PPIProject.objects.create(
                    quarterly_plan=quarterly_plan,
                    name=str(project_name).strip(),
                    completion_criteria=str(completion_criteria).strip() if completion_criteria else '',
                    responsible_user=responsible_user,
                    start_date=parsed_start_date or datetime.date.today(),
                    end_date=parsed_end_date or datetime.date.today()
                )

                # Process weekly tasks starting from column 8 (W1)
                week_task_errors = self._process_weekly_tasks(ppi_project, row, row_num, User)
                errors.extend(week_task_errors)

            except Exception as e:
                errors.append(f"PPI Row {row_num}: {str(e)}")

        return errors

    def _process_weekly_tasks(self, ppi_project, row, row_num, User):
        """Process weekly tasks from PPI row and create PPITask and Action records"""
        errors = []

        try:
            # Weekly tasks start from column 8 (index 7) - W1, W2, W3, etc.
            # Process up to 13 weeks in a quarter
            for week_num in range(1, 14):  # Week 1-13
                col_index = 6 + week_num  # Column 7 is Steps, so W1 starts at column 8 (index 7)

                if col_index < len(row):
                    weekly_task_content = row[col_index]

                    if weekly_task_content and str(weekly_task_content).strip():
                        # Split multiple tasks in one cell by common separators
                        task_separators = ['\n', '\r\n', '•', '–', '-', '|', ';']
                        tasks = [str(weekly_task_content).strip()]

                        # Split by separators to handle multiple tasks in one cell
                        for separator in task_separators:
                            new_tasks = []
                            for task in tasks:
                                if separator in task:
                                    split_tasks = [t.strip() for t in task.split(separator) if t.strip()]
                                    new_tasks.extend(split_tasks)
                                else:
                                    new_tasks.append(task)
                            tasks = new_tasks

                        # Create PPITask and Action for each task
                        for task_description in tasks:
                            if len(task_description.strip()) > 5:  # Only create for meaningful tasks
                                try:
                                    # Create PPITask
                                    ppi_task = PPITask.objects.create(
                                        project=ppi_project,
                                        task_description=task_description.strip(),
                                        week_number=week_num,
                                        assigned_to=ppi_project.responsible_user
                                    )

                                    # Calculate due date for this week
                                    # Assume quarter starts from project start_date
                                    week_due_date = ppi_project.start_date + datetime.timedelta(weeks=week_num-1, days=6)

                                    # Create corresponding Action
                                    from implement.models import Action
                                    Action.objects.create(
                                        team=ppi_project.quarterly_plan.team,
                                        source='ppi',
                                        ppi_task=ppi_task,
                                        action=f"[Week {week_num}] {task_description.strip()}",
                                        priority='medium',
                                        assigned_to=ppi_project.responsible_user,
                                        original_due_date=week_due_date,
                                        status='not_started',
                                        created_by=ppi_project.responsible_user,
                                        comments=f"From PPI project: {ppi_project.name}"
                                    )

                                except Exception as e:
                                    errors.append(f"PPI Row {row_num}, Week {week_num}: Error creating task - {str(e)}")

        except Exception as e:
            errors.append(f"PPI Row {row_num}: Error processing weekly tasks - {str(e)}")

        return errors


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

    def get(self, request, *args, **kwargs):
        # Check if this is an AJAX request for JSON response
        if request.headers.get('accept') == 'application/json' or 'application/json' in request.headers.get('accept', ''):
            return self.get_json_response()
        else:
            # Return HTML template response
            return super().get(request, *args, **kwargs)

    def get_json_response(self):
        user = self.request.user

        # Get plans for teams managed by user or where user is a team member
        if user.role == 'general':
            # For general users, show plans for teams they manage
            plans = AnnualPlan.objects.filter(
                team__manager=user
            ).select_related('team', 'financial_year', 'uploaded_by').order_by('-uploaded_at')
        else:
            # For admin/coordinator, show all plans
            plans = AnnualPlan.objects.all().select_related('team', 'financial_year', 'uploaded_by').order_by('-uploaded_at')

        # Convert plans to JSON format
        plans_data = []
        for plan in plans:
            plans_data.append({
                'id': plan.id,
                'team': plan.team.name,
                'plan_year': plan.financial_year.year,
                'file_name': plan.file_name,
                'uploaded_date': plan.uploaded_at.strftime('%b %d, %Y %H:%M'),
                'status': plan.get_upload_status_display(),
                'uploaded_by': plan.uploaded_by.get_full_name() if plan.uploaded_by else 'Unknown'
            })

        return JsonResponse({
            'success': True,
            'plans': plans_data
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get plans for teams managed by user
        if user.role == 'general':
            plans = AnnualPlan.objects.filter(
                team__manager=user
            ).select_related('team', 'financial_year', 'uploaded_by').order_by('-uploaded_at')
        else:
            plans = AnnualPlan.objects.all().select_related('team', 'financial_year', 'uploaded_by').order_by('-uploaded_at')

        context['plans'] = plans
        return context


class QuarterlyPlanHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'plans/quarterly_history.html'

    def get(self, request, *args, **kwargs):
        # Check if this is an AJAX request for JSON response
        if request.headers.get('accept') == 'application/json' or 'application/json' in request.headers.get('accept', ''):
            return self.get_json_response()
        else:
            # Return HTML template response
            return super().get(request, *args, **kwargs)

    def get_json_response(self):
        user = self.request.user

        # Get plans for teams managed by user or where user is a team member
        if user.role == 'general':
            # For general users, show plans for teams they manage
            plans = QuarterlyPlan.objects.filter(
                team__manager=user
            ).select_related('team', 'financial_year', 'uploaded_by').order_by('-uploaded_at')
        else:
            # For admin/coordinator, show all plans
            plans = QuarterlyPlan.objects.all().select_related('team', 'financial_year', 'uploaded_by').order_by('-uploaded_at')

        # Convert plans to JSON format
        plans_data = []
        for plan in plans:
            # Format quarter as "FY XX-XX – QX"
            fy_start = plan.financial_year.start_date.year
            fy_str = f'FY {str(fy_start)[2:]}-{str(fy_start + 1)[2:]} – Q{plan.quarter}'

            plans_data.append({
                'id': plan.id,
                'team': plan.team.name,
                'quarter': fy_str,
                'file_name': plan.file_name,
                'uploaded_date': plan.uploaded_at.strftime('%b %d, %Y %H:%M'),
                'status': plan.get_upload_status_display(),
                'uploaded_by': plan.uploaded_by.get_full_name() if plan.uploaded_by else 'Unknown'
            })

        return JsonResponse({
            'success': True,
            'plans': plans_data
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get plans for teams managed by user
        if user.role == 'general':
            plans = QuarterlyPlan.objects.filter(
                team__manager=user
            ).select_related('team', 'financial_year', 'uploaded_by').order_by('-uploaded_at')
        else:
            plans = QuarterlyPlan.objects.all().select_related('team', 'financial_year', 'uploaded_by').order_by('-uploaded_at')

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

