"""
Subscription & Coupon Views
============================
POST  /api/coupons/generate/          — generate unique coupon (admin/chatbot)
POST  /api/coupons/grant-free/        — superuser grants free access to a user
GET   /api/coupons/validate/<code>/   — check if code is valid (public)
POST  /api/coupons/redeem/            — redeem coupon (authenticated user)
GET   /api/coupons/                   — list all coupons (platform admin)
PATCH /api/coupons/<id>/deactivate/   — deactivate coupon (platform admin)
GET   /api/subscriptions/my/          — current user's subscription
GET   /api/subscriptions/plans/       — list available plans with pricing
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from authentication.models import User
from .models import Coupon, CouponRedemption, Subscription
from .serializers import (
    CouponSerializer, CouponGenerateSerializer, CouponValidateSerializer,
    CouponRedeemSerializer, CouponRedemptionSerializer, SubscriptionSerializer,
    SuperuserGrantSerializer,
)

logger = logging.getLogger(__name__)


# =============================================================
# Coupon Generation (admin or chatbot)
# =============================================================

class CouponGenerateView(APIView):
    """
    Generate a unique coupon code.
    Used by: platform admin, sales team, or chatbot service.
    Supports custom document/scan counts if specified.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_platform_admin:
            return Response(
                {'error': 'Only platform admins can generate coupons.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CouponGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        plan = data.get('plan', 'STARTER')
        plan_info = settings.SUBSCRIPTION_PLANS.get(plan, {})

        code = Coupon.generate_code(
            first_name=data.get('first_name', ''),
            plan=plan,
            duration_days=data.get('duration_days', 180),
        )

        coupon = Coupon.objects.create(
            code=code,
            plan_granted=plan,
            duration_days=data.get('duration_days', 180),
            price_gbp=data.get('price_gbp', 1.00),
            # Use custom counts if provided, otherwise plan defaults
            documents_included=data.get('documents_included') or plan_info.get('documents_per_month', 100),
            ai_scans_included=data.get('ai_scans_included') or plan_info.get('ai_scans_per_month', 100),
            lead_first_name=data.get('first_name', ''),
            lead_last_name=data.get('last_name', ''),
            lead_email=data.get('email', ''),
            lead_company=data.get('company', ''),
            source=data.get('source', 'ADMIN'),
            created_by=request.user,
            expires_at=timezone.now() + timedelta(days=7),
        )

        logger.info(
            f'[COUPON] Generated: {code} → {plan} '
            f'({coupon.documents_included} docs + {coupon.ai_scans_included} scans) '
            f'for {coupon.lead_first_name} {coupon.lead_last_name} ({coupon.lead_email})'
        )

        return Response(CouponSerializer(coupon).data, status=status.HTTP_201_CREATED)


# =============================================================
# Superuser Grant Free Access
# =============================================================

class SuperuserGrantFreeView(APIView):
    """
    Superuser-only: grant free docs + AI scans to any user by email.

    Creates a coupon, finds/validates the user, and auto-redeems it.
    The user doesn't need to do anything — their plan is upgraded instantly.

    POST /api/coupons/grant-free/
    {
        "email": "sarah@sparkclean.co.uk",
        "documents": 100,
        "ai_scans": 100,
        "duration_days": 90,
        "plan": "STARTER",
        "description": "Free trial for demo"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Superuser only
        if not request.user.is_superuser:
            return Response(
                {'error': 'Only superusers can grant free access.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SuperuserGrantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        email = data['email'].lower()
        documents = data.get('documents', 100)
        ai_scans = data.get('ai_scans', 100)
        duration_days = data.get('duration_days', 90)
        plan = data.get('plan', 'STARTER')
        description = data.get('description', '')

        # Find the user
        try:
            target_user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': f'No user found with email: {email}'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Generate coupon code
        first_name = target_user.full_name.split()[0] if target_user.full_name else ''
        code = Coupon.generate_code(
            first_name=first_name, plan=plan, duration_days=duration_days,
        )

        # Create the coupon (price = £0, free grant)
        coupon = Coupon.objects.create(
            code=code,
            plan_granted=plan,
            duration_days=duration_days,
            price_gbp=0.00,  # Free grant by superuser
            documents_included=documents,
            ai_scans_included=ai_scans,
            lead_first_name=first_name,
            lead_last_name=target_user.full_name.split()[-1] if target_user.full_name and ' ' in target_user.full_name else '',
            lead_email=email,
            source='ADMIN',
            description=description or f'Free grant by {request.user.email}',
            max_uses=1,
            created_by=request.user,
            expires_at=timezone.now() + timedelta(days=365),  # Long expiry for admin grants
        )

        # Auto-redeem: create subscription immediately
        now = timezone.now()
        end_date = now + timedelta(days=duration_days)

        subscription = Subscription.objects.create(
            user=target_user,
            plan=plan,
            status='ACTIVE',
            start_date=now,
            end_date=end_date,
            amount=0.00,
            currency='GBP',
            auto_renew=False,
            coupon=coupon,
        )

        # Create redemption record
        CouponRedemption.objects.create(
            coupon=coupon,
            user=target_user,
            subscription=subscription,
            plan_granted=plan,
            valid_from=now,
            valid_until=end_date,
            amount_paid=0.00,
        )

        # Update coupon status
        coupon.current_uses = 1
        coupon.status = 'REDEEMED'
        coupon.save(update_fields=['current_uses', 'status', 'updated_at'])

        # Upgrade user's plan
        target_user.subscription_plan = plan
        target_user.coupon_code = code
        target_user.save(update_fields=['subscription_plan', 'coupon_code'])

        logger.info(
            f'[COUPON] Superuser grant: {request.user.email} gave '
            f'{target_user.email} → {plan} ({documents} docs + {ai_scans} scans) '
            f'for {duration_days} days. Code: {code}'
        )

        return Response({
            'message': f'Granted {plan} access to {email} for {duration_days} days.',
            'coupon_code': code,
            'user': email,
            'plan': plan,
            'documents_included': documents,
            'ai_scans_included': ai_scans,
            'valid_until': end_date.strftime('%d %B %Y'),
            'subscription': SubscriptionSerializer(subscription).data,
        }, status=status.HTTP_201_CREATED)


# =============================================================
# Coupon Validation (public — used on signup page)
# =============================================================

class CouponValidateView(APIView):
    """
    Check if a coupon code is valid. Public endpoint (no auth needed).
    Used by the signup page to validate coupon in real-time.
    """
    permission_classes = [AllowAny]

    def get(self, request, code):
        try:
            coupon = Coupon.objects.get(code=code.upper())
        except Coupon.DoesNotExist:
            return Response(
                {'valid': False, 'error': 'Invalid coupon code.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not coupon.is_valid:
            reason = 'This coupon has expired.' if coupon.expires_at and timezone.now() > coupon.expires_at \
                else 'This coupon is no longer available.'
            return Response(
                {'valid': False, 'error': reason},
                status=status.HTTP_410_GONE,
            )

        return Response({
            'valid': True,
            'plan': coupon.plan_granted,
            'duration_days': coupon.duration_days,
            'price_gbp': str(coupon.price_gbp),
            'documents_included': coupon.documents_included,
            'ai_scans_included': coupon.ai_scans_included,
            'days_until_expiry': coupon.days_until_expiry,
        })


# =============================================================
# Coupon Redemption (authenticated user)
# =============================================================

class CouponRedeemView(APIView):
    """
    Redeem a coupon code. Creates a Subscription and upgrades the user's plan.
    Called at signup or from the billing page.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CouponRedeemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code'].upper()

        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response(
                {'error': 'Invalid coupon code.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not coupon.is_valid:
            return Response(
                {'error': 'This coupon has expired or already been used.'},
                status=status.HTTP_410_GONE,
            )

        if CouponRedemption.objects.filter(coupon=coupon, user=request.user).exists():
            return Response(
                {'error': 'You have already redeemed this coupon.'},
                status=status.HTTP_409_CONFLICT,
            )

        if coupon.lead_email and coupon.lead_email.lower() != request.user.email.lower():
            return Response(
                {'error': 'This coupon was generated for a different email address.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        now = timezone.now()
        end_date = now + timedelta(days=coupon.duration_days)

        subscription = Subscription.objects.create(
            user=request.user,
            plan=coupon.plan_granted,
            status='ACTIVE',
            start_date=now,
            end_date=end_date,
            amount=coupon.price_gbp,
            currency='GBP',
            auto_renew=False,
            coupon=coupon,
        )

        redemption = CouponRedemption.objects.create(
            coupon=coupon,
            user=request.user,
            subscription=subscription,
            plan_granted=coupon.plan_granted,
            valid_from=now,
            valid_until=end_date,
            amount_paid=coupon.price_gbp,
        )

        coupon.current_uses += 1
        if coupon.current_uses >= coupon.max_uses:
            coupon.status = 'REDEEMED'
        coupon.save(update_fields=['current_uses', 'status', 'updated_at'])

        request.user.subscription_plan = coupon.plan_granted
        request.user.coupon_code = coupon.code
        request.user.save(update_fields=['subscription_plan', 'coupon_code'])

        logger.info(
            f'[COUPON] Redeemed: {request.user.email} used {code} → '
            f'{coupon.plan_granted} until {end_date.strftime("%d %b %Y")}'
        )

        return Response({
            'message': f'Coupon applied! You now have {coupon.plan_granted} access.',
            'subscription': SubscriptionSerializer(subscription).data,
            'redemption': CouponRedemptionSerializer(redemption).data,
        }, status=status.HTTP_200_OK)


# =============================================================
# Admin views
# =============================================================

class CouponListView(APIView):
    """List all coupons (platform admin only)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_platform_admin:
            return Response({'error': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)

        coupons = Coupon.objects.all()

        coupon_status = request.query_params.get('status')
        if coupon_status:
            coupons = coupons.filter(status=coupon_status.upper())

        source = request.query_params.get('source')
        if source:
            coupons = coupons.filter(source=source.upper())

        return Response({
            'count': coupons.count(),
            'results': CouponSerializer(coupons[:100], many=True).data,
        })


class CouponDeactivateView(APIView):
    """Deactivate a coupon (platform admin only)."""
    permission_classes = [IsAuthenticated]

    def patch(self, request, coupon_id):
        if not request.user.is_platform_admin:
            return Response({'error': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            coupon = Coupon.objects.get(id=coupon_id)
        except Coupon.DoesNotExist:
            return Response({'error': 'Coupon not found.'}, status=status.HTTP_404_NOT_FOUND)

        coupon.status = 'DEACTIVATED'
        coupon.save(update_fields=['status', 'updated_at'])

        logger.info(f'[COUPON] Deactivated: {coupon.code} by {request.user.email}')
        return Response(CouponSerializer(coupon).data)


# =============================================================
# Subscription views
# =============================================================

class MySubscriptionView(APIView):
    """GET current user's active subscription."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subscription = Subscription.objects.filter(
            user=request.user, status='ACTIVE'
        ).order_by('-created_at').first()

        plan_info = settings.SUBSCRIPTION_PLANS.get(request.user.subscription_plan, {})

        return Response({
            'plan': request.user.subscription_plan,
            'plan_details': plan_info,
            'subscription': SubscriptionSerializer(subscription).data if subscription else None,
            'usage': {
                'documents': {
                    'used': request.user.documents_used_this_month,
                    'limit': request.user.documents_limit,
                    'remaining': request.user.documents_remaining,
                },
                'ai_scans': {
                    'used': request.user.ai_scans_used_this_month,
                    'limit': request.user.ai_scans_limit,
                    'remaining': request.user.ai_scans_remaining,
                },
            },
            'coupon_code': request.user.coupon_code or None,
        })


class PlansView(APIView):
    """GET available subscription plans with pricing."""
    permission_classes = [AllowAny]

    def get(self, request):
        plans = []
        for key, plan in settings.SUBSCRIPTION_PLANS.items():
            plans.append({
                'id': key,
                'name': plan['name'],
                'price_gbp': plan['price_gbp'],
                'documents_per_month': plan['documents_per_month'],
                'ai_scans_per_month': plan['ai_scans_per_month'],
                'description': plan['description'],
            })
        return Response({
            'plans': plans,
            'extras': {
                'documents': {
                    'price_gbp': float(settings.EXTRA_DOCS_PRICE_GBP),
                    'bundle_size': settings.EXTRA_DOCS_BUNDLE_SIZE,
                },
                'ai_scans': {
                    'price_gbp': float(settings.EXTRA_AI_SCANS_PRICE_GBP),
                    'bundle_size': settings.EXTRA_AI_SCANS_BUNDLE_SIZE,
                },
            },
        })
