from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, FormView
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone
from django.db import models
import openpyxl
import os
import datetime
from .models import (
    AnnualPlan, QuarterlyPlan, FinancialYear,
    GPIParameter, PPIProject, PPITask,
    GPIMilestone, PPIMilestone,
    AnnualGPIParameter, AnnualPPIProject,
    AnnualPlanUploadHistory, QuarterlyPlanUploadHistory,
    GPIWeeklyRecord, GPIMonthlyRecord,
    PPIWeeklyRecord, PPIMonthlyRecord
)
from organizations.models import Team
from django.contrib.auth import get_user_model
from accounts.utils import get_effective_user


class PlanDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'plans/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_effective_user(self.request)

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

        # Get parameters with correct names (JS sends team_id/financial_year_id)
        team_id = request.POST.get('team_id') or request.POST.get('team')
        financial_year_id = request.POST.get('financial_year_id') or request.POST.get('plan_year_id') or request.POST.get('financial_year')
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
            # Check if plan already exists for this team/year
            existing_plan = AnnualPlan.objects.filter(team=team, financial_year=financial_year).first()

            if existing_plan:
                # Re-upload: Archive the old file by renaming it with timestamp
                if existing_plan.file_path:
                    old_path = existing_plan.file_path.path
                    if os.path.exists(old_path):
                        # Rename old file with timestamp
                        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                        base_name = os.path.basename(old_path)
                        name, ext = os.path.splitext(base_name)
                        new_name = f"{name}_archived_{timestamp}{ext}"
                        new_path = os.path.join(os.path.dirname(old_path), new_name)
                        os.rename(old_path, new_path)

                        # Update all previous upload history records to point to the archived file
                        old_file_path = existing_plan.file_path.name  # e.g., 'annual_plans/file.xlsx'
                        new_file_path = f"annual_plans/{new_name}"
                        AnnualPlanUploadHistory.objects.filter(
                            annual_plan=existing_plan,
                            file_path=old_file_path
                        ).update(file_path=new_file_path)

                # Update existing plan with new file
                existing_plan.file_name = uploaded_file.name
                existing_plan.file_path = uploaded_file
                existing_plan.upload_status = 'processing'
                existing_plan.uploaded_by = request.user
                existing_plan.error_log = ''
                existing_plan.save()
                annual_plan = existing_plan
            else:
                # Create new plan
                annual_plan = AnnualPlan.objects.create(
                    team=team,
                    financial_year=financial_year,
                    file_name=uploaded_file.name,
                    file_path=uploaded_file,
                    upload_status='processing',
                    uploaded_by=request.user,
                    error_log=''
                )

            # Parse and import data from Excel
            errors = self._parse_annual_plan(annual_plan, uploaded_file)

            # Count total records
            # FPI has been removed from the system
            total_gpis = AnnualGPIParameter.objects.filter(annual_plan=annual_plan).count()
            total_ppis = AnnualPPIProject.objects.filter(annual_plan=annual_plan).count()
            total_records = total_gpis + total_ppis
            error_records = len(errors)
            processed_records = total_records

            if errors:
                annual_plan.upload_status = 'failed'
                annual_plan.error_log = '\n'.join(errors)
                annual_plan.save()

                # Create history record for failed upload
                AnnualPlanUploadHistory.objects.create(
                    annual_plan=annual_plan,
                    file_name=uploaded_file.name,
                    file_path=annual_plan.file_path,
                    upload_status='failed',
                    error_log='\n'.join(errors),
                    uploaded_by=request.user,
                    total_records=total_records,
                    processed_records=processed_records,
                    error_records=error_records
                )

                error_message = f'Upload completed with errors: {errors[0]}'
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error': error_message
                    })
                else:
                    messages.error(request, error_message)
                    return redirect('plans:dashboard')

            # Mark as successful
            annual_plan.upload_status = 'successful'
            annual_plan.save()

            # Create history record for successful upload
            AnnualPlanUploadHistory.objects.create(
                annual_plan=annual_plan,
                file_name=uploaded_file.name,
                file_path=annual_plan.file_path,
                upload_status='successful',
                error_log='',
                uploaded_by=request.user,
                total_records=total_records,
                processed_records=processed_records,
                error_records=0
            )

            success_message = 'Annual plan uploaded and processed successfully.'
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

    def _parse_annual_plan(self, annual_plan, uploaded_file):
        """Parse annual plan Excel file and import FPI, GPI, PPI data"""
        errors = []
        User = get_user_model()

        try:
            # Load workbook
            workbook = openpyxl.load_workbook(uploaded_file, data_only=True)

            # Clear existing data for this annual plan
            # FPI has been removed from the system
            AnnualGPIParameter.objects.filter(annual_plan=annual_plan).delete()
            AnnualPPIProject.objects.filter(annual_plan=annual_plan).delete()

            # FPI processing has been removed

            # Process GPI sheet (accept both 'GPI' and 'GPIs')
            gpi_sheet = None
            if 'GPI' in workbook.sheetnames:
                gpi_sheet = workbook['GPI']
            elif 'GPIs' in workbook.sheetnames:
                gpi_sheet = workbook['GPIs']

            if gpi_sheet:
                gpi_errors = self._process_annual_gpi_sheet(gpi_sheet, annual_plan, User)
                errors.extend(gpi_errors)
            else:
                errors.append("Missing GPI or GPIs sheet in uploaded file")

            # Process PPI sheet (accept both 'PPI' and 'PPIs')
            ppi_sheet = None
            if 'PPI' in workbook.sheetnames:
                ppi_sheet = workbook['PPI']
            elif 'PPIs' in workbook.sheetnames:
                ppi_sheet = workbook['PPIs']

            if ppi_sheet:
                ppi_errors = self._process_annual_ppi_sheet(ppi_sheet, annual_plan, User)
                errors.extend(ppi_errors)
            else:
                errors.append("Missing PPI or PPIs sheet in uploaded file")

        except Exception as e:
            errors.append(f"Error reading Excel file: {str(e)}")

        return errors

    def _process_annual_fpi_sheet(self, sheet, annual_plan, User):
        """FPI has been removed from the system - this method is deprecated"""
        # FPI processing has been removed
        return []

    def _process_annual_gpi_sheet(self, sheet, annual_plan, User):
        """Process GPIs sheet: Row 4 headers, data starts at row 5"""
        errors = []

        # Expected columns: Goal Progress Indicators, Cumulation Type, Indicator Type, Tracking Type, Responsibility, 1-Year Goals, Q1-Q4 Budgets
        for row_num, row in enumerate(sheet.iter_rows(min_row=5, values_only=True), start=5):
            if not any(row):  # Skip empty rows
                continue

            try:
                # Skip the first empty column
                _, name, cumulation_type, indicator_type, tracking_type, responsibility, annual_goal, q1_budget, q2_budget, q3_budget, q4_budget = row[:11]

                if not name:
                    continue

                # Find responsible user
                responsible_user = None
                if responsibility:
                    responsible_user = User.objects.filter(
                        models.Q(username__iexact=responsibility) |
                        models.Q(first_name__iexact=responsibility) |
                        models.Q(last_name__iexact=responsibility)
                    ).first()

                # Map values to model choices
                cumulation_mapping = {'Sum': 'sum', 'Average': 'average', 'NA': 'na'}
                indicator_mapping = {'Outcome': 'outcome', 'Activity': 'activity'}
                tracking_mapping = {'Weekly': 'weekly', 'Monthly': 'monthly'}

                cumulation_value = cumulation_mapping.get(str(cumulation_type).strip(), 'na')
                indicator_value = indicator_mapping.get(str(indicator_type).strip(), 'outcome')
                tracking_value = tracking_mapping.get(str(tracking_type).strip(), 'monthly')

                # Create GPI parameter
                AnnualGPIParameter.objects.create(
                    annual_plan=annual_plan,
                    name=str(name).strip(),
                    cumulation_type=cumulation_value,
                    indicator_type=indicator_value,
                    tracking_type=tracking_value,
                    responsible_user=responsible_user,
                    annual_goal=self._parse_decimal(annual_goal),
                    q1_goal=self._parse_decimal(q1_budget),
                    q2_goal=self._parse_decimal(q2_budget),
                    q3_goal=self._parse_decimal(q3_budget),
                    q4_goal=self._parse_decimal(q4_budget)
                )

            except Exception as e:
                errors.append(f"GPI Row {row_num}: {str(e)}")

        return errors

    def _process_annual_ppi_sheet(self, sheet, annual_plan, User):
        """Process PPIs sheet: Row 4 headers, data starts at row 5"""
        errors = []

        # Expected columns: Project Name, Completion Criteria, Responsibility, Start Date, End Date, 1-Year Goals, Q1-Q4 Budgets
        for row_num, row in enumerate(sheet.iter_rows(min_row=5, values_only=True), start=5):
            if not any(row):  # Skip empty rows
                continue

            try:
                # Skip the first empty column
                _, project_name, completion_criteria, responsibility, start_date, end_date, annual_goal, q1_goal, q2_goal, q3_goal, q4_goal = row[:11]

                if not project_name:
                    continue

                # Find responsible user
                responsible_user = None
                if responsibility:
                    responsible_user = User.objects.filter(
                        models.Q(username__iexact=responsibility) |
                        models.Q(first_name__iexact=responsibility) |
                        models.Q(last_name__iexact=responsibility)
                    ).first()

                # Parse dates
                start_date_parsed = self._parse_date(start_date)
                end_date_parsed = self._parse_date(end_date)

                # Create PPI project
                AnnualPPIProject.objects.create(
                    annual_plan=annual_plan,
                    name=str(project_name).strip(),
                    completion_criteria=str(completion_criteria).strip() if completion_criteria else '',
                    responsible_user=responsible_user,
                    start_date=start_date_parsed,
                    end_date=end_date_parsed,
                    annual_goal=str(annual_goal).strip() if annual_goal else '',
                    q1_goal=str(q1_goal).strip() if q1_goal else '',
                    q2_goal=str(q2_goal).strip() if q2_goal else '',
                    q3_goal=str(q3_goal).strip() if q3_goal else '',
                    q4_goal=str(q4_goal).strip() if q4_goal else ''
                )

            except Exception as e:
                errors.append(f"PPI Row {row_num}: {str(e)}")

        return errors

    def _parse_decimal(self, value):
        """Parse decimal value from Excel cell"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except:
            return None

    def _parse_date(self, value):
        """Parse date value from Excel cell"""
        if value is None or value == '':
            return None
        if isinstance(value, datetime.date):
            return value
        try:
            return datetime.datetime.strptime(str(value), '%Y-%m-%d').date()
        except:
            return None


class AnnualPlanTemplateDownloadView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        # Path to the template file
        template_path = os.path.join(settings.BASE_DIR, 'Annual Plan Template.xlsx')

        # Check if template file exists
        if not os.path.exists(template_path):
            return HttpResponse("Template file not found", status=404)

        # Read the template file
        with open(template_path, 'rb') as f:
            response = HttpResponse(
                f.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="Annual_Plan_Template.xlsx"'

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
        confirm_delete = request.POST.get('confirm_delete', 'false') == 'true'

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

        # Check if a plan already exists for this quarter
        existing_plan = QuarterlyPlan.objects.filter(
            team=team,
            financial_year=financial_year,
            quarter=quarter_num
        ).first()

        # If plan exists and user hasn't confirmed deletion, ask for confirmation
        if existing_plan and not confirm_delete:
            return JsonResponse({
                'success': False,
                'requires_confirmation': True,
                'error': f'A quarterly plan already exists for {team.name} - {financial_year.year} Q{quarter_num}. All data (plan & actual) related to the old plan including FPI, GPI, PPI, all associated actions, issues, and review data (meetings, notes, decisions, action items) will be deleted permanently. Do you want to continue?'
            })

        # If existing plan and confirmed deletion, delete all related data
        if existing_plan and confirm_delete:
            from django.db import transaction
            from implement.models import Action

            with transaction.atomic():
                # Archive the old file before updating the plan
                if existing_plan.file_path:
                    old_path = existing_plan.file_path.path
                    if os.path.exists(old_path):
                        # Rename old file with timestamp
                        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                        base_name = os.path.basename(old_path)
                        name, ext = os.path.splitext(base_name)
                        new_name = f"{name}_archived_{timestamp}{ext}"
                        new_path = os.path.join(os.path.dirname(old_path), new_name)
                        os.rename(old_path, new_path)

                        # Update all previous upload history records to point to the archived file
                        old_file_path = existing_plan.file_path.name  # e.g., 'quarterly_plans/file.xlsx'
                        new_file_path = f"quarterly_plans/{new_name}"
                        QuarterlyPlanUploadHistory.objects.filter(
                            quarterly_plan=existing_plan,
                            file_path=old_file_path
                        ).update(file_path=new_file_path)

                # Get all PPI projects for this plan
                ppi_projects = PPIProject.objects.filter(quarterly_plan=existing_plan)

                # For each PPI project, get all tasks and their associated actions
                for project in ppi_projects:
                    tasks = project.tasks.all()
                    for task in tasks:
                        # Get the action associated with this task
                        action = Action.objects.filter(ppi_task=task).first()
                        if action:
                            # Delete the action and all its hierarchical sub-actions
                            # Django will handle cascade deletion of sub_actions
                            action.delete()

                # FPI has been removed from the system

                # Get all GPI parameters and their milestones (will be cascade deleted)
                GPIParameter.objects.filter(quarterly_plan=existing_plan).delete()

                # Delete all PPI projects and their tasks (will be cascade deleted)
                ppi_projects.delete()

                # Delete all review meetings for this team, financial year, and quarter
                # This will cascade delete ReviewNotes, ReviewDecisions, and ReviewActionItems
                from reviews.models import ReviewMeeting
                ReviewMeeting.objects.filter(
                    team=existing_plan.team,
                    financial_year=existing_plan.financial_year,
                    quarter_number=existing_plan.quarter
                ).delete()

                # Update the existing plan with new file (don't delete it to preserve upload history)
                existing_plan.file_name = uploaded_file.name
                existing_plan.file_path = uploaded_file
                existing_plan.upload_status = 'processing'
                existing_plan.uploaded_by = request.user
                existing_plan.error_log = ''
                existing_plan.save()
                quarterly_plan = existing_plan
        else:
            # Create new plan or update existing one
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

        # Process and save the quarterly plan
        try:

            # Process the Excel file to create FPI, GPI, and PPI records
            processing_errors = self._process_quarterly_excel_file(quarterly_plan, uploaded_file)

            # Count total records
            # FPI has been removed from the system
            total_gpis = GPIParameter.objects.filter(quarterly_plan=quarterly_plan).count()
            total_ppis = PPIProject.objects.filter(quarterly_plan=quarterly_plan).count()
            total_records = total_gpis + total_ppis
            error_records = len(processing_errors)
            processed_records = total_records

            if processing_errors:
                quarterly_plan.upload_status = 'failed'
                quarterly_plan.error_log = '\n'.join(processing_errors)
                quarterly_plan.save()

                # Create history record for failed upload
                QuarterlyPlanUploadHistory.objects.create(
                    quarterly_plan=quarterly_plan,
                    file_name=uploaded_file.name,
                    file_path=quarterly_plan.file_path,
                    upload_status='failed',
                    error_log='\n'.join(processing_errors),
                    uploaded_by=request.user,
                    total_records=total_records,
                    processed_records=processed_records,
                    error_records=error_records
                )

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

                # Create history record for successful upload
                QuarterlyPlanUploadHistory.objects.create(
                    quarterly_plan=quarterly_plan,
                    file_name=uploaded_file.name,
                    file_path=quarterly_plan.file_path,
                    upload_status='successful',
                    error_log='',
                    uploaded_by=request.user,
                    total_records=total_records,
                    processed_records=processed_records,
                    error_records=0
                )

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
            # FPI has been removed from the system
            GPIParameter.objects.filter(quarterly_plan=quarterly_plan).delete()
            PPIProject.objects.filter(quarterly_plan=quarterly_plan).delete()

            # FPI processing has been removed

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

            # Process PPI-M sheet (monthly PPI tracking)
            if 'PPI-M' in workbook.sheetnames:
                ppi_m_errors = self._process_ppi_sheet(workbook['PPI-M'], quarterly_plan, User, 'monthly')
                errors.extend(ppi_m_errors)
            else:
                errors.append("Missing PPI-M sheet in uploaded file")

            # Process PPI-W sheet (weekly PPI tracking)
            if 'PPI-W' in workbook.sheetnames:
                ppi_w_errors = self._process_ppi_sheet(workbook['PPI-W'], quarterly_plan, User, 'weekly')
                errors.extend(ppi_w_errors)
            else:
                errors.append("Missing PPI-W sheet in uploaded file")

        except Exception as e:
            errors.append(f"Error reading Excel file: {str(e)}")

        return errors

    def _process_fpi_sheet(self, sheet, quarterly_plan, User):
        """FPI has been removed from the system - this method is deprecated"""
        # FPI processing has been removed
        return []

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

                # FPI processing has been removed from the system
                pass

            except Exception as e:
                errors.append(f"FPI Row {row_num}: {str(e)}")

        return errors

    def _process_gpi_sheet(self, sheet, quarterly_plan, User, tracking_type):
        """Process GPI sheet with full weekly/monthly milestone extraction"""
        errors = []

        # Header is at row 4, data starts at row 5
        for row_num, row in enumerate(sheet.iter_rows(min_row=5, values_only=True), start=5):
            if not any(row):  # Skip empty rows
                continue

            try:
                # New format: ['', 'Goal Progress Indicators', 'Cumulation Type', 'Indicator Type', 'Responsibility', 'Annual Goal', 'YTD till last quarter', 'Next Quarter Budget', 'Next Quarter Goal', 'W1/M1', ...]
                if len(row) < 9:
                    continue

                name = row[1] if len(row) > 1 else ''
                cumulation_type = row[2] if len(row) > 2 else ''
                indicator_type = row[3] if len(row) > 3 else ''
                responsibility = row[4] if len(row) > 4 else ''
                quarter_goal = row[8] if len(row) > 8 else 0  # Next Quarter Goal

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

                # Map cumulation type
                cumulation_str = str(cumulation_type).lower().strip()
                if 'sum' in cumulation_str:
                    cumulation_value = 'sum'
                elif 'average' in cumulation_str or 'avg' in cumulation_str:
                    cumulation_value = 'average'
                else:
                    cumulation_value = 'na'

                # Map indicator type
                indicator_str = str(indicator_type).lower().strip()
                if 'outcome' in indicator_str:
                    indicator_type_value = 'outcome'
                elif 'activity' in indicator_str:
                    indicator_type_value = 'activity'
                else:
                    indicator_type_value = 'outcome'  # Default

                # Create GPI parameter
                gpi_parameter = GPIParameter.objects.create(
                    quarterly_plan=quarterly_plan,
                    name=str(name).strip(),
                    cumulation_type=cumulation_value,
                    unit_of_measure='',  # Unit of measure not present in this format
                    tracking_type=tracking_type,
                    indicator_type=indicator_type_value,
                    responsible_user=responsible_user,
                    quarter_goal=float(quarter_goal) if quarter_goal else 0
                )

                # Extract weekly/monthly milestone data
                # W1/M1 starts at index 9 (after Next Quarter Goal)
                if tracking_type == 'weekly':
                    # Process W1-W13 columns (starting from index 9)
                    for week_num in range(1, 14):  # W1 to W13
                        col_index = 8 + week_num  # W1 is at index 9, so 8 + 1 = 9
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
                    # Process M1-M3 columns (starting from index 9)
                    for month_num in range(1, 4):  # Month 1 to Month 3
                        col_index = 8 + month_num  # M1 is at index 9, so 8 + 1 = 9
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

    def _process_ppi_sheet(self, sheet, quarterly_plan, User, tracking_type):
        """Process PPI sheet with weekly or monthly tracking: ['Project Name', 'Completion Criteria for the quarter', 'Responsibility', 'Start Date', 'End Date', 'Steps', 'W1/M1', 'W2/M2', ...]"""
        errors = []

        # Header is at row 4, data starts at row 5
        for row_num, row in enumerate(sheet.iter_rows(min_row=5, values_only=True), start=5):
            if not any(row):  # Skip empty rows
                continue

            try:
                # Format: ['', 'Project Name', 'Completion Criteria for the quarter', 'Responsibility', 'Start Date', 'End Date', 'Steps', 'W1', 'W2', ...]
                if len(row) < 7:
                    continue

                project_name = row[1] if len(row) > 1 else ''
                completion_criteria = row[2] if len(row) > 2 else ''
                responsibility = row[3] if len(row) > 3 else ''
                start_date = row[4] if len(row) > 4 else None
                end_date = row[5] if len(row) > 5 else None
                steps = row[6] if len(row) > 6 else ''

                if not project_name or project_name == 'None':
                    continue  # Skip rows without project name

                # Find responsible user by email
                responsible_user = None
                if responsibility:
                    # Convert to string first in case it's a number
                    responsibility_str = str(responsibility).strip() if responsibility else ''
                    if responsibility_str:
                        try:
                            responsible_user = User.objects.get(email__iexact=responsibility_str)
                        except User.DoesNotExist:
                            try:
                                responsible_user = User.objects.get(username__iexact=responsibility_str)
                            except User.DoesNotExist:
                                errors.append(f"PPI Row {row_num}: User '{responsibility_str}' not found")
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
                    tracking_type=tracking_type,
                    responsible_user=responsible_user,
                    start_date=parsed_start_date or datetime.date.today(),
                    end_date=parsed_end_date or datetime.date.today()
                )

                # Process weekly/monthly tasks starting from column 8 (W1/M1)
                task_errors = self._process_ppi_tasks(ppi_project, row, row_num, User, tracking_type)
                errors.extend(task_errors)

            except Exception as e:
                errors.append(f"PPI Row {row_num}: {str(e)}")

        return errors

    def _process_ppi_tasks(self, ppi_project, row, row_num, User, tracking_type):
        """Process weekly or monthly tasks from PPI row and create PPITask and Action records"""
        errors = []
        # Filter out numeric values that shouldn't be tasks

        try:
            # Tasks start from column 8 (index 7) - W1/M1, W2/M2, W3/M3, etc.
            # Process up to 13 weeks or 3 months in a quarter
            max_periods = 13 if tracking_type == 'weekly' else 3
            for period_num in range(1, max_periods + 1):
                col_index = 6 + period_num  # Column 7 is Steps, so W1/M1 starts at column 8 (index 7)

                if col_index < len(row):
                    task_content = row[col_index]

                    # Skip None, empty strings, and numeric values (which shouldn't be tasks)
                    if task_content is None or task_content == '':
                        continue

                    # Convert to string and check if it's meaningful
                    task_content_str = str(task_content).strip()

                    # Skip if empty or if it's just a number (numeric tasks don't make sense)
                    if not task_content_str or task_content_str.replace('.', '').replace('-', '').isdigit():
                        continue

                    # Split multiple tasks in one cell by common separators
                    task_separators = ['\n', '\r\n', '•', '–', '-', '|', ';']
                    tasks = [task_content_str]

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
                        # Ensure task_description is a string and has meaningful content
                        if not isinstance(task_description, str):
                            task_description = str(task_description)

                        task_description = task_description.strip()

                        # Skip numeric-only tasks and very short tasks
                        if not task_description or len(task_description) <= 5:
                            continue

                        # Skip if it's just a number
                        if task_description.replace('.', '').replace('-', '').isdigit():
                            continue

                        # Create PPITask and Action for this meaningful task
                        try:
                            # Create PPITask (week_number field stores period number - week or month)
                            ppi_task = PPITask.objects.create(
                                project=ppi_project,
                                task_description=task_description.strip(),
                                week_number=period_num,  # Stores week or month number
                                assigned_to=ppi_project.responsible_user
                            )

                            # Calculate due date based on tracking type
                            quarter_start = ppi_project.quarterly_plan.quarter_start_date
                            if tracking_type == 'weekly':
                                # For weekly: add weeks
                                due_date = quarter_start + datetime.timedelta(weeks=period_num-1, days=6)
                            else:
                                # For monthly: add months (approximate with 30 days per month, then find end of month)
                                import calendar
                                temp_date = quarter_start + datetime.timedelta(days=30*period_num)
                                last_day = calendar.monthrange(temp_date.year, temp_date.month)[1]
                                due_date = temp_date.replace(day=last_day)

                            # Create corresponding Action
                            from implement.models import Action
                            from django.db import connection
                            period_label = "Week" if tracking_type == 'weekly' else "Month"

                            # Temporarily disable foreign key checks for SQLite to avoid constraint errors
                            with connection.cursor() as cursor:
                                cursor.execute("PRAGMA foreign_keys=OFF")

                            try:
                                Action.objects.create(
                                    team=ppi_project.quarterly_plan.team,
                                    source='ppi',
                                    ppi_task=ppi_task,
                                    action=f"[{period_label} {period_num}] {task_description.strip()}",
                                    priority='medium',
                                    assigned_to=ppi_project.responsible_user,
                                    original_due_date=due_date,
                                    status='not_started',
                                    created_by=ppi_project.responsible_user,
                                    comments=f"From PPI project: {ppi_project.name}"
                                )
                            finally:
                                # Re-enable foreign key checks
                                with connection.cursor() as cursor:
                                    cursor.execute("PRAGMA foreign_keys=ON")

                        except Exception as e:
                            import traceback
                            tb = traceback.format_exc()
                            period_label = "Week" if tracking_type == 'weekly' else "Month"
                            errors.append(f"PPI-{tracking_type[0].upper()} Row {row_num}, {period_label} {period_num}: Error creating task - {str(e)}\nTraceback: {tb}")

        except Exception as e:
            errors.append(f"PPI-{tracking_type[0].upper()} Row {row_num}: Error processing tasks - {str(e)}")

        return errors


class QuarterlyPlanTemplateDownloadView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        # Serve the actual template file from the project folder
        template_path = os.path.join(settings.BASE_DIR, 'Quarter Plan Template.xlsx')

        if os.path.exists(template_path):
            with open(template_path, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename="Quarter Plan Template.xlsx"'
                return response
        else:
            messages.error(request, 'Template file not found.')
            return redirect('plans:dashboard')


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

        # Get upload history for teams managed by user or where user is a team member
        if user.role == 'general':
            # For general users, show history for teams they manage
            history = AnnualPlanUploadHistory.objects.filter(
                annual_plan__team__manager=user
            ).select_related('annual_plan__team', 'annual_plan__financial_year', 'uploaded_by').order_by('-uploaded_at')
        else:
            # For admin/coordinator, show all history
            history = AnnualPlanUploadHistory.objects.all().select_related('annual_plan__team', 'annual_plan__financial_year', 'uploaded_by').order_by('-uploaded_at')

        # Convert history to JSON format
        plans_data = []
        for record in history:
            plans_data.append({
                'id': record.id,
                'team': record.annual_plan.team.name,
                'plan_year': record.annual_plan.financial_year.year,
                'file_name': record.file_name,
                'uploaded_date': record.uploaded_at.strftime('%b %d, %Y %H:%M'),
                'status': record.get_upload_status_display(),
                'uploaded_by': record.uploaded_by.get_full_name() if record.uploaded_by else 'Unknown'
            })

        return JsonResponse({
            'success': True,
            'plans': plans_data
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get upload history for teams managed by user
        if user.role == 'general':
            history = AnnualPlanUploadHistory.objects.filter(
                annual_plan__team__manager=user
            ).select_related('annual_plan__team', 'annual_plan__financial_year', 'uploaded_by').order_by('-uploaded_at')
        else:
            history = AnnualPlanUploadHistory.objects.all().select_related('annual_plan__team', 'annual_plan__financial_year', 'uploaded_by').order_by('-uploaded_at')

        context['plans'] = history
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

        # Get upload history for teams managed by user or where user is a team member
        if user.role == 'general':
            # For general users, show history for teams they manage
            history = QuarterlyPlanUploadHistory.objects.filter(
                quarterly_plan__team__manager=user
            ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year', 'uploaded_by').order_by('-uploaded_at')
        else:
            # For admin/coordinator, show all history
            history = QuarterlyPlanUploadHistory.objects.all().select_related('quarterly_plan__team', 'quarterly_plan__financial_year', 'uploaded_by').order_by('-uploaded_at')

        # Convert history to JSON format
        plans_data = []
        for record in history:
            # Format quarter as "FY XX-XX – QX"
            fy_start = record.quarterly_plan.financial_year.start_date.year
            fy_str = f'FY {str(fy_start)[2:]}-{str(fy_start + 1)[2:]} – Q{record.quarterly_plan.quarter}'

            plans_data.append({
                'id': record.id,
                'team': record.quarterly_plan.team.name,
                'quarter': fy_str,
                'file_name': record.file_name,
                'uploaded_date': record.uploaded_at.strftime('%b %d, %Y %H:%M'),
                'status': record.get_upload_status_display(),
                'uploaded_by': record.uploaded_by.get_full_name() if record.uploaded_by else 'Unknown'
            })

        return JsonResponse({
            'success': True,
            'plans': plans_data
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get upload history for teams managed by user
        if user.role == 'general':
            history = QuarterlyPlanUploadHistory.objects.filter(
                quarterly_plan__team__manager=user
            ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year', 'uploaded_by').order_by('-uploaded_at')
        else:
            history = QuarterlyPlanUploadHistory.objects.all().select_related('quarterly_plan__team', 'quarterly_plan__financial_year', 'uploaded_by').order_by('-uploaded_at')

        context['plans'] = history
        return context


class PlanFileDownloadView(LoginRequiredMixin, TemplateView):
    def get(self, request, plan_id, plan_type):
        user = request.user

        if plan_type == 'annual':
            # Allow both team managers and members to download
            plan = AnnualPlan.objects.filter(id=plan_id).filter(
                models.Q(team__manager=user) |
                models.Q(team__members__member=user, team__members__is_active=True)
            ).first()
            if not plan:
                messages.error(request, 'Plan not found or access denied.')
                return redirect('plans:dashboard')
            file_path = plan.file_path
        else:
            # Allow both team managers and members to download
            plan = QuarterlyPlan.objects.filter(id=plan_id).filter(
                models.Q(team__manager=user) |
                models.Q(team__members__member=user, team__members__is_active=True)
            ).first()
            if not plan:
                messages.error(request, 'Plan not found or access denied.')
                return redirect('plans:dashboard')
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


class PlanHistoryFileDownloadView(LoginRequiredMixin, TemplateView):
    def get(self, request, history_id, plan_type):
        user = request.user

        if plan_type == 'annual':
            # Allow both team managers and members to download
            history = AnnualPlanUploadHistory.objects.filter(id=history_id).filter(
                models.Q(annual_plan__team__manager=user) |
                models.Q(annual_plan__team__members__member=user, annual_plan__team__members__is_active=True)
            ).first()
            if not history:
                messages.error(request, 'File not found or access denied.')
                return redirect('plans:dashboard')
            file_path = history.file_path
            file_name = history.file_name
        else:
            # Allow both team managers and members to download
            history = QuarterlyPlanUploadHistory.objects.filter(id=history_id).filter(
                models.Q(quarterly_plan__team__manager=user) |
                models.Q(quarterly_plan__team__members__member=user, quarterly_plan__team__members__is_active=True)
            ).first()
            if not history:
                messages.error(request, 'File not found or access denied.')
                return redirect('plans:dashboard')
            file_path = history.file_path
            file_name = history.file_name

        if file_path and os.path.exists(file_path.path):
            response = HttpResponse(
                file_path.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
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

