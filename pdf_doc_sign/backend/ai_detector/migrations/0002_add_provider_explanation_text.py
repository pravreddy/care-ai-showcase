from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_detector', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='aidetectionscan',
            name='extracted_text',
            field=models.TextField(blank=True, help_text='Full text extracted from the uploaded file'),
        ),
        migrations.AddField(
            model_name='aidetectionscan',
            name='provider',
            field=models.CharField(
                choices=[
                    ('huggingface', 'HuggingFace (Free)'),
                    ('grok', 'Grok (xAI)'),
                    ('openai', 'OpenAI'),
                ],
                default='huggingface',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='aidetectionscan',
            name='explanation',
            field=models.TextField(blank=True, help_text='Explanation from LLM provider (Grok/OpenAI only)'),
        ),
    ]
