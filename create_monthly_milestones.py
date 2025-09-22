#!/usr/bin/env python
"""
Script to create monthly milestone data for testing
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')
django.setup()

from plans.models import FPIParameter, GPIParameter, FPIMilestone, GPIMilestone
from accounts.models import User
from django.db import transaction

def create_monthly_milestones():
    """Create test monthly milestone data"""

    try:
        # Find user Ravi
        ravi = User.objects.filter(first_name__icontains='Ravi').first()
        if not ravi:
            print("User 'Ravi' not found")
            return

        print(f"Creating monthly milestones for user: {ravi.get_full_name()}")

        with transaction.atomic():
            # Create FPI milestones for first FPI parameter
            fpi_params = FPIParameter.objects.filter(responsible_user=ravi)
            if fpi_params.exists():
                first_fpi = fpi_params.first()
                print(f"\nCreating FPI milestones for: {first_fpi.sub_head}")

                # Create monthly milestones (1-3 for quarterly months)
                for month in range(1, 4):
                    milestone, created = FPIMilestone.objects.get_or_create(
                        fpi_parameter=first_fpi,
                        month_number=month,
                        defaults={'budget_value': 50000 + (month * 10000)}  # 60k, 70k, 80k
                    )
                    if created:
                        print(f"  Created Month {month}: Rs.{milestone.budget_value}")
                    else:
                        print(f"  Month {month} exists: Rs.{milestone.budget_value}")

            # Create GPI milestones for first monthly GPI parameter
            monthly_gpi_params = GPIParameter.objects.filter(responsible_user=ravi, tracking_type='monthly')
            if monthly_gpi_params.exists():
                first_gpi = monthly_gpi_params.first()
                print(f"\nCreating GPI milestones for: {first_gpi.name}")

                # Create monthly milestones (1-3 for quarterly months)
                for month in range(1, 4):
                    milestone, created = GPIMilestone.objects.get_or_create(
                        gpi_parameter=first_gpi,
                        period_number=month,
                        defaults={'budget_value': 25 + (month * 5)}  # 30, 35, 40
                    )
                    if created:
                        print(f"  Created Month {month}: {milestone.budget_value}")
                    else:
                        print(f"  Month {month} exists: {milestone.budget_value}")

            print(f"\nSuccess: Monthly milestone data created!")
            print(f"For September (quarter month 3):")
            print(f"  Last Month Budget (Month 2): FPI=Rs.70,000, GPI=35")
            print(f"  Next Month Budget (Month 1): FPI=Rs.60,000, GPI=30")

    except Exception as e:
        print(f"Error creating monthly milestones: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_monthly_milestones()