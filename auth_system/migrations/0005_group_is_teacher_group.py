from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_system', '0004_alter_groupmember_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='is_teacher_group',
            field=models.BooleanField(default=False),
        ),
    ]
