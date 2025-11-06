# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('implement', '0003_issue_previous_status_action_issue'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='status',
            field=models.CharField(
                choices=[
                    ('not_started', 'Not Started'),
                    ('in_progress', 'In Progress'),
                    ('at_risk', 'At Risk'),
                    ('danger', 'Danger'),
                    ('overdue', 'Overdue'),
                    ('done', 'Done'),
                    ('completed', 'Completed'),
                    ('rejected', 'Rejected'),
                    ('carry_forward', 'Carry Forward'),
                ],
                default='not_started',
                max_length=20
            ),
        ),
    ]
