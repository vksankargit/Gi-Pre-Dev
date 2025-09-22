#!/usr/bin/env python
"""
Debug script to check model_type assignment
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')
django.setup()

from plans.models import GPIParameter, FPIParameter
from accounts.models import User

def debug_model_type():
    """Debug model_type assignment"""

    try:
        # Find user Ravi
        ravi = User.objects.filter(first_name__icontains='Ravi').first()
        if not ravi:
            print("User 'Ravi' not found")
            return

        print(f"Debugging for user: {ravi.get_full_name()}")

        # Test weekly numbers
        weekly_numbers_qs = GPIParameter.objects.filter(
            responsible_user=ravi,
            tracking_type='weekly'
        )

        print(f"\nWeekly GPI Parameters: {weekly_numbers_qs.count()}")
        weekly_numbers = []
        for gpi in weekly_numbers_qs:
            gpi.model_type = 'gpi'
            weekly_numbers.append(gpi)
            print(f"  - {gpi.name}: model_type = {getattr(gpi, 'model_type', 'NOT SET')}")

        # Test monthly numbers - FPI
        monthly_fpi = FPIParameter.objects.filter(responsible_user=ravi)
        print(f"\nMonthly FPI Parameters: {monthly_fpi.count()}")
        for fpi in monthly_fpi:
            fpi.model_type = 'fpi'
            print(f"  - {fpi.sub_head}: model_type = {getattr(fpi, 'model_type', 'NOT SET')}")

        # Test monthly numbers - GPI
        monthly_gpi = GPIParameter.objects.filter(
            responsible_user=ravi,
            tracking_type='monthly'
        )
        print(f"\nMonthly GPI Parameters: {monthly_gpi.count()}")
        for gpi in monthly_gpi:
            gpi.model_type = 'gpi'
            print(f"  - {gpi.name}: model_type = {getattr(gpi, 'model_type', 'NOT SET')}")

        print("\nTest completed successfully!")

    except Exception as e:
        print(f"Error debugging model_type: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_model_type()