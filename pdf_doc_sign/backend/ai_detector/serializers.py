from rest_framework import serializers
from .models import AIDetectionScan


class AIDetectionScanSerializer(serializers.ModelSerializer):
    verdict_display = serializers.ReadOnlyField()
    ai_percentage = serializers.SerializerMethodField()
    human_percentage = serializers.SerializerMethodField()

    class Meta:
        model = AIDetectionScan
        fields = [
            'id', 'original_filename', 'file_type', 'file_size_bytes',
            'text_length', 'extracted_text', 'provider',
            'status', 'ai_probability', 'human_probability',
            'ai_percentage', 'human_percentage',
            'verdict', 'verdict_display', 'explanation',
            'sentence_analysis', 'error_message',
            # v2: chunk tracking fields
            'chunks_analysed', 'chunks_total',
            'ai_sentence_count', 'total_sentence_count',
            'created_at',
        ]
        read_only_fields = fields

    def get_ai_percentage(self, obj):
        if obj.ai_probability is None:
            return None
        return round(obj.ai_probability * 100, 1)

    def get_human_percentage(self, obj):
        if obj.human_probability is None:
            return None
        return round(obj.human_probability * 100, 1)
