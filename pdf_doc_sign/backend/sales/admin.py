"""
Sales Admin — for managing daily sales, clients, invoices.
Designed to be usable by non-technical staff.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Client, DailySale, SaleLineItem, Dispute, Invoice, Holiday


class SaleLineItemInline(admin.TabularInline):
    model = SaleLineItem
    extra = 0
    fields = ('item_name', 'quantity', 'unit_price', 'total_price')
    readonly_fields = ('total_price',)


class DisputeInline(admin.TabularInline):
    model = Dispute
    extra = 0
    fields = ('dispute_type', 'description', 'status', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'legal_name', 'organisation', 'branch', 'city', 'country', 'pricing_model', 'is_active')
    list_filter = ('organisation', 'pricing_model', 'is_active', 'country', 'city')
    search_fields = ('name', 'legal_name', 'contact_person', 'contact_email', 'gst_number', 'pan_number')
    list_editable = ('is_active',)
    fieldsets = (
        ('Basic', {'fields': ('organisation', 'branch', 'name', 'legal_name', 'is_active')}),
        ('Contact', {'fields': ('contact_person', 'contact_email', 'contact_phone', 'address', 'city', 'country')}),
        ('Tax & Registration', {
            'fields': ('gst_number', 'pan_number'),
            'description': 'Tax identifiers shown on invoices. GST/PAN for India, leave blank for other countries.',
        }),
        ('Pricing & Defaults', {'fields': (
            'pricing_model', 'fixed_daily_rate', 'per_head_rate',
            'default_num_people', 'default_packing_charge', 'default_courier_charge',
            'skip_weekends',
        )}),
        ('Portal Access', {
            'fields': ('user',),
            'description': 'Link a user account for client portal access.',
        }),
        ('Notes', {'fields': ('notes',)}),
    )


@admin.register(DailySale)
class DailySaleAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'day_name', 'client_name', 'is_holiday_display',
        'num_people', 'items_short', 'food_price_display',
        'packing_charges', 'courier_charges', 'total_display', 'status',
    )
    list_filter = ('client__organisation', 'client', 'is_holiday', 'status', 'date')
    search_fields = ('items_description', 'client__name')
    date_hierarchy = 'date'
    list_per_page = 31  # Show roughly one month
    inlines = [SaleLineItemInline, DisputeInline]

    fieldsets = (
        ('Basic', {'fields': ('client', 'date', 'is_holiday', 'holiday_reason')}),
        ('Items', {'fields': ('num_people', 'items_description')}),
        ('Pricing', {'fields': ('item_price', 'food_price_per_day', 'packing_charges', 'courier_charges', 'other_charges', 'discount', 'total_charge')}),
        ('Status', {'fields': ('status', 'notes', 'entered_by')}),
    )
    readonly_fields = ('total_charge', 'day_name')

    def client_name(self, obj):
        return obj.client.name
    client_name.short_description = 'Client'

    def items_short(self, obj):
        if obj.is_holiday:
            return format_html('<span style="color:#999">{}</span>', obj.holiday_reason or 'Holiday')
        return obj.items_description[:60] + '...' if len(obj.items_description) > 60 else obj.items_description
    items_short.short_description = 'Items'

    def is_holiday_display(self, obj):
        if obj.is_holiday:
            return format_html('<span style="background:#ffeb3b;padding:2px 8px;border-radius:3px">Yes</span>')
        return 'No'
    is_holiday_display.short_description = 'Holiday'

    def food_price_display(self, obj):
        return f'₹{obj.food_price_per_day:,.0f}'
    food_price_display.short_description = 'Food'

    def total_display(self, obj):
        if obj.total_charge > 0:
            return format_html('<b>₹{:,.0f}</b>', obj.total_charge)
        return '₹0'
    total_display.short_description = 'Total'


@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ('daily_sale', 'dispute_type', 'status', 'raised_by', 'created_at')
    list_filter = ('dispute_type', 'status')
    search_fields = ('description',)
    readonly_fields = ('created_at',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 'client_name', 'from_date', 'to_date',
        'working_days', 'grand_total_display', 'status', 'created_at',
    )
    list_filter = ('status', 'client__organisation')
    search_fields = ('invoice_number', 'client__name')
    readonly_fields = (
        'invoice_number', 'working_days', 'total_food', 'total_packing',
        'total_courier', 'total_other', 'total_discount', 'subtotal',
        'tax_amount', 'grand_total', 'pdf_file',
    )

    def client_name(self, obj):
        return obj.client.name
    client_name.short_description = 'Client'

    def grand_total_display(self, obj):
        return format_html('<b>₹{:,.2f}</b>', obj.grand_total)
    grand_total_display.short_description = 'Grand Total'


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('date', 'name', 'organisation', 'applies_to_all_clients')
    list_filter = ('organisation', 'date')
    date_hierarchy = 'date'
