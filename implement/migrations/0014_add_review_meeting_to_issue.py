# Generated manually on 2025-12-24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('implement', '0013_add_issue_type_and_new_statuses'),
        ('reviews', '0006_alter_reviewnote_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='review_meeting',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='issues', to='reviews.reviewmeeting'),
        ),
    ]
