"""
DocumentService — Handles document upload, compression, and creation.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .pdf_utils import compress_and_replace, get_pdf_page_count, convert_to_pdf

logger = logging.getLogger('documents.document')


class DocumentService:

    @staticmethod
    def handle_upload(user, title, file_obj, description='', ip_address=None):
        """
        Process and save an uploaded document.
        Compression and page count are best-effort — failures don't block upload.
        Returns: Document instance
        """
        from documents.models import Document, DocumentAuditLog

        original_filename = file_obj.name
        ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else ''
        original_size = file_obj.size
        was_converted = False

        # Step 1: Convert non-PDF to PDF (DOC/DOCX via LibreOffice, JPG/PNG via Pillow)
        if ext != 'pdf':
            try:
                file_obj, new_filename, was_converted = convert_to_pdf(file_obj, original_filename)
                ext = 'pdf'
                logger.info(f'Converted {original_filename} → {new_filename}')
            except Exception as e:
                logger.error(f'Conversion failed for {original_filename}: {e}')
                raise ValueError(
                    f'Could not convert {original_filename} to PDF. '
                    f'Please try a different file or convert to PDF manually.'
                ) from e

        # Step 2: Compress PDF (best-effort)
        try:
            compressed_file, compression_info = compress_and_replace(file_obj)
        except Exception as e:
            logger.error(f'Compression failed for {file_obj.name}: {e}')
            compressed_file = file_obj
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)
            compression_info = {
                'compressed': False, 'original_size': original_size,
                'final_size': original_size, 'savings_percent': 0,
            }

        # Page count (best-effort)
        page_count = None
        if ext == 'pdf':
            try:
                page_count = get_pdf_page_count(compressed_file)
            except Exception as e:
                logger.error(f'Page count failed for {file_obj.name}: {e}')

        # Create document
        doc = Document.objects.create(
            user=user, title=title, description=description,
            file=compressed_file,
            file_size=compression_info.get('final_size', original_size),
            file_type=ext, original_file_size=original_size,
            was_compressed=compression_info.get('compressed', False),
            compression_savings=compression_info.get('savings_percent', 0),
            expires_at=timezone.now() + timedelta(days=settings.DOCUMENT_EXPIRY_DAYS),
            page_count=page_count,
        )

        # Side effects
        user.increment_document_usage()

        desc = f'Document uploaded: {doc.title}'
        if was_converted:
            orig_ext = original_filename.rsplit('.', 1)[-1].upper() if '.' in original_filename else 'FILE'
            desc += f' (converted from {orig_ext} to PDF)'
        if compression_info.get('compressed'):
            desc += f' (compressed {compression_info["savings_percent"]}%: {original_size:,} → {compression_info["final_size"]:,} bytes)'

        DocumentAuditLog.objects.create(
            document=doc, user=user, action='CREATED',
            description=desc, ip_address=ip_address,
        )

        return doc
