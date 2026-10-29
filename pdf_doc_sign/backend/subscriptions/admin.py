from django.contrib import admin
from .models import Subscription, Payment, ExtraDocsPurchase, Coupon, CouponRedemption


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'start_date', 'end_date', 'amount', 'coupon']
    list_filter = ['plan', 'status']
    search_fields = ['user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'payment_method', 'invoice_number', 'created_at']
    list_filter = ['status', 'payment_method']
    search_fields = ['user__email', 'invoice_number']
    readonly_fields = ['id', 'created_at']


@admin.register(ExtraDocsPurchase)
class ExtraDocsPurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'documents_added', 'amount_gbp', 'created_at']
    readonly_fields = ['id', 'created_at']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'plan_granted', 'duration_days', 'price_gbp', 'lead_email', 'source', 'status', 'current_uses', 'max_uses', 'expires_at']
    list_filter = ['status', 'source', 'plan_granted']
    search_fields = ['code', 'lead_email', 'lead_first_name', 'lead_last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'coupon', 'plan_granted', 'valid_from', 'valid_until', 'amount_paid']
    search_fields = ['user__email', 'coupon__code']
    readonly_fields = ['id', 'redeemed_at']
