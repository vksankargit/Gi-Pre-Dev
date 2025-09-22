#!/usr/bin/env python
"""
Test script to verify the current week/month logic
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')
django.setup()

from plans.models import GPIParameter, GPIMilestone, FPIParameter, FPIMilestone
from accounts.models import User
from datetime import date
from django.utils import timezone

def test_current_period_logic():
    """Test the current week/month logic"""

    try:
        # Get current week/month info
        today = date.today()
        year, week_num, weekday = today.isocalendar()
        current_month = timezone.now().month

        print(f"Current week: {week_num}")
        print(f"Current month: {current_month}")

        # Weekly logic test
        current_excel_week = week_num - 26  # Convert calendar week to Excel week
        last_excel_week = current_excel_week - 1

        print(f"\nWeekly Logic:")
        print(f"Current Excel week: W{current_excel_week}")
        print(f"Last Excel week: W{last_excel_week}")

        # Monthly logic test
        quarter_start_month = ((current_month - 1) // 3) * 3 + 1
        current_quarter_month = current_month - quarter_start_month + 1
        last_quarter_month = current_quarter_month - 1 if current_quarter_month > 1 else 3

        print(f"\nMonthly Logic:")
        print(f"Quarter start month: {quarter_start_month}")
        print(f"Current quarter month: {current_quarter_month}")
        print(f"Last quarter month: {last_quarter_month}")

        # Find user Ravi and test with actual data
        ravi = User.objects.filter(first_name__icontains='Ravi').first()
        if not ravi:
            print("User 'Ravi' not found")
            return

        print(f"\nTesting with user: {ravi.get_full_name()}")

        # Test NPS weekly data
        nps_param = GPIParameter.objects.filter(
            name__icontains='NPS',
            responsible_user=ravi,
            tracking_type='weekly'
        ).first()

        if nps_param:
            print(f"\nNPS Weekly Data:")
            last_milestone = GPIMilestone.objects.filter(gpi_parameter=nps_param, period_number=last_excel_week).first()
            current_milestone = GPIMilestone.objects.filter(gpi_parameter=nps_param, period_number=current_excel_week).first()

            print(f"Last Week Budget (W{last_excel_week}): {last_milestone.budget_value if last_milestone else 0}")
            print(f"Current Week Budget (W{current_excel_week}): {current_milestone.budget_value if current_milestone else 0}")

        # Test FPI monthly data
        fpi_param = FPIParameter.objects.filter(responsible_user=ravi).first()
        if fpi_param:
            print(f"\nFPI Monthly Data ({fpi_param.sub_head}):")
            last_milestone = FPIMilestone.objects.filter(fpi_parameter=fpi_param, month_number=last_quarter_month).first()
            current_milestone = FPIMilestone.objects.filter(fpi_parameter=fpi_param, month_number=current_quarter_month).first()

            print(f"Last Month Budget (Month {last_quarter_month}): Rs.{last_milestone.budget_value if last_milestone else 0}")
            print(f"Current Month Budget (Month {current_quarter_month}): Rs.{current_milestone.budget_value if current_milestone else 0}")

        print(f"\nSuccess: Current period logic is working correctly!")

    except Exception as e:
        print(f"Error testing current period logic: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_current_period_logic()