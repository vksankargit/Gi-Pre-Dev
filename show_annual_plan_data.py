import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')
django.setup()

from plans.models import AnnualPlan, AnnualFPIParameter, AnnualGPIParameter, AnnualPPIProject, AnnualPlanUploadHistory

# Get all annual plans
plans = AnnualPlan.objects.all().select_related('team', 'financial_year', 'uploaded_by')

# Output to file with UTF-8 encoding
with open('annual_plan_data.txt', 'w', encoding='utf-8') as f:
    original_stdout = sys.stdout
    sys.stdout = f

    for plan in plans:
        print('=' * 80)
        print(f'ANNUAL PLAN: {plan.team.name} - {plan.financial_year.year}')
        print(f'File: {plan.file_name}')
        print(f'Status: {plan.upload_status}')
        print(f'Uploaded by: {plan.uploaded_by.get_full_name()} on {plan.uploaded_at.strftime("%Y-%m-%d %H:%M")}')
        print('=' * 80)

        # Show FPI parameters
        print('\nFPI PARAMETERS:')
        fpis = AnnualFPIParameter.objects.filter(annual_plan=plan)
        print(f'  Total FPIs: {fpis.count()}')
        for fpi in fpis:
            print(f'\n  [{fpi.get_main_head_display()}] {fpi.sub_head}')
            print(f'    Annual Goal: {fpi.annual_goal}')
            print(f'    Q1: {fpi.q1_goal}, Q2: {fpi.q2_goal}, Q3: {fpi.q3_goal}, Q4: {fpi.q4_goal}')
            if fpi.responsible_user:
                print(f'    Responsible: {fpi.responsible_user.get_full_name()}')

        # Show GPI parameters
        print('\n\nGPI PARAMETERS:')
        gpis = AnnualGPIParameter.objects.filter(annual_plan=plan)
        print(f'  Total GPIs: {gpis.count()}')
        for gpi in gpis:
            print(f'\n  {gpi.name}')
            print(f'    Indicator Type: {gpi.get_indicator_type_display()}')
            print(f'    Tracking Type: {gpi.get_tracking_type_display()}')
            print(f'    Cumulation Type: {gpi.get_cumulation_type_display()}')
            print(f'    Annual Goal: {gpi.annual_goal}')
            print(f'    Q1: {gpi.q1_goal}, Q2: {gpi.q2_goal}, Q3: {gpi.q3_goal}, Q4: {gpi.q4_goal}')
            if gpi.responsible_user:
                print(f'    Responsible: {gpi.responsible_user.get_full_name()}')

        # Show PPI projects
        print('\n\nPPI PROJECTS:')
        ppis = AnnualPPIProject.objects.filter(annual_plan=plan)
        print(f'  Total PPIs: {ppis.count()}')
        for ppi in ppis:
            print(f'\n  {ppi.name}')
            if ppi.completion_criteria:
                criteria = ppi.completion_criteria[:100] + '...' if len(ppi.completion_criteria) > 100 else ppi.completion_criteria
                print(f'    Completion Criteria: {criteria}')
            if ppi.start_date:
                print(f'    Duration: {ppi.start_date} to {ppi.end_date}')
            print(f'    Annual Goal: {ppi.annual_goal}')
            print(f'    Q1: {ppi.q1_goal}, Q2: {ppi.q2_goal}, Q3: {ppi.q3_goal}, Q4: {ppi.q4_goal}')
            if ppi.responsible_user:
                print(f'    Responsible: {ppi.responsible_user.get_full_name()}')

        print('\n')

    sys.stdout = original_stdout

print('Data exported to annual_plan_data.txt')
