from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.contrib import messages
from .models import Organisation, Branch, OrganisationMembership, OrganisationRequest, OrganisationInvitation


class BranchInline(admin.TabularInline):
    model = Branch
    extra = 0
    fields = ('name', 'code', 'city', 'is_active')


class MembershipInline(admin.TabularInline):
    model = OrganisationMembership
    extra = 0
    fields = ('user', 'branch', 'role', 'is_active')
    raw_id_fields = ('user',)


class InvitationInline(admin.TabularInline):
    model = OrganisationInvitation
    extra = 0
    fields = ('email', 'role', 'status', 'invited_by', 'expires_at')
    readonly_fields = ('invited_by', 'status')
    raw_id_fields = ('invited_by',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(status='PENDING')


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'domain', 'auto_join_status', 'sales_access_status', 'plan', 'status', 'documents_used_this_month', 'owner', 'created_at')
    list_filter = ('plan', 'status', 'auto_join_enabled', 'sales_access_enabled')
    search_fields = ('name', 'slug', 'domain', 'company_number', 'owner__email')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [BranchInline, MembershipInline, InvitationInline]
    readonly_fields = ('id', 'created_at', 'updated_at', 'sales_access_approved_by', 'sales_access_approved_at')
    actions = ['grant_sales_access', 'revoke_sales_access']

    fieldsets = (
        (None, {'fields': ('name', 'slug', 'domain', 'owner', 'status')}),
        ('Auto-Join Settings', {
            'fields': ('auto_join_enabled', 'auto_join_default_role'),
            'description': 'Allow users with matching email domain to join automatically on registration.'
        }),
        ('Sales & Invoicing Access', {
            'fields': ('sales_access_enabled', 'sales_access_approved_by', 'sales_access_approved_at'),
            'description': 'Enable Sales & Invoicing features for ALL members of this organisation.'
        }),
        ('Company Details', {'fields': ('company_number', 'vat_number', 'address', 'city', 'postcode', 'phone', 'email', 'website')}),
        ('White-Label Branding', {'fields': ('logo', 'logo_url', 'primary_colour', 'secondary_colour', 'custom_domain')}),
        ('Feature Flags', {
            'fields': ('feature_flags',),
            'description': 'Per-org feature toggles (JSON). E.g. {"show_courier": false, "enable_disputes": true}. All features default to enabled if not set.',
            'classes': ('collapse',),
        }),
        ('Subscription', {'fields': ('plan', 'custom_price_gbp', 'documents_per_month_override', 'documents_used_this_month', 'extra_docs_purchased', 'trial_ends_at')}),
        ('Payment', {'fields': ('payment_provider', 'payment_provider_customer_id')}),
    )

    def auto_join_status(self, obj):
        if obj.auto_join_enabled:
            return format_html(
                '<span style="color: green;">✅ ON</span><br><small>@{} → {}</small>',
                obj.domain, obj.auto_join_default_role
            )
        return format_html('<span style="color: gray;">OFF</span>')
    auto_join_status.short_description = 'Auto-Join'

    def sales_access_status(self, obj):
        """Show sales access status with color coding."""
        if obj.sales_access_enabled:
            return format_html('<span style="color: green;">✅ Enabled</span>')
        return format_html('<span style="color: gray;">❌ Disabled</span>')
    sales_access_status.short_description = 'Sales Access'

    def grant_sales_access(self, request, queryset):
        """Bulk grant sales access to selected organisations."""
        if not request.user.is_superuser:
            self.message_user(request, 'Only superusers can grant sales access.', messages.ERROR)
            return
        
        granted = 0
        for org in queryset.filter(sales_access_enabled=False):
            org.grant_sales_access(approved_by=request.user)
            granted += 1
        
        self.message_user(request, f'Sales access granted to {granted} organisation(s).', messages.SUCCESS)
    grant_sales_access.short_description = "✅ Grant Sales Access"

    def revoke_sales_access(self, request, queryset):
        """Bulk revoke sales access from selected organisations."""
        if not request.user.is_superuser:
            self.message_user(request, 'Only superusers can revoke sales access.', messages.ERROR)
            return
        
        revoked = 0
        for org in queryset.filter(sales_access_enabled=True):
            org.revoke_sales_access()
            revoked += 1
        
        self.message_user(request, f'Sales access revoked from {revoked} organisation(s).', messages.WARNING)
    revoke_sales_access.short_description = "❌ Revoke Sales Access"

    def save_model(self, request, obj, form, change):
        """Handle sales access changes."""
        if change:
            old_obj = Organisation.objects.get(pk=obj.pk)
            
            # If sales_access_enabled changed from False to True
            if not old_obj.sales_access_enabled and obj.sales_access_enabled:
                obj.sales_access_approved_by = request.user
                obj.sales_access_approved_at = timezone.now()
            # If sales_access_enabled changed from True to False
            elif old_obj.sales_access_enabled and not obj.sales_access_enabled:
                obj.sales_access_approved_by = None
                obj.sales_access_approved_at = None
        
        super().save_model(request, obj, form, change)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'organisation', 'city', 'is_active')
    list_filter = ('is_active', 'organisation')
    search_fields = ('name', 'organisation__name')


