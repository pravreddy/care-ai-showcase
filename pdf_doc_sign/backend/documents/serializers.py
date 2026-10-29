"""
Document Serializers - DocSign UK
"""
from rest_framework import serializers
from .models import Document, DocumentSigner, Signature, SignatureField, DocumentAuditLog, DocumentTemplate


class SignatureFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignatureField
        fields = [
            'id', 'signer_index', 'field_type', 'page',
            'x_percent', 'y_percent', 'width_percent', 'height_percent',
            'label', 'required', 'filled_value', 'filled_at',
        ]
        read_only_fields = ['id', 'filled_value', 'filled_at']


class SignatureFieldCreateSerializer(serializers.Serializer):
    """Accepts a list of fields to save for a document in one go."""
    fields = serializers.ListField(child=serializers.DictField(), min_length=0)

    def validate_fields(self, value):
        for i, field in enumerate(value):
            if 'field_type' not in field:
                raise serializers.ValidationError(f'Field {i}: field_type is required')
            if field['field_type'] not in dict(SignatureField.FIELD_TYPE_CHOICES):
                raise serializers.ValidationError(f'Field {i}: invalid field_type')
            if 'page' not in field or not isinstance(field['page'], int) or field['page'] < 1:
                raise serializers.ValidationError(f'Field {i}: page must be a positive integer')
            for coord in ['x_percent', 'y_percent']:
                if coord not in field:
                    raise serializers.ValidationError(f'Field {i}: {coord} is required')
                v = field[coord]
                if not isinstance(v, (int, float)) or v < 0 or v > 100:
                    raise serializers.ValidationError(f'Field {i}: {coord} must be 0-100')
        return value


class DocumentSignerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentSigner
        fields = ['id', 'signer_name', 'signer_email', 'status', 'signing_order', 'signed_at']
        read_only_fields = ['id', 'status', 'signed_at']


class DocumentSerializer(serializers.ModelSerializer):
    signers = DocumentSignerSerializer(many=True, read_only=True)
    signature_fields = SignatureFieldSerializer(many=True, read_only=True)
    file_size_mb = serializers.ReadOnlyField()
    original_file_size_mb = serializers.ReadOnlyField()

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'file', 'file_size', 'file_size_mb',
            'original_file_size', 'original_file_size_mb',
            'was_compressed', 'compression_savings',
            'file_type', 'status', 'is_encrypted', 'expires_at',
            'created_at', 'updated_at', 'signed_at', 'signers',
            'signature_fields', 'page_count', 'sequential_signing',
        ]
        read_only_fields = [
            'id', 'file_size', 'file_type', 'status', 'created_at', 'signed_at',
            'original_file_size', 'was_compressed', 'compression_savings', 'page_count',
            'sequential_signing',
        ]


class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['title', 'description', 'file']

    def validate_file(self, value):
        from django.conf import settings

        # Size check (20MB to accommodate images/office docs before conversion)
        if value.size > settings.MAX_DOCUMENT_SIZE:
            size_mb = settings.MAX_DOCUMENT_SIZE // (1024 * 1024)
            raise serializers.ValidationError(f'File too large. Maximum {size_mb}MB.')

        ext = value.name.rsplit('.', 1)[-1].lower() if '.' in value.name else ''
        if ext not in settings.ALLOWED_DOCUMENT_TYPES:
            allowed = 'PDF, DOC, DOCX, JPG, PNG'
            raise serializers.ValidationError(
                f'File type .{ext} is not supported. '
                f'Supported formats: {allowed}'
            )

        # MIME type sanity check (prevent fake extensions)
        SAFE_MIMES = {
            'pdf': ['application/pdf'],
            'doc': ['application/msword', 'application/octet-stream'],
            'docx': [
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/octet-stream', 'application/zip',
            ],
            'jpg': ['image/jpeg'],
            'jpeg': ['image/jpeg'],
            'png': ['image/png'],
        }
        content_type = getattr(value, 'content_type', '').lower()
        expected_mimes = SAFE_MIMES.get(ext, [])
        if expected_mimes and content_type and content_type not in expected_mimes:
            # Warn but don't block — browsers sometimes send wrong MIME for office docs
            import logging
            logging.getLogger('documents').warning(
                f'MIME mismatch: {value.name} ext={ext} content_type={content_type}'
            )

        return value


class SignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signature
        fields = ['id', 'signature_type', 'signature_image', 'is_default', 'created_at']
        read_only_fields = ['id', 'created_at']


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentAuditLog
        fields = ['id', 'action', 'description', 'ip_address', 'created_at']


class DocumentTemplateSerializer(serializers.ModelSerializer):
    is_system_template = serializers.ReadOnlyField()

    class Meta:
        model = DocumentTemplate
        fields = [
            'id', 'name', 'description', 'category', 'template_file',
            'is_premium', 'is_active', 'is_system_template',
            'fields_config', 'page_count', 'use_count', 'created_at',
        ]
        read_only_fields = ['id', 'is_premium', 'use_count', 'created_at']


class TemplateCreateSerializer(serializers.Serializer):
    """Create a template from an existing document with its placed fields."""
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    category = serializers.ChoiceField(
        choices=DocumentTemplate.CATEGORY_CHOICES, default='OTHER',
    )
    document_id = serializers.UUIDField(help_text='Source document to create template from')
