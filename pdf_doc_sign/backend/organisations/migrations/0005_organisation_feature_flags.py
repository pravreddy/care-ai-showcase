# Per-org feature flags
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organisations', '0004_alter_organisationrequest_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisation',
            name='feature_flags',
            field=models.JSONField(
                blank=True, default=dict,
                help_text='Per-org feature toggles, e.g. {"show_courier": true, "enable_disputes": false}',
            ),
        ),
    ]
