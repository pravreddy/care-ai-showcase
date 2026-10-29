"""
FieldService — Signature field placement management.
"""
import logging

logger = logging.getLogger('documents.fields')


class FieldService:

    @staticmethod
    def save_fields(document, fields_data, user=None, ip_address=None):
        """
        Replace all signature fields for a document.
        Returns: list of created SignatureField instances
        """
        from documents.models import SignatureField, DocumentAuditLog

        SignatureField.objects.filter(document=document).delete()

        created = []
        for field_data in fields_data:
            sf = SignatureField.objects.create(
                document=document,
                signer_index=field_data.get('signer_index', 1),
                field_type=field_data['field_type'],
                page=field_data['page'],
                x_percent=field_data['x_percent'],
                y_percent=field_data['y_percent'],
                width_percent=field_data.get('width_percent', 20),
                height_percent=field_data.get('height_percent', 5),
                label=field_data.get('label', ''),
                required=field_data.get('required', True),
            )
            created.append(sf)

        if user:
            DocumentAuditLog.objects.create(
                document=document, user=user, action='PREPARED',
                description=f'{len(created)} signature field(s) placed',
                ip_address=ip_address,
            )

        return created
