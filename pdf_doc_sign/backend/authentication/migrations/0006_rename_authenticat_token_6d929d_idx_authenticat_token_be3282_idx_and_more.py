# Fixed: removed duplicate RenameIndex (already handled by 0005 with safe_rename_index)
# Only keeps the new AddField operations for AI scan tracking + coupon code

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0005_rename_authenticat_token_6d929d_idx_authenticat_token_be3282_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='ai_scans_used_this_month',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='coupon_code',
            field=models.CharField(blank=True, help_text='Coupon code used at signup', max_length=50),
        ),
        migrations.AddField(
            model_name='user',
            name='extra_ai_scans_purchased',
            field=models.IntegerField(default=0),
        ),
    ]
