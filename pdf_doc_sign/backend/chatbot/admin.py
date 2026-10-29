from django.contrib import admin
from .models import ChatSession, ChatMessage, Lead


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'extracted_first_name', 'extracted_email', 'status', 'message_count', 'created_at']
    list_filter = ['status']
    search_fields = ['extracted_first_name', 'extracted_email', 'visitor_ip']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'content_preview', 'created_at']
    list_filter = ['role']
    readonly_fields = ['id', 'created_at']

    def content_preview(self, obj):
        return obj.content[:80] + '...' if len(obj.content) > 80 else obj.content
    content_preview.short_description = 'Content'


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'company', 'source', 'status', 'coupon', 'created_at']
    list_filter = ['status', 'source']
    search_fields = ['first_name', 'last_name', 'email', 'company']
    readonly_fields = ['id', 'created_at', 'updated_at']
