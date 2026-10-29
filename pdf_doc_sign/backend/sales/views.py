"""
Sales Views - Daily Sales Entry, Viewing, Disputes, and Invoice Generation.
Designed for non-technical users — simple, forgiving API.

IMPORTANT: Superusers with sales_access can see ALL organisations' data.
Regular users can only see data for organisations they are members of.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from organisations.models import OrganisationMembership, Organisation
from .models import Client, DailySale, SaleLineItem, Dispute, Invoice, Holiday
from .serializers import (
    ClientSerializer, DailySaleSerializer, DailySaleCreateSerializer,
    BulkDailySaleSerializer, DisputeSerializer, InvoiceSerializer,
    InvoiceGenerateSerializer, HolidaySerializer, SaleLineItemSerializer,
    DailySaleClientPortalSerializer,
)
from .services.invoice_pdf import generate_invoice_pdf

logger = logging.getLogger('sales')


def get_user_accessible_org_ids(user):
    """
    Get list of organisation IDs the user can access for sales.
    All users (including superusers) only see orgs they are members of.
    Superusers can still access all data via Django Admin.
    """
    return OrganisationMembership.objects.filter(
        user=user,
        is_active=True,
        organisation__sales_access_enabled=True,
        organisation__status__in=['ACTIVE', 'TRIAL']
    ).values_list('organisation_id', flat=True)


def get_org_from_request(request):
    """
    Get the active organisation from TenantMiddleware.
    Returns (org, error_response) — if error_response is not None, return it.
    """
    org = getattr(request, 'org', None)
    if not org:
        return None, Response(
            {'error': 'No organisation selected. Pass X-Organisation-ID header or ?org= parameter.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not org.sales_access_enabled:
        return None, Response(
            {'error': 'Sales access is not enabled for this organisation.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return org, None


class IsOrgMemberForSales(permissions.BasePermission):
    """User must be a member of the client's organisation (or superuser with sales access)."""
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Superuser with sales access can access everything
        if user.is_superuser and user.can_access_sales:
            return True
        
        if hasattr(obj, 'organisation'):
            org = obj.organisation
        elif hasattr(obj, 'client'):
            org = obj.client.organisation
        elif hasattr(obj, 'daily_sale'):
            org = obj.daily_sale.client.organisation
        else:
            return False
        return OrganisationMembership.objects.filter(
            user=user, organisation=org, is_active=True,
        ).exists()


# ============================================================
# Clients
# ============================================================

class ClientViewSet(viewsets.ModelViewSet):
    """CRUD for clients. Filtered by user's organisations."""
    serializer_class = ClientSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'contact_person', 'city']

    def get_queryset(self):
        user = self.request.user
        
        # Check if user has sales access
        if not user.can_access_sales:
            return Client.objects.none()
        
        # Use TenantMiddleware org if available (preferred)
        org = getattr(self.request, 'org', None)
        if org and org.sales_access_enabled:
            qs = Client.objects.filter(organisation=org)
        else:
            # Fallback: all accessible orgs
            org_ids = get_user_accessible_org_ids(user)
            qs = Client.objects.filter(organisation_id__in=org_ids)

            # Filter by org/branch from query params
            org_id = self.request.query_params.get('organisation')
            if org_id:
                qs = qs.filter(organisation_id=org_id)

        branch_id = self.request.query_params.get('branch')
        if branch_id:
            qs = qs.filter(branch_id=branch_id)

        return qs.select_related('organisation', 'branch')

    def perform_create(self, serializer):
        # Use TenantMiddleware org if no org specified in payload
        user = self.request.user
        org = serializer.validated_data.get('organisation')
        
        if not org:
            org = getattr(self.request, 'org', None)
            if org:
                serializer.validated_data['organisation'] = org
        
        if org:
            # Validate membership (TenantMiddleware already checked, but defence in depth)
            membership = getattr(self.request, 'org_membership', None)
            if not membership and not user.is_superuser:
                if not OrganisationMembership.objects.filter(
                    user=user, organisation=org, is_active=True
                ).exists():
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("You are not a member of this organisation")
        
        client = serializer.save()
        # Auto-create portal user if client has email
        self._auto_link_portal_user(client)

    def perform_update(self, serializer):
        client = serializer.save()
        # Auto-create portal user if email was added/changed
        self._auto_link_portal_user(client)

    def _auto_link_portal_user(self, client):
        """
        Auto-create or link a User account for client portal access.
        If client has contact_email and no linked user, create one.
        """
        from authentication.models import User
        
        if not client.contact_email or client.user:
            return  # No email, or already linked
        
        email = client.contact_email.strip().lower()
        
        # Check if user already exists with this email
        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            client.user = existing_user
            client.save(update_fields=['user'])
            logger.info(f'[CLIENT] Linked existing user {email} to client {client.name}')
            return
        
        # Create new user with password setup email
        try:
            new_user = User.objects.create_user(
                email=email,
                password=None,  # No password yet
                full_name=client.contact_person or client.name,
                is_active=True,
                email_verified=True,  # Admin-created
            )
            client.user = new_user
            client.save(update_fields=['user'])
            
            # Send password setup email
            try:
                new_user.send_password_setup_email()
                logger.info(f'[CLIENT] Created portal user {email} for client {client.name}, setup email sent')
            except Exception as e:
                logger.warning(f'[CLIENT] Created portal user {email} but email failed: {e}')
        except Exception as e:
            logger.error(f'[CLIENT] Failed to create portal user {email}: {e}')


