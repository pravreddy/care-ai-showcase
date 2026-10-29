"""
Email templates for document signing notifications.
"""
import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger('documents')


def send_signing_email(signer, document, sender):
    """
    Send signing request email to a signer.
    Returns True if sent successfully, False otherwise.
    """
    signing_url = f'https://signsimple.co.uk/sign/{signer.access_token}'
    sender_name = sender.full_name or sender.email.split('@')[0]

    subject = f'{sender_name} has sent you a document to sign — {document.title}'

    text_body = f"""Hi {signer.signer_name},

{sender_name} has sent you \"{document.title}\" to sign using SignSimple.

Click the link below to review and sign the document:

{signing_url}

This link expires on {signer.access_expires_at.strftime('%d %b %Y')}.

If you did not expect this, you can ignore this email.

Best regards,
SignSimple — Avyangah Technologies Limited
"""

    html_body = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="background: #1565c0; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
    <h1 style="margin: 0; font-size: 24px;">SignSimple</h1>
  </div>
  <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px;">
    <p>Hi {signer.signer_name},</p>
    <p><strong>{sender_name}</strong> has sent you a document to sign:</p>
    <div style="background: white; padding: 16px; border-radius: 8px; border: 1px solid #e0e0e0; margin: 20px 0;">
      <p style="margin: 0; font-weight: 600; font-size: 18px;">{document.title}</p>
      <p style="margin: 4px 0 0; color: #666; font-size: 14px;">PDF Document &middot; Expires {signer.access_expires_at.strftime('%d %b %Y')}</p>
    </div>
    <center>
      <a href="{signing_url}" style="display: inline-block; background: #4caf50; color: white; padding: 14px 40px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">Review & Sign</a>
    </center>
    <p style="margin-top: 24px; color: #666; font-size: 14px;">If the button doesn't work, copy this link into your browser:<br>
    <a href="{signing_url}" style="color: #1565c0; word-break: break-all;">{signing_url}</a></p>
    <p style="color: #999; font-size: 12px; margin-top: 24px;">If you did not expect this email, you can safely ignore it.</p>
  </div>
  <p style="text-align: center; color: #999; font-size: 12px; margin-top: 16px;">&copy; 2026 Avyangah Technologies Limited. All rights reserved.</p>
</div>
"""

    try:
        send_mail(
            subject=subject,
            message=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[signer.signer_email],
            html_message=html_body,
            fail_silently=False,
        )
        logger.info(f'[SIGNING] Email sent to {signer.signer_email} for "{document.title}"')
        return True
    except Exception as e:
        logger.error(f'[SIGNING] Failed to email {signer.signer_email}: {e}')
        return False
