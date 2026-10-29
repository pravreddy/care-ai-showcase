# Invoice content options — Batch 3
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0004_rename_sales_client_date_idx_sales_daily_client__059203_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='include_daily_breakdown',
            field=models.BooleanField(default=True, help_text="Show each day's items and totals in PDF"),
        ),
        migrations.AddField(
            model_name='invoice',
            name='include_packing_charges',
            field=models.BooleanField(default=True, help_text='Show packing charges column'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='include_courier_charges',
            field=models.BooleanField(default=True, help_text='Show courier/delivery charges column'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='include_item_detail',
            field=models.BooleanField(default=True, help_text='Show item-level detail (5x Chapathi @10) vs just Food total'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='attach_excel',
            field=models.BooleanField(default=False, help_text='Attach Excel/CSV daily breakdown with invoice email'),
        ),
    ]
