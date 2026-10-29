"""
Plagiarism Checker Models
Stores scan history per user/organisation.
"""
import uuid
from django.db import models
from django.conf import settings


class PlagiarismScan(models.Model):
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'), ('docx', 'Word Document'), ('txt', 'Plain Text'),
        ('pptx', 'PowerPoint'), ('xlsx', 'Excel'), ('doc', 'Word (Legacy)'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed'),
    ]
    PROVIDER_CHOICES = [
        ('groq', 'Groq (Free — Pattern Analysis)'),
        ('copyleaks', 'Copyleaks (Web Search)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='plagiarism_scans',
    )
    organisation = models.ForeignKey(
        'organisations.Organisation', on_delete=models.CASCADE,
        related_name='plagiarism_scans', null=True, blank=True,
    )

    # Input
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    file_size_bytes = models.IntegerField(default=0)
    text_length = models.IntegerField(default=0)
    extracted_text = models.TextField(blank=True)

    # Provider used
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='groq')

    # Result
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    plagiarism_score = models.FloatField(
        null=True, blank=True,
        help_text='0.0 = fully original, 1.0 = fully plagiarised',
    )
    original_score = models.FloatField(
        null=True, blank=True,
        help_text='0.0 to 1.0 — proportion of original content',
    )
    verdict = models.CharField(max_length=30, blank=True)

    # Summary explanation
    explanation = models.TextField(blank=True)

    # Sentence-level matches
    sentence_matches = models.JSONField(
        null=True, blank=True,
        help_text='Per-sentence plagiarism flags with matched source if available',
    )

    # External source matches (Copyleaks etc.)
    source_matches = models.JSONField(
        null=True, blank=True,
        help_text='List of matched external sources returned by provider',
    )

    raw_response = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at'], name='plagiarism_user_created_idx'),
            models.Index(fields=['organisation', 'created_at'], name='plagiarism_org_created_idx'),
        ]

    def __str__(self):
        return f"{self.original_filename} — {self.verdict or self.status} ({self.provider})"

    @property
    def verdict_display(self):
        if self.plagiarism_score is None:
            return 'Unknown'
        pct = self.plagiarism_score * 100
        if pct >= 50:
            return f'High Plagiarism ({pct:.0f}%)'
        elif pct >= 20:
            return f'Some Similarities ({pct:.0f}%)'
        return f'Mostly Original ({100 - pct:.0f}% original)'
