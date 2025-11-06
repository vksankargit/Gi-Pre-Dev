import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')
django.setup()

from django.core.management import call_command
from django.db.migrations.questioner import InteractiveMigrationQuestioner

# Patch the questioner to always return no for renames
original_ask_rename = InteractiveMigrationQuestioner.ask_rename
def patched_ask_rename(self, model_name, old_name, new_name, field_instance):
    return False

InteractiveMigrationQuestioner.ask_rename = patched_ask_rename

try:
    call_command('makemigrations', 'plans', interactive=False)
finally:
    InteractiveMigrationQuestioner.ask_rename = original_ask_rename
