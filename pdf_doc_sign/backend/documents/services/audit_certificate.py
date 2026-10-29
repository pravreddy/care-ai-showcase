"""
Audit Trail Certificate Generator — Produces a branded PDF certificate
documenting the complete signing history of a document.

Includes: document hash (SHA-256), signer details, IP addresses,
timestamps, and a tamper-evident document fingerprint.
"""
import hashlib
import io
import logging
import os

from django.conf import settings
from django.utils import timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

logger = logging.getLogger('documents.audit')

# Brand colours
BRAND_PRIMARY = HexColor('#1565C0')
BRAND_DARK = HexColor('#0D47A1')
BRAND_LIGHT = HexColor('#E3F2FD')
TEXT_DARK = HexColor('#212121')
TEXT_LIGHT = HexColor('#757575')
BORDER_GREY = HexColor('#E0E0E0')


def compute_document_hash(file_path):
    """Compute SHA-256 hash of the original document file."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        logger.error(f'Failed to hash file {file_path}: {e}')
        return 'HASH_UNAVAILABLE'


def generate_audit_certificate(document):
    """
    Generate a PDF audit trail certificate for a document.
    Returns the file path to the generated certificate, or None on failure.
    """
    from documents.models import DocumentAuditLog, DocumentSigner

    try:
        # Gather data
        signers = DocumentSigner.objects.filter(document=document).order_by('signing_order')
        audit_logs = DocumentAuditLog.objects.filter(document=document).order_by('created_at')
        doc_hash = compute_document_hash(document.file.path)

        # Output path
        cert_filename = f'audit_certificate_{document.id}.pdf'
        cert_dir = os.path.join(settings.MEDIA_ROOT, 'certificates')
        os.makedirs(cert_dir, exist_ok=True)
        cert_path = os.path.join(cert_dir, cert_filename)

        # Build PDF
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=20 * mm, rightMargin=20 * mm,
            topMargin=25 * mm, bottomMargin=20 * mm,
        )

        styles = _get_styles()
        story = []

        # --- Header ---
        story.append(Paragraph('AUDIT TRAIL CERTIFICATE', styles['CertTitle']))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(
            'Electronic Signature Verification &amp; Audit Trail',
            styles['CertSubtitle'],
        ))
        story.append(Spacer(1, 2 * mm))
        story.append(HRFlowable(
            width='100%', thickness=2, color=BRAND_PRIMARY,
            spaceAfter=4 * mm, spaceBefore=2 * mm,
        ))

        # --- Document Information ---
        story.append(Paragraph('Document Information', styles['SectionHeader']))
        story.append(Spacer(1, 2 * mm))

        doc_info = [
            ['Document Title:', document.title],
            ['Document ID:', str(document.id)],
            ['Status:', document.status],
            ['Created:', document.created_at.strftime('%d %b %Y %H:%M:%S UTC')],
            ['Pages:', str(document.page_count or 'N/A')],
            ['File Size:', f'{document.file_size_mb} MB'],
        ]
        if document.signed_at:
            doc_info.append(['Completed:', document.signed_at.strftime('%d %b %Y %H:%M:%S UTC')])

        doc_table = Table(doc_info, colWidths=[45 * mm, 120 * mm])
        doc_table.setStyle(TableStyle([
            ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 9),
            ('FONT', (1, 0), (1, -1), 'Helvetica', 9),
            ('TEXTCOLOR', (0, 0), (0, -1), BRAND_DARK),
            ('TEXTCOLOR', (1, 0), (1, -1), TEXT_DARK),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(doc_table)
        story.append(Spacer(1, 4 * mm))

        # --- Document Fingerprint ---
        story.append(Paragraph('Document Fingerprint (SHA-256)', styles['SectionHeader']))
        story.append(Spacer(1, 2 * mm))

        hash_table = Table(
            [[Paragraph(f'<font face="Courier" size="8">{doc_hash}</font>', styles['Normal'])]],
            colWidths=[170 * mm],
        )
        hash_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), BRAND_LIGHT),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_GREY),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(hash_table)
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            'This hash uniquely identifies the original document. '
            'Any modification to the document will produce a different hash.',
            styles['SmallGrey'],
        ))
        story.append(Spacer(1, 6 * mm))

        # --- Signing Summary ---
        story.append(Paragraph('Signing Summary', styles['SectionHeader']))
        story.append(Spacer(1, 3 * mm))

        if signers.exists():
            signer_header = [['#', 'Name', 'Email', 'Status', 'Signed At', 'IP Address']]
            signer_rows = []

            for s in signers:
                signed_at = s.signed_at.strftime('%d %b %Y %H:%M UTC') if s.signed_at else '\u2014'
                ip = s.ip_address or '\u2014'
                signer_rows.append([
                    str(s.signing_order),
                    s.signer_name,
                    s.signer_email,
                    s.status,
                    signed_at,
                    ip,
                ])

            signer_table = Table(
                signer_header + signer_rows,
                colWidths=[8 * mm, 30 * mm, 45 * mm, 18 * mm, 38 * mm, 28 * mm],
            )
            signer_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                # Data rows
                ('FONT', (0, 1), (-1, -1), 'Helvetica', 7.5),
                ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                # Alternating row background
                *[('BACKGROUND', (0, i), (-1, i), BRAND_LIGHT)
                  for i in range(1, len(signer_rows) + 1) if i % 2 == 0],
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(signer_table)
        else:
            story.append(Paragraph('No signers recorded.', styles['Normal']))

        story.append(Spacer(1, 6 * mm))

        # --- Detailed Activity Log ---
        story.append(Paragraph('Activity Log', styles['SectionHeader']))
        story.append(Spacer(1, 3 * mm))

        if audit_logs.exists():
            log_header = [['Timestamp (UTC)', 'Action', 'Description', 'IP Address']]
            log_rows = []

            for log in audit_logs:
                log_rows.append([
                    log.created_at.strftime('%d %b %Y %H:%M:%S'),
                    log.action,
                    Paragraph(log.description[:80] if log.description else '\u2014',
                              ParagraphStyle('logcell', fontSize=7, leading=9)),
                    log.ip_address or '\u2014',
                ])

            log_table = Table(
                log_header + log_rows,
                colWidths=[38 * mm, 22 * mm, 80 * mm, 28 * mm],
            )
            log_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), BRAND_DARK),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 8),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONT', (0, 1), (-1, -1), 'Helvetica', 7),
                ('TEXTCOLOR', (0, 1), (-1, -1), TEXT_DARK),
                *[('BACKGROUND', (0, i), (-1, i), BRAND_LIGHT)
                  for i in range(1, len(log_rows) + 1) if i % 2 == 0],
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(log_table)
        else:
            story.append(Paragraph('No activity recorded.', styles['Normal']))

        story.append(Spacer(1, 8 * mm))

        # --- Footer disclaimer ---
        story.append(HRFlowable(
            width='100%', thickness=1, color=BORDER_GREY,
            spaceAfter=3 * mm, spaceBefore=3 * mm,
        ))
        story.append(Paragraph(
            'This certificate was automatically generated by SignSimple '
            '(signsimple.co.uk) \u2014 a product of Avyangah Technologies Limited '
            '(Company No. 08235853). It provides a verifiable record of the '
            'electronic signing process. The document fingerprint (SHA-256 hash) '
            'can be used to confirm the original document has not been altered '
            'since signing.',
            styles['SmallGrey'],
        ))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            f'Certificate generated: {timezone.now().strftime("%d %b %Y %H:%M:%S UTC")}',
            styles['SmallGrey'],
        ))

        # Build
        doc.build(story, onFirstPage=_add_page_border, onLaterPages=_add_page_border)

        # Write to file
        with open(cert_path, 'wb') as f:
            f.write(buf.getvalue())

        logger.info(f'Generated audit certificate: {cert_path}')
        return cert_path

    except Exception as e:
        logger.error(f'Failed to generate audit certificate for {document.id}: {e}')
        import traceback
        logger.error(traceback.format_exc())
        return None


def _get_styles():
    """Return custom paragraph styles for the certificate."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'CertTitle', parent=styles['Title'],
        fontSize=20, textColor=BRAND_PRIMARY, spaceAfter=0,
        fontName='Helvetica-Bold', alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        'CertSubtitle', parent=styles['Normal'],
        fontSize=11, textColor=TEXT_LIGHT, alignment=TA_CENTER,
        fontName='Helvetica',
    ))
    styles.add(ParagraphStyle(
        'SectionHeader', parent=styles['Heading2'],
        fontSize=12, textColor=BRAND_DARK, spaceAfter=0,
        fontName='Helvetica-Bold', borderWidth=0,
        borderPadding=0, leftIndent=0,
    ))
    styles.add(ParagraphStyle(
        'SmallGrey', parent=styles['Normal'],
        fontSize=7.5, textColor=TEXT_LIGHT, leading=10,
    ))

    return styles


def _add_page_border(canvas, doc):
    """Draw a subtle border and header/footer on each page."""
    canvas.saveState()

    # Page border
    canvas.setStrokeColor(BRAND_PRIMARY)
    canvas.setLineWidth(1.5)
    canvas.rect(12 * mm, 12 * mm, A4[0] - 24 * mm, A4[1] - 24 * mm)

    # Top-left: SignSimple branding
    canvas.setFont('Helvetica-Bold', 9)
    canvas.setFillColor(BRAND_PRIMARY)
    canvas.drawString(16 * mm, A4[1] - 18 * mm, 'SignSimple')

    # Top-right: page number
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(TEXT_LIGHT)
    canvas.drawRightString(A4[0] - 16 * mm, A4[1] - 18 * mm, f'Page {canvas.getPageNumber()}')

    # Bottom-centre: company info
    canvas.setFont('Helvetica', 6.5)
    canvas.setFillColor(TEXT_LIGHT)
    canvas.drawCentredString(
        A4[0] / 2, 14 * mm,
        'Avyangah Technologies Limited (08235853) \u2014 signsimple.co.uk',
    )

    canvas.restoreState()
