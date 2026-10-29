"""
Document Models Package — Database schema for SignSimple.

Public API (unchanged from the monolithic models.py):
    from documents.models import Document, DocumentSigner, SignatureField, ...

IMPORTANT: Upload path helpers are exported here because existing
migrations reference them as documents.models.document_upload_path
and documents.models.signature_upload_path.

Structure:
    models/
        __init__.py         ← This file (barrel exports)
        upload_paths.py     ← Shared upload path helpers
        document.py         ← Document
        signer.py           ← DocumentSigner, Signature
        fields.py           ← SignatureField
        audit.py            ← DocumentAuditLog
        template.py         ← DocumentTemplate
"""
from .document import Document
from .signer import DocumentSigner, Signature
from .fields import SignatureField
from .audit import DocumentAuditLog
from .template import DocumentTemplate

# CRITICAL: migrations reference these as documents.models.document_upload_path
from .upload_paths import document_upload_path, signature_upload_path

__all__ = [
    'Document',
    'DocumentSigner',
    'Signature',
    'SignatureField',
    'DocumentAuditLog',
    'DocumentTemplate',
    'document_upload_path',
    'signature_upload_path',
]
