# Generated migration for adding Team Meeting Type and Scheduling fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0001_initial'),
    ]

    operations = [
        # Create TeamMeetingType model
        migrations.CreateModel(
            name='TeamMeetingType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='meeting_types', to='organizations.organization')),
            ],
            options={
                'db_table': 'team_meeting_types',
                'ordering': ['organization', 'name'],
                'unique_together': {('organization', 'name')},
            },
        ),

        # Add meeting_type field to Team
        migrations.AddField(
            model_name='team',
            name='meeting_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='teams', to='organizations.teammeetingtype'),
        ),

        # Add cadence field
        migrations.AddField(
            model_name='team',
            name='cadence',
            field=models.CharField(
                blank=True,
                choices=[
                    ('weekly', 'Weekly'),
                    ('monthly', 'Monthly'),
                    ('quarterly', 'Quarterly'),
                    ('annually', 'Annually')
                ],
                max_length=20,
                null=True
            ),
        ),

        # Add scheduling fields
        migrations.AddField(
            model_name='team',
            name='day_of_week',
            field=models.IntegerField(
                blank=True,
                choices=[
                    (0, 'Sunday'),
                    (1, 'Monday'),
                    (2, 'Tuesday'),
                    (3, 'Wednesday'),
                    (4, 'Thursday'),
                    (5, 'Friday'),
                    (6, 'Saturday')
                ],
                null=True
            ),
        ),

        migrations.AddField(
            model_name='team',
            name='week_number',
            field=models.IntegerField(
                blank=True,
                choices=[
                    (1, 'First Week'),
                    (2, 'Second Week'),
                    (3, 'Third Week'),
                    (4, 'Fourth Week'),
                    (5, 'Fifth Week')
                ],
                null=True
            ),
        ),

        migrations.AddField(
            model_name='team',
            name='month_in_quarter',
            field=models.IntegerField(
                blank=True,
                choices=[
                    (1, 'First Month'),
                    (2, 'Second Month'),
                    (3, 'Third Month')
                ],
                null=True
            ),
        ),

        migrations.AddField(
            model_name='team',
            name='quarter',
            field=models.CharField(
                blank=True,
                choices=[
                    ('Q1', 'Q1 (Jan-Mar)'),
                    ('Q2', 'Q2 (Apr-Jun)'),
                    ('Q3', 'Q3 (Jul-Sep)'),
                    ('Q4', 'Q4 (Oct-Dec)')
                ],
                max_length=2,
                null=True
            ),
        ),

        migrations.AddField(
            model_name='team',
            name='meeting_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
