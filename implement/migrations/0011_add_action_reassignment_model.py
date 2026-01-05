# Generated manually for ActionReassignment model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('implement', '0009_remove_fpi_add_ppi_to_numbersTracking'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionReassignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reassignment_reason', models.TextField(blank=True)),
                ('sequence_number', models.IntegerField(help_text='Position in the reassignment chain, starting from 1')),
                ('reassigned_at', models.DateTimeField(auto_now_add=True)),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reassignments', to='implement.action')),
                ('reassigned_from', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reassignments_made', to=settings.AUTH_USER_MODEL)),
                ('reassigned_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reassignments_received', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'action_reassignments',
                'ordering': ['action', 'sequence_number'],
                'unique_together': {('action', 'sequence_number')},
            },
        ),
    ]
