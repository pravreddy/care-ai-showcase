"""
Chatbot Models — Lead capture via AI conversation.

Flow:
  1. Visitor lands on signsimple.co.uk → chat widget opens
  2. ChatSession created (anonymous, no auth)
  3. AI conversation via Groq (ChatMessage records)
  4. When visitor shares name + email → Lead created
  5. Coupon generated and linked to Lead
  6. Email sent via Postal/Brevo with coupon code
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class ChatSession(models.Model):
    """
    A single conversation between a visitor and the AI chatbot.
    Sessions are anonymous — no login required.
    """
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed — lead captured'),
        ('ABANDONED', 'Abandoned — visitor left'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Visitor tracking (anonymous)
    visitor_ip = models.GenericIPAddressField(null=True, blank=True)
    visitor_user_agent = models.TextField(blank=True)
    visitor_referrer = models.URLField(blank=True, max_length=500)
    visitor_page = models.URLField(blank=True, max_length=500, help_text='Which page the chat was started from')

    # Session state
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    message_count = models.IntegerField(default=0)

    # Extracted info (populated as conversation progresses)
    extracted_first_name = models.CharField(max_length=100, blank=True)
    extracted_last_name = models.CharField(max_length=100, blank=True)
    extracted_email = models.EmailField(blank=True)
    extracted_company = models.CharField(max_length=255, blank=True)
    extracted_use_case = models.TextField(blank=True, help_text='What the visitor wants to use SignSimple for')

    # Which offer the AI decided on
    offer_plan = models.CharField(max_length=20, blank=True, help_text='STARTER or PROFESSIONAL')
    offer_duration_days = models.IntegerField(null=True, blank=True)

    # Links
    lead = models.OneToOneField(
        'Lead', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='chat_session',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        name = f"{self.extracted_first_name} {self.extracted_last_name}".strip()
        return f"Chat {str(self.id)[:8]} — {name or 'Anonymous'} ({self.status})"


class ChatMessage(models.Model):
    """Individual message in a chat session."""
    ROLE_CHOICES = (
        ('user', 'Visitor'),
        ('assistant', 'AI'),
        ('system', 'System'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.role}] {self.content[:80]}"


class Lead(models.Model):
    """
    A captured lead from the chatbot.
    Links to a Coupon (from subscriptions app) once generated.
    """
    STATUS_CHOICES = (
        ('NEW', 'New — just captured'),
        ('COUPON_SENT', 'Coupon email sent'),
        ('SIGNED_UP', 'Signed up on platform'),
        ('CONVERTED', 'Converted to paying customer'),
        ('LOST', 'Did not convert'),
    )
    SOURCE_CHOICES = (
        ('CHATBOT', 'AI Chatbot'),
        ('MANUAL', 'Manually added'),
        ('IMPORT', 'CSV Import'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(db_index=True)
    company = models.CharField(max_length=255, blank=True)
    use_case = models.TextField(blank=True, help_text='What they want to use SignSimple for')

    # Source
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='CHATBOT')
    conversation_summary = models.TextField(blank=True, help_text='AI-generated summary of the chat')

    # Coupon link (from subscriptions app)
    coupon = models.OneToOneField(
        'subscriptions.Coupon', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='lead',
    )

    # Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    signed_up_at = models.DateTimeField(null=True, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email}) — {self.status}"
