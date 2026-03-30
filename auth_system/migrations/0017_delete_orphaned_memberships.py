# Clean up orphaned group memberships (with null user_id)

from django.db import migrations


def delete_orphaned_memberships(apps, schema_editor):
    """Delete group memberships with null user_id"""
    GroupMember = apps.get_model('auth_system', 'GroupMember')
    count, _ = GroupMember.objects.filter(user__isnull=True).delete()
    print(f"Deleted {count} orphaned group memberships")


def noop(apps, schema_editor):
    """Reverse operation"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('auth_system', '0016_alter_groupmember_user'),
    ]

    operations = [
        migrations.RunPython(delete_orphaned_memberships, noop),
    ]
