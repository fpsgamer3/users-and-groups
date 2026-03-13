from django.core.management.base import BaseCommand
from django.db.models import Q
from auth_system.models import CustomUser, Group, GroupMember


class Command(BaseCommand):
    help = 'Initialize class groups (12A and 12B) and assign class numbers based on alphabetic sorting'

    def handle(self, *args, **options):
        admin_user = CustomUser.objects.filter(role='admin').first()
        
        # Create or get class groups
        class_12a, created = Group.objects.get_or_create(
            name='Class 12A',
            defaults={
                'description': 'Hidden group for managing class 12A numbering',
                'created_by': admin_user,
                'is_class_group': True,
            }
        )
        if not created:
            class_12a.is_class_group = True
            class_12a.save(update_fields=['is_class_group'])
        
        class_12b, created = Group.objects.get_or_create(
            name='Class 12B',
            defaults={
                'description': 'Hidden group for managing class 12B numbering',
                'created_by': admin_user,
                'is_class_group': True,
            }
        )
        if not created:
            class_12b.is_class_group = True
            class_12b.save(update_fields=['is_class_group'])
        
        # Get all students and moderators
        students_and_moderators = CustomUser.objects.filter(
            Q(role='student') | Q(group_memberships__role='moderator')
        ).distinct().order_by('last_name', 'first_name')
        
        # Separate by preferred grade
        class_12a_students = []
        class_12b_students = []
        
        for user in students_and_moderators:
            grade = user.preferred_grade or '12A'
            if grade == '12A':
                class_12a_students.append(user)
            else:
                class_12b_students.append(user)
        
        # Assign class numbers
        self.assign_class_numbers(class_12a, class_12a_students)
        self.assign_class_numbers(class_12b, class_12b_students)
        
        self.stdout.write(self.style.SUCCESS(
            f'Successfully initialized class groups: '
            f'12A ({len(class_12a_students)} students), '
            f'12B ({len(class_12b_students)} students)'
        ))
    
    def assign_class_numbers(self, class_group, users):
        """Assign class numbers to users in alphabetical order"""
        # Clear existing memberships for this class group
        GroupMember.objects.filter(group=class_group).delete()
        
        # Create new memberships with class numbers
        for index, user in enumerate(users, start=1):
            GroupMember.objects.create(
                group=class_group,
                user=user,
                role='student',
                class_number=index
            )
        
        # Also update class_number in all group memberships for this user
        for user in users:
            # Find the class number for this user
            class_member = GroupMember.objects.filter(
                group=class_group,
                user=user
            ).first()
            
            if class_member:
                # Update all other group memberships with this class number
                GroupMember.objects.filter(user=user).exclude(
                    group=class_group
                ).update(class_number=class_member.class_number)
