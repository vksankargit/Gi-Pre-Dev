# Generated migration for structural changes: Add tracking to PPI and remove FPI

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0009_add_weekly_monthly_records'),
    ]

    operations = [
        # Add tracking_type to PPIProject
        migrations.AddField(
            model_name='ppiproject',
            name='tracking_type',
            field=models.CharField(
                choices=[('weekly', 'Weekly'), ('monthly', 'Monthly')],
                default='weekly',
                max_length=10
            ),
        ),

        # Add tracking_type to AnnualPPIProject
        migrations.AddField(
            model_name='annualppiproject',
            name='tracking_type',
            field=models.CharField(
                choices=[('weekly', 'Weekly'), ('monthly', 'Monthly')],
                default='weekly',
                max_length=10
            ),
        ),

        # Create PPIMilestone model
        migrations.CreateModel(
            name='PPIMilestone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period_number', models.IntegerField()),
                ('budget_value', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('ppi_project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='milestones', to='plans.ppiproject')),
            ],
            options={
                'db_table': 'ppi_milestones',
                'unique_together': {('ppi_project', 'period_number')},
            },
        ),

        # Create PPIWeeklyRecord model
        migrations.CreateModel(
            name='PPIWeeklyRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_number', models.IntegerField()),
                ('week_goal', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('week_actual', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('explanation', models.TextField(blank=True)),
                ('is_locked', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ppi_project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='weekly_records', to='plans.ppiproject')),
            ],
            options={
                'db_table': 'ppi_weekly_records',
                'unique_together': {('ppi_project', 'week_number')},
            },
        ),

        # Create PPIMonthlyRecord model
        migrations.CreateModel(
            name='PPIMonthlyRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month_number', models.IntegerField()),
                ('month_goal', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('month_actual', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('explanation', models.TextField(blank=True)),
                ('is_locked', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ppi_project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monthly_records', to='plans.ppiproject')),
            ],
            options={
                'db_table': 'ppi_monthly_records',
                'unique_together': {('ppi_project', 'month_number')},
            },
        ),

        # Remove FPI models (delete in reverse order of dependencies)
        migrations.DeleteModel(name='FPIMonthlyRecord'),
        migrations.DeleteModel(name='FPIMilestone'),
        migrations.DeleteModel(name='AnnualFPIParameter'),
        migrations.DeleteModel(name='FPIParameter'),
    ]
