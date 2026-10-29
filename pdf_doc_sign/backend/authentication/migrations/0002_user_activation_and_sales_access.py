# Generated migration for User model updates
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='activation_token',
            field=models.UUIDField(default=uuid.uuid4),
        ),
        migrations.AddField(
            model_name='user',
            name='activation_token_created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='email_verified',
            field=models.BooleanField(default=False, help_text='Whether the user has verified their email address'),
        ),
        migrations.AddField(
            model_name='user',
            name='email_verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='sales_access_approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='sales_access_approved_by',
            field=models.ForeignKey(blank=True, help_text='Superuser who approved sales access', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales_access_approvals', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='user',
            name='sales_access_enabled',
            field=models.BooleanField(default=False, help_text='Individual sales access (usually org-level is used instead)'),
        ),
    ]
