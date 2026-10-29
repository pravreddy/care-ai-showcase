# Generated migration for Organisation model updates
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organisations', '0001_initial'),
    ]

    operations = [
        # Organisation domain and auto-join fields
        migrations.AddField(
            model_name='organisation',
            name='domain',
            field=models.CharField(blank=True, help_text='Primary email domain (e.g., acerhealthcare.co.uk)', max_length=255),
        ),
        migrations.AddField(
            model_name='organisation',
            name='auto_join_enabled',
            field=models.BooleanField(default=False, help_text='Allow users with matching domain to join automatically on registration'),
        ),
        migrations.AddField(
            model_name='organisation',
            name='auto_join_default_role',
            field=models.CharField(choices=[('MEMBER', 'Member'), ('VIEWER', 'Viewer')], default='MEMBER', help_text='Default role for auto-joined members', max_length=20),
        ),
        
        # Organisation sales access fields
        migrations.AddField(
            model_name='organisation',
            name='sales_access_enabled',
            field=models.BooleanField(default=False, help_text='Enable Sales & Invoicing features for all members of this organisation'),
        ),
        migrations.AddField(
            model_name='organisation',
            name='sales_access_approved_by',
            field=models.ForeignKey(blank=True, help_text='Superuser who approved sales access for this organisation', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='org_sales_approvals', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='organisation',
            name='sales_access_approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        
        # Add domain index
        migrations.AddIndex(
            model_name='organisation',
            index=models.Index(fields=['domain'], name='organisatio_domain_156d96_idx'),
        ),
        
        # OrganisationInvitation model
        migrations.CreateModel(
            name='OrganisationInvitation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(help_text='Email address of the person being invited', max_length=254)),
                ('role', models.CharField(choices=[('OWNER', 'Owner'), ('ADMIN', 'Admin'), ('MANAGER', 'Manager'), ('MEMBER', 'Member'), ('VIEWER', 'Viewer')], default='MEMBER', max_length=20)),
                ('token', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('EXPIRED', 'Expired'), ('REVOKED', 'Revoked')], default='PENDING', max_length=20)),
                ('expires_at', models.DateTimeField()),
                ('accepted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('accepted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='accepted_invitations', to=settings.AUTH_USER_MODEL)),
                ('branch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='organisations.branch')),
                ('invited_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_invitations', to=settings.AUTH_USER_MODEL)),
                ('organisation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='organisations.organisation')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='organisationinvitation',
            index=models.Index(fields=['email', 'status'], name='organisatio_email_b74b7d_idx'),
        ),
        migrations.AddIndex(
            model_name='organisationinvitation',
            index=models.Index(fields=['token'], name='organisatio_token_b58bc6_idx'),
        ),
        
        # OrganisationRequest model
        migrations.CreateModel(
            name='OrganisationRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('organisation_name', models.CharField(max_length=255)),
                ('organisation_domain', models.CharField(max_length=255)),
                ('company_number', models.CharField(blank=True, max_length=20)),
                ('work_email', models.EmailField(max_length=254)),
                ('work_email_verified', models.BooleanField(default=False)),
                ('work_email_verification_token', models.UUIDField(default=uuid.uuid4)),
                ('work_email_verification_sent_at', models.DateTimeField(blank=True, null=True)),
                ('work_email_verified_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PENDING_WORK_EMAIL', 'Pending Work Email Verification'), ('PENDING_APPROVAL', 'Pending Admin Approval'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING_WORK_EMAIL', max_length=30)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organisation', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='source_request', to='organisations.organisation')),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organisation_requests', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_org_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Organisation Request',
                'verbose_name_plural': 'Organisation Requests',
                'ordering': ['-created_at'],
            },
        ),
    ]
