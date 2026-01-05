# Generated manually for adding issue_type field and new statuses

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('implement', '0012_action_previous_status_action_quarter_number_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='issue_type',
            field=models.CharField(
                choices=[
                    ('acknowledge', 'Acknowledge'),
                    ('support', 'Support'),
                    ('act', 'Act'),
                    ('park', 'Park'),
                ],
                default='acknowledge',
                max_length=15
            ),
        ),
        migrations.AlterField(
            model_name='issue',
            name='status',
            field=models.CharField(
                choices=[
                    ('open', 'Open'),
                    ('resolved', 'Resolved'),
                    ('acknowledged', 'Acknowledged'),
                    ('parked', 'Parked'),
                    ('on_hold', 'On Hold'),
                    ('dropped', 'Dropped'),
                    ('escalated', 'Escalated'),
                ],
                default='open',
                max_length=20
            ),
        ),
    ]
