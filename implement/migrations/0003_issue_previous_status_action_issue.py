# Generated migration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('implement', '0002_action_improvement_task_alter_action_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='previous_status',
            field=models.CharField(blank=True, choices=[('open', 'Open'), ('resolved', 'Resolved'), ('on_hold', 'On Hold'), ('dropped', 'Dropped'), ('escalated', 'Escalated')], max_length=20),
        ),
        migrations.AddField(
            model_name='action',
            name='issue',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='related_actions', to='implement.issue'),
        ),
    ]