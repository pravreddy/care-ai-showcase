import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organisations', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AIDetectionScan',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('original_filename', models.CharField(max_length=255)),
                ('file_type', models.CharField(
                    choices=[
                        ('pdf', 'PDF'), ('docx', 'Word Document'), ('txt', 'Plain Text'),
                        ('pptx', 'PowerPoint'), ('xlsx', 'Excel'), ('doc', 'Word (Legacy)'),
                    ],
                    max_length=10,
                )),
                ('file_size_bytes', models.IntegerField(default=0)),
                ('text_length', models.IntegerField(default=0, help_text='Number of characters extracted from the file')),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')],
                    default='pending',
                    max_length=20,
                )),
                ('ai_probability', models.FloatField(
                    blank=True, null=True,
                    help_text='0.0 = likely human, 1.0 = likely AI. From HuggingFace model.',
                )),
                ('human_probability', models.FloatField(blank=True, null=True)),
                ('verdict', models.CharField(
                    blank=True, max_length=20,
                    help_text='LIKELY_AI | POSSIBLY_AI | LIKELY_HUMAN',
                )),
                ('raw_response', models.JSONField(blank=True, null=True, help_text='Raw API response from HuggingFace')),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ai_scans',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('organisation', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ai_scans',
                    to='organisations.organisation',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='aidetectionscan',
            index=models.Index(fields=['user', 'created_at'], name='ai_detector_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='aidetectionscan',
            index=models.Index(fields=['organisation', 'created_at'], name='ai_detector_org_id_idx'),
        ),
    ]
