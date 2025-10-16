# Generated manually to add parameter fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0003_fix_database_schema'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewactionitem',
            name='parameter_type',
            field=models.CharField(blank=True, choices=[('fpi', 'FPI'), ('gpi', 'GPI'), ('ppi', 'PPI')], max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='reviewactionitem',
            name='parameter_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]