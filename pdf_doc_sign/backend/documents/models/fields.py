"""
SignatureField model — positioned form fields placed on PDF pages.
"""
import uuid
from django.db import models

from .upload_paths import signature_upload_path
from .document import Document


class SignatureField(models.Model):
    """
    Defines a signature/form field placed on a specific position on a PDF page.
    Created by the document sender during the "Prepare" step.

    Coordinates are stored as percentages (0-100) of the page dimensions,
    so they work regardless of zoom level or render size.
    """
    FIELD_TYPE_CHOICES = (
        ('SIGNATURE', 'Signature'),
        ('DATE', 'Date'),
        ('NAME', 'Full Name'),
        ('TEXT', 'Text Field'),
        ('INITIALS', 'Initials'),
        ('CHECKBOX', 'Checkbox'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='signature_fields')
    signer_index = models.IntegerField(default=1, help_text='Which signer (1-indexed) this field is for')
    field_type = models.CharField(max_length=20, choices=FIELD_TYPE_CHOICES, default='SIGNATURE')

    # Position on PDF (percentages of page dimensions)
    page = models.IntegerField(help_text='Page number (1-indexed)')
    x_percent = models.FloatField(help_text='X position as percentage of page width (0-100)')
    y_percent = models.FloatField(help_text='Y position as percentage of page height (0-100)')
    width_percent = models.FloatField(default=20, help_text='Width as percentage of page width')
    height_percent = models.FloatField(default=5, help_text='Height as percentage of page height')

    # Optional label shown on the field
    label = models.CharField(max_length=100, blank=True)
    required = models.BooleanField(default=True)

    # Filled value (populated when signer completes the field)
    filled_value = models.TextField(blank=True, help_text='Text value for date/name/text fields')
    filled_signature = models.ImageField(upload_to=signature_upload_path, null=True, blank=True)
    filled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['document', 'page', 'y_percent', 'x_percent']
        indexes = [
            models.Index(fields=['document', 'signer_index']),
        ]

    def __str__(self):
        return f"{self.field_type} on page {self.page} for signer {self.signer_index}"
