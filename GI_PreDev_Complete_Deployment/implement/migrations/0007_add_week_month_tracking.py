# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('implement', '0006_add_parameter_links_to_action'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='week_number',
            field=models.IntegerField(blank=True, help_text='Week number within quarter (1-13) for weekly tracking', null=True),
        ),
        migrations.AddField(
            model_name='action',
            name='month_number',
            field=models.IntegerField(blank=True, help_text='Month number within quarter (1-3) for monthly tracking', null=True),
        ),
        migrations.AddField(
            model_name='issue',
            name='week_number',
            field=models.IntegerField(blank=True, help_text='Week number within quarter (1-13) for weekly tracking', null=True),
        ),
        migrations.AddField(
            model_name='issue',
            name='month_number',
            field=models.IntegerField(blank=True, help_text='Month number within quarter (1-3) for monthly tracking', null=True),
        ),
    ]
