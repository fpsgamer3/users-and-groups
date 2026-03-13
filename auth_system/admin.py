from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from auth_system.models import CustomUser, Group, GroupMember, Message


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email_display', 'get_full_name', 'role_badge', 'is_active_badge', 'created_at']
    list_filter = ['role', 'is_staff', 'is_superuser', 'created_at', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['created_at', 'updated_at', 'user_stats']
    ordering = ['-created_at']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'bio', 'phone', 'created_at', 'updated_at', 'user_stats')
        }),
    )
    
    def email_display(self, obj):
        return format_html('<a href="mailto:{}">{}</a>', obj.email, obj.email)
    email_display.short_description = 'Email'
    
    def get_full_name(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name if full_name else "—"
    get_full_name.short_description = 'Full Name'
    
    def role_badge(self, obj):
        colors = {
            'student': '#0ea5e9',
            'moderator': '#8b5cf6',
            'teacher': '#f59e0b',
            'admin': '#ef4444'
        }
        color = colors.get(obj.role, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-weight: bold; font-size: 12px;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = 'Role'
    
    def is_active_badge(self, obj):
        color = '#10b981' if obj.is_active else '#ef4444'
        status = '✓ Active' if obj.is_active else '✗ Inactive'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    is_active_badge.short_description = 'Status'
    
    def user_stats(self, obj):
        groups_count = obj.group_members.count()
        messages_count = Message.objects.filter(sender=obj).count()
        return format_html(
            '<div style="padding: 10px; background: #f3f4f6; border-radius: 8px;"><strong>Groups:</strong> {} | <strong>Messages:</strong> {}</div>',
            groups_count, messages_count
        )
    user_stats.short_description = 'User Statistics'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['group_name_display', 'creator_display', 'member_count_badge', 'message_count_badge', 'created_at_display']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'group_stats', 'description']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Group Information', {
            'fields': ('name', 'description')
        }),
        ('Administration', {
            'fields': ('created_by', 'created_at', 'updated_at', 'group_stats'),
            'classes': ('collapse',)
        }),
    )
    
    def group_name_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; font-size: 14px; color: #2dd46f;">{}</span>',
            obj.name
        )
    group_name_display.short_description = 'Group Name'
    
    def creator_display(self, obj):
        if obj.created_by is None:
            return mark_safe('<span style="color: #999;">—</span>')
        return format_html(
            '<strong>{}</strong> ({})',
            obj.created_by.username,
            obj.created_by.get_role_display()
        )
    creator_display.short_description = 'Created By'
    
    def member_count_badge(self, obj):
        count = obj.members.count()
        return format_html(
            '<span style="background-color: #10b981; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;">{} Members</span>',
            count
        )
    member_count_badge.short_description = 'Members'
    
    def message_count_badge(self, obj):
        count = obj.messages.count()
        return format_html(
            '<span style="background-color: #8b5cf6; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;">{} Messages</span>',
            count
        )
    message_count_badge.short_description = 'Messages'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    created_at_display.short_description = 'Created'
    
    def group_stats(self, obj):
        members = obj.members.count()
        messages = obj.messages.count()
        member_list = ', '.join([gm.user.username for gm in obj.groupmember_set.all()[:5]])
        if obj.groupmember_set.count() > 5:
            member_list += f' + {obj.groupmember_set.count() - 5} more'
        return format_html(
            '<div style="padding: 15px; background: #f3f4f6; border-radius: 8px; line-height: 1.8;">'
            '<strong style="color: #2dd46f; font-size: 14px;">📊 Group Statistics</strong><br>'
            '<strong>Total Members:</strong> {}<br>'
            '<strong>Total Messages:</strong> {}<br>'
            '<strong style="color: #666;">Members:</strong> {}'
            '</div>',
            members, messages, member_list
        )
    group_stats.short_description = 'Group Statistics'


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ['member_display', 'group_display', 'role_display', 'joined_at_display']
    list_filter = ['group', 'role', 'joined_at']
    search_fields = ['user__username', 'group__name']
    readonly_fields = ['joined_at']
    ordering = ['-joined_at']
    
    fieldsets = (
        ('Membership Information', {
            'fields': ('user', 'group', 'role', 'joined_at')
        }),
    )
    
    def member_display(self, obj):
        return format_html(
            '<strong>{}</strong><br><span style="color: #666; font-size: 12px;">{}</span>',
            obj.user.username, obj.user.email
        )
    member_display.short_description = 'Member'
    
    def group_display(self, obj):
        return format_html(
            '<strong style="color: #2dd46f;">{}</strong>',
            obj.group.name
        )
    group_display.short_description = 'Group'
    
    def role_display(self, obj):
        colors = {
            'admin': '#ef4444',
            'teacher': '#f59e0b',
            'moderator': '#8b5cf6',
            'student': '#0ea5e9'
        }
        color = colors.get(obj.role, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 8px; font-weight: bold; font-size: 11px;">{}</span>',
            color, obj.get_role_display()
        )
    role_display.short_description = 'Role'
    
    def joined_at_display(self, obj):
        return obj.joined_at.strftime('%b %d, %Y')
    joined_at_display.short_description = 'Joined'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender_display', 'group_display', 'content_display', 'created_at_display']
    list_filter = ['group', 'created_at']
    search_fields = ['sender__username', 'group__name', 'content']
    readonly_fields = ['created_at', 'updated_at', 'message_meta']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Message', {
            'fields': ('sender', 'group', 'content')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'message_meta'),
            'classes': ('collapse',)
        }),
    )
    
    def sender_display(self, obj):
        first_letter = obj.sender.username[0].upper()
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #2dd46f, #10b981); color: white; display: flex; align-items: center; justify-content: center; font-weight: bold;">{}</div>'
            '<div><strong>{}</strong><br><span style="color: #666; font-size: 11px;">{}</span></div>'
            '</div>',
            first_letter, obj.sender.username, obj.sender.email
        )
    sender_display.short_description = 'Sender'
    
    def group_display(self, obj):
        return format_html(
            '<span style="background: #2dd46f; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 12px;">📁 {}</span>',
            obj.group.name
        )
    group_display.short_description = 'Group'
    
    def content_display(self, obj):
        preview = obj.content[:60] + ('...' if len(obj.content) > 60 else '')
        return format_html(
            '<span style="color: #333; font-style: italic;">"{}"</span>',
            preview
        )
    content_display.short_description = 'Content'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%b %d, %Y %H:%M')
    created_at_display.short_description = 'Posted'
    
    def message_meta(self, obj):
        return format_html(
            '<div style="padding: 10px; background: #f3f4f6; border-radius: 8px; line-height: 1.6;">'
            '<strong>ID:</strong> {}<br>'
            '<strong>Full Content Length:</strong> {} characters<br>'
            '<strong>Last Updated:</strong> {}'
            '</div>',
            obj.id, len(obj.content), obj.updated_at.strftime('%b %d, %Y %H:%M:%S')
        )
    message_meta.short_description = 'Message Metadata'


# Unregister Django's default Groups model (we use GroupMember instead)
from django.contrib.auth.models import Group
admin.site.unregister(Group)

# Django admin site customization
admin.site.site_header = "🌿 Leav Education Platform"
admin.site.site_title = "Leav Admin"
admin.site.index_title = "Welcome to Leav Administration"
