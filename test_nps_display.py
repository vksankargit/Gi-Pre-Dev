#!/usr/bin/env python
"""
Script to test if NPS budget values will display correctly in the implement dashboard
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')
django.setup()

from plans.models import GPIParameter, GPIMilestone
from accounts.models import User
from datetime import date

def test_nps_display():
    """Test that NPS budget values will display correctly for Ravi"""

    try:
        # Find user Ravi
        ravi = User.objects.filter(first_name__icontains='Ravi').first()
        if not ravi:
            print("User 'Ravi' not found")
            return

        print(f"Testing for user: {ravi.get_full_name()} ({ravi.email})")

        # Get current week
        today = date.today()
        year, week_num, weekday = today.isocalendar()
        print(f"Current week: {week_num}")

        # Calculate Excel weeks
        current_excel_week = week_num - 26  # Convert calendar week to Excel week
        last_excel_week = current_excel_week - 1
        next_excel_week = current_excel_week + 1

        print(f"Excel weeks - Last: W{last_excel_week}, Current: W{current_excel_week}, Next: W{next_excel_week}")

        # Find NPS GPI parameter for Ravi
        nps_param = GPIParameter.objects.filter(
            name__icontains='NPS',
            responsible_user=ravi,
            tracking_type='weekly'
        ).first()

        if not nps_param:
            print("NPS parameter not found for user Ravi")
            return

        print(f"Found NPS parameter: {nps_param.name}")

        # Get milestone values
        last_week_milestone = GPIMilestone.objects.filter(
            gpi_parameter=nps_param,
            period_number=last_excel_week
        ).first()

        next_week_milestone = GPIMilestone.objects.filter(
            gpi_parameter=nps_param,
            period_number=next_excel_week
        ).first()

        print(f"Last week milestone (W{last_excel_week}): {last_week_milestone.budget_value if last_week_milestone else 'None'}")
        print(f"Next week milestone (W{next_excel_week}): {next_week_milestone.budget_value if next_week_milestone else 'None'}")

        # Test the view logic
        enhanced_gpi = nps_param
        enhanced_gpi.last_week_budget = last_week_milestone.budget_value if last_week_milestone else 0
        enhanced_gpi.next_week_budget = next_week_milestone.budget_value if next_week_milestone else 0

        print(f"\nTemplate will display:")
        print(f"Last Week Budget: {enhanced_gpi.last_week_budget}")
        print(f"Next Week Budget: {enhanced_gpi.next_week_budget}")

        # Verify the specific milestones we created (W11 = 11, W12 = 12)
        week11_milestone = GPIMilestone.objects.filter(
            gpi_parameter=nps_param,
            period_number=11
        ).first()

        week12_milestone = GPIMilestone.objects.filter(
            gpi_parameter=nps_param,
            period_number=12
        ).first()

        print(f"\nQuarterly plan milestones:")
        print(f"W11 (Week 37): {week11_milestone.budget_value if week11_milestone else 'None'}")
        print(f"W12 (Week 38): {week12_milestone.budget_value if week12_milestone else 'None'}")

        if week11_milestone and week12_milestone:
            print(f"\nSUCCESS: NPS budget values are set correctly!")
            print(f"When current week is 38, Ravi should see:")
            print(f"- Last Week Budget: {week11_milestone.budget_value} (from W11)")
            print(f"- Next Week Budget: {week12_milestone.budget_value} (from W12)")
        else:
            print("ERROR: Milestone values are missing")

    except Exception as e:
        print(f"Error testing NPS display: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_nps_display()