"""
Sales & Invoicing Tests — DocSign UK
Unit tests for models + integration tests for API endpoints.
testing the commit
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient

from authentication.models import User
from organisations.models import Organisation, Branch, OrganisationMembership
from sales.models import Client, DailySale, SaleLineItem, Dispute, Invoice, Holiday


# ============================================================
# Test Helpers
# ============================================================

class SalesTestBase(TestCase):
    """Base class that sets up org, branch, user, membership, and client."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@catering.in', password='TestPass123!', full_name='Owner',
        )
        self.org = Organisation.objects.create(
            name='Test Catering Co', slug='test-catering', owner=self.owner,
            sales_access_enabled=True,
        )
        self.branch = Branch.objects.create(
            organisation=self.org, name='Bangalore Kitchen', city='Bangalore',
        )
        # Organisation.save() auto-creates OWNER membership, so use get_or_create
        OrganisationMembership.objects.get_or_create(
            user=self.owner, organisation=self.org,
            defaults={'role': 'OWNER'},
        )
        self.client = Client.objects.create(
            organisation=self.org, branch=self.branch,
            name='TechCorp Office', contact_person='Rahul',
            contact_email='rahul@techcorp.in', city='Bangalore',
            default_num_people=11, default_packing_charge=0,
            default_courier_charge=20, pricing_model='PER_HEAD',
            per_head_rate=70,
        )


# ============================================================
# Unit Tests: Client Model
# ============================================================

class TestClientModel(SalesTestBase):

    def test_create_client(self):
        self.assertEqual(str(self.client), 'TechCorp Office (Test Catering Co)')
        self.assertEqual(self.client.default_num_people, 11)
        self.assertTrue(self.client.is_active)

    def test_client_unique_per_org(self):
        """Same name in same org should fail."""
        with self.assertRaises(Exception):
            Client.objects.create(
                organisation=self.org, name='TechCorp Office',
            )

    def test_client_same_name_different_org(self):
        """Same name in different org should work."""
        other_org = Organisation.objects.create(
            name='Other Catering', slug='other-catering', owner=self.owner,
        )
        c = Client.objects.create(organisation=other_org, name='TechCorp Office')
        self.assertIsNotNone(c.id)


# ============================================================
# Unit Tests: DailySale Model
# ============================================================

class TestDailySaleModel(SalesTestBase):

    def test_create_working_day(self):
        sale = DailySale.objects.create(
            client=self.client, date=date(2025, 12, 29),
            num_people=11, items_description='5 Chapathi, 10 Phulka, 9 Rajma Gravy',
            item_price=Decimal('70'), food_price_per_day=Decimal('770'),
            packing_charges=Decimal('10'), courier_charges=Decimal('20'),
        )
        # Total should be auto-calculated
        self.assertEqual(sale.total_charge, Decimal('800'))
        self.assertEqual(sale.day_name, 'Monday')
        self.assertFalse(sale.is_holiday)

    def test_create_holiday(self):
        sale = DailySale.objects.create(
            client=self.client, date=date(2025, 12, 27),
            is_holiday=True, holiday_reason='Weekend',
        )
        # Everything should be zero on holiday
        self.assertEqual(sale.total_charge, 0)
        self.assertEqual(sale.food_price_per_day, 0)
        self.assertEqual(sale.day_name, 'Saturday')

    def test_auto_calculate_food_price_per_head(self):
        """item_price × num_people = food_price_per_day."""
        sale = DailySale.objects.create(
            client=self.client, date=date(2025, 12, 30),
            num_people=11, item_price=Decimal('150'),
            courier_charges=Decimal('20'),
        )
        # food_price = 150 × 11 = 1650
        self.assertEqual(sale.food_price_per_day, Decimal('1650'))
        # total = 1650 + 0 + 20 = 1670
        self.assertEqual(sale.total_charge, Decimal('1670'))

    def test_unique_per_client_per_date(self):
        """Only one entry per client per date."""
        DailySale.objects.create(
            client=self.client, date=date(2025, 12, 29),
            item_price=Decimal('70'), food_price_per_day=Decimal('770'),
        )
        with self.assertRaises(Exception):
            DailySale.objects.create(
                client=self.client, date=date(2025, 12, 29),
                item_price=Decimal('100'),
            )

    def test_fixed_pricing_no_people(self):
        """When num_people=0, food_price_per_day is used directly."""
        sale = DailySale.objects.create(
            client=self.client, date=date(2025, 12, 31),
            num_people=0, items_description='5 Chapathi, 16 Phulka, 8 Papad',
            item_price=Decimal('1627'), food_price_per_day=Decimal('1627'),
            courier_charges=Decimal('20'),
        )
        self.assertEqual(sale.total_charge, Decimal('1647'))

    def test_discount_applied(self):
        sale = DailySale.objects.create(
            client=self.client, date=date(2026, 1, 5),
            food_price_per_day=Decimal('2160'), courier_charges=Decimal('20'),
            discount=Decimal('100'),
        )
        # 2160 + 20 - 100 = 2080
        self.assertEqual(sale.total_charge, Decimal('2080'))


