from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import CustomUser, Group, GroupMember, Message, AuditLog


def get_client_ip(request=None):
    """Get client IP address from request"""
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    return None


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log when a user logs in"""
    AuditLog.objects.create(
        user=user,
        action='login',
        description=f"{user.username} logged in",
        ip_address=get_client_ip(request)
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log when a user logs out"""
    if user:
        AuditLog.objects.create(
            user=user,
            action='logout',
            description=f"{user.username} logged out",
            ip_address=get_client_ip(request)
        )


@receiver(post_save, sender=CustomUser)
def log_user_changes(sender, instance, created, **kwargs):
    """Log when a user account is created or updated"""
    if created:
        AuditLog.objects.create(
            user=instance,
            action='account_create',
            description=f"Account created for {instance.username} ({instance.get_role_display()})"
        )
    else:
        AuditLog.objects.create(
            user=instance,
            action='account_update',
            description=f"Account updated for {instance.username}"
        )


@receiver(post_delete, sender=CustomUser)
def log_user_deletion(sender, instance, **kwargs):
    """Log when a user account is deleted"""
    AuditLog.objects.create(
        user=None,
        action='account_delete',
        description=f"Account deleted: {instance.username} ({instance.get_role_display()})"
    )


@receiver(post_save, sender=Message)
def log_message_sent(sender, instance, created, **kwargs):
    """Log when a message is sent"""
    if created:
        AuditLog.objects.create(
            user=instance.sender,
            action='message_send',
            description=f"{instance.sender.username} sent a message in {instance.group.name}",
            group=instance.group
        )


@receiver(post_delete, sender=Message)
def log_message_deletion(sender, instance, **kwargs):
    """Log when a message is deleted"""
    AuditLog.objects.create(
        user=None,
        action='message_delete',
        description=f"Message deleted from {instance.group.name} (was from {instance.sender.username})",
        group=instance.group
    )


@receiver(post_save, sender=Group)
def log_group_changes(sender, instance, created, **kwargs):
    """Log when a group is created or updated"""
    if created:
        AuditLog.objects.create(
            user=instance.created_by,
            action='group_create',
            description=f"Group '{instance.name}' created",
            group=instance
        )
    else:
        AuditLog.objects.create(
            user=None,
            action='group_update',
            description=f"Group '{instance.name}' updated",
            group=instance
        )


@receiver(post_delete, sender=Group)
def log_group_deletion(sender, instance, **kwargs):
    """Log when a group is deleted"""
    AuditLog.objects.create(
        user=None,
        action='group_delete',
        description=f"Group '{instance.name}' deleted",
    )


@receiver(post_save, sender=GroupMember)
def log_group_member_changes(sender, instance, created, **kwargs):
    """Log when a user joins or their role changes in a group"""
    if created:
        AuditLog.objects.create(
            user=instance.user,
            action='member_join',
            description=f"{instance.user.username} joined {instance.group.name} as {instance.get_role_display()}",
            group=instance.group,
            target_user=instance.user
        )
    else:
        AuditLog.objects.create(
            user=None,
            action='role_change',
            description=f"{instance.user.username}'s role changed to {instance.get_role_display()} in {instance.group.name}",
            group=instance.group,
            target_user=instance.user
        )


@receiver(post_delete, sender=GroupMember)
def log_group_member_removal(sender, instance, **kwargs):
    """Log when a user is removed from a group"""
    AuditLog.objects.create(
        user=None,
        action='member_remove',
        description=f"{instance.user.username} was removed from {instance.group.name}",
        group=instance.group,
        target_user=instance.user
    )
