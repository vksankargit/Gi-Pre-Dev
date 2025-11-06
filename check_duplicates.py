import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Q
from implement.models import Action

User = get_user_model()

# Get Ravi user
ravi = User.objects.get(email='ravi@groupinfinite.com')

print(f"Checking actions for user: {ravi}")
print("=" * 80)

# Query without distinct
actions_query = Action.objects.filter(
    Q(assigned_to=ravi) |
    Q(created_by=ravi) |
    Q(ppi_task__project__responsible_user=ravi) |
    Q(improvement_task__project__responsible_user=ravi)
).select_related('team', 'created_by', 'assigned_to', 'ppi_task__project', 'improvement_task__project')

print(f"\nTotal actions WITHOUT distinct: {actions_query.count()}")

# Query with distinct
actions_distinct = Action.objects.filter(
    Q(assigned_to=ravi) |
    Q(created_by=ravi) |
    Q(ppi_task__project__responsible_user=ravi) |
    Q(improvement_task__project__responsible_user=ravi)
).select_related('team', 'created_by', 'assigned_to', 'ppi_task__project', 'improvement_task__project').distinct()

print(f"Total actions WITH distinct: {actions_distinct.count()}")

# Find the specific duplicate mentioned
print("\n" + "=" * 80)
print("Looking for '[Week 1] Define personas' action:")
print("=" * 80)

for action in actions_query:
    if 'Define personas' in action.action:
        print(f"\nID: {action.id}")
        print(f"Action: {action.action}")
        print(f"Assigned to: {action.assigned_to}")
        print(f"Created by: {action.created_by}")
        if hasattr(action, 'ppi_task') and action.ppi_task:
            print(f"PPI Task: {action.ppi_task}")
            print(f"PPI Project: {action.ppi_task.project}")
            print(f"PPI Project Owner: {action.ppi_task.project.responsible_user}")
        if hasattr(action, 'improvement_task') and action.improvement_task:
            print(f"Improvement Task: {action.improvement_task}")
            print(f"Improvement Project: {action.improvement_task.project}")
        print("-" * 40)

# Check which conditions match for this action
print("\n" + "=" * 80)
print("Analyzing which query conditions match for 'Define personas' actions:")
print("=" * 80)

for action in actions_query:
    if 'Define personas' in action.action:
        conditions_matched = []

        if action.assigned_to == ravi:
            conditions_matched.append(f"assigned_to={ravi}")
        if action.created_by == ravi:
            conditions_matched.append(f"created_by={ravi}")
        if hasattr(action, 'ppi_task') and action.ppi_task and action.ppi_task.project.responsible_user == ravi:
            conditions_matched.append(f"ppi_task.project.responsible_user={ravi}")
        if hasattr(action, 'improvement_task') and action.improvement_task and action.improvement_task.project.responsible_user == ravi:
            conditions_matched.append(f"improvement_task.project.responsible_user={ravi}")

        print(f"\nAction ID {action.id}: {action.action}")
        print(f"Matches {len(conditions_matched)} conditions:")
        for condition in conditions_matched:
            print(f"  - {condition}")
