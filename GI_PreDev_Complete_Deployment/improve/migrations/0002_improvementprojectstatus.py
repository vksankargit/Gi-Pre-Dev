# Generated manually for ImprovementProjectStatus model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('improve', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImprovementProjectStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('on_track', 'On Track'), ('at_risk', 'At Risk'), ('danger', 'Danger'), ('completed', 'Completed'), ('on_hold', 'On Hold')], max_length=20)),
                ('completion_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('revised_due_date', models.DateField(blank=True, null=True)),
                ('challenge', models.TextField(blank=True)),
                ('comments', models.TextField(blank=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_history', to='improve.improvementproject')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'improve_project_status',
                'ordering': ['-updated_at'],
            },
        ),
    ]