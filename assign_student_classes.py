#!/usr/bin/env python
"""
Script to assign students to classes (1 or 2) and set grades.
Evenly distributes students between two classes.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'users_and_groups.settings')
django.setup()

from auth_system.models import Group, GroupMember

def assign_classes_to_group(group):
    """Assign all student members to classes 1 or 2"""
    # Get all student members in this group
    students = GroupMember.objects.filter(
        group=group, 
        role__in=['student', 'moderator']
    ).order_by('joined_at')
    
    if not students.exists():
        print(f"  No students in group '{group.name}'")
        return
    
    # Assign classes: odd index -> class 1, even index -> class 2
    for idx, member in enumerate(students):
        class_number = 1 if idx % 2 == 0 else 2
        member.class_number = class_number
        # Set a default grade if not set
        if not member.grade:
            member.grade = '10'  # Default grade
        member.save()
        print(f"    {member.user.username}: Class {class_number}, Grade {member.grade}")
    
    print(f"  ✓ Assigned {students.count()} students to classes\n")

def main():
    print("Assigning students to classes...\n")
    
    groups = Group.objects.filter(is_teacher_group=False)
    
    if not groups.exists():
        print("No regular groups found.")
        return
    
    for group in groups:
        print(f"Group: {group.name}")
        assign_classes_to_group(group)
    
    print("Done!")

if __name__ == '__main__':
    main()
