# Generated manually to avoid interactive prompts

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('implement', '0007_add_week_month_tracking'),
        ('plans', '0004_auto_20250929_0946'),
        ('improve', '0002_improvementprojectstatus'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='ppi_project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='plans.ppiproject'),
        ),
        migrations.AddField(
            model_name='action',
            name='improvement_project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='improve.improvementproject'),
        ),
        migrations.AddField(
            model_name='issue',
            name='ppi_project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='issues', to='plans.ppiproject'),
        ),
        migrations.AddField(
            model_name='issue',
            name='improvement_project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='issues', to='improve.improvementproject'),
        ),
        migrations.AddField(
            model_name='issue',
            name='action',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='issues', to='implement.action'),
        ),
    ]
