"""
Add Document.sequential_signing.

When true, signers are emailed one at a time in signing_order: only the
first signer is notified on send, and each subsequent signer is released
once the previous one completes (see SigningOrchestrator). Defaults to
False, preserving the existing "everyone emailed at once" behaviour.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0006_signaturefield_checkbox_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='sequential_signing',
            field=models.BooleanField(
                default=False,
                help_text=(
                    'If true, signers are emailed one at a time in signing_order; '
                    'each is released only after the previous signer completes.'
                ),
            ),
        ),
    ]
