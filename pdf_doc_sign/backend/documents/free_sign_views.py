"""
Free Sign Tool — Public file conversion endpoint.
Accepts DOC/DOCX/JPG/PNG, converts to PDF, returns bytes.
No auth required. File deleted immediately after conversion.
Rate limited to prevent abuse.
"""
import os
import tempfile
import logging
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

logger = logging.getLogger('documents')

ALLOWED_EXTENSIONS = {'doc', 'docx', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


class FreeSignConvertView(APIView):
    """
    POST /api/free-sign/convert/
    Public endpoint — no auth required.
    Accepts: DOC, DOCX, JPG, PNG
    Returns: PDF bytes (application/pdf)
    File is never stored — converted in temp dir and deleted immediately.
    """
    permission_classes = (permissions.AllowAny,)
    parser_classes = (MultiPartParser,)

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=400)

        if file.size > MAX_FILE_SIZE:
            return Response({'error': 'File too large. Maximum 20MB.'}, status=400)

        ext = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
        if ext not in ALLOWED_EXTENSIONS:
            return Response({
                'error': f'Unsupported format. Allowed: {", ".join(sorted(ALLOWED_EXTENSIONS)).upper()}'
            }, status=400)

        try:
            pdf_bytes = self._convert_to_pdf(file, ext)
            logger.info(f'[FREE_SIGN] Converted {ext} → PDF ({len(pdf_bytes)} bytes)')
            return HttpResponse(
                pdf_bytes,
                content_type='application/pdf',
                headers={'Content-Disposition': f'inline; filename="converted.pdf"'},
            )
        except Exception as e:
            logger.error(f'[FREE_SIGN] Conversion failed for {file.name}: {e}')
            return Response({'error': f'Conversion failed: {str(e)}'}, status=500)

    def _convert_to_pdf(self, file, ext):
        """Convert file to PDF bytes. Uses temp files, cleaned up immediately."""
        import subprocess

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write uploaded file to temp
            input_path = os.path.join(tmpdir, f'input.{ext}')
            with open(input_path, 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)

            if ext in ('jpg', 'jpeg', 'png'):
                return self._image_to_pdf(input_path)
            elif ext in ('doc', 'docx'):
                return self._office_to_pdf(input_path, tmpdir)
            else:
                raise ValueError(f'Unhandled extension: {ext}')

    def _image_to_pdf(self, image_path):
        """Convert JPG/PNG to PDF using Pillow — centres on A4."""
        from PIL import Image
        import io
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.utils import ImageReader

        img = Image.open(image_path)
        # Convert RGBA/palette to RGB for PDF compatibility
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')

        a4_w, a4_h = A4  # points (595 x 842)
        img_w, img_h = img.size
        # Scale to fit A4 with 40pt margin
        margin = 40
        max_w = a4_w - margin * 2
        max_h = a4_h - margin * 2
        scale = min(max_w / img_w, max_h / img_h, 1.0)
        draw_w = img_w * scale
        draw_h = img_h * scale
        x = (a4_w - draw_w) / 2
        y = (a4_h - draw_h) / 2

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)

        # Save image to temp buffer for reportlab
        img_buf = io.BytesIO()
        img.save(img_buf, format='JPEG', quality=95)
        img_buf.seek(0)
        c.drawImage(ImageReader(img_buf), x, y, width=draw_w, height=draw_h)
        c.save()
        return buf.getvalue()

    def _office_to_pdf(self, input_path, tmpdir):
        """Convert DOC/DOCX to PDF using LibreOffice headless."""
        import subprocess
        result = subprocess.run(
            [
                'libreoffice', '--headless', '--convert-to', 'pdf',
                '--outdir', tmpdir, input_path,
            ],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f'LibreOffice failed: {result.stderr}')

        # Find the output PDF
        pdf_name = os.path.splitext(os.path.basename(input_path))[0] + '.pdf'
        pdf_path = os.path.join(tmpdir, pdf_name)
        if not os.path.exists(pdf_path):
            raise RuntimeError('LibreOffice did not produce a PDF output')

        with open(pdf_path, 'rb') as f:
            return f.read()
