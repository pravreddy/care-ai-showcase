"""
DocumentViewSet — Authenticated CRUD for user's documents.
Handles upload, download, fields, signing, reminders, audit.
"""
import logging
import os

from django.http import FileResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from documents.models import Document, DocumentSigner, SignatureField, DocumentAuditLog
from documents.serializers import (
    DocumentSerializer, DocumentUploadSerializer, DocumentSignerSerializer,
    AuditLogSerializer, SignatureFieldSerializer, SignatureFieldCreateSerializer,
)
from documents.services import (
    DocumentService, SigningService, FieldService, BulkSendService,
    generate_signed_pdf, generate_progress_pdf_bytes, generate_audit_certificate,
)
from .mixins import get_client_ip

logger = logging.getLogger('documents')


class DocumentViewSet(viewsets.ModelViewSet):
    """Private dashboard for users to manage their own documents."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DocumentSerializer

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return DocumentUploadSerializer
        return DocumentSerializer

    # ─── Upload ───

    def create(self, request, *args, **kwargs):
        """Upload a document — compression and page count handled by DocumentService."""
        user = request.user

        if not user.can_upload_document:
            return Response(
                {'error': 'You have reached your document limit. Upgrade your plan or purchase extra documents.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            doc = DocumentService.handle_upload(
                user=user,
                title=serializer.validated_data['title'],
                file_obj=request.FILES['file'],
                description=serializer.validated_data.get('description', ''),
                ip_address=get_client_ip(request),
            )
        except Exception as e:
            logger.error(f'[UPLOAD] Failed: {e}')
            return Response({'error': f'Failed to save document: {str(e)}'}, status=500)

        return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)

    # ─── Signing ───

    @action(detail=True, methods=['post'])
    def send_for_signing(self, request, pk=None):
        document = self.get_object()
        signers_data = request.data.get('signers', [])

        if not signers_data:
            return Response({'error': 'At least one signer required'}, status=400)

        sequential = bool(request.data.get('sequential', False))

        result = SigningService.send_for_signing(
            document=document, signers_data=signers_data,
            sender=request.user, ip_address=get_client_ip(request),
            sequential=sequential,
        )

        return Response({
            'message': f'Document sent to {len(result["created_signers"])} signer(s)',
            'emails_sent': result['emails_sent'],
            'emails_failed': result['emails_failed'],
            'email_results': result['email_results'],
            'signers': DocumentSignerSerializer(result['created_signers'], many=True).data,
            'document': DocumentSerializer(document).data,
        })

    @action(detail=True, methods=['post'])
    def send_reminder(self, request, pk=None):
        """
        Send a reminder email to a specific pending signer, or all pending signers.
        Body: { "signer_id": "uuid" } — remind one signer
        Body: {}                      — remind all pending signers
        """
        from documents.emails.notifications import send_reminder_email

        document = self.get_object()

        if document.status != 'PENDING':
            return Response({'error': 'Reminders can only be sent for pending documents.'}, status=400)

        signer_id = request.data.get('signer_id')

        if signer_id:
            try:
                signer = DocumentSigner.objects.get(
                    id=signer_id, document=document, status='PENDING',
                )
            except DocumentSigner.DoesNotExist:
                return Response({'error': 'Signer not found or already signed.'}, status=404)

            sent = send_reminder_email(signer, document, request.user)
            return Response({
                'message': f'Reminder sent to {signer.signer_name}' if sent else 'Failed to send reminder',
                'sent': sent,
            })
        else:
            pending = DocumentSigner.objects.filter(document=document, status='PENDING')
            if not pending.exists():
                return Response({'error': 'No pending signers to remind.'}, status=400)

            results = []
            for signer in pending:
                sent = send_reminder_email(signer, document, request.user)
                results.append({'email': signer.signer_email, 'sent': sent})

            sent_count = sum(1 for r in results if r['sent'])
            return Response({
                'message': f'Reminders sent to {sent_count} of {len(results)} pending signer(s)',
                'results': results,
            })

    # ─── Bulk Send ───

    @action(detail=True, methods=['post'])
    def bulk_send(self, request, pk=None):
        """
        Send independent copies of this document to multiple recipients.
        Each recipient gets their own document + signing link.
        POST /api/documents/{id}/bulk_send/
        Body: { recipients: [{name, email}, ...] }
        """
        document = self.get_object()

        recipients = request.data.get('recipients', [])
        if not recipients:
            return Response({'error': 'At least one recipient required.'}, status=400)

        if len(recipients) > 100:
            return Response({'error': 'Maximum 100 recipients per bulk send.'}, status=400)

        # Check upload quota
        remaining = getattr(request.user, 'documents_remaining', None)
        if remaining is not None and remaining < len(recipients):
            return Response(
                {'error': f'Not enough document quota. Need {len(recipients)}, have {remaining}.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            result = BulkSendService.bulk_send(
                source_document=document,
                recipients=recipients,
                sender=request.user,
                ip_address=get_client_ip(request),
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            logger.error(f'[BULK SEND] Failed for doc {document.id}: {e}')
            return Response({'error': 'Bulk send failed.'}, status=500)

        return Response({
            'message': f'Sent to {result["emails_sent"]} of {result["total"]} recipients',
            **result,
        })

    # ─── Fields ───

    @action(detail=True, methods=['get', 'post'])
    def fields(self, request, pk=None):
        document = self.get_object()

        if request.method == 'GET':
            fields = SignatureField.objects.filter(document=document)
            return Response(SignatureFieldSerializer(fields, many=True).data)

        serializer = SignatureFieldCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created = FieldService.save_fields(
            document=document, fields_data=serializer.validated_data['fields'],
            user=request.user, ip_address=get_client_ip(request),
        )

        return Response({
            'message': f'{len(created)} field(s) saved',
            'fields': SignatureFieldSerializer(created, many=True).data,
        })

    # ─── PDF & Download ───

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        document = self.get_object()

        # Preview reflects progress: stamp any already-completed signatures
        # onto the original so the owner can see how much is signed without
        # waiting for everyone. Falls back to the original when nothing is
        # signed yet (or rendering fails).
        try:
            progress = generate_progress_pdf_bytes(document)
        except Exception:
            progress = None

        if progress is not None:
            response = FileResponse(progress, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{document.title}.pdf"'
            response['Access-Control-Allow-Origin'] = '*'
            return response

        try:
            response = FileResponse(open(document.file.path, 'rb'), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{document.title}.pdf"'
            response['Access-Control-Allow-Origin'] = '*'
            return response
        except FileNotFoundError:
            return Response({'error': 'PDF file not found'}, status=404)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download — serves signed PDF if fully signed, otherwise the original."""
        document = self.get_object()
        DocumentAuditLog.objects.create(
            document=document, user=request.user, action='DOWNLOADED',
            ip_address=get_client_ip(request),
        )

        if document.status == 'SIGNED':
            try:
                signed_path = generate_signed_pdf(document)
                if signed_path and os.path.exists(signed_path):
                    response = FileResponse(open(signed_path, 'rb'), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="signed_{document.title}.pdf"'
                    return response
                else:
                    logger.warning(f'[PDF] Signed PDF not generated for {document.id}')
            except Exception as e:
                logger.error(f'[PDF] Signed PDF generation failed: {e}')

        try:
            response = FileResponse(open(document.file.path, 'rb'), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{document.title}.pdf"'
            return response
        except FileNotFoundError:
            return Response({'error': 'PDF file not found'}, status=404)

    # ─── Audit ───

    @action(detail=True, methods=['get'])
    def audit_log(self, request, pk=None):
        document = self.get_object()
        logs = DocumentAuditLog.objects.filter(document=document)
        return Response(AuditLogSerializer(logs, many=True).data)

    @action(detail=True, methods=['get'])
    def audit_certificate(self, request, pk=None):
        """Generate and serve the audit trail certificate PDF."""
        document = self.get_object()

        if document.status == 'DRAFT':
            return Response({'error': 'Audit certificate is not available for draft documents.'}, status=400)

        try:
            cert_path = generate_audit_certificate(document)
            if cert_path and os.path.exists(cert_path):
                DocumentAuditLog.objects.create(
                    document=document, user=request.user,
                    action='DOWNLOADED',
                    description='Audit trail certificate downloaded',
                    ip_address=get_client_ip(request),
                )
                response = FileResponse(open(cert_path, 'rb'), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="audit_certificate_{document.title}.pdf"'
                return response
            else:
                return Response({'error': 'Failed to generate audit certificate.'}, status=500)
        except Exception as e:
            logger.error(f'[AUDIT CERT] Failed for {document.id}: {e}')
            return Response({'error': 'Failed to generate audit certificate.'}, status=500)
