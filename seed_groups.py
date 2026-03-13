#!/usr/bin/env python
"""
Script to seed the database with groups and add existing users to them
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'users_and_groups.settings')
django.setup()

from auth_system.models import Group, GroupMember, CustomUser

# Define school subject groups
GROUPS = [
    {
        'name': 'Mathematics',
        'description': 'Mathematics and Algebra discussions'
    },
    {
        'name': 'Physics',
        'description': 'Physics and Science discussions'
    },
    {
        'name': 'English Literature',
        'description': 'English Language and Literature discussions'
    }
]

def seed_groups():
    print("Creating groups...")
    groups = []
    
    for group_data in GROUPS:
        group, created = Group.objects.get_or_create(
            name=group_data['name'],
            defaults={'description': group_data['description']}
        )
        groups.append(group)
        status = "Created" if created else "Already exists"
        print(f"  {status}: {group.name}")
    
    return groups

def add_users_to_groups(groups):
    print("\nAdding existing users to groups...")
    
    # Get all users
    users = CustomUser.objects.all()
    
    for group in groups:
        for user in users:
            # Determine role in group based on user role
            if user.role == 'admin':
                member_role = 'admin'
            elif user.role == 'teacher':
                member_role = 'teacher'
            else:
                member_role = 'student'
            
            member, created = GroupMember.objects.get_or_create(
                group=group,
                user=user,
                defaults={'role': member_role}
            )
            
            if created:
                print(f"  Added {user.username} to {group.name} as {member_role}")

if __name__ == '__main__':
    print("=" * 50)
    print("Seeding Groups Database")
    print("=" * 50)
    
    groups = seed_groups()
    add_users_to_groups(groups)
    
    print("\n" + "=" * 50)
    print("✓ Groups seeding complete!")
    print("=" * 50)
