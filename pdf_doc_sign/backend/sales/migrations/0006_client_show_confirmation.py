from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0005_invoice_content_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='show_confirmation',
            field=models.BooleanField(
                default=True,
                help_text='Enable delivery confirmation workflow (Send for Confirmation button + Confirmed column). Disable for simple sales-only clients.',
            ),
        ),
    ]
