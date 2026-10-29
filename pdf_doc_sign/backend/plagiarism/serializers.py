from rest_framework import serializers
from .models import PlagiarismScan


class PlagiarismScanSerializer(serializers.ModelSerializer):
    verdict_display = serializers.ReadOnlyField()
    plagiarism_percentage = serializers.SerializerMethodField()
    original_percentage = serializers.SerializerMethodField()

    class Meta:
        model = PlagiarismScan
        fields = [
            'id', 'original_filename', 'file_type', 'file_size_bytes',
            'text_length', 'extracted_text', 'provider',
            'status', 'plagiarism_score', 'original_score',
            'plagiarism_percentage', 'original_percentage',
            'verdict', 'verdict_display', 'explanation',
            'sentence_matches', 'source_matches',
            'error_message', 'created_at',
        ]
        read_only_fields = fields

    def get_plagiarism_percentage(self, obj):
        if obj.plagiarism_score is None:
            return None
        return round(obj.plagiarism_score * 100, 1)

    def get_original_percentage(self, obj):
        if obj.original_score is None:
            return None
        return round(obj.original_score * 100, 1)
