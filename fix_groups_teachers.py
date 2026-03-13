#!/usr/bin/env python
"""
Script to fix groups: ensure only one teacher per group and set them as creator
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'users_and_groups.settings')
django.setup()

from auth_system.models import Group, GroupMember, CustomUser

def fix_groups():
    print("=" * 60)
    print("Fixing Groups - One Teacher Per Group")
    print("=" * 60)
    
    groups = Group.objects.all()
    teachers = CustomUser.objects.filter(role='teacher')
    
    if not teachers.exists():
        print("\n⚠️  No teachers found. Creating a default teacher...")
        teacher = CustomUser.objects.create_user(
            username='teacher_admin',
            email='teacher@example.com',
            password='default123',
            first_name='Teacher',
            last_name='Admin',
            role='teacher'
        )
        print(f"Created teacher: {teacher.username}")
        teachers = [teacher]
    else:
        teachers = list(teachers)
    
    teacher_idx = 0
    
    for group in groups:
        print(f"\n📚 Processing group: {group.name}")
        
        # Get all teacher members in this group
        teacher_members = GroupMember.objects.filter(group=group, user__role='teacher')
        
        if teacher_members.count() == 0:
            # No teacher - assign one and set as creator
            assigned_teacher = teachers[teacher_idx % len(teachers)]
            teacher_idx += 1
            
            member, created = GroupMember.objects.get_or_create(
                group=group,
                user=assigned_teacher,
                defaults={'role': 'teacher'}
            )
            group.created_by = assigned_teacher
            group.save()
            print(f"  ✓ Assigned teacher: {assigned_teacher.username}")
            print(f"  ✓ Set as creator: {assigned_teacher.username}")
            
        elif teacher_members.count() == 1:
            # Exactly one teacher - ensure they're the creator
            teacher_member = teacher_members.first()
            if group.created_by != teacher_member.user:
                group.created_by = teacher_member.user
                group.save()
                print(f"  ✓ Teacher found: {teacher_member.user.username}")
                print(f"  ✓ Set as creator: {teacher_member.user.username}")
            else:
                print(f"  ✓ Teacher found: {teacher_member.user.username} (already creator)")
                
        else:
            # Multiple teachers - keep first one, remove others
            teachers_to_keep = teacher_members.first()
            teachers_to_remove = teacher_members.exclude(id=teachers_to_keep.id)
            
            print(f"  Found {teacher_members.count()} teachers")
            print(f"  ✓ Keeping: {teachers_to_keep.user.username}")
            
            for member in teachers_to_remove:
                print(f"  ✗ Removing: {member.user.username}")
                member.delete()
            
            if group.created_by != teachers_to_keep.user:
                group.created_by = teachers_to_keep.user
                group.save()
            print(f"  ✓ Set as creator: {teachers_to_keep.user.username}")
    
    print("\n" + "=" * 60)
    print("✓ All groups fixed!")
    print("=" * 60)

if __name__ == '__main__':
    fix_groups()
