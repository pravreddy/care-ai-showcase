from django.contrib import admin
from .models import PlagiarismScan


@admin.register(PlagiarismScan)
class PlagiarismScanAdmin(admin.ModelAdmin):
    list_display = [
        'original_filename', 'user', 'provider', 'status',
        'plagiarism_score', 'verdict', 'created_at',
    ]
    list_filter = ['status', 'provider', 'verdict', 'file_type']
    search_fields = ['user__email', 'original_filename']
    readonly_fields = [
        'id', 'user', 'organisation', 'original_filename', 'file_type',
        'file_size_bytes', 'text_length', 'extracted_text', 'provider',
        'status', 'plagiarism_score', 'original_score', 'verdict',
        'explanation', 'sentence_matches', 'source_matches',
        'raw_response', 'error_message', 'created_at', 'updated_at',
    ]
    ordering = ['-created_at']
