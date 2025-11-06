# Generated manually for quarterly plan upload history tracking

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plans', '0007_annualplanuploadhistory'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuarterlyPlanUploadHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_name', models.CharField(max_length=255)),
                ('file_path', models.FileField(upload_to='quarterly_plans/')),
                ('upload_status', models.CharField(choices=[('successful', 'Successful'), ('failed', 'Failed'), ('processing', 'Processing')], max_length=20)),
                ('error_log', models.TextField(blank=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('total_records', models.IntegerField(default=0)),
                ('processed_records', models.IntegerField(default=0)),
                ('error_records', models.IntegerField(default=0)),
                ('quarterly_plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='upload_history', to='plans.quarterlyplan')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'quarterly_plan_upload_history',
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
