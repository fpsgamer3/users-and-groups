from django.core.management.base import BaseCommand
from auth_system.models import Group, GroupMember
from django.db.models import Q


class Command(BaseCommand):
    help = 'Assign grades (12A, 12B) and class numbers globally to students and moderators, sorted alphabetically'

    def handle(self, *args, **options):
        # Get all students and moderators across all groups, sorted by last_name then first_name
        # Remove duplicates by user (each user gets one class number globally)
        members = GroupMember.objects.filter(
            Q(role='student') | Q(role='moderator')
        ).select_related('user').order_by('user__last_name', 'user__first_name')
        
        # Track which users we've already assigned to avoid duplicates
        assigned_users = set()
        unique_members = []
        
        for member in members:
            if member.user.id not in assigned_users:
                assigned_users.add(member.user.id)
                unique_members.append(member)
        
        # Track class numbers per grade
        class_12a = 0
        class_12b = 0
        
        # Assign grades and class numbers
        for idx, member in enumerate(unique_members, 1):
            if idx % 2 == 1:  # Odd positions get 12A
                grade = '12A'
                class_12a += 1
                class_number = class_12a
            else:  # Even positions get 12B
                grade = '12B'
                class_12b += 1
                class_number = class_12b
            
            # Update all group memberships for this user
            GroupMember.objects.filter(
                user=member.user,
                role__in=['student', 'moderator']
            ).update(grade=grade, class_number=class_number)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Assigned {len(unique_members)} students: {class_12a} in 12A, {class_12b} in 12B'
            )
        )
