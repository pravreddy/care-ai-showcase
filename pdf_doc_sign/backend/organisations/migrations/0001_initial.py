import django.core.validators
import django.db.models.deletion
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
            name='Organisation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(help_text='Used in subdomain', max_length=100, unique=True)),
                ('company_number', models.CharField(blank=True, max_length=20)),
                ('vat_number', models.CharField(blank=True, max_length=20)),
                ('address', models.TextField(blank=True)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('postcode', models.CharField(blank=True, max_length=10)),
                ('country', models.CharField(default='United Kingdom', max_length=100)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('website', models.URLField(blank=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='org_logos/')),
                ('logo_url', models.URLField(blank=True)),
                ('primary_colour', models.CharField(default='#1565c0', max_length=7, validators=[django.core.validators.RegexValidator('^#[0-9A-Fa-f]{6}$', 'Must be a hex colour')])),
                ('secondary_colour', models.CharField(default='#f57c00', max_length=7)),
                ('custom_domain', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('plan', models.CharField(choices=[('FREE', 'Free'), ('STARTER', 'Starter'), ('PROFESSIONAL', 'Professional'), ('ENTERPRISE', 'Enterprise')], default='FREE', max_length=20)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('TRIAL', 'Trial'), ('SUSPENDED', 'Suspended'), ('CANCELLED', 'Cancelled')], default='TRIAL', max_length=20)),
                ('custom_price_gbp', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('documents_per_month_override', models.IntegerField(blank=True, null=True)),
                ('documents_used_this_month', models.IntegerField(default=0)),
                ('extra_docs_purchased', models.IntegerField(default=0)),
                ('usage_reset_date', models.DateField(blank=True, null=True)),
                ('payment_provider', models.CharField(blank=True, max_length=50)),
                ('payment_provider_customer_id', models.CharField(blank=True, max_length=255)),
                ('trial_ends_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='owned_organisations', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.AddIndex(model_name='organisation', index=models.Index(fields=['slug'], name='org_slug_idx')),
        migrations.AddIndex(model_name='organisation', index=models.Index(fields=['status'], name='org_status_idx')),
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('code', models.CharField(blank=True, max_length=20)),
                ('address', models.TextField(blank=True)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('postcode', models.CharField(blank=True, max_length=10)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='branch_logos/')),
                ('logo_url', models.URLField(blank=True)),
                ('primary_colour', models.CharField(blank=True, max_length=7)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('organisation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='branches', to='organisations.organisation')),
            ],
            options={'ordering': ['organisation', 'name'], 'verbose_name_plural': 'Branches', 'unique_together': {('organisation', 'name')}},
        ),
        migrations.CreateModel(
            name='OrganisationMembership',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('OWNER', 'Owner'), ('ADMIN', 'Admin'), ('MANAGER', 'Manager'), ('MEMBER', 'Member'), ('VIEWER', 'Viewer')], default='MEMBER', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('branch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='members', to='organisations.branch')),
                ('organisation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='organisations.organisation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['organisation', 'role'], 'unique_together': {('user', 'organisation')}},
        ),
    ]
