from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """Extended User model with role and additional fields"""
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]
    
    GRADE_CHOICES = [
        ('12A', 'Grade 12A'),
        ('12B', 'Grade 12B'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    preferred_grade = models.CharField(max_length=10, choices=GRADE_CHOICES, default='12A', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def get_role_display(self):
        return dict(self.ROLE_CHOICES).get(self.role, "Unknown")


class Group(models.Model):
    """Group model for organizing users"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_groups')
    is_teacher_group = models.BooleanField(default=False)
    is_class_group = models.BooleanField(default=False, help_text="Hidden group for managing class numbering")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class GroupMember(models.Model):
    """Association between users and groups with roles"""
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('teacher_moderator', 'Teacher Moderator'),
        ('moderator', 'Moderator'),
        ('student', 'Student'),
    ]
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='group_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_muted = models.BooleanField(default=False)
    grade = models.CharField(max_length=10, blank=True, null=True, help_text="Student grade (e.g., 10, 11, 12)")
    class_number = models.PositiveIntegerField(blank=True, null=True, help_text="Student number in class (unique per group)")
    
    class Meta:
        unique_together = ('group', 'user')
        ordering = ['group', 'user']
    
    def __str__(self):
        return f"{self.user.username} in {self.group.name} ({self.role})"


class Message(models.Model):
    """Messages sent within groups"""
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username} in {self.group.name}: {self.content[:50]}"


class AuditLog(models.Model):
    """Audit log to track system activities"""
    
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('account_create', 'Account Created'),
        ('account_delete', 'Account Deleted'),
        ('account_update', 'Account Updated'),
        ('message_send', 'Message Sent'),
        ('message_delete', 'Message Deleted'),
        ('group_create', 'Group Created'),
        ('group_delete', 'Group Deleted'),
        ('group_update', 'Group Updated'),
        ('member_join', 'Member Joined'),
        ('member_leave', 'Member Left'),
        ('member_remove', 'Member Removed'),
        ('role_change', 'Role Changed'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    target_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='target_audit_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.action} ({self.timestamp})"

