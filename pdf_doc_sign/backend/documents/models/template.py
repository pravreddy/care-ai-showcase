"""
DocumentTemplate model — reusable document templates with pre-placed fields.
"""
import uuid
from django.db import models
from django.conf import settings

from .document import Document


class DocumentTemplate(models.Model):
    CATEGORY_CHOICES = (
        ('NDA', 'Non-Disclosure Agreement'),
        ('CONTRACT', 'Contract'),
        ('INVOICE', 'Invoice'),
        ('PROPOSAL', 'Proposal'),
        ('AGREEMENT', 'Agreement'),
        ('OTHER', 'Other'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='OTHER')
    template_file = models.FileField(upload_to='templates/')
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # User-owned templates (null = system/admin template)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True, related_name='templates',
        help_text='Owner of this template. Null for system templates.',
    )

    # Pre-placed signature field positions (JSON array)
    fields_config = models.JSONField(
        default=list, blank=True,
        help_text='Saved signature field positions for this template.',
    )

    # Which document this template was created from
    source_document = models.ForeignKey(
        Document, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='derived_templates',
    )

    # Metadata
    page_count = models.IntegerField(null=True, blank=True)
    use_count = models.IntegerField(default=0, help_text='How many times this template has been used')

    class Meta:
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        owner = self.user.email if self.user else 'System'
        return f"{self.name} ({self.category}) \u2014 {owner}"

    @property
    def is_system_template(self):
        return self.user is None
