# Generated migration to remove FPI and add PPI support to NumbersTracking
# Since FPIParameter was already deleted by plans.0010, we fake the removal and just update the schema

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('implement', '0008_add_project_action_links'),
        ('plans', '0010_add_ppi_tracking_and_remove_fpi'),
    ]

    # No operations needed - FPI fields were never added to the database
    # since migrations 0005 and 0006 were updated to not include them

    operations = []
