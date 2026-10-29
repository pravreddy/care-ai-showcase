"""
URL Configuration - SignSimple UK
PDF Document Signing + Sales & Invoicing
Avyangah Technologies Limited (08235853)
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from authentication import views as auth_views
from authentication import invitation_views
from documents import views as doc_views
from documents.free_sign_views import FreeSignConvertView
from payments import views as payment_views
from organisations import views as org_views
from sales import views as sales_views
from sales.views import ConfirmDeliveryView, RaiseDisputeViaTokenView

from core.health import health

from organisations.views import (
    OrganisationDetailView, OrganisationMemberDetailView,
    ResendMemberSetupEmailView, BranchViewSet, BranchDetailView,
    SalesAccessRequestView, PlatformAdminOrgsView, PlatformAdminOrgActionView,
)

router = DefaultRouter()
router.register(r'documents', doc_views.DocumentViewSet, basename='document')
router.register(r'templates', doc_views.DocumentTemplateViewSet, basename='template')

# Sales & Invoicing
router.register(r'sales/clients', sales_views.ClientViewSet, basename='sales-client')
router.register(r'sales/daily', sales_views.DailySaleViewSet, basename='sales-daily')
router.register(r'sales/disputes', sales_views.DisputeViewSet, basename='sales-dispute')
router.register(r'sales/invoices', sales_views.InvoiceViewSet, basename='sales-invoice')
router.register(r'sales/holidays', sales_views.HolidayViewSet, basename='sales-holiday')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Health check (public) — used by Uptime Kuma; verifies DB reachability
    path('api/health/', health, name='health'),

    # ========================================
    # Auth - Registration & Login
    # ========================================
    path('api/auth/register/', auth_views.RegisterView.as_view(), name='register'),
    path('api/auth/login/', auth_views.LoginView.as_view(), name='login'),
    path('api/auth/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/auth/change-password/', auth_views.ChangePasswordView.as_view(), name='change-password'),
    path('api/auth/forgot-password/', auth_views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('api/auth/force-change-password/', auth_views.ForceChangePasswordView.as_view(), name='force-change-password'),
    path('api/auth/profile/', auth_views.UserProfileView.as_view(), name='user-profile'),
    path('api/auth/dashboard/', auth_views.UserDashboardView.as_view(), name='dashboard'),
    
    # ========================================
    # Auth - Account Activation
    # ========================================
    path('api/auth/activate/<uuid:token>/', auth_views.ActivateAccountView.as_view(), name='activate-account'),
    path('api/auth/resend-activation/', auth_views.ResendActivationView.as_view(), name='resend-activation'),

    # ========================================
    # Magic Link Invitations (Secure User Onboarding)
    # ========================================
    path('api/auth/invite/create/', invitation_views.CreateInvitationView.as_view(), name='create-invitation'),
    path('api/auth/invite/verify/<str:token>/', invitation_views.VerifyInvitationTokenView.as_view(), name='verify-invitation'),
    path('api/auth/invite/setup-password/', invitation_views.SetupPasswordView.as_view(), name='setup-password'),
    path('api/auth/invite/resend/', invitation_views.ResendInvitationView.as_view(), name='resend-invitation'),
    path('api/auth/invite/list/', invitation_views.ListInvitationsView.as_view(), name='list-invitations'),

    # ========================================
    # OAuth
    # IMPORTANT: 'providers' endpoint MUST come before '<str:provider>'
    # ========================================
    path('api/auth/oauth/providers/', auth_views.OAuthProvidersView.as_view(), name='oauth-providers'),
    path('api/auth/oauth/<str:provider>/', auth_views.OAuthRedirectView.as_view(), name='oauth-redirect'),
    path('api/auth/oauth/<str:provider>/callback/', auth_views.OAuthCallbackView.as_view(), name='oauth-callback'),
    
    # ========================================
    # Password Set/Reset (Public)
    # ========================================
    path('api/auth/set-password/<uuid:token>/', org_views.SetPasswordView.as_view(), name='set-password'),
    
    # ========================================
    # Organisation Requests (Self-Service Org Creation)
    # ========================================
    path('api/organisations/request/', org_views.OrganisationRequestCreateView.as_view(), name='org-request-create'),
    path('api/organisations/request/<uuid:request_id>/', org_views.OrganisationRequestStatusView.as_view(), name='org-request-status'),
    path('api/organisations/request/<uuid:request_id>/resend/', org_views.ResendWorkEmailVerificationView.as_view(), name='org-request-resend'),
    path('api/organisations/requests/', org_views.OrganisationRequestStatusView.as_view(), name='org-requests-list'),
    path('api/organisations/verify-work-email/<uuid:token>/', org_views.VerifyWorkEmailView.as_view(), name='org-verify-work-email'),
    path('api/organisations/my/', org_views.MyOrganisationsView.as_view(), name='my-organisations'),
    
    # ========================================
    # Organisation Members & Direct Creation
    # ========================================
    path('api/organisations/<uuid:org_id>/', OrganisationDetailView.as_view(), name='org-detail'),
    path('api/organisations/<uuid:org_id>/members/', org_views.OrganisationMembersView.as_view(), name='org-members-list'),
    path('api/organisations/<uuid:org_id>/members/create/', org_views.CreateMemberDirectlyView.as_view(), name='org-create-member'),
    path('api/organisations/<uuid:org_id>/members/<uuid:membership_id>/', OrganisationMemberDetailView.as_view(), name='org-member-detail'),
    path('api/organisations/<uuid:org_id>/members/<uuid:membership_id>/resend-setup/', ResendMemberSetupEmailView.as_view(), name='org-member-resend-setup'),
    path('api/organisations/<uuid:org_id>/branches/', BranchViewSet.as_view(), name='org-branches'),
    path('api/organisations/<uuid:org_id>/branches/<uuid:branch_id>/', BranchDetailView.as_view(), name='org-branch-detail'),
    path('api/organisations/<uuid:org_id>/request-sales-access/', SalesAccessRequestView.as_view(), name='org-request-sales-access'),
    
    # ========================================
    # Organisation Invitations (Scenario 5)
    # ========================================
    path('api/organisations/<uuid:org_id>/invite/', org_views.InviteMemberView.as_view(), name='org-invite'),
    path('api/organisations/<uuid:org_id>/invitations/', org_views.OrganisationInvitationsView.as_view(), name='org-invitations-list'),
    path('api/invitations/<uuid:token>/', org_views.AcceptInvitationView.as_view(), name='invitation-accept'),
    path('api/invitations/<uuid:invitation_id>/revoke/', org_views.RevokeInvitationView.as_view(), name='invitation-revoke'),
    
    # ========================================
    # Auto-Join (Scenario 6)
    # ========================================
    path('api/organisations/check-auto-join/', org_views.CheckAutoJoinView.as_view(), name='check-auto-join'),
    path('api/organisations/<uuid:org_id>/auto-join/', org_views.AutoJoinOrganisationView.as_view(), name='auto-join'),

    # ========================================
    # Payments
    # ========================================
    path('api/payments/providers/', payment_views.AvailableProvidersView.as_view(), name='payment-providers'),
    path('api/payments/plans/', payment_views.PlansView.as_view(), name='payment-plans'),
    path('api/payments/checkout/', payment_views.CheckoutView.as_view(), name='payment-checkout'),
    path('api/payments/status/<str:payment_id>/', payment_views.PaymentStatusView.as_view(), name='payment-status'),
    path('api/payments/webhook/truelayer/', payment_views.TrueLayerWebhookView.as_view(), name='webhook-truelayer'),
    path('api/payments/webhook/stripe/', payment_views.StripeWebhookView.as_view(), name='webhook-stripe'),

    # ========================================
    # Subscriptions & Coupons
    # ========================================
    path('api/', include('subscriptions.urls')),

    # ========================================
    # Document Signing (Public)
    # ========================================
    path('api/sign/<str:access_token>/', doc_views.SignDocumentView.as_view(), name='sign-document'),
    path('api/sign/<str:access_token>/pdf/', doc_views.SignDocumentPdfView.as_view(), name='sign-document-pdf'),
    # Post-completion download — used as the fallback in the completion email
    # when the signed PDF is too large to attach. Only serves SIGNED docs.
    path('api/sign/<str:access_token>/download/', doc_views.SignDocumentDownloadSignedView.as_view(), name='sign-document-download'),

    # ========================================
    # Free Sign Tool — public file conversion
    # ========================================
    path('api/free-sign/convert/', FreeSignConvertView.as_view(), name='free-sign-convert'),

    # ========================================
    # Public Delivery Confirmation (no login)
    # ========================================
    path('api/confirm-delivery/<str:token>/', ConfirmDeliveryView.as_view(), name='confirm-delivery'),
    path('api/confirm-delivery/<str:token>/dispute/', RaiseDisputeViaTokenView.as_view(), name='confirm-delivery-dispute'),

    # ========================================
    # AI Content Detector
    # ========================================
    path('api/ai-detector/', include('ai_detector.urls')),

    # ========================================
    # Plagiarism Checker
    # ========================================
    path('api/plagiarism/', include('plagiarism.urls')),

    # ========================================
    # AI Chatbot & Lead Capture (public)
    # ========================================
    path('api/chatbot/', include('chatbot.urls')),

    # ========================================
    # Router (documents, templates, sales)
    # ========================================
    path('api/', include(router.urls)),

    # ========================================
    # Platform Admin (superuser only)
    # ========================================
    path('api/platform/organisations/', PlatformAdminOrgsView.as_view(), name='platform-orgs'),
    path('api/platform/organisations/<uuid:org_id>/<str:action>/', PlatformAdminOrgActionView.as_view(), name='platform-org-action'),

    # Allauth
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'SignSimple - Avyangah Technologies'
admin.site.site_title = 'SignSimple Admin'
admin.site.index_title = 'Document Signing & Sales Administration'