# ============================================================
# Unit Tests: SaleLineItem Model
# ============================================================

class TestSaleLineItemModel(SalesTestBase):

    def test_line_item_auto_total(self):
        sale = DailySale.objects.create(
            client=self.client, date=date(2025, 8, 20),
            food_price_per_day=Decimal('3400'),
        )
        item = SaleLineItem.objects.create(
            daily_sale=sale, item_name='Veg Biryani',
            quantity=8, unit_price=Decimal('230'),
        )
        self.assertEqual(item.total_price, Decimal('1840'))

    def test_line_item_str(self):
        sale = DailySale.objects.create(
            client=self.client, date=date(2025, 8, 20),
            food_price_per_day=Decimal('720'),
        )
        item = SaleLineItem.objects.create(
            daily_sale=sale, item_name='Cheesecorn Sandwich',
            quantity=8, unit_price=Decimal('90'),
        )
        self.assertEqual(str(item), '8x Cheesecorn Sandwich = ₹720')


# ============================================================
# Unit Tests: Dispute Model
# ============================================================

class TestDisputeModel(SalesTestBase):

    def test_create_dispute(self):
        sale = DailySale.objects.create(
            client=self.client, date=date(2025, 12, 29),
            food_price_per_day=Decimal('1500'),
        )
        dispute = Dispute.objects.create(
            daily_sale=sale, raised_by=self.owner,
            dispute_type='MISSING_ITEM',
            description='Missing 2 Phulka',
        )
        self.assertEqual(dispute.status, 'OPEN')
        self.assertIn('MISSING_ITEM', str(dispute))

    def test_resolve_dispute(self):
        sale = DailySale.objects.create(
            client=self.client, date=date(2025, 12, 30),
            food_price_per_day=Decimal('1680'), status='DISPUTED',
        )
        dispute = Dispute.objects.create(
            daily_sale=sale, raised_by=self.owner,
            dispute_type='QUANTITY', description='Only 8 Phulka instead of 10',
        )
        dispute.resolve(user=self.owner, notes='Adjusted in next delivery')

        dispute.refresh_from_db()
        self.assertEqual(dispute.status, 'RESOLVED')
        self.assertIsNotNone(dispute.resolved_at)

        sale.refresh_from_db()
        self.assertEqual(sale.status, 'CONFIRMED')


# ============================================================
# Unit Tests: Invoice Model
# ============================================================

