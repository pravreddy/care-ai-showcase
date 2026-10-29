from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.utils.html import format_html
from django.contrib import messages
from .models import User, UserProfile
from .invitation_models import InvitationToken


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'subscription_plan', 'sales_access_status', 'auth_provider', 'documents_used_this_month', 'created_at')
    list_filter = ('subscription_plan', 'auth_provider', 'is_active', 'is_staff', 'sales_access_enabled')
    search_fields = ('email', 'full_name', 'company_name')
    ordering = ('-created_at',)
    inlines = [UserProfileInline]
    actions = ['grant_sales_access', 'revoke_sales_access']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('full_name', 'phone', 'company_name', 'profile_picture')}),
        ('Account Status', {'fields': ('email_verified', 'email_verified_at', 'must_change_password')}),
        ('Subscription', {'fields': ('subscription_plan', 'documents_used_this_month', 'extra_docs_purchased', 'usage_reset_date')}),
        ('Sales Access', {
            'fields': ('sales_access_enabled', 'sales_access_approved_by', 'sales_access_approved_at'),
            'description': 'Control access to Sales & Invoicing features. Only superusers can grant this.'
        }),
        ('OAuth', {'fields': ('auth_provider', 'provider_user_id')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'full_name'),
        }),
    )

    readonly_fields = ('sales_access_approved_by', 'sales_access_approved_at', 'email_verified_at')

    def sales_access_status(self, obj):
        """Show sales access status with color coding."""
        if obj.is_superuser:
            return format_html('<span style="color: green;">✅ Superuser</span>')
        if obj.sales_access_enabled:
            return format_html('<span style="color: green;">✅ Enabled</span>')
        return format_html('<span style="color: gray;">❌ Disabled</span>')
    sales_access_status.short_description = 'Sales Access'

    def grant_sales_access(self, request, queryset):
        """Bulk grant sales access to selected users."""
        if not request.user.is_superuser:
            self.message_user(request, 'Only superusers can grant sales access.', messages.ERROR)
            return
        
        granted = 0
        for user in queryset.filter(sales_access_enabled=False):
            user.grant_sales_access(approved_by=request.user)
            granted += 1
        
        self.message_user(request, f'Sales access granted to {granted} user(s).', messages.SUCCESS)
    grant_sales_access.short_description = "✅ Grant Sales Access"

    def revoke_sales_access(self, request, queryset):
        """Bulk revoke sales access from selected users."""
        if not request.user.is_superuser:
            self.message_user(request, 'Only superusers can revoke sales access.', messages.ERROR)
            return
        
        revoked = 0
        for user in queryset.filter(sales_access_enabled=True):
            user.revoke_sales_access()
            revoked += 1
        
        self.message_user(request, f'Sales access revoked from {revoked} user(s).', messages.WARNING)
    revoke_sales_access.short_description = "❌ Revoke Sales Access"

    def save_model(self, request, obj, form, change):
        """Handle sales access changes."""
        if change:
            old_obj = User.objects.get(pk=obj.pk)
            
            # If sales_access_enabled changed from False to True
            if not old_obj.sales_access_enabled and obj.sales_access_enabled:
                obj.sales_access_approved_by = request.user
                obj.sales_access_approved_at = timezone.now()
            # If sales_access_enabled changed from True to False
            elif old_obj.sales_access_enabled and not obj.sales_access_enabled:
                obj.sales_access_approved_by = None
                obj.sales_access_approved_at = None
        
        super().save_model(request, obj, form, change)


@admin.register(InvitationToken)
class InvitationTokenAdmin(admin.ModelAdmin):
    list_display = ('email', 'full_name', 'organisation', 'status_display', 'created_by', 'created_at', 'expires_at')
    list_filter = ('is_used', 'organisation')
    search_fields = ('email', 'full_name')
    readonly_fields = ('token', 'created_at', 'used_at', 'user')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Invitee', {'fields': ('email', 'full_name', 'organisation')}),
        ('Token', {'fields': ('token', 'expires_at', 'is_used', 'used_at')}),
        ('Admin', {'fields': ('created_by', 'user')}),
    )

    def status_display(self, obj):
        if obj.is_used:
            return format_html('<span style="color: green;">✅ Used</span>')
        elif obj.is_expired:
            return format_html('<span style="color: red;">⏰ Expired</span>')
        else:
            return format_html('<span style="color: blue;">🔗 Active</span>')
    status_display.short_description = 'Status'

    def get_magic_link(self, obj):
        return obj.get_magic_link()
    get_magic_link.short_description = 'Magic Link'
