from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from django.http import FileResponse
from django.db import models
from auth_system.models import CustomUser, Group, GroupMember, Message, AuditLog
from auth_system.serializers import (
    UserLoginSerializer, UserRegisterSerializer, CustomUserSerializer,
    GroupSerializer, GroupDetailSerializer, GroupMemberSerializer, MessageSerializer, AuditLogSerializer
)
from auth_system.export_utils import generate_group_export


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    'message': 'User registered successfully',
                    'user': CustomUserSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def ensure_teacher_group_membership():
    teacher_group, created = Group.objects.get_or_create(
        name='Teachers',
        defaults={
            'description': 'Teachers only group',
            'is_teacher_group': True,
            'created_by': CustomUser.objects.filter(role='admin').first()
        }
    )

    if not teacher_group.is_teacher_group:
        teacher_group.is_teacher_group = True
        teacher_group.save(update_fields=['is_teacher_group'])

    GroupMember.objects.filter(group=teacher_group).exclude(user__role='teacher').delete()

    teacher_users = CustomUser.objects.filter(role='teacher')
    existing = GroupMember.objects.filter(group=teacher_group, user__in=teacher_users)
    existing_ids = set(existing.values_list('user_id', flat=True))

    to_create = [
        GroupMember(group=teacher_group, user=teacher, role='teacher')
        for teacher in teacher_users
        if teacher.id not in existing_ids
    ]
    if to_create:
        GroupMember.objects.bulk_create(to_create)

    GroupMember.objects.filter(
        group=teacher_group,
        user__role='teacher'
    ).exclude(role='teacher_moderator').update(role='teacher')


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            ensure_teacher_group_membership()
            return Response(
                {
                    'message': 'Login successful',
                    'user': CustomUserSerializer(user).data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(
            {'message': 'Logout successful'},
            status=status.HTTP_200_OK
        )


class CurrentUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            user = request.user
            ensure_teacher_group_membership()
            return Response(
                CustomUserSerializer(user).data,
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'user': None},
                status=status.HTTP_200_OK
            )


class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = CustomUser.objects.all()
        serializer = CustomUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GroupListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all groups the user is a member of, plus all groups for admins"""
        ensure_teacher_group_membership()
        if request.user.role == 'admin':
            # Admins see all groups except class groups
            groups = Group.objects.filter(is_class_group=False)
        else:
            # Other users see only groups they're members of (excluding class groups)
            groups = Group.objects.filter(members__user=request.user, is_class_group=False)
        
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new group (admin/teacher only)"""
        if request.user.role not in ['admin', 'teacher']:
            return Response(
                {'error': 'Only admins and teachers can create groups'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # If admin is creating the group, they must specify a teacher to manage it
        if request.user.role == 'admin':
            teacher_id = request.data.get('teacher_id')
            if not teacher_id:
                return Response(
                    {'error': 'Admin must appoint a teacher to manage the group'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                teacher = CustomUser.objects.get(id=teacher_id, role='teacher')
            except CustomUser.DoesNotExist:
                return Response(
                    {'error': 'Invalid teacher ID or user is not a teacher'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = GroupSerializer(data=request.data)
        if serializer.is_valid():
            group = serializer.save(created_by=request.user)
            
            # If admin created it, add the appointed teacher
            if request.user.role == 'admin':
                GroupMember.objects.get_or_create(
                    group=group,
                    user=teacher,
                    defaults={'role': 'teacher'}
                )
            else:
                # If teacher created it, add themselves as teacher
                GroupMember.objects.get_or_create(
                    group=group,
                    user=request.user,
                    defaults={'role': 'teacher'}
                )
            return Response(
                GroupSerializer(group).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GroupDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_group_or_404(self, group_id, user):
        try:
            group = Group.objects.get(id=group_id)
            # Check if user has access (member or admin)
            if user.role != 'admin' and not group.members.filter(user=user).exists():
                return None
            return group
        except Group.DoesNotExist:
            return None

    def get(self, request, group_id):
        """Get group details with messages and members"""
        ensure_teacher_group_membership()
        group = self.get_group_or_404(group_id, request.user)
        if not group:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = GroupDetailSerializer(group)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, group_id):
        """Delete a group (admin or group creator only)"""
        group = self.get_group_or_404(group_id, request.user)
        if not group:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
        # Teachers-only group can only be deleted by admin
        if group.is_teacher_group:
            moderator_member = GroupMember.objects.filter(
                group=group, role='teacher_moderator', user=request.user
            ).first()
            if request.user.role != 'admin' and not moderator_member:
                return Response(
                    {'error': 'Only admins or teacher moderators can delete the teachers group'},
                    status=status.HTTP_403_FORBIDDEN
                )
            group.delete()
            return Response({'message': 'Group deleted'}, status=status.HTTP_200_OK)

        # Only admin or group creator can delete (NOT moderators)
        if request.user.role == 'admin' or group.created_by == request.user:
            group.delete()
            return Response({'message': 'Group deleted'}, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Only admins or the group creator can delete groups'},
                status=status.HTTP_403_FORBIDDEN
            )


class GroupMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        """Add a user to a group (teacher/admin only)"""
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)

        if group.is_teacher_group:
            return Response(
                {'error': 'Members cannot be added to the teachers group manually'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.user.role not in ['admin', 'teacher']:
            return Response(
                {'error': 'Only admins and teachers can add members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if user.role != 'teacher' and group.is_teacher_group:
            return Response(
                {'error': 'Only teachers can be members of the teachers group'},
                status=status.HTTP_403_FORBIDDEN
            )

        if user.role == 'teacher' and user != group.created_by:
            return Response(
                {'error': 'Only the group creator can be the teacher'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use user's actual role, not a provided one
        member, created = GroupMember.objects.get_or_create(
            group=group, user=user,
            defaults={
                'role': user.role,
                'grade': user.preferred_grade if user.role == 'student' else None
            }
        )
        
        # If new student member, auto-assign class_number
        if created and user.role == 'student':
            max_class_number = GroupMember.objects.filter(
                group=group,
                user__role='student',
                class_number__isnull=False
            ).aggregate(max_num=models.Max('class_number'))['max_num']
            
            next_class_number = (max_class_number or 0) + 1
            member.class_number = next_class_number
            member.save(update_fields=['class_number'])
        
        # If member already existed, update their grade and class_number
        if not created and user.role == 'student':
            member.grade = user.preferred_grade
            member.save(update_fields=['grade'])
        
        serializer = GroupMemberSerializer(member)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    def delete(self, request, group_id, user_id):
        """Remove a user from a group (admin or group teacher only)"""
        try:
            group = Group.objects.get(id=group_id)
            member = GroupMember.objects.get(group=group, user_id=user_id)
        except (Group.DoesNotExist, GroupMember.DoesNotExist):
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        if group.is_teacher_group:
            if request.user.role == 'admin':
                pass
            else:
                moderator_member = GroupMember.objects.filter(
                    group=group, role='teacher_moderator', user=request.user
                ).first()
                if not moderator_member:
                    return Response(
                        {'error': 'Only admins or the teacher moderator can remove members'},
                        status=status.HTTP_403_FORBIDDEN
                    )
        else:
            if request.user.role == 'admin':
                pass
            else:
                # Check if user is teacher or moderator of this group
                teacher_member = GroupMember.objects.filter(group=group, role='teacher').first()
                moderator_member = GroupMember.objects.filter(group=group, role='moderator', user=request.user).first()
                if (not teacher_member or teacher_member.user != request.user) and not moderator_member:
                    return Response(
                        {'error': 'Only admins, the group teacher, or moderators can remove members'},
                        status=status.HTTP_403_FORBIDDEN
                    )

        # Prevent moderators from removing teachers
        if member.user.role == 'teacher' and request.user.role != 'admin':
            # Check if the requester is a moderator (not the teacher)
            teacher_member = GroupMember.objects.filter(group=group, role='teacher').first()
            is_requesting_user_teacher = teacher_member and teacher_member.user == request.user
            if not is_requesting_user_teacher:
                return Response(
                    {'error': 'Teachers cannot be removed by moderators'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        member.delete()
        return Response({'message': 'Member removed'}, status=status.HTTP_200_OK)

    def patch(self, request, group_id, user_id):
        """Update member grade and class_number (teacher/admin only)"""
        try:
            group = Group.objects.get(id=group_id)
            member = GroupMember.objects.get(group=group, user_id=user_id)
        except (Group.DoesNotExist, GroupMember.DoesNotExist):
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        # Permission check
        if request.user.role == 'admin':
            pass
        else:
            if group.is_teacher_group:
                moderator_member = GroupMember.objects.filter(
                    group=group, role='teacher_moderator', user=request.user
                ).first()
                if not moderator_member:
                    return Response(
                        {'error': 'Only admins or the teacher moderator can update members'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            else:
                teacher_member = GroupMember.objects.filter(group=group, role='teacher').first()
                if not teacher_member or teacher_member.user != request.user:
                    return Response(
                        {'error': 'Only admins or the group teacher can update members'},
                        status=status.HTTP_403_FORBIDDEN
                    )

        # Update fields
        grade = request.data.get('grade')
        class_number = request.data.get('class_number')

        if grade is not None:
            member.grade = grade if grade else None
        if class_number is not None:
            member.class_number = class_number if class_number else None

        member.save()
        serializer = GroupMemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ModeratorToggleView(APIView):
    """Toggle moderator status for a group member"""
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id, user_id):
        """Toggle moderator role for a student (teacher of group or admin)"""
        try:
            group = Group.objects.get(id=group_id)
            member = GroupMember.objects.get(group=group, user_id=user_id)
        except (Group.DoesNotExist, GroupMember.DoesNotExist):
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if group.is_teacher_group:
            if request.user.role != 'admin':
                return Response(
                    {'error': 'Only admins can manage teacher moderators'},
                    status=status.HTTP_403_FORBIDDEN
                )
            if member.user.role != 'teacher':
                return Response(
                    {'error': 'Only teachers can be teacher moderators'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if member.role == 'teacher_moderator':
                member.role = 'teacher'
                message = 'User removed from teacher moderator role'
            else:
                existing = GroupMember.objects.filter(
                    group=group, role='teacher_moderator'
                ).exclude(id=member.id).first()
                if existing:
                    existing.role = 'teacher'
                    existing.save()
                member.role = 'teacher_moderator'
                message = 'User promoted to teacher moderator'
            member.save()
            serializer = GroupMemberSerializer(member)
            return Response(
                {'message': message, 'member': serializer.data},
                status=status.HTTP_200_OK
            )
        
        # Admins can manage moderators in all groups
        # Teachers can only manage in their own group
        if request.user.role == 'admin':
            # Admin is allowed
            pass
        else:
            # Non-admin: must be the group's teacher
            teacher_member = GroupMember.objects.filter(group=group, role='teacher').first()
            if not teacher_member or teacher_member.user != request.user:
                return Response(
                    {'error': 'Only the group teacher or admin can manage moderators'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Can only make students into moderators
        if member.user.role != 'student':
            return Response(
                {'error': 'Only students can be moderators'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Toggle between student and moderator
        if member.role == 'moderator':
            member.role = 'student'
            message = 'User removed from moderator role'
        else:
            existing_moderator = GroupMember.objects.filter(
                group=group, role='moderator'
            ).exclude(id=member.id).first()
            if existing_moderator:
                existing_moderator.role = 'student'
                existing_moderator.save()
            member.role = 'moderator'
            message = 'User promoted to moderator'
        
        member.save()
        serializer = GroupMemberSerializer(member)
        return Response(
            {'message': message, 'member': serializer.data},
            status=status.HTTP_200_OK
        )


class MessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        """Get all messages in a group"""
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user has access
        if request.user.role != 'admin' and not group.members.filter(user=request.user).exists():
            return Response(
                {'error': 'You do not have access to this group'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        messages = group.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, group_id):
        """Send a message to a group"""
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is a member
        if request.user.role != 'admin' and not group.members.filter(user=request.user).exists():
            return Response(
                {'error': 'You are not a member of this group'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user is muted
        if request.user.role != 'admin':
            member = group.members.filter(user=request.user).first()
            if member and member.is_muted:
                return Response(
                    {'error': 'You have been muted and cannot send messages'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        content = request.data.get('content', '').strip()
        if not content:
            return Response(
                {'error': 'Message content cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message = Message.objects.create(
            group=group,
            sender=request.user,
            content=content
        )
        
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, group_id, message_id):
        """Edit a message (own message only, or admin)"""
        try:
            group = Group.objects.get(id=group_id)
            message = Message.objects.get(id=message_id, group=group)
        except (Group.DoesNotExist, Message.DoesNotExist):
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Only the sender or admin can edit the message
        is_moderator = GroupMember.objects.filter(
            group=group, role='moderator', user=request.user
        ).exists()
        if message.sender.id != request.user.id and request.user.role != 'admin' and not is_moderator:
            return Response(
                {'error': 'You can only edit your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        content = request.data.get('content', '').strip()
        if not content:
            return Response(
                {'error': 'Message content cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message.content = content
        message.save()
        
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, group_id, message_id):
        """Delete a message (own message or teacher/admin of the group)"""
        try:
            group = Group.objects.get(id=group_id)
            message = Message.objects.get(id=message_id, group=group)
        except (Group.DoesNotExist, Message.DoesNotExist):
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions
        is_own_message = message.sender == request.user
        is_moderator = GroupMember.objects.filter(
            group=group, role='moderator', user=request.user
        ).exists()
        is_group_staff = request.user.role in ['admin', 'teacher'] or is_moderator
        
        if not (is_own_message or is_group_staff):
            return Response(
                {'error': 'You can only delete your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.delete()
        return Response({'message': 'Message deleted'}, status=status.HTTP_200_OK)


class MuteToggleView(APIView):
    """Toggle mute status for a group member"""
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id, user_id):
        """Toggle mute status for a student (teacher of group or admin only)"""
        try:
            group = Group.objects.get(id=group_id)
            member = GroupMember.objects.get(group=group, user_id=user_id)
        except (Group.DoesNotExist, GroupMember.DoesNotExist):
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        # Only teachers and admins can mute students
        if request.user.role == 'admin':
            # Admins can mute anyone
            pass
        else:
            # Non-admin: must be the group's teacher
            teacher_member = GroupMember.objects.filter(group=group, role='teacher').first()
            if not teacher_member or teacher_member.user != request.user:
                # For teacher group, also allow teacher_moderator
                if group.is_teacher_group:
                    moderator_member = GroupMember.objects.filter(
                        group=group, role='teacher_moderator', user=request.user
                    ).first()
                    if not moderator_member:
                        return Response(
                            {'error': 'Only teachers/moderators or admin can mute members'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                else:
                    moderator_member = GroupMember.objects.filter(
                        group=group, role='moderator', user=request.user
                    ).first()
                    if not moderator_member:
                        return Response(
                            {'error': 'Only the group teacher, moderator, or admin can mute members'},
                            status=status.HTTP_403_FORBIDDEN
                        )
        
        # Can only mute students
        if member.user.role != 'student':
            return Response(
                {'error': 'Only students can be muted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Toggle mute status
        member.is_muted = not member.is_muted
        member.save()
        
        message = 'User muted' if member.is_muted else 'User unmuted'
        serializer = GroupMemberSerializer(member)
        return Response(
            {'message': message, 'member': serializer.data},
            status=status.HTTP_200_OK
        )

class GroupExportView(APIView):
    """Export group data as DOCX file"""
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        """Export group data to DOCX"""
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user has access to the group
        if request.user.role != 'admin' and not group.members.filter(user=request.user).exists():
            return Response(
                {'error': 'You do not have access to this group'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user has permission to export (teacher, moderator, or admin)
        current_member = group.members.filter(user=request.user).first()
        user_role = current_member.role if current_member else None
        
        # Only admin, teacher, teacher_moderator, or moderator can export
        if request.user.role != 'admin' and user_role not in ['teacher', 'teacher_moderator', 'moderator']:
            return Response(
                {'error': 'Only teachers, moderators, and admins can export groups'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get group members
            members = group.members.select_related('user').order_by('joined_at')
            
            # Get group messages
            messages = group.messages.select_related('sender').order_by('created_at')
            
            # Get language from request (default to 'en')
            language = request.query_params.get('language', 'en')
            if language not in ['en', 'bg']:
                language = 'en'
            
            # Generate DOCX
            filepath, filename = generate_group_export(group, members, messages, language)
            
            # Return file as response
            response = FileResponse(open(filepath, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            return response
        except Exception as e:
            return Response(
                {'error': f'Failed to generate export: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminGraphDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Only admins can view the graph
        if request.user.role != 'admin':
            return Response(
                {'error': 'Access denied. Admin only.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Fetch all users
            users = CustomUser.objects.all()
            groups = Group.objects.filter(is_class_group=False)
            members = GroupMember.objects.filter(group__is_class_group=False).select_related('user', 'group')

            # Create nodes
            nodes = []
            node_ids = set()
            
            # Track which users are moderators in any group
            moderator_users = set()
            for member in members:
                if member.role in ['moderator', 'teacher_moderator']:
                    moderator_users.add(member.user.id)

            # Add user nodes
            for user in users:
                node_id = f"user_{user.id}"
                if node_id not in node_ids:
                    is_mod = user.id in moderator_users
                    nodes.append({
                        'id': node_id,
                        'label': user.first_name or user.username,
                        'type': 'user',
                        'role': 'moderator' if is_mod and user.role == 'student' else user.role,
                        'is_moderator': is_mod
                    })
                    node_ids.add(node_id)

            # Add group nodes
            for group in groups:
                node_id = f"group_{group.id}"
                if node_id not in node_ids:
                    nodes.append({
                        'id': node_id,
                        'label': group.name[:15],  # Truncate long names
                        'type': 'group',
                        'role': 'group',
                        'is_moderator': False
                    })
                    node_ids.add(node_id)

            # Create links
            links = []

            # Add member relationships
            for member in members:
                user_id = f"user_{member.user.id}"
                group_id = f"group_{member.group.id}"
                
                link_type = 'member'
                if member.role == 'teacher_moderator':
                    link_type = 'admin'
                elif member.role == 'moderator':
                    link_type = 'moderator'

                links.append({
                    'source': user_id,
                    'target': group_id,
                    'type': link_type
                })

            # Add creator relationships
            for group in groups:
                creator_id = f"user_{group.created_by.id}"
                group_id = f"group_{group.id}"
                
                links.append({
                    'source': creator_id,
                    'target': group_id,
                    'type': 'creator'
                })

            return Response({
                'nodes': nodes,
                'links': links
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': f'Failed to generate graph data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AuditLogView(APIView):
    """View for retrieving audit logs - admin only"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Only admins can view audit logs
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can view audit logs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all audit logs, ordered by timestamp (newest first)
        logs = AuditLog.objects.all().order_by('-timestamp')
        
        # Optional filtering
        action = request.query_params.get('action')
        if action:
            logs = logs.filter(action=action)
        
        user_id = request.query_params.get('user_id')
        if user_id:
            logs = logs.filter(user_id=user_id)
        
        group_id = request.query_params.get('group_id')
        if group_id:
            logs = logs.filter(group_id=group_id)
        
        # Pagination
        limit = request.query_params.get('limit', 100)
        try:
            limit = int(limit)
        except ValueError:
            limit = 100
        
        logs = logs[:limit]
        
        serializer = AuditLogSerializer(logs, many=True)
        return Response({
            'count': len(serializer.data),
            'logs': serializer.data
        }, status=status.HTTP_200_OK)