class TestInvoiceModel(SalesTestBase):

    def _create_week_of_sales(self):
        """Create a week of daily sales for testing."""
        sales_data = [
            (date(2025, 12, 29), False, 1500, 10, 20),   # Mon
            (date(2025, 12, 30), False, 1680, 0, 20),     # Tue
            (date(2025, 12, 31), False, 1627, 0, 20),     # Wed
            (date(2026, 1, 1), False, 1075, 0, 20),       # Thu
            (date(2026, 1, 2), False, 1005, 0, 20),       # Fri
            (date(2026, 1, 3), True, 0, 0, 0),            # Sat (holiday)
            (date(2026, 1, 4), True, 0, 0, 0),            # Sun (holiday)
        ]
        for d, is_holiday, food, packing, courier in sales_data:
            DailySale.objects.create(
                client=self.client, date=d, is_holiday=is_holiday,
                holiday_reason='Weekend' if is_holiday else '',
                food_price_per_day=Decimal(str(food)),
                packing_charges=Decimal(str(packing)),
                courier_charges=Decimal(str(courier)),
            )

    def test_invoice_number_auto_generated(self):
        self._create_week_of_sales()
        invoice = Invoice.objects.create(
            client=self.client,
            from_date=date(2025, 12, 29),
            to_date=date(2026, 1, 4),
        )
        self.assertTrue(invoice.invoice_number.startswith('INV-'))

    def test_calculate_totals(self):
        self._create_week_of_sales()
        invoice = Invoice.objects.create(
            client=self.client,
            from_date=date(2025, 12, 29),
            to_date=date(2026, 1, 4),
        )
        invoice.calculate_totals()

        self.assertEqual(invoice.working_days, 5)
        self.assertEqual(invoice.total_food, Decimal('6887'))  # 1500+1680+1627+1075+1005
        self.assertEqual(invoice.total_packing, Decimal('10'))
        self.assertEqual(invoice.total_courier, Decimal('100'))  # 20×5
        # subtotal = 6887 + 10 + 100 = 6997 (sum of total_charges)
        # total_charge per day: 1530, 1700, 1647, 1095, 1025 = 6997
        self.assertEqual(invoice.subtotal, Decimal('6997'))
        self.assertEqual(invoice.grand_total, Decimal('6997'))

    def test_calculate_totals_with_gst(self):
        self._create_week_of_sales()
        invoice = Invoice.objects.create(
            client=self.client,
            from_date=date(2025, 12, 29),
            to_date=date(2026, 1, 4),
            tax_percentage=Decimal('5'),
        )
        invoice.calculate_totals()

        expected_tax = (Decimal('6997') * Decimal('5')) / 100
        self.assertEqual(invoice.tax_amount, expected_tax)
        self.assertEqual(invoice.grand_total, Decimal('6997') + expected_tax)

    def test_invoiced_sales_marked(self):
        """Daily sales should be marked as INVOICED after invoice generation."""
        self._create_week_of_sales()
        invoice = Invoice.objects.create(
            client=self.client,
            from_date=date(2025, 12, 29),
            to_date=date(2026, 1, 4),
        )
        invoice.calculate_totals()

        invoiced_count = DailySale.objects.filter(
            client=self.client, status='INVOICED',
        ).count()
        self.assertEqual(invoiced_count, 5)  # Only working days


# ============================================================
# Unit Tests: Holiday Model
# ============================================================

class TestHolidayModel(SalesTestBase):

    def test_create_holiday(self):
        h = Holiday.objects.create(
            organisation=self.org, date=date(2025, 8, 15),
            name='Independence Day',
        )
        self.assertEqual(str(h), 'Independence Day — 2025-08-15')
        self.assertTrue(h.applies_to_all_clients)


# ============================================================
# Integration Tests: Sales API
# ============================================================

