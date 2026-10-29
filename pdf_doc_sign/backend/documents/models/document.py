"""
Document model — the core entity representing an uploaded PDF.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

from .upload_paths import document_upload_path


class Document(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Signature'),
        ('SIGNED', 'Signed'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=document_upload_path)
    file_size = models.BigIntegerField(help_text='Final size after compression')
    file_type = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    is_encrypted = models.BooleanField(default=True)
    sequential_signing = models.BooleanField(
        default=False,
        help_text='If true, signers are emailed one at a time in signing_order; '
                  'each is released only after the previous signer completes.',
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    signed_at = models.DateTimeField(null=True, blank=True)

    # PDF compression metadata
    original_file_size = models.BigIntegerField(null=True, blank=True, help_text='Size before compression')
    was_compressed = models.BooleanField(default=False)
    compression_savings = models.FloatField(default=0, help_text='Percentage saved by compression')

    # PDF metadata
    page_count = models.IntegerField(null=True, blank=True, help_text='Number of pages in PDF')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)

    @property
    def original_file_size_mb(self):
        if self.original_file_size:
            return round(self.original_file_size / (1024 * 1024), 2)
        return self.file_size_mb

    def mark_as_signed(self):
        self.status = 'SIGNED'
        self.signed_at = timezone.now()
        self.save(update_fields=['status', 'signed_at'])
