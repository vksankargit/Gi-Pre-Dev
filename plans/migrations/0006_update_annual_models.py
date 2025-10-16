# Generated manually for annual plan model updates

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plans', '0005_annual_plan_template_updates'),
    ]

    operations = [
        # AnnualGPIParameter: Add cumulation_type and update indicator_type choices
        migrations.AddField(
            model_name='annualgpiparameter',
            name='cumulation_type',
            field=models.CharField(choices=[('sum', 'Sum'), ('average', 'Average'), ('na', 'NA')], default='na', max_length=10),
        ),
        migrations.AlterField(
            model_name='annualgpiparameter',
            name='indicator_type',
            field=models.CharField(choices=[('outcome', 'Outcome'), ('activity', 'Activity')], max_length=10),
        ),

        # AnnualPPIProject: Add completion_criteria, start_date, end_date
        migrations.AddField(
            model_name='annualppiproject',
            name='completion_criteria',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='annualppiproject',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='annualppiproject',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
