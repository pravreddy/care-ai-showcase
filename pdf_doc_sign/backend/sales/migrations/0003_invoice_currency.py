"""
Migration: Add currency field to Invoice model.
User selects currency at invoice generation time.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0002_dailysale_client_confirmation'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='currency',
            field=models.CharField(
                choices=[('GBP', 'GBP'), ('INR', 'INR'), ('USD', 'USD'), ('EUR', 'EUR')],
                default='INR',
                max_length=3,
            ),
        ),
    ]
