"""
Plagiarism Checker Views

POST /api/plagiarism/scan/         — upload file, get plagiarism score + extracted text
POST /api/plagiarism/scan-text/    — paste text directly, get plagiarism score
GET  /api/plagiarism/history/      — list user's past scans
DELETE /api/plagiarism/scans/<id>/ — delete a specific scan
GET  /api/plagiarism/providers/    — list available providers
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings

from .models import PlagiarismScan
from .serializers import PlagiarismScanSerializer
from .services import check_plagiarism, DEFAULT_PROVIDER

# Reuse the text extraction utilities from ai_detector
from ai_detector.utils import extract_text, get_extension, SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
VALID_PROVIDERS = ['groq', 'copyleaks']


def _save_result(scan, result):
    """Save plagiarism result onto a scan object."""
    scan.status = 'completed' if not result.get('error') else 'failed'
    scan.plagiarism_score = result.get('plagiarism_score')
    scan.original_score = result.get('original_score')
    scan.verdict = result.get('verdict', '')
    scan.explanation = result.get('explanation') or ''
    scan.sentence_matches = result.get('sentence_matches') or []
    scan.source_matches = result.get('source_matches') or []
    scan.raw_response = result.get('raw')
    scan.error_message = result.get('error') or ''
    scan.save()
    return scan


class PlagiarismScanFileView(APIView):
    """POST a file — returns plagiarism score + extracted text + sentence analysis."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        if file.size > MAX_FILE_SIZE:
            return Response(
                {'error': 'File too large. Maximum size is 10MB.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ext = get_extension(file.name)
        if ext not in SUPPORTED_EXTENSIONS:
            return Response(
                {'error': f'.{ext} is not supported.', 'supported': SUPPORTED_EXTENSIONS},
                status=status.HTTP_400_BAD_REQUEST,
            )

        provider = (
            request.data.get('provider')
            or request.query_params.get('provider')
            or DEFAULT_PROVIDER
        )
        if provider not in VALID_PROVIDERS:
            return Response(
                {'error': f'Unknown provider "{provider}". Valid: {VALID_PROVIDERS}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        organisation = getattr(request, 'organisation', None)

        scan = PlagiarismScan.objects.create(
            user=request.user,
            organisation=organisation,
            original_filename=file.name,
            file_type=ext,
            file_size_bytes=file.size,
            status='pending',
            provider=provider,
        )

        try:
            text, _ = extract_text(file, file.name)
        except ValueError as e:
            scan.status = 'failed'
            scan.error_message = str(e)
            scan.save(update_fields=['status', 'error_message'])
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            logger.error(f'Text extraction error for {file.name}: {e}')
            scan.status = 'failed'
            scan.error_message = 'Failed to read file content.'
            scan.save(update_fields=['status', 'error_message'])
            return Response(
                {'error': 'Could not read file content.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        scan.text_length = len(text)
        scan.extracted_text = text
        scan.save(update_fields=['text_length', 'extracted_text'])

        if not text.strip():
            scan.status = 'failed'
            scan.error_message = 'No text could be extracted from this file.'
            scan.save(update_fields=['status', 'error_message', 'text_length', 'extracted_text'])
            return Response({'error': scan.error_message}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        result = check_plagiarism(text, provider=provider)
        _save_result(scan, result)

        return Response(PlagiarismScanSerializer(scan).data, status=status.HTTP_200_OK)


class PlagiarismScanTextView(APIView):
    """POST plain text directly — no file needed."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get('text', '').strip()
        if len(text) < 100:
            return Response(
                {'error': 'Text too short. Minimum 100 characters required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(text) > 50000:
            text = text[:50000]

        provider = request.data.get('provider') or DEFAULT_PROVIDER
        if provider not in VALID_PROVIDERS:
            return Response(
                {'error': f'Unknown provider "{provider}". Valid: {VALID_PROVIDERS}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        organisation = getattr(request, 'organisation', None)

        scan = PlagiarismScan.objects.create(
            user=request.user,
            organisation=organisation,
            original_filename='Pasted text',
            file_type='txt',
            file_size_bytes=len(text.encode('utf-8')),
            text_length=len(text),
            extracted_text=text,
            status='pending',
            provider=provider,
        )

        result = check_plagiarism(text, provider=provider)
        _save_result(scan, result)

        return Response(PlagiarismScanSerializer(scan).data, status=status.HTTP_200_OK)


class PlagiarismHistoryView(APIView):
    """GET list of past scans for the current user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organisation = getattr(request, 'organisation', None)
        scans = PlagiarismScan.objects.filter(user=request.user)
        if organisation:
            scans = scans.filter(organisation=organisation)
        scans = scans.order_by('-created_at')[:50]
        return Response({'results': PlagiarismScanSerializer(scans, many=True).data})


class PlagiarismScanDeleteView(APIView):
    """DELETE a specific scan by ID."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, scan_id):
        try:
            scan = PlagiarismScan.objects.get(id=scan_id, user=request.user)
            scan.delete()
            return Response({'deleted': str(scan_id)}, status=status.HTTP_200_OK)
        except PlagiarismScan.DoesNotExist:
            return Response({'error': 'Scan not found.'}, status=status.HTTP_404_NOT_FOUND)


class PlagiarismProvidersView(APIView):
    """GET — returns which providers are configured and available."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        groq_key = getattr(settings, 'GROQ_API_KEY', '')
        copyleaks_key = getattr(settings, 'COPYLEAKS_API_KEY', '')
        copyleaks_email = getattr(settings, 'COPYLEAKS_EMAIL', '')

        return Response({
            'default': DEFAULT_PROVIDER,
            'providers': [
                {
                    'id': 'groq',
                    'name': 'Groq Pattern Analysis (Free)',
                    'description': (
                        'Uses Llama 3.1 to detect copied patterns, style shifts, '
                        'and known text signatures. No live web search.'
                    ),
                    'available': bool(groq_key),
                    'configured': bool(groq_key),
                    'has_source_urls': False,
                    'cost': 'Free',
                },
                {
                    'id': 'copyleaks',
                    'name': 'Copyleaks (Web + Academic Search)',
                    'description': (
                        'Real-time search against billions of web pages, '
                        'academic papers, and journals. Returns matched source URLs.'
                    ),
                    'available': bool(copyleaks_key and copyleaks_email),
                    'configured': bool(copyleaks_key and copyleaks_email),
                    'has_source_urls': True,
                    'cost': 'Paid (per scan)',
                },
            ],
        })
