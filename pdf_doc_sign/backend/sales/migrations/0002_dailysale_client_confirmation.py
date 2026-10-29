"""
Migration: Add client delivery confirmation fields to DailySale.
Adds: client_confirmed, client_confirmed_at, client_confirmation_note,
      confirmation_token, confirmation_token_expires_at.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailysale',
            name='client_confirmed',
            field=models.BooleanField(default=False, help_text='Client confirmed delivery received'),
        ),
        migrations.AddField(
            model_name='dailysale',
            name='client_confirmed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='dailysale',
            name='client_confirmation_note',
            field=models.TextField(blank=True, help_text='Optional note from client on confirmation'),
        ),
        migrations.AddField(
            model_name='dailysale',
            name='confirmation_token',
            field=models.CharField(
                blank=True, max_length=100, null=True, unique=True,
                help_text='Token for email-based confirmation (no login needed)',
            ),
        ),
        migrations.AddField(
            model_name='dailysale',
            name='confirmation_token_expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
