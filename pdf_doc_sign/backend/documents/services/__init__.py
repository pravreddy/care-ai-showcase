"""
Document Services Package — Business logic layer for SignSimple.

Usage in views.py:
    from .services import DocumentService, SigningService, FieldService, generate_signed_pdf, generate_audit_certificate

Usage in models.py:
    from documents.services import get_structured_upload_path

Structure:
    services/
        __init__.py             ← This file (exports)
        document.py             ← DocumentService (upload, compression)
        signing/                ← SigningService package
            __init__.py         ← SigningService entry point + send_for_signing
            orchestrator.py     ← SigningOrchestrator (process_signature workflow)
            field_processor.py  ← FieldProcessor (fill signature/name/date fields)
            notifications.py    ← SigningNotificationService (email triggers)
        fields.py               ← FieldService (field placement)
        pdf_utils.py            ← PDF compression, page count
        pdf_generator.py        ← Signed PDF generation
        audit_certificate.py    ← Audit trail PDF certificate
        storage.py              ← Storage path helpers
"""

# Service classes
from .document import DocumentService
from .signing import SigningService
from .fields import FieldService

# Bulk send
from .bulk_send import BulkSendService

# PDF functions
from .pdf_utils import compress_and_replace, compress_pdf, get_pdf_page_count
from .pdf_generator import generate_signed_pdf, generate_progress_pdf_bytes
from .audit_certificate import generate_audit_certificate

# Storage path helpers (used by models.py)
from .storage import get_structured_upload_path, get_sales_document_path, get_invoice_path

__all__ = [
    'DocumentService',
    'SigningService',
    'FieldService',
    'BulkSendService',
    'compress_and_replace',
    'compress_pdf',
    'get_pdf_page_count',
    'generate_signed_pdf',
    'generate_progress_pdf_bytes',
    'generate_audit_certificate',
    'get_structured_upload_path',
    'get_sales_document_path',
    'get_invoice_path',
]
