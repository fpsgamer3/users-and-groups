from django.core.management.base import BaseCommand
from django.db import connection
from auth_system.models import CustomUser


class Command(BaseCommand):
    help = 'Delete a user and handle foreign key constraints properly'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int, help='ID of the user to delete')

    def handle(self, *args, **options):
        user_id = options['user_id']
        
        # Enable foreign keys for SQLite
        if 'sqlite' in connection.settings_dict['ENGINE']:
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA foreign_keys = ON')
        
        try:
            user = CustomUser.objects.get(id=user_id)
            username = user.username
            user.delete()
            self.stdout.write(self.style.SUCCESS(f'✓ Successfully deleted user: {username}'))
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
