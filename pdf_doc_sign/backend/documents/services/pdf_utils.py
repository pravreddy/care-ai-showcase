"""
PDF utility functions — compression and page count.
"""
import io
import os
import subprocess
import tempfile
import logging

logger = logging.getLogger('documents.pdf')

GS_QUALITY_SETTINGS = {
    'screen': '/screen',
    'ebook': '/ebook',
    'printer': '/printer',
    'prepress': '/prepress',
}
DEFAULT_QUALITY = 'ebook'


def get_pdf_page_count(file_obj):
    """
    Get the number of pages in a PDF.
    Accepts Django UploadedFile or file-like object.
    Returns int or None on failure.
    """
    try:
        # pypdf is the maintained successor to PyPDF2 (same PdfReader API).
        # PyPDF2 is frozen at 3.0.1 and has an unpatched infinite-loop CVE.
        from pypdf import PdfReader
        if hasattr(file_obj, 'read'):
            file_obj.seek(0)
            reader = PdfReader(file_obj)
            file_obj.seek(0)
        else:
            reader = PdfReader(io.BytesIO(file_obj))
        count = len(reader.pages)
        logger.info(f'Page count: {count}')
        return count
    except Exception as e:
        logger.error(f'Failed to get page count: {e}')
        return None


def compress_pdf(input_file, quality=DEFAULT_QUALITY):
    """
    Compress a PDF using Ghostscript.
    Returns: (compressed_bytes, original_size, compressed_size, savings_percent)
             or (None, original_size, original_size, 0) if compression fails/not beneficial.
    """
    gs_setting = GS_QUALITY_SETTINGS.get(quality, GS_QUALITY_SETTINGS[DEFAULT_QUALITY])

    if hasattr(input_file, 'read'):
        original_bytes = input_file.read()
        input_file.seek(0)
    else:
        original_bytes = input_file

    original_size = len(original_bytes)

    # Skip tiny files (< 50KB)
    if original_size < 50 * 1024:
        logger.info(f'Skipping compression: {original_size} bytes (too small)')
        return None, original_size, original_size, 0

    tmp_in_path = None
    tmp_out_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_in:
            tmp_in.write(original_bytes)
            tmp_in_path = tmp_in.name

        tmp_out_path = tmp_in_path + '.compressed.pdf'
        gs_cmd = [
            'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
            f'-dPDFSETTINGS={gs_setting}',
            '-dNOPAUSE', '-dQUIET', '-dBATCH', '-dAutoRotatePages=/None',
            '-dColorImageResolution=150', '-dGrayImageResolution=150', '-dMonoImageResolution=300',
            f'-sOutputFile={tmp_out_path}', tmp_in_path,
        ]

        result = subprocess.run(gs_cmd, capture_output=True, timeout=60)
        if result.returncode != 0:
            logger.warning(f'Ghostscript failed: {result.stderr.decode()[:200]}')
            return None, original_size, original_size, 0

        with open(tmp_out_path, 'rb') as f:
            compressed_bytes = f.read()

        compressed_size = len(compressed_bytes)
        savings = ((original_size - compressed_size) / original_size) * 100

        if savings > 10:
            logger.info(f'Compressed: {original_size:,} → {compressed_size:,} bytes ({savings:.1f}%)')
            return compressed_bytes, original_size, compressed_size, round(savings, 1)
        else:
            return None, original_size, original_size, 0

    except subprocess.TimeoutExpired:
        logger.error('Ghostscript timed out')
        return None, original_size, original_size, 0
    except FileNotFoundError:
        logger.error('Ghostscript not installed')
        return None, original_size, original_size, 0
    except Exception as e:
        logger.error(f'Compression error: {e}')
        return None, original_size, original_size, 0
    finally:
        for path in [tmp_in_path, tmp_out_path]:
            if path:
                try:
                    os.unlink(path)
                except Exception:
                    pass


