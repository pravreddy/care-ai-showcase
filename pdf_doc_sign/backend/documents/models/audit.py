"""
DocumentAuditLog model — tracks all actions on a document.
"""
import uuid
from django.db import models
from django.conf import settings

from .document import Document


class DocumentAuditLog(models.Model):
    ACTION_CHOICES = (
        ('CREATED', 'Created'),
        ('VIEWED', 'Viewed'),
        ('DOWNLOADED', 'Downloaded'),
        ('SIGNED', 'Signed'),
        ('SENT', 'Sent for Signing'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
        ('PREPARED', 'Fields Placed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['document', 'created_at'])]
