from rest_framework import serializers
from auth_system.models import CustomUser, Group, GroupMember, Message, AuditLog


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    grade = serializers.ChoiceField(choices=[('12A', '12A'), ('12B', '12B')], required=False)
    role = serializers.ChoiceField(choices=[('student', 'Student'), ('teacher', 'Teacher')], required=False, default='student')

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'password', 'password_confirm', 'role', 'grade'
        ]

    def validate(self, data):
        if data.get('password') != data.pop('password_confirm'):
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        grade = validated_data.pop('grade', '12A')
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.preferred_grade = grade
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError('Invalid username or password')

        if not user.check_password(password):
            raise serializers.ValidationError('Invalid username or password')

        data['user'] = user
        return data


class GroupMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)
    
    class Meta:
        model = GroupMember
        fields = ['id', 'user', 'username', 'email', 'first_name', 'last_name', 'role', 'user_role', 'grade', 'class_number', 'joined_at', 'is_muted']
        read_only_fields = ['id', 'joined_at']


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_first_name = serializers.CharField(source='sender.first_name', read_only=True)
    sender_last_name = serializers.CharField(source='sender.last_name', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_username', 'sender_first_name', 'sender_last_name', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'sender', 'created_at', 'updated_at']


class GroupSerializer(serializers.ModelSerializer):
    members = GroupMemberSerializer(many=True, read_only=True)
    created_by_username = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'created_by', 'created_by_username', 'is_teacher_group', 'created_at', 'updated_at', 'members', 'message_count']
        read_only_fields = ['id', 'created_by', 'is_teacher_group', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()

    def get_created_by_username(self, obj):
        return obj.created_by.username if obj.created_by else None


class GroupDetailSerializer(serializers.ModelSerializer):
    members = GroupMemberSerializer(many=True, read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    created_by_username = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'created_by', 'created_by_username', 'is_teacher_group', 'created_at', 'updated_at', 'members', 'messages']
        read_only_fields = ['id', 'created_by', 'is_teacher_group', 'created_at', 'updated_at']

    def get_created_by_username(self, obj):
        return obj.created_by.username if obj.created_by else None


class AuditLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    target_user_username = serializers.CharField(source='target_user.username', read_only=True, allow_null=True)
    group_name = serializers.CharField(source='group.name', read_only=True, allow_null=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_username', 'action', 'action_display', 'description', 'group', 'group_name', 'target_user', 'target_user_username', 'timestamp', 'ip_address']
        read_only_fields = ['id', 'timestamp']