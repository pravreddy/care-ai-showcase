"""
Sales Serializers - Daily Sales & Invoicing
"""
from rest_framework import serializers
from .models import Client, DailySale, SaleLineItem, Dispute, Invoice, Holiday


class SaleLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleLineItem
        fields = ['id', 'item_name', 'quantity', 'unit_price', 'total_price', 'notes']
        read_only_fields = ['id', 'total_price']


class DisputeSerializer(serializers.ModelSerializer):
    raised_by_email = serializers.CharField(source='raised_by.email', read_only=True, default='')
    resolved_by_email = serializers.CharField(source='resolved_by.email', read_only=True, default='')

    class Meta:
        model = Dispute
        fields = [
            'id', 'daily_sale', 'dispute_type', 'description', 'photo', 'status',
            'resolution_notes', 'raised_by_email', 'resolved_by_email',
            'resolved_at', 'created_at',
        ]
        read_only_fields = ['id', 'status', 'resolved_at', 'created_at']


class DailySaleSerializer(serializers.ModelSerializer):
    line_items = SaleLineItemSerializer(many=True, read_only=True)
    disputes = DisputeSerializer(many=True, read_only=True)
    client_name = serializers.CharField(source='client.name', read_only=True)
    has_dispute = serializers.SerializerMethodField()

    class Meta:
        model = DailySale
        fields = [
            'id', 'client', 'client_name', 'date', 'day_name',
            'is_holiday', 'holiday_reason', 'num_people',
            'items_description', 'item_price', 'food_price_per_day',
            'packing_charges', 'courier_charges', 'other_charges', 'discount',
            'total_charge', 'status', 'notes',
            'client_confirmed', 'client_confirmed_at', 'client_confirmation_note',
            'line_items', 'disputes', 'has_dispute',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'day_name', 'total_charge',
            'client_confirmed', 'client_confirmed_at', 'client_confirmation_note',
            'created_at', 'updated_at',
        ]

    def get_has_dispute(self, obj):
        return obj.disputes.filter(status__in=['OPEN', 'ACKNOWLEDGED']).exists()


class DailySaleCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating/updating daily sales — easy for non-technical users."""

    class Meta:
        model = DailySale
        fields = [
            'client', 'date', 'is_holiday', 'holiday_reason',
            'num_people', 'items_description',
            'item_price', 'food_price_per_day',
            'packing_charges', 'courier_charges', 'other_charges', 'discount',
            'notes',
        ]
        # Disable unique_together validation — bulk_create view handles upsert logic
        validators = []

    def validate(self, attrs):
        # If holiday, clear all prices
        if attrs.get('is_holiday'):
            attrs['item_price'] = 0
            attrs['food_price_per_day'] = 0
            attrs['packing_charges'] = 0
            attrs['courier_charges'] = 0
            attrs['other_charges'] = 0
        return attrs


class BulkDailySaleSerializer(serializers.Serializer):
    """For entering multiple days at once (like filling in a week)."""
    sales = DailySaleCreateSerializer(many=True)


class ClientSerializer(serializers.ModelSerializer):
    total_sales_this_month = serializers.SerializerMethodField()
    organisation_name = serializers.CharField(source='organisation.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True, default='')

    invoice_name = serializers.ReadOnlyField()
    tax_label = serializers.ReadOnlyField()
    suggested_currency = serializers.ReadOnlyField()

    class Meta:
        model = Client
        fields = [
            'id', 'organisation', 'organisation_name', 'branch', 'branch_name',
            'name', 'legal_name', 'contact_person', 'contact_email', 'contact_phone',
            'address', 'city', 'country',
            'gst_number', 'pan_number',
            'default_num_people', 'default_packing_charge',
            'default_courier_charge', 'pricing_model', 'fixed_daily_rate',
            'per_head_rate', 'skip_weekends', 'show_confirmation', 'is_active', 'notes',
            'invoice_name', 'tax_label', 'suggested_currency',
            'total_sales_this_month', 'created_at',
        ]
        read_only_fields = ['id', 'invoice_name', 'tax_label', 'created_at']

    def get_total_sales_this_month(self, obj):
        from django.utils import timezone
        now = timezone.now()
        total = DailySale.objects.filter(
            client=obj, date__year=now.year, date__month=now.month, is_holiday=False,
        ).aggregate(total=serializers.models.Sum('total_charge'))['total']
        return float(total or 0)


class InvoiceSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    generated_by_email = serializers.CharField(source='generated_by.email', read_only=True, default='')
    currency_symbol = serializers.ReadOnlyField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'client', 'client_name', 'invoice_number',
            'from_date', 'to_date', 'working_days',
            'total_food', 'total_packing', 'total_courier',
            'total_other', 'total_discount', 'subtotal',
            'tax_percentage', 'tax_amount', 'grand_total',
            'currency', 'currency_symbol',
            'include_daily_breakdown', 'include_packing_charges',
            'include_courier_charges', 'include_item_detail', 'attach_excel',
            'status', 'pdf_file', 'generated_by_email',
            'sent_at', 'paid_at', 'notes', 'created_at',
        ]
        read_only_fields = [
            'id', 'invoice_number', 'working_days',
            'total_food', 'total_packing', 'total_courier',
            'total_other', 'total_discount', 'subtotal',
            'tax_amount', 'grand_total', 'pdf_file', 'created_at',
        ]


class InvoiceGenerateSerializer(serializers.Serializer):
    """Request to generate an invoice."""
    client_id = serializers.UUIDField()
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    tax_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, default=0)
    currency = serializers.ChoiceField(choices=['GBP', 'INR', 'USD', 'EUR', 'CAD', 'AUD'], default='INR')
    notes = serializers.CharField(required=False, default='', allow_blank=True)

    # Invoice content options
    include_daily_breakdown = serializers.BooleanField(default=True)
    include_packing_charges = serializers.BooleanField(default=True)
    include_courier_charges = serializers.BooleanField(default=True)
    include_item_detail = serializers.BooleanField(default=True)
    attach_excel = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if attrs['from_date'] > attrs['to_date']:
            raise serializers.ValidationError('from_date must be before to_date')
        return attrs


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = ['id', 'organisation', 'date', 'name', 'applies_to_all_clients', 'specific_client']
        read_only_fields = ['id']


class DailySaleClientPortalSerializer(serializers.ModelSerializer):
    """
    Serializer for client portal users — hides all prices.
    Client only sees date, items, status, and confirmation.
    """
    client_name = serializers.CharField(source='client.name', read_only=True)
    has_dispute = serializers.SerializerMethodField()

    class Meta:
        model = DailySale
        fields = [
            'id', 'client', 'client_name', 'date', 'day_name',
            'is_holiday', 'holiday_reason', 'num_people',
            'items_description', 'status', 'notes',
            'client_confirmed', 'client_confirmed_at', 'client_confirmation_note',
            'has_dispute',
            'created_at', 'updated_at',
        ]

    def get_has_dispute(self, obj):
        return obj.disputes.filter(status__in=['OPEN', 'ACKNOWLEDGED']).exists()
