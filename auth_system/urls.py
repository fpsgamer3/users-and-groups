from django.urls import path
from auth_system.views import (
    RegisterView, LoginView, LogoutView, CurrentUserView, UserListView,
    GroupListView, GroupDetailView, GroupMemberView, ModeratorToggleView, MuteToggleView, MessageView, MessageDetailView, GroupExportView, AdminGraphDataView, AuditLogView
)

app_name = 'auth_system'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('current-user/', CurrentUserView.as_view(), name='current-user'),
    path('users/', UserListView.as_view(), name='user-list'),
    
    # Admin endpoints
    path('admin/graph-data/', AdminGraphDataView.as_view(), name='admin-graph-data'),
    path('admin/audit-logs/', AuditLogView.as_view(), name='audit-logs'),
    
    # Group endpoints
    path('groups/', GroupListView.as_view(), name='group-list'),
    path('groups/<int:group_id>/', GroupDetailView.as_view(), name='group-detail'),
    path('groups/<int:group_id>/members/', GroupMemberView.as_view(), name='group-members'),
    path('groups/<int:group_id>/members/<int:user_id>/', GroupMemberView.as_view(), name='group-member-detail'),
    path('groups/<int:group_id>/members/<int:user_id>/moderator/', ModeratorToggleView.as_view(), name='moderator-toggle'),
    path('groups/<int:group_id>/members/<int:user_id>/mute/', MuteToggleView.as_view(), name='mute-toggle'),
    
    # Message endpoints
    path('groups/<int:group_id>/messages/', MessageView.as_view(), name='group-messages'),
    path('groups/<int:group_id>/messages/<int:message_id>/', MessageDetailView.as_view(), name='message-detail'),
    
    # Export endpoint
    path('groups/<int:group_id>/export/', GroupExportView.as_view(), name='group-export'),
]

