#!/usr/bin/env python
"""
Test script to verify save functionality is working
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')
django.setup()

from plans.models import GPIParameter, FPIParameter
from accounts.models import User

def test_save_functionality():
    """Test that we can save data to GPI and FPI parameters"""

    try:
        # Find user Ravi
        ravi = User.objects.filter(first_name__icontains='Ravi').first()
        if not ravi:
            print("User 'Ravi' not found")
            return

        print(f"Testing save functionality for user: {ravi.get_full_name()}")

        # Test GPI parameter save
        gpi_param = GPIParameter.objects.filter(responsible_user=ravi).first()
        if gpi_param:
            print(f"\nTesting GPI parameter: {gpi_param.name}")
            old_value = gpi_param.last_week_actual
            print(f"Current last_week_actual: {old_value}")

            # Set a test value
            test_value = 123.45
            gpi_param.last_week_actual = test_value
            gpi_param.save()
            print(f"Set last_week_actual to: {test_value}")

            # Refresh from database
            gpi_param.refresh_from_db()
            new_value = gpi_param.last_week_actual
            print(f"After refresh from DB: {new_value}")

            if new_value == test_value:
                print("✅ GPI save test PASSED")
            else:
                print("❌ GPI save test FAILED")

        # Test FPI parameter save
        fpi_param = FPIParameter.objects.filter(responsible_user=ravi).first()
        if fpi_param:
            print(f"\nTesting FPI parameter: {fpi_param.sub_head}")
            old_value = fpi_param.last_month_actual
            print(f"Current last_month_actual: {old_value}")

            # Set a test value
            test_value = 678.90
            fpi_param.last_month_actual = test_value
            fpi_param.save()
            print(f"Set last_month_actual to: {test_value}")

            # Refresh from database
            fpi_param.refresh_from_db()
            new_value = fpi_param.last_month_actual
            print(f"After refresh from DB: {new_value}")

            if new_value == test_value:
                print("✅ FPI save test PASSED")
            else:
                print("❌ FPI save test FAILED")

        print("\nTest completed!")

    except Exception as e:
        print(f"Error testing save functionality: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_save_functionality()