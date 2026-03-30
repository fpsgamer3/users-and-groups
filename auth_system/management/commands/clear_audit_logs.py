from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from auth_system.models import AuditLog


class Command(BaseCommand):
    help = 'Clear audit logs with various filtering options'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=None,
            help='Delete logs older than N days'
        )
        parser.add_argument(
            '--action',
            type=str,
            default=None,
            help='Delete logs with specific action (e.g., login, logout, message_send)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Delete all audit logs (WARNING: irreversible)'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt'
        )

    def handle(self, *args, **options):
        query = AuditLog.objects.all()

        # Build the query based on options
        if options['days']:
            cutoff_date = timezone.now() - timedelta(days=options['days'])
            query = query.filter(timestamp__lt=cutoff_date)
            self.stdout.write(f"Filtering logs older than {options['days']} days ({cutoff_date})")

        if options['action']:
            query = query.filter(action=options['action'])
            self.stdout.write(f"Filtering logs with action: {options['action']}")

        if not options['all'] and not options['days'] and not options['action']:
            self.stdout.write(
                self.style.ERROR('Please specify --all, --days, or --action to delete logs')
            )
            return

        count = query.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No audit logs match the criteria'))
            return

        self.stdout.write(self.style.WARNING(f'About to delete {count} audit log(s)'))

        if not options['confirm']:
            confirm = input('Are you sure? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('Cancelled'))
                return

        deleted_count, _ = query.delete()
        self.stdout.write(
            self.style.SUCCESS(f'✓ Successfully deleted {deleted_count} audit log(s)')
        )
