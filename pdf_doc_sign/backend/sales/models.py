"""
Daily Sales & Invoicing Models - DocSign Platform
Tracks daily food/catering deliveries per client, generates invoices.

Data flow:
  Organisation (Catering Company)
  └── Branch (Kitchen Location)
      └── Client (Office/Company receiving food)
          └── DailySale (one per day)
              ├── items, item_price, num_people
              ├── packing_charges, courier_charges
              ├── total_charge
              └── Disputes[] (client can flag issues)

Invoice = sum of DailySales for a Client in a date range.
"""
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator


class Client(models.Model):
    """
    A client who receives daily deliveries from an Organisation/Branch.
    e.g. "TechCorp Bangalore Office" receiving food from "Acme Catering → Bangalore Kitchen"
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        'organisations.Organisation', on_delete=models.CASCADE, related_name='clients',
    )
    branch = models.ForeignKey(
        'organisations.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='clients',
    )

    # Client details
    name = models.CharField(max_length=255, help_text='Client company/office name')
    legal_name = models.CharField(
        max_length=255, blank=True,
        help_text='Registered legal/trading name (appears on invoices if set)',
    )
    contact_person = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(
        max_length=100, blank=True, default='',
        help_text='Client country (used for tax label and currency defaults)',
    )

    # Tax identifiers (country-dependent)
    gst_number = models.CharField(
        max_length=20, blank=True,
        help_text='GST/GSTIN number (India)',
    )
    pan_number = models.CharField(
        max_length=10, blank=True,
        help_text='PAN number (India)',
    )

    # Delivery defaults (pre-fill for daily entry)
    default_num_people = models.IntegerField(default=0, help_text='Default headcount (0 = not tracked)')
    default_packing_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    default_courier_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Pricing model
    PRICING_CHOICES = (
        ('FIXED', 'Fixed daily rate'),
        ('PER_HEAD', 'Price per person'),
        ('ITEMISED', 'Itemised pricing'),
    )
    pricing_model = models.CharField(max_length=20, choices=PRICING_CHOICES, default='ITEMISED')
    fixed_daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='For FIXED pricing')
    per_head_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='For PER_HEAD pricing')

    # Holiday settings
    skip_weekends = models.BooleanField(default=True, help_text='Auto-mark Sat/Sun as holidays')

    # Confirmation workflow
    show_confirmation = models.BooleanField(
        default=True,
        help_text='Enable delivery confirmation workflow (Send for Confirmation button + Confirmed column). Disable for simple sales-only clients.',
    )

    # User account (optional — for client portal access)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='client_accounts', help_text='User account for client portal access',
    )

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['organisation', 'name']
        unique_together = ['organisation', 'name']

    def __str__(self):
        return f"{self.name} ({self.organisation.name})"

    @property
    def invoice_name(self):
        """Name to show on invoices — legal_name if set, otherwise name."""
        return self.legal_name or self.name

    @property
    def suggested_currency(self):
        """
        Derive a sensible default currency from the client's country.
        Falls back to the organisation's country if client country is blank.
        Rule: client country wins; if blank use org country.
        """
        COUNTRY_CURRENCY = {
            # India
            'india': 'INR', 'in': 'INR',
            # UK
            'united kingdom': 'GBP', 'uk': 'GBP', 'gb': 'GBP', 'great britain': 'GBP',
            # USA
            'united states': 'USD', 'us': 'USD', 'usa': 'USD', 'united states of america': 'USD',
            # Eurozone
            'germany': 'EUR', 'de': 'EUR',
            'france': 'EUR', 'fr': 'EUR',
            'italy': 'EUR', 'it': 'EUR',
            'spain': 'EUR', 'es': 'EUR',
            'netherlands': 'EUR', 'nl': 'EUR',
            'ireland': 'EUR', 'ie': 'EUR',
            'portugal': 'EUR', 'pt': 'EUR',
            'belgium': 'EUR', 'be': 'EUR',
            'austria': 'EUR', 'at': 'EUR',
            'finland': 'EUR', 'fi': 'EUR',
            'greece': 'EUR', 'gr': 'EUR',
            # Canada
            'canada': 'CAD', 'ca': 'CAD',
            # Australia
            'australia': 'AUD', 'au': 'AUD',
        }
        client_country = (self.country or '').strip().lower()
        if client_country:
            currency = COUNTRY_CURRENCY.get(client_country)
            if currency:
                return currency
        # Fall back to org country
        org_country = (self.organisation.country or '').strip().lower()
        return COUNTRY_CURRENCY.get(org_country, 'INR')

    @property
    def tax_label(self):
        """
        Country-aware tax label.
        India → GST, UK/EU → VAT, US → Sales Tax, default → Tax.
        """
        c = (self.country or '').strip().lower()
        if c in ('india', 'in'):
            return 'GST'
        if c in ('united kingdom', 'uk', 'gb') or c in (
            'germany', 'france', 'italy', 'spain', 'netherlands',
            'ireland', 'de', 'fr', 'it', 'es', 'nl', 'ie',
        ):
            return 'VAT'
        if c in ('united states', 'us', 'usa'):
            return 'Sales Tax'
        return 'Tax'


class DailySale(models.Model):
    """
    One record per client per day.
    Matches your spreadsheet: Date | Day | Holiday | Items | Prices | Charges
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='daily_sales')
    date = models.DateField()
    day_name = models.CharField(max_length=10, blank=True)  # Auto-filled: Monday, Tuesday, etc.

    # Holiday
    is_holiday = models.BooleanField(default=False)
    holiday_reason = models.CharField(max_length=255, blank=True, help_text='e.g. Diwali, Company Holiday')

    # Headcount (optional — some clients track per-person, some don't)
    num_people = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    # Items delivered (free text — matches your spreadsheet format)
    items_description = models.TextField(
        blank=True,
        help_text='e.g. "5 Chapathi, 10 Phulka, 9 Aloo Matar Gravy Sabji, 9 half rice, 6 dal fry"',
    )

    # Pricing
    item_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        help_text='Base price for items (before per-person multiplication)',
    )
    food_price_per_day = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        help_text='Total food cost for the day (item_price × num_people, or just item_price)',
    )
    packing_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    courier_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    other_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])

    total_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Status
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('CONFIRMED', 'Confirmed'),
        ('DISPUTED', 'Disputed'),
        ('INVOICED', 'Invoiced'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')

    # Client confirmation
    client_confirmed = models.BooleanField(default=False, help_text='Client confirmed delivery received')
    client_confirmed_at = models.DateTimeField(null=True, blank=True)
    client_confirmation_note = models.TextField(blank=True, help_text='Optional note from client on confirmation')
    confirmation_token = models.CharField(
        max_length=100, unique=True, null=True, blank=True,
        help_text='Token for email-based confirmation (no login needed)',
    )
    confirmation_token_expires_at = models.DateTimeField(null=True, blank=True)

    # Audit
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sales_entered',
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['client', 'date']
        indexes = [
            models.Index(fields=['client', 'date']),
            models.Index(fields=['date', 'status']),
        ]

    def __str__(self):
        return f"{self.client.name} — {self.date} — ₹{self.total_charge}"

    def save(self, *args, **kwargs):
        # Auto-fill day name
        if self.date:
            self.day_name = self.date.strftime('%A')

        # Auto-calculate food price
        if self.num_people > 0 and self.item_price > 0 and self.food_price_per_day == 0:
            self.food_price_per_day = self.item_price * self.num_people

        # Auto-calculate total
        if self.is_holiday:
            self.total_charge = 0
            self.food_price_per_day = 0
            self.item_price = 0
            self.packing_charges = 0
            self.courier_charges = 0
        else:
            self.total_charge = (
                self.food_price_per_day
                + self.packing_charges
                + self.courier_charges
                + self.other_charges
                - self.discount
            )

        super().save(*args, **kwargs)


class SaleLineItem(models.Model):
    """
    Optional: Individual items within a daily sale for detailed tracking.
    Use when you need per-item pricing (e.g. "8 Veg Biryani = 1840").
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    daily_sale = models.ForeignKey(DailySale, on_delete=models.CASCADE, related_name='line_items')
    item_name = models.CharField(max_length=255)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['item_name']

    def __str__(self):
        return f"{self.quantity}x {self.item_name} = ₹{self.total_price}"

    def save(self, *args, **kwargs):
        if self.unit_price and self.quantity:
            self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class Dispute(models.Model):
    """
    Client can raise a dispute on a daily sale.
    e.g. "Missing 2 Phulka" or "Received stale food"
    """
    TYPE_CHOICES = (
        ('MISSING_ITEM', 'Item Missing'),
        ('WRONG_ITEM', 'Wrong Item Delivered'),
        ('QUALITY', 'Quality Issue'),
        ('QUANTITY', 'Quantity Mismatch'),
        ('OVERCHARGE', 'Overcharged'),
        ('OTHER', 'Other'),
    )

    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('RESOLVED', 'Resolved'),
        ('REJECTED', 'Rejected'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    daily_sale = models.ForeignKey(DailySale, on_delete=models.CASCADE, related_name='disputes')
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='disputes_raised')

    dispute_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField(help_text='Describe the issue')
    photo = models.ImageField(upload_to='dispute_photos/', null=True, blank=True, help_text='Photo evidence')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='disputes_resolved',
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Dispute: {self.daily_sale.client.name} — {self.daily_sale.date} — {self.dispute_type}"

    def resolve(self, user, notes=''):
        self.status = 'RESOLVED'
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save()
        # Also update the daily sale status back to CONFIRMED
        self.daily_sale.status = 'CONFIRMED'
        self.daily_sale.save(update_fields=['status'])


class Invoice(models.Model):
    """
    Generated invoice for a client over a date range.
    PDF is generated from DailySale records and stored.
    """
    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('PAID', 'Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)

    # Date range
    from_date = models.DateField()
    to_date = models.DateField()

    # Totals (calculated from daily sales in the range)
    working_days = models.IntegerField(default=0)
    total_food = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_packing = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_courier = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_other = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Tax
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='GST %')
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Invoice content options (selected at generation time)
    include_daily_breakdown = models.BooleanField(default=True, help_text='Show each day\'s items and totals in PDF')
    include_packing_charges = models.BooleanField(default=True, help_text='Show packing charges column')
    include_courier_charges = models.BooleanField(default=True, help_text='Show courier/delivery charges column')
    include_item_detail = models.BooleanField(default=True, help_text='Show item-level detail (5x Chapathi @10) vs just Food total')
    attach_excel = models.BooleanField(default=False, help_text='Attach Excel/CSV daily breakdown with invoice email')

    # Currency (user selects at invoice time)
    CURRENCY_CHOICES = (
        ('GBP', 'GBP'),
        ('INR', 'INR'),
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('CAD', 'CAD'),
        ('AUD', 'AUD'),
    )
    CURRENCY_SYMBOLS = {'GBP': '\u00a3', 'INR': 'Rs.', 'USD': 'USD ', 'EUR': 'EUR ', 'CAD': 'CAD ', 'AUD': 'AUD '}
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    # PDF
    pdf_file = models.FileField(upload_to='invoices/', null=True, blank=True)

    # Audit
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='invoices_generated')
    sent_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'from_date', 'to_date']),
            models.Index(fields=['status']),
        ]

    @property
    def currency_symbol(self):
        return self.CURRENCY_SYMBOLS.get(self.currency, 'Rs.')

    def __str__(self):
        return f"Invoice {self.invoice_number} — {self.client.name} — {self.currency_symbol}{self.grand_total}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            now = timezone.now()
            count = Invoice.objects.filter(
                created_at__year=now.year, created_at__month=now.month,
            ).count() + 1
            self.invoice_number = f"INV-{now.year}-{now.month:02d}-{count:05d}"
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Recalculate totals from linked daily sales."""
        sales = DailySale.objects.filter(
            client=self.client,
            date__gte=self.from_date,
            date__lte=self.to_date,
            is_holiday=False,
        )

        self.working_days = sales.count()
        self.total_food = sum(s.food_price_per_day for s in sales)
        self.total_packing = sum(s.packing_charges for s in sales)
        self.total_courier = sum(s.courier_charges for s in sales)
        self.total_other = sum(s.other_charges for s in sales)
        self.total_discount = sum(s.discount for s in sales)
        self.subtotal = sum(s.total_charge for s in sales)

        if self.tax_percentage > 0:
            self.tax_amount = (self.subtotal * self.tax_percentage) / 100
        else:
            self.tax_amount = 0

        self.grand_total = self.subtotal + self.tax_amount

        # Mark daily sales as invoiced
        sales.update(status='INVOICED')

        self.save()


class Holiday(models.Model):
    """
    Custom holidays per organisation (beyond weekends).
    e.g. Diwali, company annual day, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        'organisations.Organisation', on_delete=models.CASCADE, related_name='holidays',
    )
    date = models.DateField()
    name = models.CharField(max_length=255)
    applies_to_all_clients = models.BooleanField(default=True)
    specific_client = models.ForeignKey(
        Client, on_delete=models.CASCADE, null=True, blank=True,
        help_text='If not all clients, which specific client',
    )

    class Meta:
        ordering = ['date']
        unique_together = ['organisation', 'date', 'specific_client']

    def __str__(self):
        return f"{self.name} — {self.date}"
