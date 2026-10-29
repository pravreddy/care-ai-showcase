# This migration is no longer needed.
# The fields (ai_scans_used_this_month, extra_ai_scans_purchased, coupon_code)
# are now in 0006 after it was fixed to remove duplicate RenameIndex operations.
# This file is kept to avoid breaking the migration chain.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0006_rename_authenticat_token_6d929d_idx_authenticat_token_be3282_idx_and_more'),
    ]

    operations = [
        # No operations — fields already added in 0006
    ]