class SalesAPITestBase(APITestCase):
    """Base with authenticated user + org + client."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='api@catering.in', password='TestPass123!', full_name='API User',
        )
        self.org = Organisation.objects.create(
            name='API Catering', slug='api-catering', owner=self.user,
            sales_access_enabled=True,
        )
        self.branch = Branch.objects.create(
            organisation=self.org, name='Main Kitchen',
        )
        # Organisation.save() auto-creates OWNER membership, so use get_or_create
        OrganisationMembership.objects.get_or_create(
            user=self.user, organisation=self.org,
            defaults={'role': 'OWNER'},
        )
        self.client_obj = Client.objects.create(
            organisation=self.org, branch=self.branch,
            name='Test Office', contact_email='office@test.in',
            default_num_people=10,
        )
        self.api = APIClient()
        self.api.force_authenticate(user=self.user)


class TestClientAPI(SalesAPITestBase):

    def test_list_clients(self):
        resp = self.api.get('/api/sales/clients/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        results = data.get('results', data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Test Office')

    def test_create_client(self):
        resp = self.api.post('/api/sales/clients/', {
            'organisation': str(self.org.id),
            'name': 'New Client Ltd',
            'contact_email': 'new@client.in',
        })
        self.assertEqual(resp.status_code, 201)

    def test_filter_by_organisation(self):
        resp = self.api.get(f'/api/sales/clients/?organisation={self.org.id}')
        self.assertEqual(resp.status_code, 200)

    def test_cannot_see_other_org_clients(self):
        other_user = User.objects.create_user(email='other@x.in', password='Test123!')
        other_org = Organisation.objects.create(name='Other', slug='other', owner=other_user)
        Client.objects.create(organisation=other_org, name='Hidden Client')

        resp = self.api.get('/api/sales/clients/')
        results = resp.json().get('results', resp.json())
        names = [c['name'] for c in results]
        self.assertNotIn('Hidden Client', names)


class TestDailySaleAPI(SalesAPITestBase):

    def test_create_daily_sale(self):
        resp = self.api.post('/api/sales/daily/', {
            'client': str(self.client_obj.id),
            'date': '2025-12-29',
            'num_people': 11,
            'items_description': '5 Chapathi, 10 Phulka',
            'item_price': '70',
            'food_price_per_day': '770',
            'courier_charges': '20',
        })
        self.assertEqual(resp.status_code, 201)

    def test_create_holiday_entry(self):
        resp = self.api.post('/api/sales/daily/', {
            'client': str(self.client_obj.id),
            'date': '2025-12-27',
            'is_holiday': True,
            'holiday_reason': 'Weekend',
        })
        self.assertEqual(resp.status_code, 201)
        # Verify in DB that holiday has zero total
        sale = DailySale.objects.get(client=self.client_obj, date='2025-12-27')
        self.assertEqual(sale.total_charge, 0)
        self.assertTrue(sale.is_holiday)

    def test_bulk_create(self):
        resp = self.api.post('/api/sales/daily/bulk_create/', {
            'sales': [
                {'client': str(self.client_obj.id), 'date': '2025-12-29', 'food_price_per_day': '1500', 'courier_charges': '20'},
                {'client': str(self.client_obj.id), 'date': '2025-12-30', 'food_price_per_day': '1680', 'courier_charges': '20'},
                {'client': str(self.client_obj.id), 'date': '2025-12-27', 'is_holiday': True},
            ],
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()['created'], 3)

    def test_summary(self):
        DailySale.objects.create(
            client=self.client_obj, date=date(2025, 12, 29),
            food_price_per_day=Decimal('1500'), courier_charges=Decimal('20'),
        )
        DailySale.objects.create(
            client=self.client_obj, date=date(2025, 12, 30),
            food_price_per_day=Decimal('1680'), courier_charges=Decimal('20'),
        )

        resp = self.api.get('/api/sales/daily/summary/', {
            'client': str(self.client_obj.id),
            'from_date': '2025-12-29',
            'to_date': '2025-12-31',
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['working_days'], 2)
        self.assertEqual(data['total_food'], 3180)  # 1500 + 1680

    def test_filter_by_date_range(self):
        DailySale.objects.create(client=self.client_obj, date=date(2025, 12, 29), food_price_per_day=100)
        DailySale.objects.create(client=self.client_obj, date=date(2026, 1, 5), food_price_per_day=200)

        resp = self.api.get('/api/sales/daily/', {
            'from_date': '2025-12-01', 'to_date': '2025-12-31',
        })
        results = resp.json().get('results', resp.json())
        self.assertEqual(len(results), 1)


class TestDisputeAPI(SalesAPITestBase):

    def test_create_dispute(self):
        sale = DailySale.objects.create(
            client=self.client_obj, date=date(2025, 12, 29),
            food_price_per_day=Decimal('1500'),
        )
        resp = self.api.post('/api/sales/disputes/', {
            'daily_sale': str(sale.id),
            'dispute_type': 'MISSING_ITEM',
            'description': 'Missing 2 Phulka',
        })
        self.assertEqual(resp.status_code, 201)

        sale.refresh_from_db()
        self.assertEqual(sale.status, 'DISPUTED')

    def test_resolve_dispute(self):
        sale = DailySale.objects.create(
            client=self.client_obj, date=date(2025, 12, 30),
            food_price_per_day=Decimal('1680'), status='DISPUTED',
        )
        dispute = Dispute.objects.create(
            daily_sale=sale, raised_by=self.user,
            dispute_type='QUANTITY', description='Short delivery',
        )
        resp = self.api.post(f'/api/sales/disputes/{dispute.id}/resolve/', {
            'resolution_notes': 'Extra delivered next day',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'RESOLVED')


class TestInvoiceAPI(SalesAPITestBase):

    def _seed_sales(self):
        for day_offset in range(5):
            DailySale.objects.create(
                client=self.client_obj,
                date=date(2025, 12, 29) + timedelta(days=day_offset),
                food_price_per_day=Decimal('1000'),
                courier_charges=Decimal('20'),
            )

    def test_generate_invoice(self):
        self._seed_sales()
        resp = self.api.post('/api/sales/invoices/generate/', {
            'client_id': str(self.client_obj.id),
            'from_date': '2025-12-29',
            'to_date': '2026-01-02',
            'tax_percentage': '5',
        })
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertTrue(data['invoice_number'].startswith('INV-'))
        self.assertEqual(data['working_days'], 5)
        self.assertGreater(float(data['grand_total']), 0)

    def test_generate_invoice_no_sales(self):
        resp = self.api.post('/api/sales/invoices/generate/', {
            'client_id': str(self.client_obj.id),
            'from_date': '2099-01-01',
            'to_date': '2099-01-31',
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn('No sales', resp.json()['error'])

    def test_generate_invoice_invalid_dates(self):
        resp = self.api.post('/api/sales/invoices/generate/', {
            'client_id': str(self.client_obj.id),
            'from_date': '2026-01-31',
            'to_date': '2026-01-01',
        })
        self.assertEqual(resp.status_code, 400)

    def test_list_invoices(self):
        self._seed_sales()
        self.api.post('/api/sales/invoices/generate/', {
            'client_id': str(self.client_obj.id),
            'from_date': '2025-12-29', 'to_date': '2026-01-02',
        })
        resp = self.api.get('/api/sales/invoices/')
        self.assertEqual(resp.status_code, 200)
        results = resp.json().get('results', resp.json())
        self.assertEqual(len(results), 1)

    def test_mark_paid(self):
        self._seed_sales()
        gen_resp = self.api.post('/api/sales/invoices/generate/', {
            'client_id': str(self.client_obj.id),
            'from_date': '2025-12-29', 'to_date': '2026-01-02',
        })
        inv_id = gen_resp.json()['id']

        resp = self.api.post(f'/api/sales/invoices/{inv_id}/mark_paid/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'PAID')


# ============================================================
# Tests: bulk_create upsert (second save on same row must work)
# ============================================================

class TestBulkCreateUpsert(SalesAPITestBase):
    """
    Regression tests for the bug where saving the same row a second time
    failed with a unique_together validation error.

    Root cause: DailySaleCreateSerializer auto-generated a UniqueTogetherValidator
    for (client, date) which fired BEFORE the view's upsert logic ran.
    Fix: validators = [] on DailySaleCreateSerializer.
    """

    def test_bulk_create_first_save(self):
        """First save creates the record and returns it."""
        resp = self.api.post('/api/sales/daily/bulk_create/', {
            'sales': [{
                'client': str(self.client_obj.id),
                'date': '2026-01-10',
                'food_price_per_day': '1500',
                'courier_charges': '20',
            }],
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['created'], 1)
        self.assertEqual(len(data['errors']), 0)
        # Response includes the saved sale with an id
        self.assertIn('id', data['sales'][0])

    def test_bulk_create_second_save_same_row_updates_not_fails(self):
        """
        Saving the same client+date twice must update, not raise a 400.
        This is the exact scenario that was broken before the fix.
        """
        payload = {
            'sales': [{
                'client': str(self.client_obj.id),
                'date': '2026-01-11',
                'food_price_per_day': '1000',
                'courier_charges': '20',
            }],
        }
        # First save — creates
        resp1 = self.api.post('/api/sales/daily/bulk_create/', payload, format='json')
        self.assertEqual(resp1.status_code, 201)
        self.assertEqual(resp1.json()['created'], 1)

        # Second save — same date, updated amount — must UPDATE not fail
        payload['sales'][0]['food_price_per_day'] = '1800'
        resp2 = self.api.post('/api/sales/daily/bulk_create/', payload, format='json')
        self.assertEqual(resp2.status_code, 201,
            msg=f'Second save failed: {resp2.json()}')
        self.assertEqual(resp2.json()['created'], 1)
        self.assertEqual(len(resp2.json()['errors']), 0)

        # DB should have only one record with the updated amount
        sales = DailySale.objects.filter(client=self.client_obj, date='2026-01-11')
        self.assertEqual(sales.count(), 1)
        self.assertEqual(sales.first().food_price_per_day, Decimal('1800'))

    def test_bulk_create_third_save_also_works(self):
        """Save same row three times — all must succeed."""
        payload = {
            'sales': [{
                'client': str(self.client_obj.id),
                'date': '2026-01-12',
                'food_price_per_day': '1000',
                'courier_charges': '0',
            }],
        }
        for price in ['1000', '1500', '2000']:
            payload['sales'][0]['food_price_per_day'] = price
            resp = self.api.post('/api/sales/daily/bulk_create/', payload, format='json')
            self.assertEqual(resp.status_code, 201,
                msg=f'Save with price={price} failed: {resp.json()}')

        # Final value in DB should be 2000
        sale = DailySale.objects.get(client=self.client_obj, date='2026-01-12')
        self.assertEqual(sale.food_price_per_day, Decimal('2000'))

    def test_bulk_create_multiple_days_some_existing(self):
        """Mix of new and already-saved rows in one bulk call."""
        # Pre-create day 13
        DailySale.objects.create(
            client=self.client_obj, date=date(2026, 1, 13),
            food_price_per_day=Decimal('900'), courier_charges=Decimal('20'),
        )
        resp = self.api.post('/api/sales/daily/bulk_create/', {
            'sales': [
                # existing row — update
                {'client': str(self.client_obj.id), 'date': '2026-01-13', 'food_price_per_day': '1200', 'courier_charges': '20'},
                # new row — create
                {'client': str(self.client_obj.id), 'date': '2026-01-14', 'food_price_per_day': '1100', 'courier_charges': '20'},
            ],
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()['created'], 2)
        self.assertEqual(len(resp.json()['errors']), 0)

        # Confirm the update took effect
        updated = DailySale.objects.get(client=self.client_obj, date='2026-01-13')
        self.assertEqual(updated.food_price_per_day, Decimal('1200'))

    def test_bulk_create_holiday_toggle_then_resave(self):
        """
        Mark a day as holiday, save, then un-mark and save again.
        Both saves must succeed and DB must reflect the latest state.
        """
        client_id = str(self.client_obj.id)

        # First: mark as holiday
        resp1 = self.api.post('/api/sales/daily/bulk_create/', {
            'sales': [{'client': client_id, 'date': '2026-01-15', 'is_holiday': True, 'holiday_reason': 'Holiday'}],
        }, format='json')
        self.assertEqual(resp1.status_code, 201)
        self.assertTrue(DailySale.objects.get(client=self.client_obj, date='2026-01-15').is_holiday)

        # Second: un-mark holiday, add items
        resp2 = self.api.post('/api/sales/daily/bulk_create/', {
            'sales': [{'client': client_id, 'date': '2026-01-15', 'is_holiday': False, 'food_price_per_day': '1400', 'courier_charges': '20'}],
        }, format='json')
        self.assertEqual(resp2.status_code, 201,
            msg=f'Re-save after holiday toggle failed: {resp2.json()}')

        sale = DailySale.objects.get(client=self.client_obj, date='2026-01-15')
        self.assertFalse(sale.is_holiday)
        self.assertEqual(sale.food_price_per_day, Decimal('1400'))

    def test_bulk_create_returns_id_for_frontend_state(self):
        """
        The response must include the sale id so the frontend can write it
        back into state — preventing the row from being treated as new on
        subsequent edits.
        """
        resp = self.api.post('/api/sales/daily/bulk_create/', {
            'sales': [{
                'client': str(self.client_obj.id),
                'date': '2026-01-16',
                'food_price_per_day': '1300',
                'courier_charges': '20',
            }],
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        sales = resp.json()['sales']
        self.assertEqual(len(sales), 1)
        self.assertIn('id', sales[0])
        # id should be a valid UUID string
        import uuid
        uuid.UUID(str(sales[0]['id']))  # raises if not valid UUID
