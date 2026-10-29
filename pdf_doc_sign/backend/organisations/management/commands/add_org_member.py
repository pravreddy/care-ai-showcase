"""
Management command to manage organisation members and create organisations.

Examples:
  # Add existing user to an org
  python manage.py add_org_member --email user@example.com --org avyangah --role ADMIN

  # Create a new org and add yourself as owner
  python manage.py add_org_member --email admin@example.com --org krsna-foods --org-name "Krsna Foods" --create-org --role OWNER --sales

  # List all orgs
  python manage.py add_org_member --list-orgs

  # List members of an org
  python manage.py add_org_member --list-members --org avyangah
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from authentication.models import User
from organisations.models import Organisation, OrganisationMembership


class Command(BaseCommand):
    help = 'Add a user to an organisation, or create a new organisation'

    def add_arguments(self, parser):
        parser.add_argument('--email', help='User email address')
        parser.add_argument('--org', help='Organisation slug')
        parser.add_argument('--org-name', help='Organisation display name (for --create-org)')
        parser.add_argument('--role', default='MEMBER',
                            choices=['OWNER', 'ADMIN', 'MEMBER', 'VIEWER'],
                            help='Role (default: MEMBER)')
        parser.add_argument('--sales', action='store_true',
                            help='Enable sales access on the organisation')
        parser.add_argument('--create-org', action='store_true',
                            help='Create the organisation if it does not exist')
        parser.add_argument('--list-orgs', action='store_true',
                            help='List all organisations')
        parser.add_argument('--list-members', action='store_true',
                            help='List members of an organisation (use with --org)')

    def handle(self, *args, **options):
        # ─── List orgs ───
        if options['list_orgs']:
            orgs = Organisation.objects.all().order_by('name')
            if not orgs.exists():
                self.stdout.write('No organisations found.')
                return
            self.stdout.write(f'\n{"Slug":<25} {"Name":<30} {"Sales":<8} {"Status":<10} {"Members"}')
            self.stdout.write('─' * 90)
            for o in orgs:
                count = OrganisationMembership.objects.filter(organisation=o, is_active=True).count()
                sales = '✅' if o.sales_access_enabled else '❌'
                self.stdout.write(f'{o.slug:<25} {o.name:<30} {sales:<8} {o.status:<10} {count}')
            return

        # ─── List members ───
        if options['list_members']:
            if not options['org']:
                self.stdout.write(self.style.ERROR('--org is required with --list-members'))
                return
            try:
                org = Organisation.objects.get(slug=options['org'])
            except Organisation.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Organisation not found: {options["org"]}'))
                return
            members = OrganisationMembership.objects.filter(
                organisation=org, is_active=True
            ).select_related('user').order_by('role')
            self.stdout.write(f'\nMembers of {org.name} ({org.slug}):')
            self.stdout.write(f'{"Email":<40} {"Name":<25} {"Role":<10}')
            self.stdout.write('─' * 75)
            for m in members:
                self.stdout.write(f'{m.user.email:<40} {(m.user.full_name or "—"):<25} {m.role:<10}')
            self.stdout.write(f'\nTotal: {members.count()} members')
            return

        # ─── Add member ───
        if not options['email']:
            self.stdout.write(self.style.ERROR('--email is required'))
            return
        if not options['org']:
            self.stdout.write(self.style.ERROR('--org is required'))
            return

        email = options['email']
        org_slug = options['org']
        role = options['role']

        # Find user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User not found: {email}'))
            return

        # Find or create org
        try:
            org = Organisation.objects.get(slug=org_slug)
        except Organisation.DoesNotExist:
            if options['create_org']:
                org_name = options['org_name'] or org_slug.replace('-', ' ').title()
                org = Organisation.objects.create(
                    name=org_name,
                    slug=org_slug,
                    owner=user,  # The first user becomes the owner
                    status='ACTIVE',
                    plan='FREE',
                    sales_access_enabled=options['sales'],
                    sales_access_approved_at=timezone.now() if options['sales'] else None,
                )
                self.stdout.write(self.style.SUCCESS(f'✅ Created organisation: {org_name} ({org_slug})'))
            else:
                self.stdout.write(self.style.ERROR(f'Organisation not found: {org_slug}'))
                self.stdout.write('Use --create-org to create it, or pick from:')
                for o in Organisation.objects.all():
                    self.stdout.write(f'  {o.slug} — {o.name}')
                return

        # Enable sales if requested
        if options['sales'] and not org.sales_access_enabled:
            org.sales_access_enabled = True
            org.sales_access_approved_at = timezone.now()
            org.save(update_fields=['sales_access_enabled', 'sales_access_approved_at'])
            self.stdout.write(self.style.SUCCESS(f'✅ Enabled sales access for {org.name}'))

        # Add membership
        membership, created = OrganisationMembership.objects.get_or_create(
            user=user,
            organisation=org,
            defaults={'role': role, 'is_active': True}
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Added {email} to {org.name} as {role}'))
        else:
            if membership.role != role:
                membership.role = role
                membership.save(update_fields=['role'])
                self.stdout.write(self.style.SUCCESS(f'✅ Updated {email} role to {role} in {org.name}'))
            else:
                self.stdout.write(f'Already a member: {email} in {org.name} as {membership.role}')

        self.stdout.write('')
        self.stdout.write('User needs to log out and log back in to see changes.')
