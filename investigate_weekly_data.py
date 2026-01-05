#!/usr/bin/env python
"""
Script to investigate all weekly numbers data for Ravi
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')
django.setup()

from plans.models import GPIParameter, GPIMilestone
from accounts.models import User

def investigate_weekly_data():
    """Investigate all weekly numbers data"""

    try:
        # Find user Ravi
        ravi = User.objects.filter(first_name__icontains='Ravi').first()
        if not ravi:
            print("User 'Ravi' not found")
            return

        print(f"Investigating weekly data for user: {ravi.get_full_name()}")

        # Get all weekly GPI parameters for Ravi
        weekly_params = GPIParameter.objects.filter(
            responsible_user=ravi,
            tracking_type='weekly'
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year')

        print(f"\nFound {weekly_params.count()} weekly GPI parameters for Ravi:")
        print("=" * 80)

        for i, param in enumerate(weekly_params, 1):
            print(f"\n{i}. Parameter: {param.name}")
            print(f"   Team: {param.quarterly_plan.team.name}")
            print(f"   Financial Year: {param.quarterly_plan.financial_year.year}")
            print(f"   Quarter Goal: {param.quarter_goal}")
            print(f"   Quarter Budget: {param.quarter_budget}")
            print(f"   Indicator Type: {param.get_indicator_type_display()}")

            # Check milestones for this parameter
            milestones = GPIMilestone.objects.filter(gpi_parameter=param).order_by('period_number')
            print(f"   Milestones: {milestones.count()}")

            if milestones.exists():
                print("   Weekly budget values:")
                for milestone in milestones:
                    print(f"      Week {milestone.period_number}: {milestone.budget_value}")
            else:
                print("   NO MILESTONE DATA - This is why budget shows 0")

            print(f"   Data Source: {'OK From quarterly plan upload' if milestones.exists() else 'MISSING - needs milestone data'}")

        print(f"\n" + "=" * 80)
        print("SUMMARY:")
        print(f"OK NPS: Has milestone data (manually created)")

        other_params = weekly_params.exclude(name__icontains='NPS')
        params_with_milestones = 0
        params_without_milestones = 0

        for param in other_params:
            has_milestones = GPIMilestone.objects.filter(gpi_parameter=param).exists()
            if has_milestones:
                params_with_milestones += 1
            else:
                params_without_milestones += 1

        print(f"OK Other parameters with milestone data: {params_with_milestones}")
        print(f"MISSING Other parameters missing milestone data: {params_without_milestones}")

        if params_without_milestones > 0:
            print(f"\nROOT CAUSE:")
            print(f"   The quarterly plan Excel upload process is not creating")
            print(f"   GPIMilestone records for weekly GPI parameters.")
            print(f"   Only the quarter_goal is being saved to the GPIParameter,")
            print(f"   but the individual weekly values (W1-W13) are not being")
            print(f"   extracted and saved as GPIMilestone records.")

    except Exception as e:
        print(f"Error investigating weekly data: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    investigate_weekly_data()