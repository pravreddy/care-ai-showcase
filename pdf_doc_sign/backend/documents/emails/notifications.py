"""
Email notification templates for document signing lifecycle.

Three notification types:
1. notify_sender_signer_completed  — sent to doc owner when each signer signs
2. notify_all_document_completed   — sent to all parties when doc is fully signed
   (attaches the signed PDF + audit certificate when they fit under the
   attachment size limit; falls back to download links otherwise)
3. send_reminder_email             — sent to a pending signer as a nudge
"""
import logging
import os
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives

logger = logging.getLogger('documents.emails')

BRAND_COLOR = '#1565c0'
SUCCESS_COLOR = '#2e7d32'
WARNING_COLOR = '#e65100'

# Keep attachments comfortably under Brevo / Gmail / Outlook inbound limits.
# Real cap on many corporate mail servers is 10MB; 8MB leaves headroom for
# base64 overhead (~+33%) and server-added headers. If combined artifacts
# exceed this, we fall back to secure download links in the email body.
MAX_ATTACHMENT_BYTES = 8 * 1024 * 1024


def _base_html(content_html, preheader=''):
    """Wrap content in the standard SignSimple email template."""
    return f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <span style="display:none;font-size:1px;color:#fff;max-height:0;overflow:hidden;">{preheader}</span>
  <div style="background: {BRAND_COLOR}; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
    <h1 style="margin: 0; font-size: 24px;">SignSimple</h1>
  </div>
  <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px;">
    {content_html}
  </div>
  <p style="text-align: center; color: #999; font-size: 12px; margin-top: 16px;">
    &copy; 2026 Avyangah Technologies Limited. All rights reserved.<br>
    <a href="https://signsimple.co.uk" style="color: #999;">signsimple.co.uk</a>
  </p>
</div>
"""


def _document_card(title, subtitle=''):
    """Reusable document info card for emails."""
    return f"""
    <div style="background: white; padding: 16px; border-radius: 8px; border: 1px solid #e0e0e0; margin: 20px 0;">
      <p style="margin: 0; font-weight: 600; font-size: 18px;">{title}</p>
      {f'<p style="margin: 4px 0 0; color: #666; font-size: 14px;">{subtitle}</p>' if subtitle else ''}
    </div>
"""


def _cta_button(url, label, color=SUCCESS_COLOR):
    """Reusable call-to-action button."""
    return f"""
    <center>
      <a href="{url}" style="display: inline-block; background: {color}; color: white; padding: 14px 40px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">{label}</a>
    </center>
