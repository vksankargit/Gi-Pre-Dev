#!/usr/bin/env python
"""
Script to clean up test data and prepare for fresh quarterly plan upload
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')
django.setup()

from plans.models import GPIParameter, GPIMilestone, FPIParameter, FPIMilestone, QuarterlyPlan
from accounts.models import User

def cleanup_test_data():
    """Clean up all test data"""

    try:
        # Find user Ravi
        ravi = User.objects.filter(first_name__icontains='Ravi').first()
        if not ravi:
            print("User 'Ravi' not found")
            return

        print(f"Cleaning up test data for user: {ravi.get_full_name()}")

        # Delete all GPI parameters and their milestones for Ravi
        gpi_params = GPIParameter.objects.filter(responsible_user=ravi)
        gpi_count = gpi_params.count()

        for param in gpi_params:
            GPIMilestone.objects.filter(gpi_parameter=param).delete()

        gpi_params.delete()
        print(f"Deleted {gpi_count} GPI parameters and their milestones")

        # Delete all FPI parameters and their milestones for Ravi
        fpi_params = FPIParameter.objects.filter(responsible_user=ravi)
        fpi_count = fpi_params.count()

        for param in fpi_params:
            FPIMilestone.objects.filter(fpi_parameter=param).delete()

        fpi_params.delete()
        print(f"Deleted {fpi_count} FPI parameters and their milestones")

        print("Cleanup completed successfully!")

    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    cleanup_test_data()