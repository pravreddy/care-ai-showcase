"""
Signed PDF generation — renders signatures at field positions or legacy bottom-of-page.

Uses pdfrw to stamp the reportlab overlay onto the original PDF.
This preserves the original content stream intact (unlike PyPDF2's merge_page
which can corrupt coordinate transforms and break rendering).
"""
import io
import os
import logging

from django.conf import settings

logger = logging.getLogger('documents.pdf')


def generate_signed_pdf(document):
    """
    Generate a PDF with signatures embedded at their field positions.
    Falls back to bottom-of-page placement if no positioned fields exist.
    Returns the file path of the signed PDF, or None.
    """
    from documents.models import SignatureField

    signers = document.signers.filter(status='SIGNED').order_by('signing_order')
    if not signers.exists():
        logger.warning(f'No signed signers for document {document.id}')
        return None

    try:
        positioned_fields = SignatureField.objects.filter(
            document=document, filled_at__isnull=False,
        ).order_by('page')

        # Step 1: Build the overlay PDF with reportlab
        overlay_buf = _build_overlay(document, signers, positioned_fields)

        # Step 2: Stamp overlay onto original using pdfrw (preserves original streams)
        signed_buf = _stamp_overlay(document.file.path, overlay_buf)

        # Step 3: Save
        signed_filename = f'signed_{document.id}.pdf'
        signed_dir = os.path.join(settings.MEDIA_ROOT, 'signed')
        os.makedirs(signed_dir, exist_ok=True)
        signed_path = os.path.join(signed_dir, signed_filename)

        with open(signed_path, 'wb') as f:
            f.write(signed_buf.getvalue())

        logger.info(f'Generated signed PDF: {signed_path}')
        return signed_path

    except Exception as e:
        logger.error(f'Failed to generate signed PDF for {document.id}: {e}')
        import traceback
        logger.error(traceback.format_exc())
        return None


def generate_progress_pdf_bytes(document):
    """
    Render an in-memory PDF showing the CURRENT signing progress: every
    field already filled by a completed signer is stamped onto the original
    PDF. Fields that haven't been filled yet (e.g. the current signer's)
    are left blank so the signing overlay can still render them as
    interactive click targets.

    Returns a BytesIO of the stamped PDF, or None if nothing has been
    filled yet — in which case callers should serve the pristine original.

    Unlike generate_signed_pdf, this:
      - does NOT require the document to be fully complete,
      - does NOT write anything to disk,
      - does NOT draw the "electronically signed" completion footer.
    """
    from documents.models import SignatureField

    signers = document.signers.filter(status='SIGNED').order_by('signing_order')
    positioned_fields = SignatureField.objects.filter(
        document=document, filled_at__isnull=False,
    ).order_by('page')

    # Nothing signed yet — let the caller serve the original file.
    if not signers.exists() and not positioned_fields.exists():
        return None

    try:
        overlay_buf = _build_overlay(
            document, signers, positioned_fields, include_footer=False,
        )
        return _stamp_overlay(document.file.path, overlay_buf)
    except Exception as e:
        logger.error(f'Failed to render progress PDF for {document.id}: {e}')
        import traceback
        logger.error(traceback.format_exc())
        return None


def _build_overlay(document, signers, positioned_fields, include_footer=True):
    """
    Build a multi-page overlay PDF using reportlab.
    Each page matches the original PDF page dimensions and contains only
    the signature images/text that need to be stamped.
    Returns a BytesIO buffer with the overlay PDF.

    include_footer controls whether the "electronically signed via
    SignSimple" footer is drawn on the last page. It's suppressed for
    in-progress (partially signed) renders so a half-finished document
    isn't stamped as if it were complete.
    """
    from reportlab.pdfgen import canvas as rl_canvas
    from pdfrw import PdfReader

    # Read original to get page dimensions
    original = PdfReader(document.file.path)
    num_pages = len(original.pages)

    buf = io.BytesIO()

    # Determine which pages need overlays
    pages_needing_overlay = set()

    if positioned_fields.exists():
        for field in positioned_fields:
            pages_needing_overlay.add(field.page)
    else:
        # Legacy mode: signatures go on last page
        pages_needing_overlay.add(num_pages)

    # Always add footer on last page
    pages_needing_overlay.add(num_pages)

    # Create overlay with one page per original page
    # (blank pages for those that don't need overlays)
    first_page = True
    c = None

    for page_num in range(1, num_pages + 1):
        orig_page = original.pages[page_num - 1]
        # Get page dimensions from the original
        mbox = orig_page.MediaBox
        pw = float(mbox[2]) - float(mbox[0])
        ph = float(mbox[3]) - float(mbox[1])

        if c is None:
            c = rl_canvas.Canvas(buf, pagesize=(pw, ph))
        else:
            c.showPage()
            c.setPageSize((pw, ph))

        if page_num in pages_needing_overlay:
            if positioned_fields.exists():
                _draw_positioned_fields(c, pw, ph, page_num, positioned_fields)
            elif page_num == num_pages:
                _draw_legacy_signatures(c, pw, ph, signers)

            if page_num == num_pages and include_footer:
                _draw_footer(c, pw, document)

    if c:
        c.save()

    buf.seek(0)
    return buf


