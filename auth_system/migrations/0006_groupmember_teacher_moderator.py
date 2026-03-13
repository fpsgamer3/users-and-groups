from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_system', '0005_group_is_teacher_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupmember',
            name='role',
            field=models.CharField(choices=[('admin', 'Administrator'), ('teacher', 'Teacher'), ('teacher_moderator', 'Teacher Moderator'), ('moderator', 'Moderator'), ('student', 'Student')], default='student', max_length=20),
        ),
    ]
