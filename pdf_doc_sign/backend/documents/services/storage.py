"""
Storage path helpers for documents, sales, and invoices.
"""
import os
import logging
from django.utils import timezone
from django.utils.text import slugify

logger = logging.getLogger('documents.storage')


def get_structured_upload_path(document, filename):
    """
    Generate structured storage path for uploaded documents.
    Pattern: documents/{org_slug}/{client_or_branch}/{YYYY-MM-DD}/{filename}
    """
    now = timezone.now()
    date_folder = now.strftime('%Y-%m-%d')

    name, ext = os.path.splitext(filename)
    clean_name = slugify(name)[:80] or 'document'
    clean_filename = f"{clean_name}{ext.lower()}"

    user = document.user
    org_slug = 'personal'
    client_folder = slugify(user.email.split('@')[0])[:40]

    try:
        from organisations.models import OrganisationMembership
        membership = OrganisationMembership.objects.filter(
            user=user, is_active=True,
        ).select_related('organisation', 'branch').first()
        if membership:
            org_slug = membership.organisation.slug
            if membership.branch:
                client_folder = slugify(membership.branch.name)[:40]
            else:
                client_folder = slugify(membership.organisation.name)[:40]
    except Exception:
        pass

    path = f"documents/{org_slug}/{client_folder}/{date_folder}/{clean_filename}"
    logger.info(f'Path: {path}')
    return path


def get_sales_document_path(client, filename):
    """Storage path for sales documents: sales/{org}/{client}/{date}/{file}"""
    now = timezone.now()
    org_slug = client.organisation.slug
    client_slug = slugify(client.name)[:40]
    date_folder = now.strftime('%Y-%m-%d')
    name, ext = os.path.splitext(filename)
    clean_filename = f"{slugify(name)[:80]}{ext.lower()}"
    return f"sales/{org_slug}/{client_slug}/{date_folder}/{clean_filename}"


def get_invoice_path(invoice, filename):
    """Storage path for invoices: invoices/{org}/{client}/{YYYY-MM}/{file}"""
    org_slug = invoice.client.organisation.slug
    client_slug = slugify(invoice.client.name)[:40]
    month_folder = invoice.from_date.strftime('%Y-%m')
    return f"invoices/{org_slug}/{client_slug}/{month_folder}/{filename}"
