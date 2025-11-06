# Generated manually for historical record tracking

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0008_quarterlyplanuploadhistory'),
    ]

    operations = [
        migrations.CreateModel(
            name='GPIWeeklyRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_number', models.IntegerField()),
                ('week_goal', models.DecimalField(blank=True, decimal_places=2, help_text='Goal entered for this week', max_digits=15, null=True)),
                ('week_actual', models.DecimalField(blank=True, decimal_places=2, help_text='Actual achieved for this week', max_digits=15, null=True)),
                ('explanation', models.TextField(blank=True)),
                ('is_locked', models.BooleanField(default=False, help_text='Locked after weekly review is completed')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('gpi_parameter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='weekly_records', to='plans.gpiparameter')),
            ],
            options={
                'db_table': 'gpi_weekly_records',
                'ordering': ['week_number'],
            },
        ),
        migrations.CreateModel(
            name='GPIMonthlyRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month_number', models.IntegerField()),
                ('month_goal', models.DecimalField(blank=True, decimal_places=2, help_text='Goal entered for this month', max_digits=15, null=True)),
                ('month_actual', models.DecimalField(blank=True, decimal_places=2, help_text='Actual achieved for this month', max_digits=15, null=True)),
                ('explanation', models.TextField(blank=True)),
                ('is_locked', models.BooleanField(default=False, help_text='Locked after monthly review is completed')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('gpi_parameter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monthly_records', to='plans.gpiparameter')),
            ],
            options={
                'db_table': 'gpi_monthly_records',
                'ordering': ['month_number'],
            },
        ),
        migrations.CreateModel(
            name='FPIMonthlyRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month_number', models.IntegerField()),
                ('month_goal', models.DecimalField(blank=True, decimal_places=2, help_text='Goal entered for this month', max_digits=15, null=True)),
                ('month_actual', models.DecimalField(blank=True, decimal_places=2, help_text='Actual achieved for this month', max_digits=15, null=True)),
                ('explanation', models.TextField(blank=True)),
                ('is_locked', models.BooleanField(default=False, help_text='Locked after monthly review is completed')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('fpi_parameter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monthly_records', to='plans.fpiparameter')),
            ],
            options={
                'db_table': 'fpi_monthly_records',
                'ordering': ['month_number'],
            },
        ),
        migrations.AddConstraint(
            model_name='gpiweeklyrecord',
            constraint=models.UniqueConstraint(fields=('gpi_parameter', 'week_number'), name='unique_gpi_weekly_record'),
        ),
        migrations.AddConstraint(
            model_name='gpimonthlyrecord',
            constraint=models.UniqueConstraint(fields=('gpi_parameter', 'month_number'), name='unique_gpi_monthly_record'),
        ),
        migrations.AddConstraint(
            model_name='fpimonthlyrecord',
            constraint=models.UniqueConstraint(fields=('fpi_parameter', 'month_number'), name='unique_fpi_monthly_record'),
        ),
    ]
