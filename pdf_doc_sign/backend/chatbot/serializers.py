"""
Chatbot Serializers
"""
from rest_framework import serializers
from .models import ChatSession, ChatMessage, Lead


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatStartSerializer(serializers.Serializer):
    """Start a new chat session."""
    page = serializers.URLField(required=False, default='', help_text='Page URL where chat started')
    referrer = serializers.URLField(required=False, default='')


class ChatSendSerializer(serializers.Serializer):
    """Send a message in an existing session."""
    message = serializers.CharField(max_length=2000)


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = [
            'id', 'status', 'message_count',
            'extracted_first_name', 'extracted_last_name',
            'extracted_email', 'extracted_company',
            'offer_plan', 'offer_duration_days',
            'messages', 'created_at',
        ]


class LeadSerializer(serializers.ModelSerializer):
    coupon_code = serializers.CharField(source='coupon.code', read_only=True, default=None)

    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'email', 'company',
            'use_case', 'source', 'conversation_summary',
            'coupon_code', 'status', 'created_at',
        ]
