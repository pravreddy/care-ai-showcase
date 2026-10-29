import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('plan', models.CharField(choices=[('FREE', 'Free'), ('STARTER', 'Starter'), ('PROFESSIONAL', 'Professional')], max_length=20)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('CANCELLED', 'Cancelled'), ('EXPIRED', 'Expired'), ('PAST_DUE', 'Past Due')], default='ACTIVE', max_length=20)),
                ('start_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('end_date', models.DateTimeField()),
                ('auto_renew', models.BooleanField(default=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='GBP', max_length=3)),
                ('payment_provider', models.CharField(blank=True, max_length=50)),
                ('payment_provider_subscription_id', models.CharField(blank=True, max_length=255)),
                ('payment_provider_customer_id', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cancelled_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(model_name='subscription', index=models.Index(fields=['user', 'status'], name='subs_user_status_idx')),
        migrations.AddIndex(model_name='subscription', index=models.Index(fields=['end_date'], name='subs_end_date_idx')),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='GBP', max_length=3)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('SUCCESS', 'Success'), ('FAILED', 'Failed'), ('REFUNDED', 'Refunded')], default='PENDING', max_length=20)),
                ('payment_method', models.CharField(blank=True, choices=[('CARD', 'Credit/Debit Card'), ('DIRECT_DEBIT', 'Direct Debit'), ('BANK_TRANSFER', 'Bank Transfer')], max_length=20)),
                ('payment_provider', models.CharField(blank=True, max_length=50)),
                ('provider_payment_id', models.CharField(blank=True, max_length=255)),
                ('provider_reference', models.CharField(blank=True, max_length=255)),
                ('invoice_number', models.CharField(blank=True, max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
                ('failure_reason', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('subscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='subscriptions.subscription')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddIndex(model_name='payment', index=models.Index(fields=['user', 'status'], name='pay_user_status_idx')),
        migrations.CreateModel(
            name='ExtraDocsPurchase',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('documents_added', models.IntegerField(default=100)),
                ('amount_gbp', models.DecimalField(decimal_places=2, default=1.0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('payment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='subscriptions.payment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='extra_purchases', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
