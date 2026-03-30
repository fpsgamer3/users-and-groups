# Change GroupMember.user to SET_NULL with pre_delete signal handling deletion

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth_system', '0018_alter_groupmember_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupmember',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='group_memberships', to='auth_system.customuser'),
        ),
    ]