@admin.register(OrganisationMembership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'organisation', 'branch', 'role', 'is_active', 'joined_at')
    list_filter = ('role', 'is_active')
    search_fields = ('user__email', 'organisation__name')
    raw_id_fields = ('user',)


@admin.register(OrganisationInvitation)
class OrganisationInvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'organisation', 'role', 'status_colored', 'invited_by', 'expires_status', 'created_at')
    list_filter = ('status', 'role', 'organisation')
    search_fields = ('email', 'organisation__name', 'invited_by__email')
    raw_id_fields = ('invited_by', 'accepted_by')
    readonly_fields = ('id', 'token', 'accepted_by', 'accepted_at', 'created_at')
    actions = ['revoke_invitations', 'resend_invitations']

    fieldsets = (
        (None, {'fields': ('organisation', 'branch', 'email', 'role')}),
        ('Status', {'fields': ('status', 'expires_at')}),
        ('Tracking', {'fields': ('invited_by', 'accepted_by', 'accepted_at', 'token')}),
    )

    def status_colored(self, obj):
        colors = {
            'PENDING': 'orange',
            'ACCEPTED': 'green',
            'EXPIRED': 'gray',
            'REVOKED': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_colored.short_description = 'Status'

    def expires_status(self, obj):
        if obj.status != 'PENDING':
            return '-'
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        days_left = (obj.expires_at - timezone.now()).days
        if days_left <= 1:
            return format_html('<span style="color: orange;">{}d left</span>', days_left)
        return format_html('<span style="color: green;">{}d left</span>', days_left)
    expires_status.short_description = 'Expires'

    def revoke_invitations(self, request, queryset):
        revoked = queryset.filter(status='PENDING').update(status='REVOKED')
        self.message_user(request, f'{revoked} invitation(s) revoked.', messages.WARNING)
    revoke_invitations.short_description = "❌ Revoke selected invitations"

    def resend_invitations(self, request, queryset):
        resent = 0
        for inv in queryset.filter(status='PENDING'):
            if not inv.is_expired:
                try:
                    inv.send_invitation_email()
                    resent += 1
                except Exception:
                    pass
        self.message_user(request, f'{resent} invitation(s) resent.', messages.SUCCESS)
    resend_invitations.short_description = "📧 Resend selected invitations"


@admin.register(OrganisationRequest)
class OrganisationRequestAdmin(admin.ModelAdmin):
    list_display = (
        'organisation_name', 
        'requested_by', 
        'work_email', 
        'domain_match_status',
        'work_email_verified', 
        'status_colored', 
        'created_at'
    )
    list_filter = ('status', 'work_email_verified')
    search_fields = ('organisation_name', 'work_email', 'requested_by__email')
    readonly_fields = (
        'id', 'requested_by', 'work_email_verified', 'work_email_verified_at',
        'work_email_verification_token', 'work_email_verification_sent_at',
        'reviewed_by', 'reviewed_at', 'organisation', 'created_at', 'updated_at',
        'domain_match_info',
    )
    raw_id_fields = ('requested_by',)
    actions = ['approve_requests', 'reject_requests']

    fieldsets = (
        ('Request Details', {
            'fields': ('organisation_name', 'organisation_domain', 'company_number', 'requested_by')
        }),
        ('Email Verification', {
            'fields': ('work_email', 'domain_match_info', 'work_email_verified', 'work_email_verified_at')
        }),
        ('Status', {
            'fields': ('status', 'rejection_reason')
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_at', 'organisation')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def domain_match_status(self, obj):
        """Show if work email domain matches org domain."""
        if obj.domain_matches:
            return format_html('<span style="color: green;">✅ Match</span>')
        else:
            return format_html(
                '<span style="color: orange;">⚠️ Mismatch</span><br>'
                '<small>{} ≠ {}</small>',
                obj.work_email_domain, obj.organisation_domain
            )
    domain_match_status.short_description = 'Domain Match'

    def domain_match_info(self, obj):
        """Detailed domain match info."""
        if obj.domain_matches:
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ MATCH</span><br>'
                'Work email domain: {}<br>'
                'Organisation domain: {}',
                obj.work_email_domain, obj.organisation_domain
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ MISMATCH - Manual Review Required</span><br>'
                'Work email domain: <strong>{}</strong><br>'
                'Claimed org domain: <strong>{}</strong><br><br>'
                '<em>The user claims to work at {} but their verified email is @{}. '
                'Please verify they are authorized (contractor, partner, etc.) before approving.</em>',
                obj.work_email_domain, obj.organisation_domain,
                obj.organisation_domain, obj.work_email_domain
            )
    domain_match_info.short_description = 'Domain Match Details'

    def status_colored(self, obj):
        """Show status with color coding."""
        colors = {
            'PENDING_WORK_EMAIL': 'gray',
            'PENDING_APPROVAL': 'orange',
            'APPROVED': 'green',
            'REJECTED': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_colored.short_description = 'Status'

    def approve_requests(self, request, queryset):
        """Bulk approve selected requests."""
        approved = 0
        for org_request in queryset.filter(status='PENDING_APPROVAL', work_email_verified=True):
            org_request.approve(reviewed_by=request.user)
            approved += 1
        
        self.message_user(
            request,
            f'{approved} request(s) approved.',
            messages.SUCCESS
        )
    approve_requests.short_description = "✅ Approve selected requests"

    def reject_requests(self, request, queryset):
        """Bulk reject selected requests."""
        rejected = 0
        for org_request in queryset.filter(status__in=['PENDING_WORK_EMAIL', 'PENDING_APPROVAL']):
            org_request.reject(
                reviewed_by=request.user,
                reason='Rejected by admin via bulk action.'
            )
            rejected += 1
        
        self.message_user(
            request,
            f'{rejected} request(s) rejected.',
            messages.WARNING
        )
    reject_requests.short_description = "❌ Reject selected requests"

    def save_model(self, request, obj, form, change):
        """Handle individual approval/rejection from edit form."""
        if change:
            old_status = OrganisationRequest.objects.get(pk=obj.pk).status
            new_status = obj.status
            
            # Manual status change
            if old_status != new_status:
                if new_status == 'APPROVED' and obj.work_email_verified:
                    obj.reviewed_by = request.user
                    obj.reviewed_at = timezone.now()
                    # Don't call approve() as it would save again, just create org
                    obj._create_organisation()
                    messages.success(request, f'Organisation "{obj.organisation_name}" has been approved and created!')
                elif new_status == 'REJECTED':
                    obj.reviewed_by = request.user
                    obj.reviewed_at = timezone.now()
                    obj._send_rejection_email()
                    messages.warning(request, f'Request for "{obj.organisation_name}" has been rejected.')
        
        super().save_model(request, obj, form, change)