def convert_image_to_pdf(file_obj):
    """
    Convert JPG/PNG to a single-page PDF using Pillow.
    Returns: (pdf_bytes, original_size) or raises on failure.
    """
    from PIL import Image

    if hasattr(file_obj, 'read'):
        file_obj.seek(0)
        img_bytes = file_obj.read()
        file_obj.seek(0)
    else:
        img_bytes = file_obj

    original_size = len(img_bytes)

    img = Image.open(io.BytesIO(img_bytes))

    # Convert to RGB — PDF doesn't support RGBA/P modes
    if img.mode in ('RGBA', 'P', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # A4 at 96dpi = 794 x 1123 px — scale image to fit with margins
    max_w, max_h = 760, 1080
    img.thumbnail((max_w, max_h), Image.LANCZOS)

    # Centre on A4 page
    page = Image.new('RGB', (794, 1123), (255, 255, 255))
    x = (794 - img.width) // 2
    y = (1123 - img.height) // 2
    page.paste(img, (x, y))

    pdf_buffer = io.BytesIO()
    page.save(pdf_buffer, format='PDF', resolution=96)
    pdf_bytes = pdf_buffer.getvalue()

    logger.info(f'Image→PDF: {original_size:,} → {len(pdf_bytes):,} bytes')
    return pdf_bytes, original_size


def convert_office_to_pdf(file_obj, filename):
    """
    Convert DOC/DOCX to PDF using LibreOffice headless.
    Returns: (pdf_bytes, original_size) or raises on failure.
    """
    if hasattr(file_obj, 'read'):
        file_obj.seek(0)
        file_bytes = file_obj.read()
        file_obj.seek(0)
    else:
        file_bytes = file_obj

    original_size = len(file_bytes)
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'docx'

    tmp_in_path = None
    tmp_out_dir = None
    try:
        import tempfile
        # Write input file
        with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp_in:
            tmp_in.write(file_bytes)
            tmp_in_path = tmp_in.name

        tmp_out_dir = tempfile.mkdtemp()

        # LibreOffice converts to PDF in the output directory
        result = subprocess.run(
            [
                'libreoffice', '--headless', '--norestore', '--nofirststartwizard',
                '--convert-to', 'pdf',
                '--outdir', tmp_out_dir,
                tmp_in_path,
            ],
            capture_output=True,
            timeout=120,
            env={**os.environ, 'HOME': '/tmp'},
        )

        if result.returncode != 0:
            err = result.stderr.decode()[:500]
            logger.error(f'LibreOffice conversion failed: {err}')
            raise RuntimeError(f'LibreOffice conversion failed: {err}')

        # Find the output PDF
        base_name = os.path.splitext(os.path.basename(tmp_in_path))[0]
        pdf_path = os.path.join(tmp_out_dir, f'{base_name}.pdf')

        if not os.path.exists(pdf_path):
            # Sometimes LibreOffice uses the original filename without temp prefix
            pdfs = [f for f in os.listdir(tmp_out_dir) if f.endswith('.pdf')]
            if not pdfs:
                raise RuntimeError('LibreOffice produced no output PDF')
            pdf_path = os.path.join(tmp_out_dir, pdfs[0])

        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        logger.info(f'Office→PDF ({ext}): {original_size:,} → {len(pdf_bytes):,} bytes')
        return pdf_bytes, original_size

    finally:
        # Cleanup
        if tmp_in_path and os.path.exists(tmp_in_path):
            try:
                os.unlink(tmp_in_path)
            except Exception:
                pass
        if tmp_out_dir and os.path.exists(tmp_out_dir):
            import shutil
            try:
                shutil.rmtree(tmp_out_dir)
            except Exception:
                pass


def convert_to_pdf(file_obj, filename):
    """
    Convert any supported file to PDF.
    Returns: (pdf_django_file, original_filename_with_pdf_ext, was_converted)
    Raises ValueError for unsupported types.
    Raises RuntimeError if conversion fails.
    """
    from django.core.files.uploadedfile import InMemoryUploadedFile

    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
    pdf_filename = f'{name_without_ext}.pdf'

    if ext == 'pdf':
        # Already PDF — return as-is
        return file_obj, filename, False

    elif ext in ('jpg', 'jpeg', 'png'):
        pdf_bytes, _ = convert_image_to_pdf(file_obj)

    elif ext in ('doc', 'docx'):
        pdf_bytes, _ = convert_office_to_pdf(file_obj, filename)

    else:
        raise ValueError(f'Unsupported file type: .{ext}')

    # Wrap in Django file object
    pdf_io = io.BytesIO(pdf_bytes)
    django_file = InMemoryUploadedFile(
        pdf_io,
        getattr(file_obj, 'field_name', 'file'),
        pdf_filename,
        'application/pdf',
        len(pdf_bytes),
        None,
    )
    return django_file, pdf_filename, True


def compress_and_replace(uploaded_file, quality=DEFAULT_QUALITY):
    """
    Compress an uploaded PDF and return a Django-friendly file object.
    Returns: (file_object, compression_info_dict)
    """
    if not uploaded_file.name.lower().endswith('.pdf'):
        return uploaded_file, {'compressed': False, 'reason': 'Not a PDF'}

    compressed, original_size, compressed_size, savings = compress_pdf(uploaded_file, quality=quality)
    info = {
        'compressed': compressed is not None,
        'original_size': original_size,
        'final_size': compressed_size if compressed else original_size,
        'savings_percent': savings,
        'quality': quality,
    }

    if compressed:
        from django.core.files.uploadedfile import InMemoryUploadedFile
        compressed_io = io.BytesIO(compressed)
        new_file = InMemoryUploadedFile(
            compressed_io, uploaded_file.field_name, uploaded_file.name,
            'application/pdf', compressed_size, uploaded_file.charset,
        )
        return new_file, info
    else:
        uploaded_file.seek(0)
        return uploaded_file, info