def _draw_positioned_fields(canvas, pw, ph, page_num, positioned_fields):
    """Draw signature/text fields at their exact positions on a page."""
    fields_on_page = [f for f in positioned_fields if f.page == page_num]

    for field in fields_on_page:
        x = (field.x_percent / 100) * pw
        y = ph - ((field.y_percent / 100) * ph)
        w = (field.width_percent / 100) * pw
        h = (field.height_percent / 100) * ph
        y = y - h  # bottom of field box

        if field.field_type in ('SIGNATURE', 'INITIALS') and field.filled_signature:
            try:
                canvas.drawImage(
                    field.filled_signature.path, x, y,
                    width=w, height=h,
                    preserveAspectRatio=True, mask='auto',
                )
            except Exception as e:
                logger.warning(f'Failed to draw signature image: {e}')
                canvas.setFont('Helvetica-Oblique', 12)
                canvas.drawString(x, y + h / 2, '[Signature]')
        elif field.field_type == 'CHECKBOX':
            _draw_checkbox(canvas, x, y, w, h, field.filled_value)
        elif field.filled_value:
            font_size = min(h * 0.6, 14)
            canvas.setFont('Helvetica', max(font_size, 8))
            canvas.drawString(x + 2, y + h * 0.3, field.filled_value)


def _draw_checkbox(canvas, x, y, w, h, filled_value):
    """
    Draw a checkbox. Outline is always drawn; a tick appears only when
    the signer submitted 'true'. 'false' or blank renders as an empty box.

    The box is squared off the smaller of the field's width/height so it
    looks like a real checkbox even if the sender drew a wide rectangle.
    """
    # Square the box to the smaller side, centred within the field
    side = min(w, h)
    box_x = x + (w - side) / 2
    box_y = y + (h - side) / 2

    # Outline
    canvas.setStrokeColorRGB(0, 0, 0)
    canvas.setLineWidth(max(0.8, side * 0.04))
    canvas.rect(box_x, box_y, side, side, stroke=1, fill=0)

    # Tick only if explicitly 'true'
    if (filled_value or '').strip().lower() == 'true':
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.setLineWidth(max(1.2, side * 0.10))
        canvas.setLineCap(1)  # round
        canvas.setLineJoin(1)
        # Classic checkmark path: left-low, middle-bottom, right-high
        pad = side * 0.20
        p1 = (box_x + pad,             box_y + side * 0.52)
        p2 = (box_x + side * 0.42,     box_y + pad)
        p3 = (box_x + side - pad,      box_y + side * 0.80)
        path = canvas.beginPath()
        path.moveTo(*p1)
        path.lineTo(*p2)
        path.lineTo(*p3)
        canvas.drawPath(path, stroke=1, fill=0)


def _draw_legacy_signatures(canvas, pw, ph, signers):
    """Render signatures stacked at the bottom of the last page (legacy mode)."""
    y_pos, x_pos = 120, 50
    sig_w, sig_h = 150, 50

    for signer in signers:
        if signer.signature_image:
            try:
                canvas.drawImage(
                    signer.signature_image.path, x_pos, y_pos,
                    width=sig_w, height=sig_h,
                    preserveAspectRatio=True, mask='auto',
                )
            except Exception:
                canvas.setFont('Helvetica-Oblique', 14)
                canvas.drawString(x_pos, y_pos + 20, signer.signer_name)
        else:
            canvas.setFont('Helvetica-Oblique', 14)
            canvas.drawString(x_pos, y_pos + 20, signer.signer_name)

        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.setLineWidth(0.5)
        canvas.line(x_pos, y_pos - 5, x_pos + sig_w, y_pos - 5)
        canvas.setFont('Helvetica', 8)
        canvas.drawString(x_pos, y_pos - 18, signer.signer_name)
        canvas.drawString(x_pos, y_pos - 28, signer.signer_email)
        if signer.signed_at:
            canvas.drawString(x_pos, y_pos - 38, f'Signed: {signer.signed_at.strftime("%d %b %Y %H:%M UTC")}')

        x_pos += sig_w + 40
        if x_pos + sig_w > pw - 50:
            x_pos = 50
            y_pos += sig_h + 60


def _draw_footer(canvas, pw, document):
    """Add SignSimple footer."""
    canvas.setFont('Helvetica', 7)
    canvas.setFillColorRGB(0.5, 0.5, 0.5)
    canvas.drawString(
        50, 20,
        f'Electronically signed via SignSimple (signsimple.co.uk) — Document ID: {document.id}',
    )


def _stamp_overlay(original_path, overlay_buf):
    """
    Stamp the overlay PDF onto the original using pdfrw.
    This preserves the original content streams intact — no rewriting,
    no coordinate transform corruption.
    Returns a BytesIO with the stamped PDF.
    """
    from pdfrw import PdfReader, PdfWriter, PageMerge

    original = PdfReader(original_path)
    overlay = PdfReader(overlay_buf)

    for i, orig_page in enumerate(original.pages):
        if i < len(overlay.pages):
            overlay_page = overlay.pages[i]
            # Only merge if the overlay page has content
            # (check if it has any drawing operations)
            if overlay_page and overlay_page.Contents:
                merger = PageMerge(orig_page)
                merger.add(overlay_page).render()

    output = io.BytesIO()
    writer = PdfWriter(output)
    writer.trailer = original
    writer.write()
    output.seek(0)
    return output
