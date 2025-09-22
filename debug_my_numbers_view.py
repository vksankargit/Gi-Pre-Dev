#!/usr/bin/env python
"""
Debug script to check what MyNumbersView is returning
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')
django.setup()

from plans.models import GPIParameter, FPIParameter
from accounts.models import User

def debug_my_numbers_view():
    """Debug what MyNumbersView is returning"""

    try:
        # Find user Ravi
        ravi = User.objects.filter(first_name__icontains='Ravi').first()
        if not ravi:
            print("User 'Ravi' not found")
            return

        print(f"Debugging MyNumbersView data for user: {ravi.get_full_name()}")

        # Simulate MyNumbersView logic
        print("\n=== WEEKLY NUMBERS ===")
        weekly_numbers_qs = GPIParameter.objects.filter(
            responsible_user=ravi,
            tracking_type='weekly'
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year').prefetch_related('milestones')

        weekly_numbers = []
        for gpi in weekly_numbers_qs:
            gpi.model_type = 'gpi'
            weekly_numbers.append(gpi)
            print(f"GPI: {gpi.name}")
            print(f"  - last_week_actual: {gpi.last_week_actual}")
            print(f"  - current_week_plan: {gpi.current_week_plan}")
            print(f"  - last_month_actual: {gpi.last_month_actual}")
            print(f"  - current_month_plan: {gpi.current_month_plan}")

        print("\n=== MONTHLY NUMBERS - FPI ===")
        monthly_fpi = FPIParameter.objects.filter(
            responsible_user=ravi
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year').prefetch_related('milestones')

        for fpi in monthly_fpi:
            fpi.model_type = 'fpi'
            print(f"FPI: {fpi.sub_head}")
            print(f"  - last_month_actual: {fpi.last_month_actual}")
            print(f"  - current_month_plan: {fpi.current_month_plan}")

        print("\n=== MONTHLY NUMBERS - GPI ===")
        monthly_gpi = GPIParameter.objects.filter(
            responsible_user=ravi,
            tracking_type='monthly'
        ).select_related('quarterly_plan__team', 'quarterly_plan__financial_year').prefetch_related('milestones')

        for gpi in monthly_gpi:
            gpi.model_type = 'gpi'
            print(f"GPI: {gpi.name}")
            print(f"  - last_week_actual: {gpi.last_week_actual}")
            print(f"  - current_week_plan: {gpi.current_week_plan}")
            print(f"  - last_month_actual: {gpi.last_month_actual}")
            print(f"  - current_month_plan: {gpi.current_month_plan}")

        print("\nDebug completed!")

    except Exception as e:
        print(f"Error debugging MyNumbersView: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_my_numbers_view()