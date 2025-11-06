# Generated manually to add assigned_to_team field
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0001_initial'),
        ('reviews', '0004_add_parameter_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewactionitem',
            name='assigned_to_team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='review_actions_team_assigned', to='organizations.team'),
        ),
    ]