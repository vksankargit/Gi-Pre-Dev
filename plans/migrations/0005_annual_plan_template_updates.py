# Generated manually for annual plan template updates

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0004_auto_20250929_0946'),
    ]

    operations = [
        # FPIParameter: Add Q1-Q4 budget fields
        migrations.AddField(
            model_name='fpiparameter',
            name='q1_budget',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='fpiparameter',
            name='q2_budget',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='fpiparameter',
            name='q3_budget',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='fpiparameter',
            name='q4_budget',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),

        # GPIParameter: Add cumulation_type and update indicator_type choices
        migrations.AddField(
            model_name='gpiparameter',
            name='cumulation_type',
            field=models.CharField(choices=[('sum', 'Sum'), ('average', 'Average'), ('na', 'NA')], default='na', max_length=10),
        ),
        migrations.AlterField(
            model_name='gpiparameter',
            name='indicator_type',
            field=models.CharField(choices=[('outcome', 'Outcome'), ('activity', 'Activity')], max_length=10),
        ),

        # GPIParameter: Add Q1-Q4 budget fields
        migrations.AddField(
            model_name='gpiparameter',
            name='q1_budget',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='gpiparameter',
            name='q2_budget',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='gpiparameter',
            name='q3_budget',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='gpiparameter',
            name='q4_budget',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),

        # PPIProject: Add annual_goal and Q1-Q4 budget fields
        migrations.AddField(
            model_name='ppiproject',
            name='annual_goal',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='ppiproject',
            name='q1_budget',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='ppiproject',
            name='q2_budget',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='ppiproject',
            name='q3_budget',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='ppiproject',
            name='q4_budget',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
