"""
AI Detector Models — v2
Stores scan history per user/organisation.
New in v2: chunk tracking fields for full-document analysis.
"""
import uuid
from django.db import models
from django.conf import settings


class AIDetectionScan(models.Model):
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'), ('docx', 'Word Document'), ('txt', 'Plain Text'),
        ('pptx', 'PowerPoint'), ('xlsx', 'Excel'), ('doc', 'Word (Legacy)'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'), ('processing', 'Processing'),
        ('completed', 'Completed'), ('failed', 'Failed'),
    ]
    PROVIDER_CHOICES = [
        ('auto', 'Auto (smart fallback)'),
        ('groq', 'Quick Scan (Llama 8B)'),
        ('groq_deep', 'Deep Scan (Llama 70B)'),
        ('gemini', 'Gemini Flash (1M context)'),
        ('mistral', 'Mistral AI (European)'),
        ('siliconflow', 'SiliconFlow (Llama 70B)'),
        ('cloudflare', 'Cloudflare Workers AI'),
        ('huggingface', 'HuggingFace (Free)'),
        ('grok', 'Grok (xAI)'),
        ('openai', 'OpenAI'),
        ('binoculars', 'Binoculars (local statistical)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_scans')
    organisation = models.ForeignKey(
        'organisations.Organisation', on_delete=models.CASCADE,
        related_name='ai_scans', null=True, blank=True,
    )

    # File info
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    file_size_bytes = models.IntegerField(default=0)
    text_length = models.IntegerField(default=0)

    # Extracted document text (shown in UI)
    extracted_text = models.TextField(blank=True, help_text='Full text extracted from the uploaded file')

    # Which AI provider was used
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='groq')

    # Detection result
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ai_probability = models.FloatField(null=True, blank=True)
    human_probability = models.FloatField(null=True, blank=True)
    verdict = models.CharField(max_length=20, blank=True)

    # LLM providers return a human-readable explanation
    explanation = models.TextField(blank=True, help_text='Explanation from LLM provider')

    # Sentence-level analysis (from LLM providers)
    sentence_analysis = models.JSONField(
        null=True, blank=True,
        help_text='Per-sentence AI probability scores from LLM providers',
    )

    # v2: Chunk tracking
    chunks_analysed = models.IntegerField(default=0, help_text='Number of chunks successfully analysed')
    chunks_total = models.IntegerField(default=1, help_text='Total chunks document was split into')
    ai_sentence_count = models.IntegerField(default=0, help_text='Number of sentences flagged as AI')
    total_sentence_count = models.IntegerField(default=0, help_text='Total sentences analysed')

    raw_response = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at'], name='ai_detector_user_id_idx'),
            models.Index(fields=['organisation', 'created_at'], name='ai_detector_org_id_idx'),
        ]

    def __str__(self):
        return f"{self.original_filename} — {self.verdict or self.status} ({self.provider})"

    @property
    def verdict_display(self):
        if self.ai_probability is None:
            return 'Unknown'
        pct = self.ai_probability * 100
        if pct >= 70:
            return f'Likely AI ({pct:.0f}%)'
        elif pct >= 40:
            return f'Possibly AI ({pct:.0f}%)'
        return f'Likely Human ({100 - pct:.0f}% human)'
