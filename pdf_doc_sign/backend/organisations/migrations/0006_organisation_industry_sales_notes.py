from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organisations', '0005_organisation_feature_flags'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisation',
            name='industry',
            field=models.CharField(
                blank=True, default='', max_length=20,
                help_text='Industry vertical — determines column labels and terminology in Sales module',
                choices=[
                    ('CATERING', 'Catering & Food Delivery'),
                    ('HEALTHCARE', 'Home Healthcare & Nursing'),
                    ('WASTE', 'Waste Management & Skip Hire'),
                    ('PLANT_HIRE', 'Equipment & Plant Hire'),
                    ('LOGISTICS', 'Logistics & Courier'),
                    ('CLEANING', 'Cleaning Services'),
                    ('CONSTRUCTION', 'Construction & Trades'),
                    ('RETAIL', 'Retail & Wholesale'),
                    ('OTHER', 'Other'),
                ],
            ),
        ),
        migrations.AddField(
            model_name='organisation',
            name='sales_access_notes',
            field=models.TextField(
                blank=True,
                help_text='Notes from org admin when requesting sales access (use case description)',
            ),
        ),
    ]
