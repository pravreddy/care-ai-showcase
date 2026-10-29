"""
Management command to set up the Django Site for allauth.
Run once after first migration: python manage.py setup_site
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Configure the Django Site for allauth OAuth'

    def add_arguments(self, parser):
        parser.add_argument('--domain', type=str, default='localhost:8001', help='Site domain')
        parser.add_argument('--name', type=str, default='DocSign UK - Avyangah Technologies', help='Site name')

    def handle(self, *args, **options):
        domain = options['domain']
        name = options['name']

        site, created = Site.objects.update_or_create(
            id=1,
            defaults={'domain': domain, 'name': name},
        )

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} site: {name} ({domain})'))
