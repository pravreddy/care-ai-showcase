"""
Migration: Add user-owned templates support to DocumentTemplate.
Adds: user (FK), fields_config (JSON), source_document (FK), page_count, use_count.
Makes description blank=True and category default='OTHER'.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('documents', '0002_signaturefield_page_count'),
    ]

    operations = [
        # Add user FK (nullable — null means system template)
        migrations.AddField(
            model_name='documenttemplate',
            name='user',
            field=models.ForeignKey(
                blank=True, null=True,
                help_text='Owner of this template. Null for system templates.',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='templates',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Add fields_config JSON
        migrations.AddField(
            model_name='documenttemplate',
            name='fields_config',
            field=models.JSONField(
                blank=True, default=list,
                help_text='Saved signature field positions for this template.',
            ),
        ),
        # Add source_document FK
        migrations.AddField(
            model_name='documenttemplate',
            name='source_document',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='derived_templates',
                to='documents.document',
            ),
        ),
        # Add page_count
        migrations.AddField(
            model_name='documenttemplate',
            name='page_count',
            field=models.IntegerField(blank=True, null=True),
        ),
        # Add use_count
        migrations.AddField(
            model_name='documenttemplate',
            name='use_count',
            field=models.IntegerField(default=0, help_text='How many times this template has been used'),
        ),
        # Make description optional
        migrations.AlterField(
            model_name='documenttemplate',
            name='description',
            field=models.TextField(blank=True),
        ),
        # Set default for category
        migrations.AlterField(
            model_name='documenttemplate',
            name='category',
            field=models.CharField(choices=[
                ('NDA', 'Non-Disclosure Agreement'), ('CONTRACT', 'Contract'),
                ('INVOICE', 'Invoice'), ('PROPOSAL', 'Proposal'),
                ('AGREEMENT', 'Agreement'), ('OTHER', 'Other'),
            ], default='OTHER', max_length=20),
        ),
        # Indexes
        migrations.AddIndex(
            model_name='documenttemplate',
            index=models.Index(fields=['user', 'is_active'], name='documents_d_user_id_active_idx'),
        ),
        migrations.AddIndex(
            model_name='documenttemplate',
            index=models.Index(fields=['category'], name='documents_d_category_idx'),
        ),
    ]
