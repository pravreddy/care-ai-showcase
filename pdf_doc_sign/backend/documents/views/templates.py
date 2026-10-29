"""
DocumentTemplateViewSet — Template library with save-from-document and use-template flows.
Lists system templates + user's own templates. Full CRUD for user templates.
"""
import logging

from django.core.files.base import ContentFile
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from documents.models import Document, DocumentTemplate, SignatureField, DocumentAuditLog
from documents.serializers import (
    DocumentSerializer, DocumentTemplateSerializer,
    SignatureFieldSerializer, TemplateCreateSerializer,
)
from .mixins import get_client_ip

logger = logging.getLogger('documents')


class DocumentTemplateViewSet(viewsets.ModelViewSet):
    """
    Template library — lists system templates + user's own templates.
    Supports full CRUD for user templates, read-only for system templates.
    """
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DocumentTemplateSerializer

    def get_queryset(self):
        """Return active system templates + user's own templates."""
        return DocumentTemplate.objects.filter(
            Q(user__isnull=True, is_active=True) | Q(user=self.request.user, is_active=True)
        )

    def perform_destroy(self, instance):
        """Only allow deleting own templates (soft-delete via is_active=False)."""
        if instance.user != self.request.user:
            raise PermissionDenied('Cannot delete system templates.')
        instance.is_active = False
        instance.save(update_fields=['is_active'])

    # ─── Save from document ───

    @action(detail=False, methods=['post'])
    def save_from_document(self, request):
        """
        Save a document (with its placed fields) as a reusable template.
        POST /api/templates/save_from_document/
        Body: { name, description?, category?, document_id }
        """
        serializer = TemplateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Get the source document (must belong to the user)
        try:
            doc = Document.objects.get(id=data['document_id'], user=request.user)
        except Document.DoesNotExist:
            return Response({'error': 'Document not found.'}, status=404)

        # Snapshot the current signature fields as JSON config
        fields = SignatureField.objects.filter(document=doc).order_by('page', 'y_percent')
        fields_config = [
            {
                'field_type': f.field_type,
                'signer_index': f.signer_index,
                'page': f.page,
                'x_percent': f.x_percent,
                'y_percent': f.y_percent,
                'width_percent': f.width_percent,
                'height_percent': f.height_percent,
                'label': f.label,
                'required': f.required,
            }
            for f in fields
        ]

        # Copy the PDF file for the template
        try:
            with open(doc.file.path, 'rb') as src:
                pdf_content = ContentFile(src.read())
        except FileNotFoundError:
            return Response({'error': 'Source document PDF not found.'}, status=404)

        template = DocumentTemplate.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            category=data.get('category', 'OTHER'),
            user=request.user,
            source_document=doc,
            fields_config=fields_config,
            page_count=doc.page_count,
        )
        template.template_file.save(
            f'template_{template.id}.pdf', pdf_content, save=True,
        )

        return Response(
            DocumentTemplateSerializer(template).data,
            status=status.HTTP_201_CREATED,
        )

    # ─── Use template ───

    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """
        Create a new document from a template.
        Copies the template PDF, creates a DRAFT document, and pre-places fields.
        POST /api/templates/{id}/use_template/
        Body: { title? }  (optional override title)
        """
        template = self.get_object()

        if template.is_premium and getattr(request.user, 'subscription_plan', 'FREE') == 'FREE':
            return Response({'error': 'Premium templates require a paid plan.'}, status=403)

        if not request.user.can_upload_document:
            return Response(
                {'error': 'Document limit reached. Upgrade your plan.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        title = request.data.get('title', f'{template.name} \u2014 Copy')

        # Copy the template PDF
        try:
            with open(template.template_file.path, 'rb') as src:
                pdf_content = ContentFile(src.read())
                file_size = len(pdf_content)
        except FileNotFoundError:
            return Response({'error': 'Template file not found.'}, status=404)

        # Create draft document
        doc = Document.objects.create(
            user=request.user,
            title=title,
            description=f'Created from template: {template.name}',
            file_size=file_size,
            file_type='pdf',
            page_count=template.page_count,
        )
        doc.file.save(f'{doc.id}.pdf', pdf_content, save=True)

        # Pre-place signature fields from template config
        if template.fields_config:
            for fc in template.fields_config:
                SignatureField.objects.create(
                    document=doc,
                    field_type=fc.get('field_type', 'SIGNATURE'),
                    signer_index=fc.get('signer_index', 1),
                    page=fc.get('page', 1),
                    x_percent=fc.get('x_percent', 10),
                    y_percent=fc.get('y_percent', 80),
                    width_percent=fc.get('width_percent', 20),
                    height_percent=fc.get('height_percent', 5),
                    label=fc.get('label', ''),
                    required=fc.get('required', True),
                )

        # Increment template use count
        template.use_count += 1
        template.save(update_fields=['use_count'])

        # Increment user document usage
        request.user.increment_document_usage()

        # Audit log
        DocumentAuditLog.objects.create(
            document=doc, user=request.user, action='CREATED',
            description=f'Created from template: {template.name}',
            ip_address=get_client_ip(request),
        )

        return Response({
            'document': DocumentSerializer(doc).data,
            'message': f'Document created from template "{template.name}"',
            'fields_placed': len(template.fields_config) if template.fields_config else 0,
        }, status=status.HTTP_201_CREATED)
