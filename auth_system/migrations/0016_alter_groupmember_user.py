# Change GroupMember.user from CASCADE to SET_NULL to fix SQLite deletion issues

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth_system', '0015_alter_group_created_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupmember',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='group_memberships', to='auth_system.customuser'),
        ),
    ]
