from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime
from improve.models import ImprovementTask
from implement.models import Action


class Command(BaseCommand):
    help = 'Create Actions from existing ImprovementTask objects'

    def handle(self, *args, **options):
        improvement_tasks = ImprovementTask.objects.all()
        created_count = 0
        skipped_count = 0

        self.stdout.write(f"Found {improvement_tasks.count()} improvement tasks to process...")

        for task in improvement_tasks:
            # Check if Action already exists for this improvement task
            if Action.objects.filter(improvement_task=task).exists():
                skipped_count += 1
                continue

            try:
                # Calculate due date for this week
                # Assume quarter starts from project start_date
                week_due_date = task.project.start_date + datetime.timedelta(weeks=task.week_number-1, days=6)

                # Create corresponding Action
                Action.objects.create(
                    team=task.project.upload.team,
                    source='improvement',
                    improvement_task=task,
                    action=f"[Week {task.week_number}] {task.task_description}",
                    priority='medium',
                    assigned_to=task.assigned_to,
                    original_due_date=week_due_date,
                    status='not_started',
                    created_by=task.assigned_to,
                    comments=f"From Improvement project: {task.project.name}"
                )
                created_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error creating action for task {task.id}: {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {created_count} actions, skipped {skipped_count} existing")
        )