"""


def _send(subject, text_body, html_body, recipient_email):
    """Wrapper around Django send_mail with logging."""
    try:
        send_mail(
            subject=subject,
            message=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_body,
            fail_silently=False,
        )
        logger.info(f'[NOTIFY] Email sent to {recipient_email}: {subject}')
        return True
    except Exception as e:
        logger.error(f'[NOTIFY] Failed to email {recipient_email}: {e}')
        return False


def _send_with_attachments(subject, text_body, html_body, recipient_email, attachments):
    """
    Send an email with one or more file attachments.

    attachments is a list of (filepath, display_filename, mime_type) tuples.
    Missing files are skipped silently (we already logged their absence in the
    caller). Total attachment size is assumed to have been checked by the
    caller — this function doesn't second-guess.
    """
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        msg.attach_alternative(html_body, 'text/html')
        for filepath, display_name, mime in attachments:
            if filepath and os.path.exists(filepath):
                msg.attach_file(filepath, mime)
                # attach_file uses the file's basename; we want a cleaner
                # display name (e.g. "signed_Contract.pdf" not
                # "signed_abc123....pdf"). Rewrite the last attachment's
                # filename to the display name the caller chose.
                if display_name:
                    msg.attachments[-1] = (display_name, msg.attachments[-1][1], mime)
            else:
                logger.warning(f'[NOTIFY] Attachment missing, skipping: {filepath}')
        msg.send(fail_silently=False)
        logger.info(
            f'[NOTIFY] Email with {len(msg.attachments)} attachment(s) '
            f'sent to {recipient_email}: {subject}'
        )
        return True
    except Exception as e:
        logger.error(f'[NOTIFY] Failed to email {recipient_email} with attachments: {e}')
        return False


def _collect_completion_artifacts(document):
    """
    Locate the signed PDF + audit certificate on disk for a completed
    document. Returns a dict with:
      - attachments: list of (path, display_name, mime) ready for attachment
      - total_size: sum of existing file sizes in bytes
      - fits_inline: whether total_size <= MAX_ATTACHMENT_BYTES
      - signed_path / cert_path: individual paths (or None if missing)

    Files are expected to have been pre-generated by
    SigningOrchestrator._generate_completion_artifacts on completion.
    """
    signed_path = os.path.join(
        settings.MEDIA_ROOT, 'signed', f'signed_{document.id}.pdf',
    )
    cert_path = os.path.join(
        settings.MEDIA_ROOT, 'certificates', f'audit_certificate_{document.id}.pdf',
    )

    # Safe title for filename — strip path separators, keep it short
    safe_title = ''.join(c for c in (document.title or 'document') if c.isalnum() or c in ' -_').strip()
    safe_title = safe_title[:60] or 'document'

    attachments = []
    total_size = 0

    if os.path.exists(signed_path):
        total_size += os.path.getsize(signed_path)
        attachments.append((
            signed_path,
            f'signed_{safe_title}.pdf',
            'application/pdf',
        ))
    else:
        logger.warning(f'[NOTIFY] Signed PDF missing for doc {document.id}: {signed_path}')

    if os.path.exists(cert_path):
        total_size += os.path.getsize(cert_path)
        attachments.append((
            cert_path,
            f'audit_certificate_{safe_title}.pdf',
            'application/pdf',
        ))
    else:
        logger.warning(f'[NOTIFY] Audit certificate missing for doc {document.id}: {cert_path}')

    return {
        'attachments': attachments,
        'total_size': total_size,
        'fits_inline': total_size > 0 and total_size <= MAX_ATTACHMENT_BYTES,
        'signed_path': signed_path if os.path.exists(signed_path) else None,
        'cert_path': cert_path if os.path.exists(cert_path) else None,
    }


# =================================================================
# 1. Notify sender when a signer completes
# =================================================================

def notify_sender_signer_completed(document, signer):
    """
    Notify the document owner that a specific signer has signed.
    Called each time a signer completes their signature.
    """
    sender = document.user
    sender_name = sender.full_name or sender.email.split('@')[0]
    doc_url = f'https://signsimple.co.uk/documents/{document.id}'

    # Count progress
    total_signers = document.signers.count()
    signed_count = document.signers.filter(status='SIGNED').count()
    pending_count = total_signers - signed_count

    subject = f'{signer.signer_name} has signed "{document.title}"'

    text_body = f"""Hi {sender_name},

{signer.signer_name} ({signer.signer_email}) has signed your document "{document.title}".

Progress: {signed_count} of {total_signers} signers completed.
{f'{pending_count} signer(s) still pending.' if pending_count > 0 else 'All signers have completed!'}

View the document: {doc_url}

Best regards,
SignSimple — Avyangah Technologies Limited
"""

    progress_text = f'{signed_count} of {total_signers} signed'
    if pending_count > 0:
        progress_bar = f"""
        <div style="background: #e0e0e0; border-radius: 10px; height: 8px; margin: 12px 0;">
          <div style="background: {SUCCESS_COLOR}; border-radius: 10px; height: 8px; width: {int(signed_count/total_signers*100)}%;"></div>
        </div>
        <p style="color: #666; font-size: 14px; text-align: center;">{progress_text} &mdash; {pending_count} pending</p>