# ============================================================
# Daily Sales
# ============================================================

class DailySaleViewSet(viewsets.ModelViewSet):
    """
    CRUD for daily sales entries.
    Supports filtering by client, date range, and status.
    """
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = [filters.SearchFilter]
    search_fields = ['items_description', 'notes']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return DailySaleCreateSerializer
        # Client portal users get price-free serializer
        if self.request.user.is_client_user and not self.request.user.can_access_sales:
            return DailySaleClientPortalSerializer
        return DailySaleSerializer

    def get_queryset(self):
        user = self.request.user
        
        if not user.can_access_sales:
            return DailySale.objects.none()
        
        # Use TenantMiddleware org if available (preferred)
        org = getattr(self.request, 'org', None)
        if org and org.sales_access_enabled:
            qs = DailySale.objects.filter(
                client__organisation=org,
            ).select_related('client', 'entered_by')
        else:
            # Fallback: all accessible orgs
            org_ids = get_user_accessible_org_ids(user)
            qs = DailySale.objects.filter(
                client__organisation_id__in=org_ids,
            ).select_related('client', 'entered_by')

            org_id = self.request.query_params.get('organisation')
            if org_id:
                qs = qs.filter(client__organisation_id=org_id)

        # Filters
        client_id = self.request.query_params.get('client')
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        sale_status = self.request.query_params.get('status')

        if client_id:
            qs = qs.filter(client_id=client_id)
        if from_date:
            qs = qs.filter(date__gte=from_date)
        if to_date:
            qs = qs.filter(date__lte=to_date)
        if sale_status:
            qs = qs.filter(status=sale_status)

        return qs

    def perform_create(self, serializer):
        sale = serializer.save(entered_by=self.request.user)

        # Auto-set food_price_per_day if not provided
        if sale.num_people > 0 and sale.item_price > 0 and sale.food_price_per_day == 0:
            sale.food_price_per_day = sale.item_price * sale.num_people
            sale.save()

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Create multiple daily sales at once (e.g. entering a whole week).
        POST /api/sales/daily/bulk_create/
        Body: { "sales": [ { client, date, items, prices... }, ... ] }
        """
        serializer = BulkDailySaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created = []
        errors = []

        for i, sale_data in enumerate(serializer.validated_data['sales']):
            try:
                # Check if already exists for this client+date
                existing = DailySale.objects.filter(
                    client=sale_data['client'], date=sale_data['date'],
                ).first()

                if existing:
                    # Update existing
                    for key, val in sale_data.items():
                        setattr(existing, key, val)
                    existing.entered_by = request.user
                    existing.save()
                    created.append(DailySaleSerializer(existing).data)
                else:
                    sale = DailySale.objects.create(entered_by=request.user, **sale_data)
                    created.append(DailySaleSerializer(sale).data)

            except Exception as e:
                errors.append({'index': i, 'error': str(e)})

        return Response({
            'created': len(created),
            'errors': errors,
            'sales': created,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get summary totals for a client and date range.
        GET /api/sales/daily/summary/?client=xxx&from_date=2025-12-01&to_date=2025-12-31
        """
        client_id = request.query_params.get('client')
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')

        if not all([client_id, from_date, to_date]):
            return Response({'error': 'client, from_date, and to_date are required'}, status=400)

        sales = DailySale.objects.filter(
            client_id=client_id, date__gte=from_date, date__lte=to_date,
        )

        working_sales = sales.filter(is_holiday=False)

        return Response({
            'client_id': client_id,
            'from_date': from_date,
            'to_date': to_date,
            'total_days': sales.count(),
            'working_days': working_sales.count(),
            'holidays': sales.filter(is_holiday=True).count(),
            'total_food': sum(s.food_price_per_day for s in working_sales),
            'total_packing': sum(s.packing_charges for s in working_sales),
            'total_courier': sum(s.courier_charges for s in working_sales),
            'grand_total': sum(s.total_charge for s in working_sales),
            'open_disputes': Dispute.objects.filter(
                daily_sale__client_id=client_id,
                daily_sale__date__gte=from_date,
                daily_sale__date__lte=to_date,
                status__in=['OPEN', 'ACKNOWLEDGED'],
            ).count(),
        })

    @action(detail=True, methods=['post'])
    def send_confirmation(self, request, pk=None):
        """
        Send a confirmation email to the client for a specific daily sale.
        POST /api/sales/daily/{id}/send_confirmation/
        Body (all optional):
          show_prices: bool   — include price info (default True)
          show_breakdown: bool — show food/packing/courier breakdown vs just total (default False)
        """
        import secrets
        from datetime import timedelta
        from django.core.mail import send_mail

        sale = self.get_object()

        if sale.is_holiday:
            return Response({'error': 'Cannot send confirmation for a holiday.'}, status=400)

        if not sale.client.contact_email:
            return Response({'error': 'Client has no email address.'}, status=400)

        # Price visibility options (admin chooses what to share)
        show_prices = request.data.get('show_prices', True)
        show_breakdown = request.data.get('show_breakdown', False)

        # Generate token
        sale.confirmation_token = secrets.token_urlsafe(48)
        sale.confirmation_token_expires_at = timezone.now() + timedelta(days=7)
        sale.save(update_fields=['confirmation_token', 'confirmation_token_expires_at'])

        # Build confirm URL
        # Encode price visibility in URL so the page knows what to show
        price_params = f'?sp={(1 if show_prices else 0)}&sb={(1 if show_breakdown else 0)}'
        confirm_url = f'https://signsimple.co.uk/confirm-delivery/{sale.confirmation_token}{price_params}'
        dispute_url = f'{confirm_url}#dispute'
        org_name = sale.client.organisation.name
        items = sale.items_description[:200] if sale.items_description else 'Daily delivery'

        # Build price block for email
        if show_prices and show_breakdown:
            price_html = (
                f'<table style="width:100%;border-collapse:collapse;margin:8px 0;">'
                f'<tr><td style="color:#666;padding:3px 0;">Food</td><td style="text-align:right;">Rs.{sale.food_price_per_day:,.0f}</td></tr>'
                + (f'<tr><td style="color:#666;padding:3px 0;">Packing</td><td style="text-align:right;">Rs.{sale.packing_charges:,.0f}</td></tr>' if sale.packing_charges else '')
                + (f'<tr><td style="color:#666;padding:3px 0;">Courier</td><td style="text-align:right;">Rs.{sale.courier_charges:,.0f}</td></tr>' if sale.courier_charges else '')
                + f'<tr><td style="font-weight:bold;padding:6px 0 0;">Total</td><td style="text-align:right;font-weight:bold;">Rs.{sale.total_charge:,.0f}</td></tr>'
                f'</table>'
            )
            price_text = f'Food: Rs.{sale.food_price_per_day:,.0f}\nPacking: Rs.{sale.packing_charges:,.0f}\nCourier: Rs.{sale.courier_charges:,.0f}\nTotal: Rs.{sale.total_charge:,.0f}'
        elif show_prices:
            price_html = f'<p style="margin:8px 0;"><strong>Total: Rs.{sale.total_charge:,.0f}</strong></p>'
            price_text = f'Total: Rs.{sale.total_charge:,.0f}'
        else:
            price_html = ''
            price_text = ''

        subject = f'Please confirm delivery — {sale.date.strftime("%d %b %Y")} — {org_name}'
        text_body = (
            f'Hi {sale.client.contact_person or sale.client.name},\n\n'
            f'{org_name} has recorded a delivery to you on {sale.date.strftime("%d %b %Y")}:\n\n'
            f'Items: {items}\n'
            + (f'{price_text}\n' if price_text else '')
            + f'\nPlease confirm you received this delivery:\n{confirm_url}\n\n'
            f'If there is an issue with this delivery, you can report it here:\n{dispute_url}\n\n'
            f'Best regards,\n{org_name}\nPowered by SignSimple'
        )

        html_body = f"""
<div style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="background: #1565c0; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
    <h2 style="margin: 0;">Delivery Confirmation</h2>
    <p style="margin: 4px 0 0; opacity: 0.85; font-size: 14px;">{org_name}</p>
  </div>
  <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px;">
    <p>Hi {sale.client.contact_person or sale.client.name},</p>
    <p><strong>{org_name}</strong> has recorded a delivery to you on <strong>{sale.date.strftime('%d %b %Y')} ({sale.day_name})</strong>.</p>
    <div style="background: white; padding: 16px; border-radius: 8px; border: 1px solid #e0e0e0; margin: 16px 0;">
      <p style="margin: 0 0 8px; color: #666; font-size: 13px;">Items delivered:</p>
      <p style="margin: 0; font-weight: 500;">{items}</p>
      {price_html}
    </div>
    <p style="font-size: 14px; color: #555;">Did you receive this delivery? Please click one of the buttons below:</p>
    <table style="width:100%;margin:20px 0;">
      <tr>
        <td style="width:50%;padding-right:8px;">
          <a href="{confirm_url}" style="display:block;background:#4caf50;color:white;padding:14px 0;text-decoration:none;border-radius:6px;font-weight:bold;font-size:15px;text-align:center;">✓ Confirm Received</a>
        </td>
        <td style="width:50%;padding-left:8px;">
          <a href="{confirm_url}#dispute" style="display:block;background:#ff9800;color:white;padding:14px 0;text-decoration:none;border-radius:6px;font-weight:bold;font-size:15px;text-align:center;">⚠ Report Issue</a>
        </td>
      </tr>
    </table>
    <p style="color: #888; font-size: 13px;">If the buttons don't work, copy this link: <a href="{confirm_url}">{confirm_url}</a></p>
  </div>
  <p style="text-align: center; color: #999; font-size: 12px; margin-top: 16px;">Powered by SignSimple — signsimple.co.uk</p>
</div>
"""

        try:
            send_mail(
                subject=subject,
                message=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[sale.client.contact_email],
                html_message=html_body,
                fail_silently=False,
            )
            return Response({'message': f'Confirmation email sent to {sale.client.contact_email}'})
        except Exception as e:
            logger.error(f'[CONFIRM] Email failed for sale {sale.id}: {e}')
            return Response({'error': 'Failed to send confirmation email.'}, status=500)

    @action(detail=False, methods=['post'])
    def send_bulk_confirmation(self, request):
        """
        Send confirmation emails for all unconfirmed sales for a client in a date range.
        POST /api/sales/daily/send_bulk_confirmation/
        Body: { client_id, from_date, to_date }
        """
        import secrets
        from datetime import timedelta
        from django.core.mail import send_mail

        client_id = request.data.get('client_id')
        from_date = request.data.get('from_date')
        to_date = request.data.get('to_date')

        if not all([client_id, from_date, to_date]):
            return Response({'error': 'client_id, from_date, to_date required.'}, status=400)

        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found.'}, status=404)

        if not client.contact_email:
            return Response({'error': 'Client has no email address.'}, status=400)

        # Get unconfirmed, non-holiday sales
        sales = DailySale.objects.filter(
            client=client, date__gte=from_date, date__lte=to_date,
            is_holiday=False, client_confirmed=False,
        ).order_by('date')

        if not sales.exists():
            return Response({'error': 'No unconfirmed deliveries in this range.'}, status=400)

        # Generate tokens for each
        for sale in sales:
            if not sale.confirmation_token:
                sale.confirmation_token = secrets.token_urlsafe(48)
                sale.confirmation_token_expires_at = timezone.now() + timedelta(days=7)
                sale.save(update_fields=['confirmation_token', 'confirmation_token_expires_at'])

        # Build summary email with all dates
        org_name = client.organisation.name
        rows_html = ''
        for s in sales:
            items = s.items_description[:60] if s.items_description else 'Delivery'
            url = f'https://signsimple.co.uk/confirm-delivery/{s.confirmation_token}'
            rows_html += (
                f'<tr>'
                f'<td style="padding:8px;border-bottom:1px solid #eee;">{s.date.strftime("%d %b %Y")} ({s.day_name[:3]})</td>'
                f'<td style="padding:8px;border-bottom:1px solid #eee;">{items}</td>'
                f'<td style="padding:8px;border-bottom:1px solid #eee;">Rs.{s.total_charge:,.0f}</td>'
                f'<td style="padding:8px;border-bottom:1px solid #eee;"><a href="{url}" style="color:#4caf50;font-weight:bold;">Confirm</a></td>'
                f'</tr>'
            )

        subject = f'Please confirm {sales.count()} deliveries — {org_name}'
        html_body = f"""
<div style="font-family: -apple-system, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px;">
  <div style="background: #1565c0; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
    <h2 style="margin: 0;">Delivery Confirmation</h2>
  </div>
  <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px;">
    <p>Hi {client.contact_person or client.name},</p>
    <p><strong>{org_name}</strong> has {sales.count()} deliveries pending your confirmation:</p>
    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
      <tr style="background:#1565c0;color:white;">
        <th style="padding:10px;text-align:left;">Date</th>
        <th style="padding:10px;text-align:left;">Items</th>
        <th style="padding:10px;text-align:left;">Total</th>
        <th style="padding:10px;text-align:left;">Action</th>
      </tr>
      {rows_html}
    </table>
    <p style="color: #666; font-size: 14px;">Click "Confirm" next to each delivery to acknowledge receipt.</p>
  </div>
  <p style="text-align: center; color: #999; font-size: 12px; margin-top: 16px;">Powered by SignSimple — signsimple.co.uk</p>
</div>
"""

        try:
            send_mail(
                subject=subject,
                message=f'{org_name} has {sales.count()} deliveries pending confirmation.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[client.contact_email],
                html_message=html_body,
                fail_silently=False,
            )
            return Response({
                'message': f'Confirmation email sent for {sales.count()} deliveries to {client.contact_email}',
                'count': sales.count(),
            })
        except Exception as e:
            logger.error(f'[CONFIRM] Bulk email failed for client {client.name}: {e}')
            return Response({'error': 'Failed to send confirmation email.'}, status=500)

    @action(detail=True, methods=['post'])
    def confirm_in_app(self, request, pk=None):
        """
        Authenticated client confirms delivery in-app (no email, no token needed).
        POST /api/sales/daily/{id}/confirm_in_app/
        Body: { note? }
        """
        sale = self.get_object()

        if sale.is_holiday:
            return Response({'error': 'Cannot confirm a holiday.'}, status=400)

        if sale.client_confirmed:
            return Response({'message': 'Already confirmed.', 'confirmed_at': sale.client_confirmed_at})

        sale.client_confirmed = True
        sale.client_confirmed_at = timezone.now()
        sale.client_confirmation_note = request.data.get('note', '')
        sale.save(update_fields=['client_confirmed', 'client_confirmed_at', 'client_confirmation_note'])

        return Response({
            'message': 'Delivery confirmed.',
            'confirmed_at': sale.client_confirmed_at,
        })

    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        """
        Export daily sales as Excel for a client and date range.
        GET /api/sales/daily/export_excel/?client=xxx&from_date=2025-12-01&to_date=2025-12-31
        """
        client_id = request.query_params.get('client')
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')

        if not all([client_id, from_date, to_date]):
            return Response({'error': 'client, from_date, and to_date are required'}, status=400)

        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=404)

        sales = DailySale.objects.filter(
            client=client, date__gte=from_date, date__lte=to_date,
        ).order_by('date')

        if not sales.exists():
            return Response({'error': 'No sales found in this date range'}, status=400)

        import io
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from sales.services.invoice_pdf import _format_items

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Daily Sales'

        header_font = Font(bold=True, color='FFFFFF', size=10)
        header_fill = PatternFill(start_color='1565C0', end_color='1565C0', fill_type='solid')
        bold_font = Font(bold=True, size=10)
        money_fmt = '#,##0.00'
        thin_border = Border(bottom=Side(style='thin', color='CCCCCC'))

        ws.merge_cells('A1:G1')
        ws['A1'] = f"{client.organisation.name} \u2014 {client.name}"
        ws['A1'].font = Font(bold=True, size=14, color='1565C0')
        ws.merge_cells('A2:G2')
        ws['A2'] = f"Period: {from_date} to {to_date}"

        headers = ['Date', 'Day', 'Holiday', 'Items', 'Food', 'Packing', 'Courier', 'Total']
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')

        row = 5
        totals = {'food': 0, 'packing': 0, 'courier': 0, 'total': 0}
        for sale in sales:
            ws.cell(row=row, column=1, value=sale.date.strftime('%d/%m/%Y'))
            ws.cell(row=row, column=2, value=sale.day_name[:3])
            ws.cell(row=row, column=3, value='Yes' if sale.is_holiday else '')
            if sale.is_holiday:
                ws.cell(row=row, column=4, value=sale.holiday_reason or 'Holiday')
            else:
                ws.cell(row=row, column=4, value=_format_items(sale.items_description, show_detail=True))
            ws.cell(row=row, column=5, value=float(sale.food_price_per_day)).number_format = money_fmt
            ws.cell(row=row, column=6, value=float(sale.packing_charges)).number_format = money_fmt
            ws.cell(row=row, column=7, value=float(sale.courier_charges)).number_format = money_fmt
            ws.cell(row=row, column=8, value=float(sale.total_charge)).number_format = money_fmt
            if not sale.is_holiday:
                totals['food'] += float(sale.food_price_per_day)
                totals['packing'] += float(sale.packing_charges)
                totals['courier'] += float(sale.courier_charges)
                totals['total'] += float(sale.total_charge)
            for c in range(1, 9):
                ws.cell(row=row, column=c).border = thin_border
            row += 1

        row += 1
        ws.cell(row=row, column=4, value='TOTALS').font = bold_font
        ws.cell(row=row, column=5, value=totals['food']).number_format = money_fmt
        ws.cell(row=row, column=5).font = bold_font
        ws.cell(row=row, column=6, value=totals['packing']).number_format = money_fmt
        ws.cell(row=row, column=6).font = bold_font
        ws.cell(row=row, column=7, value=totals['courier']).number_format = money_fmt
        ws.cell(row=row, column=7).font = bold_font
        ws.cell(row=row, column=8, value=totals['total']).number_format = money_fmt
        ws.cell(row=row, column=8).font = bold_font

        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 6
        ws.column_dimensions['C'].width = 8
        ws.column_dimensions['D'].width = 45
        ws.column_dimensions['E'].width = 14
        ws.column_dimensions['F'].width = 12
        ws.column_dimensions['G'].width = 12
        ws.column_dimensions['H'].width = 14

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="sales_{from_date}_to_{to_date}.xlsx"'
        return response

    @action(detail=True, methods=['post'])
    def add_line_items(self, request, pk=None):
        """Add detailed line items to a daily sale."""
        sale = self.get_object()
        serializer = SaleLineItemSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        items = []
        for item_data in serializer.validated_data:
            item = SaleLineItem.objects.create(daily_sale=sale, **item_data)
            items.append(item)

        return Response(SaleLineItemSerializer(items, many=True).data, status=201)


