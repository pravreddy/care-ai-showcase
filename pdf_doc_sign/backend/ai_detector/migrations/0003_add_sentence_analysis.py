from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_detector', '0002_add_provider_explanation_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='aidetectionscan',
            name='sentence_analysis',
            field=models.JSONField(
                blank=True, null=True,
                help_text='Per-sentence AI probability scores from LLM providers',
            ),
        ),
    ]