"""
    else:
        progress_bar = f"""
        <div style="background: {SUCCESS_COLOR}; border-radius: 10px; height: 8px; margin: 12px 0;"></div>
        <p style="color: {SUCCESS_COLOR}; font-size: 14px; text-align: center; font-weight: 600;">All signers completed!</p>
"""

    content = f"""
    <p>Hi {sender_name},</p>
    <p><strong>{signer.signer_name}</strong> ({signer.signer_email}) has signed your document:</p>
    {_document_card(document.title, f'Signed at {signer.signed_at.strftime("%d %b %Y %H:%M UTC") if signer.signed_at else "just now"}')}
    {progress_bar}
    {_cta_button(doc_url, 'View Document')}
"""

    html_body = _base_html(content, preheader=f'{signer.signer_name} signed — {progress_text}')
    return _send(subject, text_body, html_body, sender.email)


# =================================================================
# 2. Notify all parties when document is fully signed
# =================================================================

def notify_all_document_completed(document):
    """
    Notify sender and all signers that the document is fully signed.
    Called once when the last signer completes.

    Attaches the signed PDF + audit certificate to every email when total
    attachment size is within MAX_ATTACHMENT_BYTES. Otherwise falls back
    to a 'download from your account' link for the sender and per-signer
    tokenised links for each signer.
    """
    sender = document.user
    sender_name = sender.full_name or sender.email.split('@')[0]
    doc_url = f'https://signsimple.co.uk/documents/{document.id}'
    signers = document.signers.all().order_by('signing_order')

    # Locate the pre-generated attachments + decide delivery mode
    artifacts = _collect_completion_artifacts(document)
    deliver_inline = artifacts['fits_inline']

    if not deliver_inline and artifacts['total_size'] > 0:
        size_mb = artifacts['total_size'] / (1024 * 1024)
        logger.warning(
            f'[NOTIFY] Doc {document.id} artifacts total {size_mb:.1f}MB > '
            f'{MAX_ATTACHMENT_BYTES / (1024 * 1024):.1f}MB limit; sending download links instead.'
        )

    # Build signer list HTML (reused across recipient templates)
    signer_list_html = ''
    for s in signers:
        signer_list_html += f"""
        <div style="display: flex; align-items: center; padding: 8px 0; border-bottom: 1px solid #eee;">
          <span style="color: {SUCCESS_COLOR}; font-size: 18px; margin-right: 10px;">&#10004;</span>
          <span style="font-size: 14px;">{s.signer_name} ({s.signer_email})
            <span style="color: #999; font-size: 12px;"> &mdash; {s.signed_at.strftime('%d %b %Y %H:%M') if s.signed_at else ''}</span>
          </span>
        </div>
"""

    # Shared attachment-status notice for email bodies
    if deliver_inline:
        attachment_notice_html = f"""
    <p style="color: {SUCCESS_COLOR}; font-size: 14px; font-weight: 600; margin-top: 16px;">
      &#128206; Your signed document and audit certificate are attached to this email.
    </p>
"""
        attachment_notice_text = (
            'Your signed document and audit certificate are attached to this email.\n'
        )
    else:
        attachment_notice_html = f"""
    <p style="color: {WARNING_COLOR}; font-size: 14px; margin-top: 16px;">
      The signed document is too large to attach directly. Use the link below to download it.
    </p>
"""
        attachment_notice_text = (
            'The signed document is too large to attach directly; use the link below to download it.\n'
        )

    # --- Send to document owner ---
    subject_sender = f'All signed — "{document.title}" is complete'
    text_sender = f"""Hi {sender_name},

Great news! All signers have completed signing "{document.title}".

{attachment_notice_text}
View document: {doc_url}

