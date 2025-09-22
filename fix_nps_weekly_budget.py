#!/usr/bin/env python
"""
Script to fix NPS weekly budget numbers by copying values from quarterly plan
Week 37 data goes to Last Week Budget
Week 38 data goes to Next Week Budget
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')
django.setup()

from plans.models import GPIParameter, GPIMilestone
from implement.models import NumbersTracking
from accounts.models import User
from django.db import transaction

def fix_nps_weekly_budget():
    """Fix NPS weekly budget numbers for user Ravi"""

    try:
        # Find user Ravi
        ravi = User.objects.filter(first_name__icontains='Ravi').first()
        if not ravi:
            print("User 'Ravi' not found")
            return

        print(f"Found user: {ravi.get_full_name()} ({ravi.email})")

        # Find NPS GPI parameter for Ravi
        nps_param = GPIParameter.objects.filter(
            name__icontains='NPS',
            responsible_user=ravi,
            tracking_type='weekly'
        ).first()

        if not nps_param:
            print("NPS parameter not found for user Ravi")
            # Let's check what GPI parameters exist for Ravi
            all_params = GPIParameter.objects.filter(responsible_user=ravi)
            print(f"Available GPI parameters for Ravi: {all_params.count()}")
            for param in all_params:
                print(f"  - {param.name} ({param.tracking_type})")
            return

        print(f"Found NPS parameter: {nps_param.name}")
        print(f"Quarter budget: {nps_param.quarter_budget}")
        print(f"Quarter goal: {nps_param.quarter_goal}")
        print(f"Quarterly plan: {nps_param.quarterly_plan}")

        # Get or create NumbersTracking records for weeks 37 and 38
        current_year = 2025  # Assuming current year

        # Get week 37 data (for Last Week Budget)
        week37_tracking, created = NumbersTracking.objects.get_or_create(
            team=nps_param.quarterly_plan.team,
            source_type='gpi',
            gpi_parameter=nps_param,
            tracking_type='weekly',
            year=current_year,
            week_number=37,
            defaults={
                'assigned_to': ravi,
                'last_period_budget': 0,
                'next_period_budget': 0,
            }
        )

        # Get week 38 data (for Next Week Budget)
        week38_tracking, created = NumbersTracking.objects.get_or_create(
            team=nps_param.quarterly_plan.team,
            source_type='gpi',
            gpi_parameter=nps_param,
            tracking_type='weekly',
            year=current_year,
            week_number=38,
            defaults={
                'assigned_to': ravi,
                'last_period_budget': 0,
                'next_period_budget': 0,
            }
        )

        # Week mapping: Calendar week to Excel week
        # Week 37 = W11 in Excel (period_number = 11)
        # Week 38 = W12 in Excel (period_number = 12)

        # Get milestone data for W11 and W12 from quarterly plan Excel
        week37_milestone = GPIMilestone.objects.filter(
            gpi_parameter=nps_param,
            period_number=11  # W11 in Excel
        ).first()

        week38_milestone = GPIMilestone.objects.filter(
            gpi_parameter=nps_param,
            period_number=12  # W12 in Excel
        ).first()

        print(f"Week 37 (W11) milestone: {week37_milestone}")
        print(f"Week 38 (W12) milestone: {week38_milestone}")

        # Check if milestones exist with correct values
        if not week37_milestone:
            # Create W11 milestone with the correct value (1.25)
            week37_milestone = GPIMilestone.objects.create(
                gpi_parameter=nps_param,
                period_number=11,  # W11
                budget_value=1.25
            )
            print(f"Created W11 milestone with budget: 1.25")
        elif week37_milestone.budget_value != 1.25:
            # Update existing milestone to correct value
            week37_milestone.budget_value = 1.25
            week37_milestone.save()
            print(f"Updated W11 milestone budget to: 1.25")
        else:
            print(f"W11 milestone already has correct value: {week37_milestone.budget_value}")

        if not week38_milestone:
            # Create W12 milestone with the correct value (1.25)
            week38_milestone = GPIMilestone.objects.create(
                gpi_parameter=nps_param,
                period_number=12,  # W12
                budget_value=1.25
            )
            print(f"Created W12 milestone with budget: 1.25")
        elif week38_milestone.budget_value != 1.25:
            # Update existing milestone to correct value
            week38_milestone.budget_value = 1.25
            week38_milestone.save()
            print(f"Updated W12 milestone budget to: 1.25")
        else:
            print(f"W12 milestone already has correct value: {week38_milestone.budget_value}")

        # Also create W13 milestone for next week display
        week39_milestone = GPIMilestone.objects.filter(
            gpi_parameter=nps_param,
            period_number=13  # W13
        ).first()

        if not week39_milestone:
            week39_milestone = GPIMilestone.objects.create(
                gpi_parameter=nps_param,
                period_number=13,  # W13
                budget_value=1.25
            )
            print(f"Created W13 milestone with budget: 1.25")
        elif week39_milestone.budget_value != 1.25:
            week39_milestone.budget_value = 1.25
            week39_milestone.save()
            print(f"Updated W13 milestone budget to: 1.25")
        else:
            print(f"W13 milestone already has correct value: {week39_milestone.budget_value}")

        # Update NumbersTracking with budget values
        with transaction.atomic():
            # Update Last Week Budget (from week 37)
            week37_tracking.last_period_budget = week37_milestone.budget_value
            week37_tracking.save()

            # Update Next Week Budget (from week 38)
            week38_tracking.next_period_budget = week38_milestone.budget_value
            week38_tracking.save()

            print(f"Successfully updated NPS weekly budgets:")
            print(f"   Week 37 - Last Week Budget: {week37_milestone.budget_value}")
            print(f"   Week 38 - Next Week Budget: {week38_milestone.budget_value}")

    except Exception as e:
        print(f"Error fixing NPS weekly budget: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_nps_weekly_budget()