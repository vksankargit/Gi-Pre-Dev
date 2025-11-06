from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from implement.models import Action

User = get_user_model()

class Command(BaseCommand):
    help = 'Debug action data and user assignments'

    def handle(self, *args, **options):
        self.stdout.write("=== DEBUG ACTIONS ===")

        # Check all users and their action counts
        users = User.objects.all()
        for user in users:
            action_count = Action.objects.filter(assigned_to=user).count()
            self.stdout.write(f"User: {user.username} ({user.email}) - Actions: {action_count}")

            if action_count > 0:
                actions = Action.objects.filter(assigned_to=user)[:3]
                for action in actions:
                    self.stdout.write(f"  - Action ID: {action.id}, Text: {action.action[:50]}...")

        self.stdout.write("\n=== SAMPLE ACTIONS ===")
        all_actions = Action.objects.all()[:10]
        for action in all_actions:
            self.stdout.write(f"ID: {action.id}, Assigned: {action.assigned_to.username if action.assigned_to else 'None'}")

        self.stdout.write(f"\nTotal actions in DB: {Action.objects.count()}")