Best regards,
SignSimple — Avyangah Technologies Limited
"""
    content_sender = f"""
    <p>Hi {sender_name},</p>
    <p style="font-size: 16px;">&#127881; Great news! All signers have completed signing your document:</p>
    {_document_card(document.title, f'Completed {document.signed_at.strftime("%d %b %Y %H:%M UTC") if document.signed_at else "just now"}')}
    <div style="background: white; padding: 16px; border-radius: 8px; border: 1px solid #e0e0e0; margin: 20px 0;">
      <p style="margin: 0 0 8px; font-weight: 600;">Signers:</p>
      {signer_list_html}
    </div>
    {attachment_notice_html}
    {_cta_button(doc_url, 'View in Dashboard')}
"""
    html_sender = _base_html(content_sender, preheader=f'All signers completed — {document.title}')

    if deliver_inline:
        _send_with_attachments(subject_sender, text_sender, html_sender, sender.email, artifacts['attachments'])
    else:
        _send(subject_sender, text_sender, html_sender, sender.email)

    # --- Send to each signer ---
    for s in signers:
        # Per-signer tokenised download link for the fallback case.
        # Points directly at the backend download endpoint so clicking
        # the email returns the PDF binary without needing a React route.
        signer_download_url = f'https://signsimple.co.uk/api/sign/{s.access_token}/download/'

        subject_signer = f'Signed copy — "{document.title}"'
        text_signer = f"""Hi {s.signer_name},

All parties have now signed "{document.title}".

{attachment_notice_text}
{('Download your signed copy: ' + signer_download_url) if not deliver_inline else ''}

Thank you for using SignSimple.

Best regards,
SignSimple — Avyangah Technologies Limited
"""
        download_block_html = '' if deliver_inline else f"""
    {_cta_button(signer_download_url, 'Download Signed Copy')}
"""
        content_signer = f"""
    <p>Hi {s.signer_name},</p>
    <p>All parties have now signed the document:</p>
    {_document_card(document.title, f'Sent by {sender_name}')}
    {attachment_notice_html}
    {download_block_html}
    <p style="color: #666; font-size: 14px; margin-top: 16px;">
      Thank you for using SignSimple.
    </p>
"""
        html_signer = _base_html(content_signer, preheader=f'Your signed copy of {document.title}')

        if deliver_inline:
            _send_with_attachments(subject_signer, text_signer, html_signer, s.signer_email, artifacts['attachments'])
        else:
            _send(subject_signer, text_signer, html_signer, s.signer_email)


# =================================================================
# 3. Reminder email for pending signers
# =================================================================

def send_reminder_email(signer, document, sender_user):
    """
    Send a reminder to a pending signer.
    Called manually by the document owner via the API.
    """
    signing_url = f'https://signsimple.co.uk/sign/{signer.access_token}'
    sender_name = sender_user.full_name or sender_user.email.split('@')[0]

    subject = f'Reminder: "{document.title}" is waiting for your signature'

    text_body = f"""Hi {signer.signer_name},

This is a friendly reminder that {sender_name} is waiting for you to sign "{document.title}".

Click the link below to review and sign:

{signing_url}

This link expires on {signer.access_expires_at.strftime('%d %b %Y')}.

Best regards,
SignSimple — Avyangah Technologies Limited
"""

    content = f"""
    <p>Hi {signer.signer_name},</p>
    <p>This is a friendly reminder that <strong>{sender_name}</strong> is waiting for you to sign:</p>
    {_document_card(document.title, f'Expires {signer.access_expires_at.strftime("%d %b %Y")}')}
    {_cta_button(signing_url, 'Review &amp; Sign')}
    <p style="margin-top: 24px; color: #666; font-size: 14px;">
      If the button doesn't work, copy this link into your browser:<br>
      <a href="{signing_url}" style="color: {BRAND_COLOR}; word-break: break-all;">{signing_url}</a>
    </p>
"""

    html_body = _base_html(content, preheader=f'Reminder — {document.title} needs your signature')
    return _send(subject, text_body, html_body, signer.signer_email)
