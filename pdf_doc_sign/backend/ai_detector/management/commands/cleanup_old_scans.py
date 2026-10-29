"""
Management command to delete old AI detection scans.

Usage:
    python manage.py cleanup_old_scans                    # Delete scans older than 30 days
    python manage.py cleanup_old_scans --days 60          # Delete scans older than 60 days
    python manage.py cleanup_old_scans --days 30 --dry-run  # Preview what would be deleted
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from ai_detector.models import AIDetectionScan


class Command(BaseCommand):
    help = 'Delete AI detection scans older than N days (default 30)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=30,
            help='Delete scans older than this many days (default: 30)'
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        cutoff = timezone.now() - timedelta(days=days)
        old_scans = AIDetectionScan.objects.filter(created_at__lt=cutoff)
        count = old_scans.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS(f'No scans older than {days} days found.'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'[DRY RUN] Would delete {count} scans older than {days} days (before {cutoff.strftime("%Y-%m-%d")})'
            ))
            for scan in old_scans[:10]:
                self.stdout.write(f'  - {scan.created_at.strftime("%Y-%m-%d")} | {scan.original_filename} | {scan.user.email}')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        else:
            deleted, _ = old_scans.delete()
            self.stdout.write(self.style.SUCCESS(
                f'Deleted {deleted} scans older than {days} days (before {cutoff.strftime("%Y-%m-%d")})'
            ))
