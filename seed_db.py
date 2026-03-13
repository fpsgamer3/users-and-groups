import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'users_and_groups.settings')
django.setup()

from auth_system.models import CustomUser

# Clear existing data (optional)
CustomUser.objects.all().delete()

# Create sample users
teachers = [
    {
        'username': 'john_doe',
        'email': 'john@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'password': 'teacher123',
        'phone': '+1234567890',
        'bio': 'Mathematics Teacher',
        'role': 'teacher'
    },
    {
        'username': 'jane_smith',
        'email': 'jane@example.com',
        'first_name': 'Jane',
        'last_name': 'Smith',
        'password': 'teacher123',
        'phone': '+0987654321',
        'bio': 'English Language Teacher',
        'role': 'teacher'
    },
    {
        'username': 'robert_brown',
        'email': 'robert@example.com',
        'first_name': 'Robert',
        'last_name': 'Brown',
        'password': 'teacher123',
        'phone': '+1122334455',
        'bio': 'Science Teacher',
        'role': 'teacher'
    }
]

students = [
    {
        'username': 'alice_student',
        'email': 'alice@example.com',
        'first_name': 'Alice',
        'last_name': 'Johnson',
        'password': 'student123',
        'phone': '+5555555555',
        'bio': 'Grade 10 Student',
        'role': 'student'
    },
    {
        'username': 'bob_student',
        'email': 'bob@example.com',
        'first_name': 'Bob',
        'last_name': 'Wilson',
        'password': 'student123',
        'phone': '+6666666666',
        'bio': 'Grade 11 Student',
        'role': 'student'
    },
]

admin = {
    'username': 'admin',
    'email': 'admin@example.com',
    'first_name': 'Admin',
    'last_name': 'User',
    'password': 'admin123',
    'phone': '+9999999999',
    'bio': 'System Administrator',
    'is_staff': True,
    'is_superuser': True,
    'role': 'admin'
}

# Create teacher users
for teacher_data in teachers:
    password = teacher_data.pop('password')
    user = CustomUser.objects.create_user(**teacher_data)
    user.set_password(password)
    user.save()

print(f"✓ {len(teachers)} teacher(s) created successfully")

# Create student users
for student_data in students:
    password = student_data.pop('password')
    user = CustomUser.objects.create_user(**student_data)
    user.set_password(password)
    user.save()

print(f"✓ {len(students)} student(s) created successfully")

# Create admin user
password = admin.pop('password')
admin_user = CustomUser.objects.create_user(**admin)
admin_user.set_password(password)
admin_user.save()

print("✓ Admin user created successfully")

# Display summary
print("\n" + "="*50)
print("DATABASE SEED COMPLETED")
print("="*50)
print(f"\nTotal Users Created: {CustomUser.objects.count()}")
print("\n--- Sample Login Credentials ---")
print("Teacher: john_doe / teacher123")
print("Student: alice_student / student123")
print("Admin:   admin / admin123")
print("="*50)
