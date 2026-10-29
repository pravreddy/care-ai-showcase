"""
Add CHECKBOX to SignatureField.field_type choices.

Signers can tick/untick a checkbox; the filled_value stores 'true' or 'false'
(or stays blank if the signer skipped a non-required checkbox). Required
checkboxes must be ticked to submit — see FieldProcessor.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0005_rename_documents_d_user_id_idx_documents_d_user_id_200c84_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='signaturefield',
            name='field_type',
            field=models.CharField(
                choices=[
                    ('SIGNATURE', 'Signature'),
                    ('DATE', 'Date'),
                    ('NAME', 'Full Name'),
                    ('TEXT', 'Text Field'),
                    ('INITIALS', 'Initials'),
                    ('CHECKBOX', 'Checkbox'),
                ],
                default='SIGNATURE',
                max_length=20,
            ),
        ),
    ]
