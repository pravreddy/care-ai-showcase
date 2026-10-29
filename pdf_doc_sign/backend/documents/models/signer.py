"""
Signer models — DocumentSigner (per-document signer record) and Signature (reusable saved signatures).
"""
import uuid
from django.db import models
from django.conf import settings

from .upload_paths import signature_upload_path
from .document import Document


class DocumentSigner(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SIGNED', 'Signed'),
        ('DECLINED', 'Declined'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='signers')
    signer_name = models.CharField(max_length=255)
    signer_email = models.EmailField()
    signer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    signing_order = models.IntegerField(default=1)
    signed_at = models.DateTimeField(null=True, blank=True)
    signature_image = models.ImageField(upload_to=signature_upload_path, null=True, blank=True)
    access_token = models.CharField(max_length=100, unique=True)
    access_expires_at = models.DateTimeField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['document', 'signing_order']
        unique_together = ['document', 'signer_email']

    def __str__(self):
        return f"{self.signer_name} - {self.document.title}"


class Signature(models.Model):
    """Reusable saved signature (drawn/typed/uploaded) for a user."""
    TYPE_CHOICES = (
        ('DRAWN', 'Hand Drawn'),
        ('TYPED', 'Typed'),
        ('UPLOADED', 'Uploaded'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='signatures')
    signature_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    signature_image = models.ImageField(upload_to=signature_upload_path)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.is_default:
            Signature.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
