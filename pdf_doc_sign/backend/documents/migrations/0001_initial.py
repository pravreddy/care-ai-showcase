import django.db.models.deletion
import documents.models
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('file', models.FileField(upload_to=documents.models.document_upload_path)),
                ('file_size', models.BigIntegerField(help_text='Final size after compression')),
                ('file_type', models.CharField(max_length=10)),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('PENDING', 'Pending Signature'), ('SIGNED', 'Signed'), ('EXPIRED', 'Expired'), ('CANCELLED', 'Cancelled')], default='DRAFT', max_length=20)),
                ('is_encrypted', models.BooleanField(default=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('signed_at', models.DateTimeField(blank=True, null=True)),
                ('original_file_size', models.BigIntegerField(blank=True, help_text='Size before compression', null=True)),
                ('was_compressed', models.BooleanField(default=False)),
                ('compression_savings', models.FloatField(default=0, help_text='Percentage saved by compression')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(model_name='document', index=models.Index(fields=['user', 'status'], name='documents_d_user_id_idx')),
        migrations.AddIndex(model_name='document', index=models.Index(fields=['created_at'], name='documents_d_created_idx')),
        migrations.CreateModel(
            name='DocumentSigner',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('signer_name', models.CharField(max_length=255)),
                ('signer_email', models.EmailField(max_length=254)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('SIGNED', 'Signed'), ('DECLINED', 'Declined')], default='PENDING', max_length=20)),
                ('signing_order', models.IntegerField(default=1)),
                ('signed_at', models.DateTimeField(blank=True, null=True)),
                ('signature_image', models.ImageField(blank=True, null=True, upload_to=documents.models.signature_upload_path)),
                ('access_token', models.CharField(max_length=100, unique=True)),
                ('access_expires_at', models.DateTimeField()),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='signers', to='documents.document')),
                ('signer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['document', 'signing_order'], 'unique_together': {('document', 'signer_email')}},
        ),
        migrations.CreateModel(
            name='Signature',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('signature_type', models.CharField(choices=[('DRAWN', 'Hand Drawn'), ('TYPED', 'Typed'), ('UPLOADED', 'Uploaded')], max_length=20)),
                ('signature_image', models.ImageField(upload_to=documents.models.signature_upload_path)),
                ('is_default', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='signatures', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='DocumentAuditLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('action', models.CharField(choices=[('CREATED', 'Created'), ('VIEWED', 'Viewed'), ('DOWNLOADED', 'Downloaded'), ('SIGNED', 'Signed'), ('SENT', 'Sent for Signing'), ('CANCELLED', 'Cancelled'), ('EXPIRED', 'Expired')], max_length=20)),
                ('description', models.TextField(blank=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='documents.document')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(model_name='documentauditlog', index=models.Index(fields=['document', 'created_at'], name='documents_a_doc_created_idx')),
        migrations.CreateModel(
            name='DocumentTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('category', models.CharField(choices=[('NDA', 'Non-Disclosure Agreement'), ('CONTRACT', 'Contract'), ('INVOICE', 'Invoice'), ('PROPOSAL', 'Proposal'), ('AGREEMENT', 'Agreement'), ('OTHER', 'Other')], max_length=20)),
                ('template_file', models.FileField(upload_to='templates/')),
                ('is_active', models.BooleanField(default=True)),
                ('is_premium', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['category', 'name']},
        ),
    ]
