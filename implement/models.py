from django.db import models
from django.conf import settings
from organizations.models import Team
from plans.models import GPIParameter, PPIProject


class NumbersTracking(models.Model):
    TRACKING_TYPES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    SOURCE_TYPES = [
        ('gpi', 'GPI'),
        ('ppi', 'PPI'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    source_type = models.CharField(max_length=3, choices=SOURCE_TYPES)
    gpi_parameter = models.ForeignKey(GPIParameter, on_delete=models.CASCADE, null=True, blank=True)
    ppi_project = models.ForeignKey(PPIProject, on_delete=models.CASCADE, null=True, blank=True)
    tracking_type = models.CharField(max_length=10, choices=TRACKING_TYPES)
    
    # For tracking period
    year = models.IntegerField()
    week_number = models.IntegerField(null=True, blank=True)  # 1-52
    month_number = models.IntegerField(null=True, blank=True)  # 1-12
    
    # Data fields
    last_period_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    last_period_plan = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    last_period_actual = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    next_period_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    next_period_plan = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    comments = models.TextField(blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'numbers_tracking'
        
    def __str__(self):
        if self.source_type == 'gpi':
            return f"GPI: {self.gpi_parameter.name}"
        else:
            return f"PPI: {self.ppi_project.name}"


class ProjectStatus(models.Model):
    STATUS_CHOICES = [
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('danger', 'Danger'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('dropped', 'Dropped'),
    ]
    
    project = models.ForeignKey(PPIProject, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    revised_due_date = models.DateField(null=True, blank=True)
    challenge = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_status'
        ordering = ['-updated_at']
        
    def __str__(self):
        return f"{self.project.name} - {self.status}"


class Action(models.Model):
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('at_risk', 'At Risk'),
        ('danger', 'Danger'),
        ('overdue', 'Overdue'),
        ('done', 'Done'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('carry_forward', 'Carry Forward'),
        ('on_hold', 'On Hold'),
        ('dropped', 'Dropped'),
    ]
    
    SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('ppi', 'PPI Task'),
        ('improvement', 'Improvement Task'),
        ('review', 'Review Meeting'),
        ('issue', 'Issue Resolution'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    ppi_task = models.OneToOneField('plans.PPITask', on_delete=models.CASCADE, null=True, blank=True)
    improvement_task = models.OneToOneField('improve.ImprovementTask', on_delete=models.CASCADE, null=True, blank=True)
    parent_action = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_actions')
    issue = models.ForeignKey('Issue', on_delete=models.CASCADE, null=True, blank=True, related_name='related_actions')

    # Link to GPI parameters (for My Numbers)
    gpi_parameter = models.ForeignKey('plans.GPIParameter', on_delete=models.CASCADE, null=True, blank=True, related_name='actions')

    # Link to projects (for My Projects)
    ppi_project = models.ForeignKey('plans.PPIProject', on_delete=models.CASCADE, null=True, blank=True, related_name='actions')
    improvement_project = models.ForeignKey('improve.ImprovementProject', on_delete=models.CASCADE, null=True, blank=True, related_name='actions')

    # Week/Month tracking for My Numbers (only used when linked to parameters)
    week_number = models.IntegerField(null=True, blank=True, help_text='Week number within quarter (1-13) for weekly tracking')
    month_number = models.IntegerField(null=True, blank=True, help_text='Month number within quarter (1-3) for monthly tracking')

    # Quarter tracking for My Projects (only used when linked to projects)
    quarter_number = models.IntegerField(null=True, blank=True, help_text='Quarter number (1-4) for quarterly tracking')

    action = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_actions')
    original_due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    previous_status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, help_text='Previous status before on_hold or dropped')
    revised_due_date = models.DateField(null=True, blank=True)
    challenge = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_actions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'actions'
        ordering = ['original_due_date', '-created_at']

    @property
    def effective_status(self):
        """
        Returns the effective status, considering overdue conditions.
        If the action is incomplete and past its due date, returns 'overdue'.
        Otherwise returns the actual status.
        """
        from datetime import date

        # If already completed or done, return actual status
        if self.status in ['done', 'completed']:
            return self.status

        # Check if overdue
        today = date.today()
        due_date = self.revised_due_date if self.revised_due_date else self.original_due_date

        if due_date < today:
            return 'overdue'

        return self.status

    @property
    def source_display(self):
        """Returns a human-readable description of where this action originated from"""
        if self.ppi_task:
            task_desc = self.ppi_task.task_description[:50] + "..." if len(self.ppi_task.task_description) > 50 else self.ppi_task.task_description
            return f"PPI Task: {task_desc}"
        elif self.improvement_task:
            task_desc = self.improvement_task.task_description[:50] + "..." if len(self.improvement_task.task_description) > 50 else self.improvement_task.task_description
            return f"Improvement Task: {task_desc}"
        elif self.parent_action:
            action_text = self.parent_action.action[:50] + "..." if len(self.parent_action.action) > 50 else self.parent_action.action
            return f"Sub-action of: {action_text}"
        elif self.issue:
            return f"Issue Resolution: {self.issue.title}"
        elif self.gpi_parameter:
            period = f"Week {self.week_number}" if self.week_number else f"Month {self.month_number}" if self.month_number else "N/A"
            return f"My Numbers - GPI: {self.gpi_parameter.name} ({period})"
        elif self.ppi_project:
            return f"PPI Project: {self.ppi_project.name}"
        elif self.improvement_project:
            return f"Improvement Project: {self.improvement_project.name}"
        elif self.source == 'review':
            return "Review Meeting"
        else:
            return "Manual Entry"

    def get_next_assignee_in_chain(self, current_user):
        """
        Get the next assignee in the reassignment chain after the current user.
        Returns None if current user is the last in chain or not in chain.
        """
        # Get all reassignments for this action, ordered by sequence
        reassignments = ActionReassignment.objects.filter(
            action=self
        ).order_by('sequence_number')

        # Find the current user's position
        current_position = None
        for reassignment in reassignments:
            if reassignment.reassigned_to == current_user:
                current_position = reassignment.sequence_number
                break

        # If current user is not in the chain, return the current assignee
        if current_position is None:
            return self.assigned_to

        # Get the next reassignment after current user's position
        next_reassignment = reassignments.filter(
            sequence_number=current_position + 1
        ).first()

        if next_reassignment:
            return next_reassignment.reassigned_to
        else:
            # Current user is the last in chain
            return None

    def is_final_assignee(self, current_user):
        """
        Check if the current user is the final assignee in the reassignment chain.
        Final assignee has full edit permissions.
        """
        # If user is not the current assignee, they are not the final assignee
        if self.assigned_to != current_user:
            return False

        # Check if there are any reassignments at all
        has_reassignments = ActionReassignment.objects.filter(action=self).exists()

        if not has_reassignments:
            # No reassignments exist, so current assignee is the final assignee
            return True

        # There are reassignments, check if there's anyone after this user
        next_assignee = self.get_next_assignee_in_chain(current_user)
        return next_assignee is None

    def is_in_reassignment_chain(self, current_user):
        """
        Check if the current user is anywhere in the reassignment chain.
        Users in the chain (but not final assignee) have view and reassign permissions.
        """
        # Check if user is the current assignee
        if self.assigned_to == current_user:
            return True

        # Check if user is in the reassignment chain
        reassignments = ActionReassignment.objects.filter(
            action=self,
            reassigned_to=current_user
        )
        return reassignments.exists()

    def can_edit_action(self, current_user):
        """
        Check if user can edit this action.
        Only the final assignee can edit.
        """
        return self.is_final_assignee(current_user)

    def can_view_action(self, current_user):
        """
        Check if user can view this action.
        Anyone in the reassignment chain can view.
        """
        return self.is_in_reassignment_chain(current_user)

    def can_reassign_action(self, current_user):
        """
        Check if user can reassign this action.
        Anyone in the chain except the final assignee can reassign.
        """
        return self.is_in_reassignment_chain(current_user) and not self.is_final_assignee(current_user)

    def can_create_sub_items(self, current_user):
        """
        Check if user can create sub-actions or issues.
        Only the final assignee can create sub-items.
        """
        return self.is_final_assignee(current_user)

    def __str__(self):
        return f"{self.action[:50]}... - {self.assigned_to.get_full_name()}"


class ActionHistory(models.Model):
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=20)
    revised_due_date = models.DateField(null=True, blank=True)
    challenge = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'action_history'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.action.action[:30]} - {self.status} - {self.updated_at}"


class ActionReassignment(models.Model):
    """Track the reassignment chain/hierarchy for actions"""
    action = models.ForeignKey(Action, on_delete=models.CASCADE, related_name='reassignments')
    reassigned_from = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reassignments_made')
    reassigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reassignments_received')
    reassignment_reason = models.TextField(blank=True)
    sequence_number = models.IntegerField(help_text='Position in the reassignment chain, starting from 1')
    reassigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'action_reassignments'
        ordering = ['action', 'sequence_number']
        unique_together = ['action', 'sequence_number']

    def __str__(self):
        return f"{self.action.action[:30]} - {self.reassigned_from.get_full_name()} → {self.reassigned_to.get_full_name()} (#{self.sequence_number})"


class Issue(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('resolved', 'Resolved'),
        ('acknowledged', 'Acknowledged'),
        ('parked', 'Parked'),
        ('on_hold', 'On Hold'),
        ('dropped', 'Dropped'),
        ('escalated', 'Escalated'),
    ]

    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    ISSUE_TYPE_CHOICES = [
        ('acknowledge', 'Acknowledge'),
        ('support', 'Support'),
        ('act', 'Act'),
        ('park', 'Park'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    issue_type = models.CharField(max_length=15, choices=ISSUE_TYPE_CHOICES, default='acknowledge')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    previous_status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True)
    required_by = models.DateField(null=True, blank=True)
    escalated_to_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='escalated_issues')

    # Link to review meeting (for issues created during review meetings)
    review_meeting = models.ForeignKey('reviews.ReviewMeeting', on_delete=models.SET_NULL, null=True, blank=True, related_name='issues')

    # Link to GPI parameters (for My Numbers)
    gpi_parameter = models.ForeignKey('plans.GPIParameter', on_delete=models.CASCADE, null=True, blank=True, related_name='issues')

    # Link to projects (for My Projects)
    ppi_project = models.ForeignKey('plans.PPIProject', on_delete=models.CASCADE, null=True, blank=True, related_name='issues')
    improvement_project = models.ForeignKey('improve.ImprovementProject', on_delete=models.CASCADE, null=True, blank=True, related_name='issues')

    # Link to actions (for My To Do)
    action = models.ForeignKey(Action, on_delete=models.CASCADE, null=True, blank=True, related_name='issues')

    # Week/Month tracking for My Numbers (only used when linked to parameters)
    week_number = models.IntegerField(null=True, blank=True, help_text='Week number within quarter (1-13) for weekly tracking')
    month_number = models.IntegerField(null=True, blank=True, help_text='Month number within quarter (1-3) for monthly tracking')

    # Quarter tracking for My Projects (only used when linked to projects)
    quarter_number = models.IntegerField(null=True, blank=True, help_text='Quarter number (1-4) for quarterly tracking')

    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reported_issues')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'issues'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.team.name}"
        
    @property
    def actions_completed_count(self):
        return self.related_actions.filter(status='completed').count()

    @property
    def total_actions_count(self):
        return self.related_actions.count()

    @property
    def source_display(self):
        """Returns a human-readable description of where this issue originated from"""
        if self.action:
            return f"Action: {self.action.action[:50]}..."
        elif self.gpi_parameter:
            period = f"Week {self.week_number}" if self.week_number else f"Month {self.month_number}" if self.month_number else "N/A"
            return f"My Numbers - GPI: {self.gpi_parameter.name} ({period})"
        elif self.ppi_project:
            return f"PPI Project: {self.ppi_project.name}"
        elif self.improvement_project:
            return f"Improvement Project: {self.improvement_project.name}"
        else:
            return "Manual Entry"