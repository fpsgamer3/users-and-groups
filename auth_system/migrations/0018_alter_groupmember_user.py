# Revert GroupMember.user back to CASCADE (deletion handled via pre_delete signal)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth_system', '0017_delete_orphaned_memberships'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupmember',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_memberships', to='auth_system.customuser'),
        ),
    ]
