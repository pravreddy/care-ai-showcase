"""
Public Signing Views — Endpoints for external signers (no auth required).
Handles the /sign/:token flow for viewing and submitting signatures.
"""
import logging
import os

from django.conf import settings
from django.http import FileResponse
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import DocumentSigner, SignatureField, DocumentAuditLog
from documents.serializers import (
    DocumentSerializer, DocumentSignerSerializer, SignatureFieldSerializer,
)
from documents.services import SigningService, generate_progress_pdf_bytes

logger = logging.getLogger('documents')


class SignDocumentView(APIView):
    """Public endpoint for signers to view and submit signatures."""
    permission_classes = (permissions.AllowAny,)

    def get(self, request, access_token):
        """Load document, signer info, and assigned fields for the signing page."""
        try:
            signer = DocumentSigner.objects.select_related('document').get(
                access_token=access_token,
                access_expires_at__gt=timezone.now(),
            )
        except DocumentSigner.DoesNotExist:
            return Response({'error': 'Invalid or expired signing link'}, status=404)

        fields = SignatureField.objects.filter(
            document=signer.document,
            signer_index=signer.signing_order,
        )

        return Response({
            'document': DocumentSerializer(signer.document).data,
            'signer': DocumentSignerSerializer(signer).data,
            'fields': SignatureFieldSerializer(fields, many=True).data,
        })

    def post(self, request, access_token):
        """Process the signature submission."""
        try:
            signer = DocumentSigner.objects.select_related('document').get(
                access_token=access_token,
                access_expires_at__gt=timezone.now(),
                status='PENDING',
            )
        except DocumentSigner.DoesNotExist:
            return Response({'error': 'Invalid or expired signing link'}, status=404)

        # In sequential mode, refuse to accept a signature until every
        # earlier-order signer has completed — protects against a link being
        # forwarded and signed out of turn.
        if signer.document.sequential_signing:
            earlier_pending = DocumentSigner.objects.filter(
                document=signer.document,
                status='PENDING',
                signing_order__lt=signer.signing_order,
            ).exists()
            if earlier_pending:
                return Response(
                    {'error': 'It is not your turn to sign yet. This document must be '
                              'signed in order — you will be emailed when the signers '
                              'before you have completed.'},
                    status=403,
                )

        signature_image = request.FILES.get('signature')
        if not signature_image:
            return Response({'error': 'Signature image required'}, status=400)

        # Optional per-field text values (filled_values is a JSON-encoded
        # mapping of { field_id: value } for TEXT / NAME / DATE fields).
        # Missing or malformed input is treated as an empty dict — the
        # backend will still auto-fill NAME/DATE with sensible defaults.
        filled_values = {}
        raw_filled = request.data.get('filled_values')
        if raw_filled:
            import json
            try:
                parsed = json.loads(raw_filled) if isinstance(raw_filled, str) else raw_filled
                if isinstance(parsed, dict):
                    filled_values = {str(k): str(v) for k, v in parsed.items() if v is not None}
            except (ValueError, TypeError):
                logger.warning(f'Ignoring malformed filled_values from signer {signer.id}')

        signer.ip_address = request.META.get('REMOTE_ADDR')
        signer.user_agent = request.META.get('HTTP_USER_AGENT', '')

        result = SigningService.process_signature(signer, signature_image, filled_values=filled_values)

        # Signed PDF + audit certificate are now generated inside the
        # orchestrator when the final signer completes — see
        # SigningOrchestrator._generate_completion_artifacts. Attachment
        # happens in the completion email.

        return Response({
            'message': 'Document signed successfully',
            'all_signed': result['all_signed'],
        })


class SignDocumentPdfView(APIView):
    """Public endpoint to serve the PDF for the signing page viewer."""
    permission_classes = (permissions.AllowAny,)

    def get(self, request, access_token):
        try:
            signer = DocumentSigner.objects.select_related('document').get(
                access_token=access_token,
                access_expires_at__gt=timezone.now(),
            )
        except DocumentSigner.DoesNotExist:
            return Response({'error': 'Invalid or expired signing link'}, status=404)

        # Serve a "progress" PDF that already has any previously-completed
        # signatures stamped in, so each signer sees what's been signed so
        # far instead of a blank document. Falls back to the pristine
        # original when nothing has been signed yet (or rendering fails).
        try:
            progress = generate_progress_pdf_bytes(signer.document)
        except Exception:
            progress = None

        if progress is not None:
            response = FileResponse(progress, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{signer.document.title}.pdf"'
            return response

        try:
            response = FileResponse(
                open(signer.document.file.path, 'rb'),
                content_type='application/pdf',
            )
            response['Content-Disposition'] = f'inline; filename="{signer.document.title}.pdf"'
            return response
        except FileNotFoundError:
            return Response({'error': 'PDF file not found'}, status=404)


class SignDocumentDownloadSignedView(APIView):
    """
    Public endpoint for signers to download the final signed PDF after
    all parties have completed. Used as the fallback delivery mechanism
    when the signed PDF is too large to attach to the completion email.

    Only returns the signed PDF if the document is in SIGNED status —
    partially-signed or draft documents return 404 rather than leaking
    an incomplete file. The signer's access_token is the authorisation
    (matches the signing URL scheme).
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, access_token):
        try:
            signer = DocumentSigner.objects.select_related('document').get(
                access_token=access_token,
            )
        except DocumentSigner.DoesNotExist:
            return Response({'error': 'Invalid signing link'}, status=404)

        document = signer.document

        # Only serve the signed PDF when the document is fully complete.
        # We deliberately don't expose partially-signed PDFs via this
        # endpoint — signers should only get the final version.
        if document.status != 'SIGNED':
            return Response(
                {'error': 'Document is not yet fully signed'},
                status=404,
            )

        signed_path = os.path.join(
            settings.MEDIA_ROOT, 'signed', f'signed_{document.id}.pdf',
        )
        if not os.path.exists(signed_path):
            logger.warning(
                f'[DOWNLOAD] Signer {signer.id} requested signed PDF for '
                f'doc {document.id} but file missing at {signed_path}'
            )
            return Response({'error': 'Signed document not available'}, status=404)

        # Audit log: who downloaded and when
        DocumentAuditLog.objects.create(
            document=document,
            action='DOWNLOADED',
            description=f'Signer {signer.signer_name} ({signer.signer_email}) downloaded signed copy',
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        # Safe filename for the response header
        safe_title = ''.join(c for c in (document.title or 'document') if c.isalnum() or c in ' -_').strip()
        safe_title = safe_title[:60] or 'document'

        try:
            response = FileResponse(open(signed_path, 'rb'), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="signed_{safe_title}.pdf"'
            return response
        except FileNotFoundError:
            return Response({'error': 'Signed document not available'}, status=404)
