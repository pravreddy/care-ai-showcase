# Generated migration for InvitationToken model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


def generate_secure_token():
    import secrets
    return secrets.token_urlsafe(32)


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_user_password_reset_fields'),
        ('organisations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvitationToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(help_text='Email address of the person being invited', max_length=254)),
                ('full_name', models.CharField(blank=True, help_text='Optional: Full name of invitee', max_length=255)),
                ('token', models.CharField(default=generate_secure_token, help_text='One-time use secure token', max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(help_text='Token expiry date (default: 7 days from creation)')),
                ('used_at', models.DateTimeField(blank=True, help_text='When the token was used (if at all)', null=True)),
                ('is_used', models.BooleanField(default=False, help_text='Whether token has been used')),
                ('created_by', models.ForeignKey(help_text='Admin who created this invitation', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invitations_sent', to=settings.AUTH_USER_MODEL)),
                ('organisation', models.ForeignKey(blank=True, help_text='Organisation the user is being invited to (optional)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='auth_invitation_tokens', to='organisations.organisation')),
                ('user', models.ForeignKey(blank=True, help_text='User created from this invitation', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='received_invitation', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='invitationtoken',
            index=models.Index(fields=['token'], name='authenticat_token_6d929d_idx'),
        ),
        migrations.AddIndex(
            model_name='invitationtoken',
            index=models.Index(fields=['email'], name='authenticat_email_a98e3f_idx'),
        ),
        migrations.AddIndex(
            model_name='invitationtoken',
            index=models.Index(fields=['is_used', 'expires_at'], name='authenticat_is_used_d6e4c8_idx'),
        ),
    ]
