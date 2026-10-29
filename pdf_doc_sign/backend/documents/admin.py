from django.contrib import admin
from .models import Document, DocumentSigner, Signature, SignatureField, DocumentAuditLog, DocumentTemplate


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'file_type', 'page_count', 'file_size_mb', 'created_at')
    list_filter = ('status', 'file_type', 'created_at')
    search_fields = ('title', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'signed_at')


@admin.register(DocumentSigner)
class DocumentSignerAdmin(admin.ModelAdmin):
    list_display = ('signer_name', 'signer_email', 'document', 'status', 'signed_at')
    list_filter = ('status',)
    search_fields = ('signer_name', 'signer_email')


@admin.register(SignatureField)
class SignatureFieldAdmin(admin.ModelAdmin):
    list_display = ('document', 'field_type', 'page', 'signer_index', 'required', 'filled_at')
    list_filter = ('field_type', 'required')
    search_fields = ('document__title',)
    readonly_fields = ('id', 'created_at', 'filled_at')


@admin.register(Signature)
class SignatureAdmin(admin.ModelAdmin):
    list_display = ('user', 'signature_type', 'is_default', 'created_at')
    list_filter = ('signature_type', 'is_default')


@admin.register(DocumentAuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('document', 'action', 'user', 'ip_address', 'created_at')
    list_filter = ('action', 'created_at')
    readonly_fields = ('id', 'created_at')


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'is_premium')
    list_filter = ('category', 'is_active', 'is_premium')
