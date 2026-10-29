"""
Chatbot Views — Public API for lead capture conversations.
==========================================================
POST  /api/chatbot/start/                   — start a new chat (public, no auth)
POST  /api/chatbot/<session_id>/message/    — send message, get AI reply (public)
GET   /api/chatbot/<session_id>/            — get session info (public)
GET   /api/chatbot/leads/                   — list all leads (platform admin only)
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from subscriptions.models import Coupon
from .models import ChatSession, ChatMessage, Lead
from .serializers import (
    ChatStartSerializer, ChatSendSerializer,
    ChatMessageSerializer, ChatSessionSerializer, LeadSerializer,
)
from .services import chat_reply, extract_visitor_info

logger = logging.getLogger(__name__)

GREETING = (
    "Hi there! Welcome to SignSimple. "
    "I can help you with document signing, pricing, or anything else. "
    "What brings you here today?"
)


class ChatStartView(APIView):
    """
    Start a new chat session. Public — no auth needed.
    Returns the session ID and a greeting message.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ChatStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get visitor info from request
        ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        session = ChatSession.objects.create(
            visitor_ip=ip,
            visitor_user_agent=user_agent,
            visitor_referrer=serializer.validated_data.get('referrer', ''),
            visitor_page=serializer.validated_data.get('page', ''),
        )

        # Save greeting as first message
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=GREETING,
        )
        session.message_count = 1
        session.save(update_fields=['message_count'])

        return Response({
            'session_id': str(session.id),
            'message': {
                'role': 'assistant',
                'content': GREETING,
            },
        }, status=status.HTTP_201_CREATED)

    def _get_client_ip(self, request):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class ChatMessageView(APIView):
    """
    Send a message in an existing session. Public — no auth needed.
    Returns the AI's reply and any extracted info.
    """
    permission_classes = [AllowAny]

    def post(self, request, session_id):
        # Find session
        try:
            session = ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            return Response(
                {'error': 'Chat session not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if session.status != 'ACTIVE':
            return Response(
                {'error': 'This chat session has ended.'},
                status=status.HTTP_410_GONE,
            )

        serializer = ChatSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_message = serializer.validated_data['message']

        # Save user message
        ChatMessage.objects.create(
            session=session, role='user', content=user_message,
        )

        # Build conversation history for Groq
        history = list(
            ChatMessage.objects.filter(session=session)
            .order_by('created_at')
            .values('role', 'content')
        )

        # Get session context (what we already know)
        session_context = {
            'first_name': session.extracted_first_name,
            'last_name': session.extracted_last_name,
            'email': session.extracted_email,
            'company': session.extracted_company,
        }

        # Get AI reply
        result = chat_reply(history, session_context=session_context)
        ai_reply = result['reply']

        # Save AI reply
        ChatMessage.objects.create(
            session=session, role='assistant', content=ai_reply,
        )

        session.message_count = ChatMessage.objects.filter(session=session).count()
        session.save(update_fields=['message_count', 'updated_at'])

        # Extract visitor info from conversation (every few messages)
        extracted = {}
        coupon_generated = None
        if session.message_count >= 3:
            extracted = extract_visitor_info(history)
            if extracted:
                self._update_session_from_extraction(session, extracted)

                # If we have name + email and no lead yet → create lead + coupon
                if (extracted.get('ready_for_offer') and
                        extracted.get('email') and
                        extracted.get('first_name') and
                        not session.lead):
                    coupon_generated = self._create_lead_and_coupon(session, extracted)

        response_data = {
            'message': {
                'role': 'assistant',
                'content': ai_reply,
            },
            'session_id': str(session.id),
        }

        if coupon_generated:
            response_data['coupon'] = {
                'code': coupon_generated.code,
                'plan': coupon_generated.plan_granted,
                'duration_days': coupon_generated.duration_days,
                'price_gbp': str(coupon_generated.price_gbp),
            }

        return Response(response_data)

    def _update_session_from_extraction(self, session, extracted):
        """Update session with any newly extracted info."""
        changed = []
        if extracted.get('first_name') and not session.extracted_first_name:
            session.extracted_first_name = extracted['first_name']
            changed.append('extracted_first_name')
        if extracted.get('last_name') and not session.extracted_last_name:
            session.extracted_last_name = extracted['last_name']
            changed.append('extracted_last_name')
        if extracted.get('email') and not session.extracted_email:
            session.extracted_email = extracted['email']
            changed.append('extracted_email')
        if extracted.get('company') and not session.extracted_company:
            session.extracted_company = extracted['company']
            changed.append('extracted_company')
        if extracted.get('use_case') and not session.extracted_use_case:
            session.extracted_use_case = extracted['use_case']
            changed.append('extracted_use_case')
        if extracted.get('suggested_plan') and not session.offer_plan:
            session.offer_plan = extracted['suggested_plan']
            changed.append('offer_plan')
        if extracted.get('suggested_duration_days') and not session.offer_duration_days:
            session.offer_duration_days = extracted['suggested_duration_days']
            changed.append('offer_duration_days')

        if changed:
            session.save(update_fields=changed + ['updated_at'])

    def _create_lead_and_coupon(self, session, extracted):
        """Create a Lead record and generate a Coupon."""
        first_name = extracted.get('first_name', '')
        last_name = extracted.get('last_name', '')
        email = extracted.get('email', '')
        company = extracted.get('company', '')
        use_case = extracted.get('use_case', '')
        summary = extracted.get('conversation_summary', '')
        plan = extracted.get('suggested_plan', 'STARTER')
        duration = extracted.get('suggested_duration_days', 180)

        # Check if lead with this email already exists
        existing_lead = Lead.objects.filter(email=email).first()
        if existing_lead:
            session.lead = existing_lead
            session.status = 'COMPLETED'
            session.save(update_fields=['lead', 'status', 'updated_at'])
            return existing_lead.coupon

        # Generate coupon
        plan_info = settings.SUBSCRIPTION_PLANS.get(plan, settings.SUBSCRIPTION_PLANS['STARTER'])
        code = Coupon.generate_code(first_name=first_name, plan=plan, duration_days=duration)

        coupon = Coupon.objects.create(
            code=code,
            plan_granted=plan,
            duration_days=duration,
            price_gbp=1.00,
            documents_included=plan_info.get('documents_per_month', 100),
            ai_scans_included=plan_info.get('ai_scans_per_month', 100),
            lead_first_name=first_name,
            lead_last_name=last_name,
            lead_email=email,
            lead_company=company,
            source='CHATBOT',
            description=summary,
            max_uses=1,
            expires_at=timezone.now() + timedelta(days=7),
        )

        # Create lead
        lead = Lead.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            company=company,
            use_case=use_case,
            source='CHATBOT',
            conversation_summary=summary,
            coupon=coupon,
            status='COUPON_SENT',
        )

        # Update session
        session.lead = lead
        session.status = 'COMPLETED'
        session.save(update_fields=['lead', 'status', 'updated_at'])

        logger.info(
            f'[CHATBOT] Lead captured: {first_name} {last_name} ({email}) '
            f'→ Coupon {code} ({plan} for {duration} days)'
        )

        # TODO: Send email via Postal/Brevo with coupon code
        # from django.core.mail import send_mail
        # send_mail(subject, message, from_email, [email])

        return coupon


class ChatSessionDetailView(APIView):
    """Get session info and messages. Public."""
    permission_classes = [AllowAny]

    def get(self, request, session_id):
        try:
            session = ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            return Response(
                {'error': 'Chat session not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ChatSessionSerializer(session).data)


# =============================================================
# Admin views
# =============================================================

class LeadListView(APIView):
    """List all captured leads (platform admin only)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_platform_admin:
            return Response({'error': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)

        leads = Lead.objects.select_related('coupon').all()

        # Filters
        lead_status = request.query_params.get('status')
        if lead_status:
            leads = leads.filter(status=lead_status.upper())

        source = request.query_params.get('source')
        if source:
            leads = leads.filter(source=source.upper())

        return Response({
            'count': leads.count(),
            'results': LeadSerializer(leads[:100], many=True).data,
        })


class ChatSessionListView(APIView):
    """List all chat sessions (platform admin only)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_platform_admin:
            return Response({'error': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)

        sessions = ChatSession.objects.all()

        session_status = request.query_params.get('status')
        if session_status:
            sessions = sessions.filter(status=session_status.upper())

        return Response({
            'count': sessions.count(),
            'results': ChatSessionSerializer(sessions[:50], many=True).data,
        })