# ============================================================
# Disputes
# ============================================================

class DisputeViewSet(viewsets.ModelViewSet):
    """Client can raise and view disputes."""
    serializer_class = DisputeSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        
        if not user.can_access_sales:
            return Dispute.objects.none()
        
        # Use TenantMiddleware org if available
        org = getattr(self.request, 'org', None)
        if org and org.sales_access_enabled:
            qs = Dispute.objects.filter(
                daily_sale__client__organisation=org,
            ).select_related('daily_sale__client', 'raised_by', 'resolved_by')
        else:
            org_ids = get_user_accessible_org_ids(user)
            qs = Dispute.objects.filter(
                daily_sale__client__organisation_id__in=org_ids,
            ).select_related('daily_sale__client', 'raised_by', 'resolved_by')

        sale_id = self.request.query_params.get('daily_sale')
        dispute_status = self.request.query_params.get('status')

        if sale_id:
            qs = qs.filter(daily_sale_id=sale_id)
        if dispute_status:
            qs = qs.filter(status=dispute_status)

        return qs

    def perform_create(self, serializer):
        dispute = serializer.save(raised_by=self.request.user)
        # Mark the daily sale as disputed
        dispute.daily_sale.status = 'DISPUTED'
        dispute.daily_sale.save(update_fields=['status'])

        # Only send email if explicitly requested (saves Brevo quota)
        send_email = self.request.data.get('send_email', False)
        if send_email:
            try:
                from django.core.mail import send_mail
                org = dispute.daily_sale.client.organisation
                send_mail(
                    subject=f'Concern raised — {dispute.daily_sale.date.strftime("%d %b %Y")} — {dispute.daily_sale.client.name}',
                    message=(
                        f'A concern has been raised for delivery on {dispute.daily_sale.date.strftime("%d %b %Y")}:\n\n'
                        f'Type: {dispute.get_dispute_type_display()}\n'
                        f'Description: {dispute.description}\n\n'
                        f'Raised by: {self.request.user.email}\n\n'
                        f'Please review in the SignSimple dashboard.'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[org.email] if org.email else [],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f'[DISPUTE] Email failed: {e}')

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Admin resolves a dispute."""
        dispute = self.get_object()
        notes = request.data.get('resolution_notes', '')
        dispute.resolve(user=request.user, notes=notes)

        # Only send email if explicitly requested
        send_email = request.data.get('send_email', False)
        if send_email and dispute.raised_by and dispute.raised_by.email:
            try:
                from django.core.mail import send_mail
                send_mail(
                    subject=f'Concern resolved — {dispute.daily_sale.date.strftime("%d %b %Y")}',
                    message=(
                        f'Your concern about the delivery on {dispute.daily_sale.date.strftime("%d %b %Y")} '
                        f'has been resolved.\n\nResolution: {notes or "Resolved"}\n\n'
                        f'Thank you for your feedback.\n\nSignSimple'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[dispute.raised_by.email],
                    fail_silently=True,
                )
            except Exception as e:
                logger.error(f'[DISPUTE] Resolve email failed: {e}')

        return Response(DisputeSerializer(dispute).data)

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Admin acknowledges a dispute (working on it)."""
        dispute = self.get_object()
        dispute.status = 'ACKNOWLEDGED'
        dispute.save(update_fields=['status'])
        return Response(DisputeSerializer(dispute).data)


# ============================================================
# Invoices
# ============================================================

class InvoiceViewSet(viewsets.ModelViewSet):
    """View and manage invoices."""
    serializer_class = InvoiceSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        
        if not user.can_access_sales:
            return Invoice.objects.none()
        
        # Use TenantMiddleware org if available
        org = getattr(self.request, 'org', None)
        if org and org.sales_access_enabled:
            qs = Invoice.objects.filter(
                client__organisation=org,
            ).select_related('client', 'generated_by')
        else:
            org_ids = get_user_accessible_org_ids(user)
            qs = Invoice.objects.filter(
                client__organisation_id__in=org_ids,
            ).select_related('client', 'generated_by')

        client_id = self.request.query_params.get('client')
        inv_status = self.request.query_params.get('status')

        if client_id:
            qs = qs.filter(client_id=client_id)
        if inv_status:
            qs = qs.filter(status=inv_status)

        return qs

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate a new invoice for a client + date range.
        POST /api/sales/invoices/generate/
        Body: { client_id, from_date, to_date, tax_percentage, notes }
        """
        serializer = InvoiceGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            client = Client.objects.get(id=data['client_id'])
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=404)

        # Check user has access (superuser with sales access OR member of org)
        user = request.user
        has_access = False
        
        if user.is_superuser and user.can_access_sales:
            has_access = True
        elif OrganisationMembership.objects.filter(
            user=user, organisation=client.organisation, is_active=True,
        ).exists():
            has_access = True
        
        if not has_access:
            return Response({'error': 'Access denied'}, status=403)

        # Check there are sales in range
        sales_count = DailySale.objects.filter(
            client=client, date__gte=data['from_date'], date__lte=data['to_date'],
            is_holiday=False,
        ).count()

        if sales_count == 0:
            return Response({'error': 'No sales found in this date range'}, status=400)

        # Create invoice with content options
        invoice = Invoice.objects.create(
            client=client,
            from_date=data['from_date'],
            to_date=data['to_date'],
            tax_percentage=data.get('tax_percentage', 0),
            currency=data.get('currency', 'INR'),
            notes=data.get('notes', ''),
            include_daily_breakdown=data.get('include_daily_breakdown', True),
            include_packing_charges=data.get('include_packing_charges', True),
            include_courier_charges=data.get('include_courier_charges', True),
            include_item_detail=data.get('include_item_detail', True),
            attach_excel=data.get('attach_excel', False),
            generated_by=user,
        )

        # Calculate totals
        invoice.calculate_totals()

        # Generate PDF
        try:
            generate_invoice_pdf(invoice)
            logger.info(f'[INVOICE] Generated {invoice.invoice_number} for {client.name}')
        except Exception as e:
            logger.error(f'[INVOICE] PDF generation failed: {e}')
            # Invoice is still saved, PDF can be regenerated

        return Response(InvoiceSerializer(invoice).data, status=201)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download invoice PDF."""
        invoice = self.get_object()
        if not invoice.pdf_file:
            # Try to regenerate
            try:
                generate_invoice_pdf(invoice)
            except Exception as e:
                return Response({'error': 'PDF not available'}, status=404)

        response = HttpResponse(invoice.pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
        return response

    @action(detail=True, methods=['post'])
    def send_email(self, request, pk=None):
        """Send invoice to client via email. Attaches Excel breakdown if enabled."""
        from .services.invoice_pdf import generate_invoice_excel

        invoice = self.get_object()

        if not invoice.client.contact_email:
            return Response({'error': 'Client has no email address'}, status=400)

        if not invoice.pdf_file:
            try:
                generate_invoice_pdf(invoice)
            except Exception:
                return Response({'error': 'Could not generate PDF'}, status=500)

        # Send email
        try:
            from django.core.mail import EmailMessage
            email = EmailMessage(
                subject=f'Invoice {invoice.invoice_number} — {invoice.client.organisation.name}',
                body=(
                    f"Dear {invoice.client.contact_person or invoice.client.name},\n\n"
                    f"Please find attached your invoice for the period "
                    f"{invoice.from_date.strftime('%d %b %Y')} to {invoice.to_date.strftime('%d %b %Y')}.\n\n"
                    f"Total Amount: {invoice.currency_symbol}{invoice.grand_total:,.2f}\n\n"
                    f"Thank you for your business.\n\n"
                    f"Best regards,\n{invoice.client.organisation.name}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[invoice.client.contact_email],
            )
            email.attach(
                f'{invoice.invoice_number}.pdf',
                invoice.pdf_file.read(),
                'application/pdf',
            )

            # Attach Excel breakdown if enabled
            if invoice.attach_excel:
                try:
                    excel_filename, excel_bytes = generate_invoice_excel(invoice)
                    email.attach(
                        excel_filename,
                        excel_bytes,
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    )
                    logger.info(f'[INVOICE] Excel attachment added for {invoice.invoice_number}')
                except Exception as e:
                    logger.warning(f'[INVOICE] Excel generation failed for {invoice.invoice_number}: {e}')
                    # Don't fail the whole email — send PDF without Excel

            email.send()

            invoice.status = 'SENT'
            invoice.sent_at = timezone.now()
            invoice.save(update_fields=['status', 'sent_at'])

            logger.info(f'[INVOICE] Sent {invoice.invoice_number} to {invoice.client.contact_email}')
            return Response({'message': f'Invoice sent to {invoice.client.contact_email}'})

        except Exception as e:
            logger.error(f'[INVOICE] Email failed: {e}')
            return Response({'error': f'Failed to send email: {str(e)}'}, status=500)

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark invoice as paid."""
        invoice = self.get_object()
        invoice.status = 'PAID'
        invoice.paid_at = timezone.now()
        invoice.save(update_fields=['status', 'paid_at'])
        return Response(InvoiceSerializer(invoice).data)


# ============================================================
# Holidays
# ============================================================

# ============================================================
# Public Delivery Confirmation (no login needed)
# ============================================================

class ConfirmDeliveryView(APIView):
    """Public endpoint for clients to confirm delivery via email token link."""
    permission_classes = (permissions.AllowAny,)

    def get(self, request, token):
        """Load delivery details for the confirmation page."""
        try:
            sale = DailySale.objects.select_related('client', 'client__organisation').get(
                confirmation_token=token,
            )
        except DailySale.DoesNotExist:
            return Response({'error': 'Invalid confirmation link.'}, status=404)

        if sale.confirmation_token_expires_at and timezone.now() > sale.confirmation_token_expires_at:
            return Response({'error': 'This confirmation link has expired.'}, status=410)

        if sale.client_confirmed:
            return Response({
                'already_confirmed': True,
                'confirmed_at': sale.client_confirmed_at,
                'delivery': {
                    'date': sale.date,
                    'day_name': sale.day_name,
                    'items': sale.items_description,
                    'total': float(sale.total_charge),
                    'client_name': sale.client.name,
                    'org_name': sale.client.organisation.name,
                },
            })

        # Read price visibility from query params (set by admin when sending)
        show_prices = request.query_params.get('sp', '1') == '1'
        show_breakdown = request.query_params.get('sb', '0') == '1'

        return Response({
            'already_confirmed': False,
            'delivery': {
                'date': sale.date,
                'day_name': sale.day_name,
                'items': sale.items_description,
                'num_people': sale.num_people,
                'food_total': float(sale.food_price_per_day),
                'packing': float(sale.packing_charges),
                'courier': float(sale.courier_charges),
                'total': float(sale.total_charge),
                'client_name': sale.client.name,
                'org_name': sale.client.organisation.name,
                # Price visibility — admin-controlled at send time
                'show_prices': show_prices,
                'show_breakdown': show_breakdown,
            },
        })

    def post(self, request, token):
        """Confirm the delivery."""
        try:
            sale = DailySale.objects.select_related('client', 'client__organisation').get(
                confirmation_token=token,
            )
        except DailySale.DoesNotExist:
            return Response({'error': 'Invalid confirmation link.'}, status=404)

        if sale.confirmation_token_expires_at and timezone.now() > sale.confirmation_token_expires_at:
            return Response({'error': 'This confirmation link has expired.'}, status=410)

        if sale.client_confirmed:
            return Response({'message': 'Already confirmed.', 'confirmed_at': sale.client_confirmed_at})

        sale.client_confirmed = True
        sale.client_confirmed_at = timezone.now()
        sale.client_confirmation_note = request.data.get('note', '')
        sale.save(update_fields=['client_confirmed', 'client_confirmed_at', 'client_confirmation_note'])

        return Response({
            'message': 'Delivery confirmed. Thank you!',
            'confirmed_at': sale.client_confirmed_at,
        })


class RaiseDisputeViaTokenView(APIView):
    """
    Public endpoint — client raises a dispute via the email confirmation link.
    No login required. Uses the same confirmation_token as ConfirmDeliveryView.
    POST /confirm-delivery/{token}/dispute/
    Body: { dispute_type, description }
    """
    permission_classes = (permissions.AllowAny,)

    VALID_TYPES = ['MISSING_ITEM', 'WRONG_ITEM', 'QUALITY', 'QUANTITY', 'OVERCHARGE', 'OTHER']

    def post(self, request, token):
        try:
            sale = DailySale.objects.select_related('client', 'client__organisation').get(
                confirmation_token=token,
            )
        except DailySale.DoesNotExist:
            return Response({'error': 'Invalid or expired link.'}, status=404)

        if sale.confirmation_token_expires_at and timezone.now() > sale.confirmation_token_expires_at:
            return Response({'error': 'This link has expired.'}, status=410)

        dispute_type = request.data.get('dispute_type', 'OTHER')
        description = request.data.get('description', '').strip()

        if not description:
            return Response({'error': 'Please describe the issue.'}, status=400)

        if dispute_type not in self.VALID_TYPES:
            dispute_type = 'OTHER'

        # Prevent duplicate disputes of same type on same sale
        if Dispute.objects.filter(
            daily_sale=sale,
            dispute_type=dispute_type,
            status__in=['OPEN', 'ACKNOWLEDGED'],
        ).exists():
            return Response({
                'message': 'A concern of this type has already been raised for this delivery.',
                'already_disputed': True,
            })

        dispute = Dispute.objects.create(
            daily_sale=sale,
            raised_by=None,  # No logged-in user — raised via token link
            dispute_type=dispute_type,
            description=description,
            status='OPEN',
        )

        # Mark sale as disputed
        sale.status = 'DISPUTED'
        sale.save(update_fields=['status'])

        # Notify the org (always — this is an issue, not a routine confirmation)
        try:
            from django.core.mail import send_mail
            org = sale.client.organisation
            if org.email:
                send_mail(
                    subject=f'[Issue Raised] {sale.client.name} — {sale.date.strftime("%d %b %Y")}',
                    message=(
                        f'A concern has been raised via the delivery confirmation link.\n\n'
                        f'Client: {sale.client.name}\n'
                        f'Date: {sale.date.strftime("%d %b %Y")}\n'
                        f'Type: {dispute.get_dispute_type_display()}\n'
                        f'Description: {description}\n\n'
                        f'Review in your SignSimple dashboard.'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[org.email],
                    fail_silently=True,
                )
        except Exception as e:
            logger.error(f'[DISPUTE-TOKEN] Notify email failed: {e}')

        return Response({
            'message': 'Your concern has been raised. The provider will be notified.',
            'dispute_id': str(dispute.id),
        }, status=201)


# ============================================================
# Holidays
# ============================================================

class HolidayViewSet(viewsets.ModelViewSet):
    serializer_class = HolidaySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        
        if not user.can_access_sales:
            return Holiday.objects.none()
        
        # Use TenantMiddleware org if available
        org = getattr(self.request, 'org', None)
        if org and org.sales_access_enabled:
            qs = Holiday.objects.filter(organisation=org)
        else:
            org_ids = get_user_accessible_org_ids(user)
            qs = Holiday.objects.filter(organisation_id__in=org_ids)

            org_id = self.request.query_params.get('organisation')
            if org_id:
                qs = qs.filter(organisation_id=org_id)

        return qs
