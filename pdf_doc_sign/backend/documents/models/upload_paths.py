"""
Upload path helpers — shared across multiple models.
"""


def document_upload_path(instance, filename):
    """Structured path: documents/{org}/{client_or_branch}/{date}/{filename}"""
    from documents.services import get_structured_upload_path
    return get_structured_upload_path(instance, filename)


def signature_upload_path(instance, filename):
    return f'signatures/{instance.id}/{filename}'
