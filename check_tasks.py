from plans.models import PPITask
from implement.models import Action

for task_id in [754, 755, 756]:
    try:
        task = PPITask.objects.get(id=task_id)
        print(f'Task {task_id}: assigned_to={task.assigned_to.get_full_name()} (ID: {task.assigned_to.id})')
        action = Action.objects.filter(ppi_task=task).first()
        if action:
            print(f'  Action {action.id}: assigned_to={action.assigned_to.get_full_name()} (ID: {action.assigned_to.id})')
        else:
            print(f'  No action found')
        print()
    except PPITask.DoesNotExist:
        print(f'Task {task_id}: Not found\n')
