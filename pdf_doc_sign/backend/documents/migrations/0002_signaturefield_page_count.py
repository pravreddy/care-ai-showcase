"""
Migration: Add SignatureField model and page_count to Document.
Phase 2 — PDF preview with drag-and-drop signature field placement.
"""
import uuid
import documents.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        # Add page_count to Document
        migrations.AddField(
            model_name='document',
            name='page_count',
            field=models.IntegerField(blank=True, help_text='Number of pages in PDF', null=True),
        ),

        # Create SignatureField model
        migrations.CreateModel(
            name='SignatureField',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('signer_index', models.IntegerField(default=1, help_text='Which signer (1-indexed) this field is for')),
                ('field_type', models.CharField(choices=[
                    ('SIGNATURE', 'Signature'),
                    ('DATE', 'Date'),
                    ('NAME', 'Full Name'),
                    ('TEXT', 'Text Field'),
                    ('INITIALS', 'Initials'),
                ], default='SIGNATURE', max_length=20)),
                ('page', models.IntegerField(help_text='Page number (1-indexed)')),
                ('x_percent', models.FloatField(help_text='X position as percentage of page width (0-100)')),
                ('y_percent', models.FloatField(help_text='Y position as percentage of page height (0-100)')),
                ('width_percent', models.FloatField(default=20, help_text='Width as percentage of page width')),
                ('height_percent', models.FloatField(default=5, help_text='Height as percentage of page height')),
                ('label', models.CharField(blank=True, max_length=100)),
                ('required', models.BooleanField(default=True)),
                ('filled_value', models.TextField(blank=True, help_text='Text value for date/name/text fields')),
                ('filled_signature', models.ImageField(blank=True, null=True, upload_to=documents.models.signature_upload_path)),
                ('filled_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='signature_fields', to='documents.document')),
            ],
            options={
                'ordering': ['document', 'page', 'y_percent', 'x_percent'],
            },
        ),

        # Add indexes for SignatureField
        migrations.AddIndex(
            model_name='signaturefield',
            index=models.Index(fields=['document', 'signer_index'], name='documents_s_documen_idx'),
        ),

        # Update DocumentAuditLog action choices (add PREPARED)
        migrations.AlterField(
            model_name='documentauditlog',
            name='action',
            field=models.CharField(choices=[
                ('CREATED', 'Created'),
                ('VIEWED', 'Viewed'),
                ('DOWNLOADED', 'Downloaded'),
                ('SIGNED', 'Signed'),
                ('SENT', 'Sent for Signing'),
                ('CANCELLED', 'Cancelled'),
                ('EXPIRED', 'Expired'),
                ('PREPARED', 'Fields Placed'),
            ], max_length=20),
        ),
    ]
