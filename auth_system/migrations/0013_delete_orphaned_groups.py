# Data migration to handle groups without creators before applying CASCADE constraint

from django.db import migrations


def delete_orphaned_groups(apps, schema_editor):
    """Delete groups that don't have a creator (created_by is NULL)"""
    Group = apps.get_model('auth_system', 'Group')
    orphaned_count = Group.objects.filter(created_by__isnull=True).delete()[0]
    print(f"Deleted {orphaned_count} orphaned groups without a creator")


def noop(apps, schema_editor):
    """Reverse operation - no-op since we can't restore deleted groups"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('auth_system', '0012_populate_student_grades'),
    ]

    operations = [
        migrations.RunPython(delete_orphaned_groups, noop),
    ]
