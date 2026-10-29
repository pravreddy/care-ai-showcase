"""
Add 'binoculars' to AIDetectionScan.provider choices.

Choices are not enforced at the database level, so this is a no-op for the
table schema — but keeping the migration in sync means `makemigrations
--check` stays clean and the admin dropdown lists the new provider.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_detector', '0007_add_chunk_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='aidetectionscan',
            name='provider',
            field=models.CharField(
                choices=[
                    ('auto', 'Auto (smart fallback)'),
                    ('groq', 'Quick Scan (Llama 8B)'),
                    ('groq_deep', 'Deep Scan (Llama 70B)'),
                    ('gemini', 'Gemini Flash (1M context)'),
                    ('mistral', 'Mistral AI (European)'),
                    ('siliconflow', 'SiliconFlow (Llama 70B)'),
                    ('cloudflare', 'Cloudflare Workers AI'),
                    ('huggingface', 'HuggingFace (Free)'),
                    ('grok', 'Grok (xAI)'),
                    ('openai', 'OpenAI'),
                    ('binoculars', 'Binoculars (local statistical)'),
                ],
                default='groq',
                max_length=20,
            ),
        ),
    ]
