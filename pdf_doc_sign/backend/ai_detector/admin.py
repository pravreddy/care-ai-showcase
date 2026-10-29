from django.contrib import admin
from .models import AIDetectionScan


@admin.register(AIDetectionScan)
class AIDetectionScanAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'file_type', 'verdict', 'ai_probability', 'user', 'created_at']
    list_filter = ['verdict', 'file_type', 'status']
    search_fields = ['original_filename', 'user__email']
    readonly_fields = ['id', 'raw_response', 'created_at', 'updated_at']
    ordering = ['-created_at']
