# Fixed: RenameIndex replaced with safe_rename_index to handle missing indexes
# Renumbered to 0007 to follow main's 0006_client_show_confirmation

from django.db import migrations, models


def safe_rename_index(old_name, new_name):
    def forwards(apps, schema_editor):
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_indexes WHERE indexname = %s", [old_name])
            if cursor.fetchone():
                schema_editor.execute(f'ALTER INDEX IF EXISTS "{old_name}" RENAME TO "{new_name}"')
    return forwards


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0006_client_show_confirmation'),
    ]

    operations = [
        migrations.RunPython(safe_rename_index('sales_client_date_idx', 'sales_daily_client__059203_idx'), noop),
        migrations.RunPython(safe_rename_index('sales_date_status_idx', 'sales_daily_date_98cfa4_idx'), noop),
        migrations.RunPython(safe_rename_index('inv_client_dates_idx', 'sales_invoi_client__939fb1_idx'), noop),
        migrations.RunPython(safe_rename_index('inv_status_idx', 'sales_invoi_status_4e3758_idx'), noop),
        migrations.AlterField(
            model_name='invoice',
            name='currency',
            field=models.CharField(choices=[('GBP', 'GBP'), ('INR', 'INR'), ('USD', 'USD'), ('EUR', 'EUR'), ('CAD', 'CAD'), ('AUD', 'AUD')], default='INR', max_length=3),
        ),
    ]
