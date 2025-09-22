#!/usr/bin/env python
"""
Script to test monthly budget display logic
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')
django.setup()

from plans.models import FPIParameter, GPIParameter, FPIMilestone, GPIMilestone
from accounts.models import User
from datetime import datetime
from django.utils import timezone

def test_monthly_budget_logic():
    """Test the monthly budget calculation logic"""

    try:
        # Find user Ravi
        ravi = User.objects.filter(first_name__icontains='Ravi').first()
        if not ravi:
            print("User 'Ravi' not found")
            return

        print(f"Testing monthly budget for user: {ravi.get_full_name()}")

        # Get current month info
        current_month = timezone.now().month
        print(f"Current month: {current_month}")

        # Calculate quarterly month numbers
        quarter_start_month = ((current_month - 1) // 3) * 3 + 1
        current_quarter_month = current_month - quarter_start_month + 1
        last_quarter_month = current_quarter_month - 1 if current_quarter_month > 1 else 3
        next_quarter_month = current_quarter_month + 1 if current_quarter_month < 3 else 1

        print(f"Quarter start month: {quarter_start_month}")
        print(f"Current quarter month: {current_quarter_month} (1-3)")
        print(f"Last quarter month: {last_quarter_month} (1-3)")
        print(f"Next quarter month: {next_quarter_month} (1-3)")

        # Test FPI parameters
        print("\n=== FPI Parameters ===")
        fpi_params = FPIParameter.objects.filter(responsible_user=ravi)
        print(f"Found {fpi_params.count()} FPI parameters for Ravi")

        for fpi in fpi_params[:3]:  # Test first 3
            print(f"\nFPI: {fpi.sub_head}")

            # Check for milestones
            milestones = FPIMilestone.objects.filter(fpi_parameter=fpi)
            print(f"  Milestones: {milestones.count()}")

            for milestone in milestones:
                print(f"    Month {milestone.month_number}: {milestone.budget_value}")

            # Test logic
            last_milestone = FPIMilestone.objects.filter(fpi_parameter=fpi, month_number=last_quarter_month).first()
            next_milestone = FPIMilestone.objects.filter(fpi_parameter=fpi, month_number=next_quarter_month).first()

            last_budget = last_milestone.budget_value if last_milestone else 0
            next_budget = next_milestone.budget_value if next_milestone else 0

            print(f"  Last Month Budget: {last_budget}")
            print(f"  Next Month Budget: {next_budget}")

        # Test GPI parameters (monthly)
        print("\n=== Monthly GPI Parameters ===")
        gpi_params = GPIParameter.objects.filter(responsible_user=ravi, tracking_type='monthly')
        print(f"Found {gpi_params.count()} monthly GPI parameters for Ravi")

        for gpi in gpi_params[:3]:  # Test first 3
            print(f"\nGPI: {gpi.name}")

            # Check for milestones
            milestones = GPIMilestone.objects.filter(gpi_parameter=gpi)
            print(f"  Milestones: {milestones.count()}")

            for milestone in milestones:
                print(f"    Period {milestone.period_number}: {milestone.budget_value}")

            # Test logic
            last_milestone = GPIMilestone.objects.filter(gpi_parameter=gpi, period_number=last_quarter_month).first()
            next_milestone = GPIMilestone.objects.filter(gpi_parameter=gpi, period_number=next_quarter_month).first()

            last_budget = last_milestone.budget_value if last_milestone else 0
            next_budget = next_milestone.budget_value if next_milestone else 0

            print(f"  Last Month Budget: {last_budget}")
            print(f"  Next Month Budget: {next_budget}")

        print("\n✅ Monthly budget logic test completed!")

    except Exception as e:
        print(f"❌ Error testing monthly budget logic: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_monthly_budget_logic()