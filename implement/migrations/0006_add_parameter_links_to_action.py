# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('implement', '0005_add_parameter_links_to_issue'),
        ('plans', '0004_auto_20250929_0946'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='gpi_parameter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='plans.gpiparameter'),
        ),
        # FPI parameter field removed - not needed anymore
    ]
