from django.db import models
from django.conf import settings


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizations'
        ordering = ['name']
        
    def __str__(self):
        return self.name


class OrganizationCoordinator(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='coordinators')
    coordinator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coordinated_organizations')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'organization_coordinators'
        unique_together = ['organization', 'coordinator']
        
    def __str__(self):
        return f"{self.coordinator.get_full_name()} - {self.organization.name}"


class TeamMeetingType(models.Model):
    """Meeting types specific to each organization (e.g., Operations, Planning, Review)"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='meeting_types')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'team_meeting_types'
        unique_together = ['organization', 'name']
        ordering = ['organization', 'name']

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Team(models.Model):
    CADENCE_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ]

    DAY_OF_WEEK_CHOICES = [
        (0, 'Sunday'),
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
    ]

    WEEK_NUMBER_CHOICES = [
        (1, 'First Week'),
        (2, 'Second Week'),
        (3, 'Third Week'),
        (4, 'Fourth Week'),
        (5, 'Fifth Week'),
    ]

    MONTH_IN_QUARTER_CHOICES = [
        (1, 'First Month'),
        (2, 'Second Month'),
        (3, 'Third Month'),
    ]

    QUARTER_CHOICES = [
        ('Q1', 'Q1 (Apr-Jun)'),
        ('Q2', 'Q2 (Jul-Sep)'),
        ('Q3', 'Q3 (Oct-Dec)'),
        ('Q4', 'Q4 (Jan-Mar)'),
    ]

    name = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='teams')
    meeting_type = models.ForeignKey(TeamMeetingType, on_delete=models.SET_NULL, null=True, blank=True, related_name='teams')
    cadence = models.CharField(max_length=20, choices=CADENCE_CHOICES, null=True, blank=True)

    # Scheduling fields (applicable based on cadence)
    day_of_week = models.IntegerField(choices=DAY_OF_WEEK_CHOICES, null=True, blank=True)
    week_number = models.IntegerField(choices=WEEK_NUMBER_CHOICES, null=True, blank=True)  # For monthly, quarterly, annually
    month_in_quarter = models.IntegerField(choices=MONTH_IN_QUARTER_CHOICES, null=True, blank=True)  # For quarterly, annually
    quarter = models.CharField(max_length=2, choices=QUARTER_CHOICES, null=True, blank=True)  # For annually
    meeting_time = models.TimeField(null=True, blank=True)

    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='managed_teams')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teams'
        unique_together = ['organization', 'name']
        ordering = ['organization', 'name']
        verbose_name = 'Team Meeting'
        verbose_name_plural = 'Team Meetings'

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

    def get_schedule_display(self):
        """Returns a human-readable schedule string"""
        if not self.cadence:
            return "No schedule set"

        parts = [self.get_cadence_display()]

        if self.cadence == 'weekly':
            if self.day_of_week is not None:
                parts.append(f"on {self.get_day_of_week_display()}")

        elif self.cadence == 'monthly':
            if self.week_number and self.day_of_week is not None:
                parts.append(f"on {self.get_week_number_display()} {self.get_day_of_week_display()}")

        elif self.cadence == 'quarterly':
            if self.month_in_quarter and self.week_number and self.day_of_week is not None:
                parts.append(f"in {self.get_month_in_quarter_display()}, {self.get_week_number_display()} {self.get_day_of_week_display()}")

        elif self.cadence == 'annually':
            if self.quarter and self.month_in_quarter and self.week_number and self.day_of_week is not None:
                parts.append(f"in {self.quarter} {self.get_month_in_quarter_display()}, {self.get_week_number_display()} {self.get_day_of_week_display()}")

        if self.meeting_time:
            parts.append(f"at {self.meeting_time.strftime('%I:%M %p')}")

        return " ".join(parts)

    def get_next_meeting_date(self, after_date=None):
        """Calculate the next meeting date based on the team's cadence schedule"""
        from datetime import datetime, timedelta
        from django.utils import timezone

        if not self.cadence:
            return None

        # Use provided date or current date
        base_date = after_date if after_date else timezone.now().date()

        if self.cadence == 'weekly':
            # Find next occurrence of the specified day of week
            if self.day_of_week is not None:
                days_ahead = self.day_of_week - base_date.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                next_date = base_date + timedelta(days=days_ahead)
                return next_date

        elif self.cadence == 'monthly':
            # Find the specified week and day in the next month
            if self.week_number and self.day_of_week is not None:
                # Start from next month
                if base_date.month == 12:
                    next_month = base_date.replace(year=base_date.year + 1, month=1, day=1)
                else:
                    next_month = base_date.replace(month=base_date.month + 1, day=1)

                # Find the first occurrence of the target day in that month
                first_day_weekday = next_month.weekday()
                days_to_target = (self.day_of_week - first_day_weekday) % 7
                first_occurrence = next_month + timedelta(days=days_to_target)

                # Add weeks to get to the target week number
                target_date = first_occurrence + timedelta(weeks=self.week_number - 1)

                # Make sure we're still in the same month
                if target_date.month == next_month.month:
                    return target_date

        return None


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='team_memberships')
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'team_members'
        unique_together = ['team', 'member']
        
    def __str__(self):
        return f"{self.member.get_full_name()} - {self.team.name}"