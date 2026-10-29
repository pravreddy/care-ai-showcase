"""
Document Views Package — HTTP layer for SignSimple.

Public API (unchanged from the monolithic views.py):
    from documents import views as doc_views
    doc_views.DocumentViewSet
    doc_views.SignDocumentView
    doc_views.SignDocumentPdfView
    doc_views.DocumentTemplateViewSet

Structure:
    views/
        __init__.py             ← This file (barrel exports)
        mixins.py               ← get_client_ip helper
        document_viewset.py     ← DocumentViewSet (authenticated CRUD)
        public_signing.py       ← SignDocumentView, SignDocumentPdfView (AllowAny)
        templates.py            ← DocumentTemplateViewSet (template library)
"""
from .document_viewset import DocumentViewSet
from .public_signing import SignDocumentView, SignDocumentPdfView, SignDocumentDownloadSignedView
from .templates import DocumentTemplateViewSet

__all__ = [
    'DocumentViewSet',
    'SignDocumentView',
    'SignDocumentPdfView',
    'SignDocumentDownloadSignedView',
    'DocumentTemplateViewSet',
]
