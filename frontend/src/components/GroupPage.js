import React, { useState, useEffect } from 'react';
import './GroupPage.css';
import GroupList from './GroupList';
import MessageList from './MessageList';
import MembersList from './MembersList';
import MessageInput from './MessageInput';
import AdminVisualization from './AdminVisualization';
import AuditLogs from './AuditLogs';
import { useLanguage } from '../LanguageContext';

function GroupPage({ user, onLogout }) {
  const { t, language, toggleLanguage } = useLanguage();
  const [groups, setGroups] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [messages, setMessages] = useState([]);
  const [members, setMembers] = useState([]);
  const [error, setError] = useState('');
  const [showVisualization, setShowVisualization] = useState(false);
  const [showAuditLogs, setShowAuditLogs] = useState(false);

  // Fetch groups on component mount
  useEffect(() => {
    fetchGroups();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fetch group details when a group is selected
  useEffect(() => {
    if (selectedGroupId) {
      fetchGroupDetails(selectedGroupId);
    }
  }, [selectedGroupId]);

  const fetchGroups = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/groups/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setGroups(data);
        if (data.length > 0 && !selectedGroupId) {
          setSelectedGroupId(data[0].id);
        }
      } else {
        setError('Failed to load groups');
      }
    } catch (err) {
      setError('Error loading groups');
      console.error('Error fetching groups:', err);
    }
  };

  const fetchGroupDetails = async (groupId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/auth/groups/${groupId}/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedGroup(data);
        setMessages(data.messages || []);
        setMembers(data.members || []);
      } else {
        setError('Failed to load group details');
      }
    } catch (err) {
      setError('Error loading group details');
      console.error('Error fetching group details:', err);
    }
  };

  const handleGroupSelect = (groupId) => {
    setSelectedGroupId(groupId);
  };

  const handleRefreshMembers = () => {
    if (selectedGroupId) {
      fetchGroupDetails(selectedGroupId);
    }
  };

  const handleSendMessage = async (content) => {
    if (!selectedGroupId) return;

    try {
      const response = await fetch(`http://localhost:8000/api/auth/groups/${selectedGroupId}/messages/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        credentials: 'include',
        body: JSON.stringify({ content }),
      });

      if (response.ok) {
        // Refresh messages
        fetchGroupDetails(selectedGroupId);
      } else {
        setError('Failed to send message');
      }
    } catch (err) {
      setError('Error sending message');
      console.error('Error sending message:', err);
    }
  };

  const handleDeleteMessage = async (messageId) => {
    if (!selectedGroupId || !window.confirm('Delete this message?')) return;

    try {
      const response = await fetch(
        `http://localhost:8000/api/auth/groups/${selectedGroupId}/messages/${messageId}/`,
        {
          method: 'DELETE',
          headers: {
            'X-CSRFToken': getCsrfToken(),
          },
          credentials: 'include',
        }
      );

      if (response.ok) {
        fetchGroupDetails(selectedGroupId);
      } else {
        setError('Failed to delete message');
      }
    } catch (err) {
      setError('Error deleting message');
      console.error('Error deleting message:', err);
    }
  };

  const handleEditMessage = async (messageId, newContent) => {
    if (!selectedGroupId || !newContent.trim()) return;

    try {
      const response = await fetch(
        `http://localhost:8000/api/auth/groups/${selectedGroupId}/messages/${messageId}/`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
          },
          credentials: 'include',
          body: JSON.stringify({ content: newContent }),
        }
      );

      if (response.ok) {
        fetchGroupDetails(selectedGroupId);
      } else {
        const data = await response.json();
        console.error('Edit failed:', response.status, data);
        setError(data.error || 'Failed to edit message');
      }
    } catch (err) {
      setError('Error editing message');
      console.error('Error editing message:', err);
    }
  };

  const handleExportGroup = async () => {
    if (!selectedGroupId) return;
    
    try {
      const response = await fetch(
        `http://localhost:8000/api/auth/groups/${selectedGroupId}/export/`,
        {
          method: 'GET',
          credentials: 'include',
        }
      );
      
      if (response.ok) {
        const blob = await response.blob();
        
        // Extract filename from content-disposition header
        let filename = `group_export_${selectedGroupId}.docx`;
        const contentDisposition = response.headers.get('content-disposition');
        if (contentDisposition) {
          const match = contentDisposition.match(/filename="(.+?)"/);
          if (match && match[1]) {
            filename = match[1];
          }
        }
        
        // Trigger download
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        const data = await response.json();
        alert('Failed to export group: ' + (data.error || 'Unknown error'));
      }
    } catch (err) {
      console.error('Error exporting group:', err);
      alert('Error exporting group: ' + err.message);
    }
  };

  const getCsrfToken = () => {
    const name = 'csrftoken';
    let cookieValue = null;
    
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + '=') {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  };

  return (
    <div className="group-page">
      {showVisualization ? (
        <AdminVisualization onClose={() => setShowVisualization(false)} />
      ) : (
        <>
      <div className="group-header">
        <div className="header-logo">
          <img src="/logo.png" alt="Leav" className="logo-img" />
          <h1>{user ? user.first_name + t('groups_title') : 'Groups'}</h1>
        </div>
        <div className="header-actions">
          <span className="user-info">{user?.username}</span>
          <button className="btn-language" onClick={toggleLanguage} title="Toggle language">
            🌐 {language.toUpperCase()}
          </button>
          {user?.role === 'admin' && (
            <>
              <button 
                className="btn-visualization" 
                onClick={() => setShowVisualization(true)}
                title="View system visualization"
              >
                📊 {t('groups_visualize')}
              </button>
              <button 
                className="btn-records" 
                onClick={() => setShowAuditLogs(true)}
                title="View audit logs"
              >
                📋 {t('groups_records')}
              </button>
            </>
          )}
          <button className="btn-logout" onClick={onLogout}>{t('groups_logout')}</button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="group-container">
        <div className="group-sidebar">
          <GroupList 
            groups={groups} 
            selectedGroupId={selectedGroupId}
            onSelectGroup={handleGroupSelect}
            onRefresh={fetchGroups}
            currentUserRole={user?.role}
            currentUserId={user?.id}
          />
        </div>

        <div className="group-main">
          {selectedGroup ? (
            <>
              <div className="group-header-bar">
                <div className="header-left">
                  <h2>{selectedGroup.name}</h2>
                  <p className="group-description">{selectedGroup.description}</p>
                </div>
                {(user?.role === 'admin' || user?.role === 'teacher' || members.find(m => m.user === user?.id)?.role === 'moderator' || members.find(m => m.user === user?.id)?.role === 'teacher_moderator') && (
                  <button className="btn-export" onClick={handleExportGroup} title="Export group to DOCX">
                    📄 {t('groups_export')}
                  </button>
                )}
              </div>

              <div className="group-content">
                <div className="messages-section">
                  <MessageList 
                    messages={messages}
                    currentUserId={user?.id}
                    currentUserRole={user?.role}
                    currentUserGroupRole={members.find(m => m.user === user?.id)?.role}
                    onDeleteMessage={handleDeleteMessage}
                    onEditMessage={handleEditMessage}
                  />
                  <MessageInput 
                    onSendMessage={handleSendMessage}
                    isMuted={members.some(m => m.user === user?.id && m.is_muted)}
                  />
                </div>

                <div className="members-section">
                  <MembersList 
                    members={members}
                    groupId={selectedGroupId}
                    currentUserRole={user?.role}
                    currentUserId={user?.id}
                    isTeacherGroup={selectedGroup?.is_teacher_group}
                    onMembersChange={handleRefreshMembers}
                  />
                </div>
              </div>
            </>
          ) : (
            <div className="no-group-selected">
              <p>{t('no_group_selected')}</p>
            </div>
          )}
        </div>
      </div>
        </>
      )}
      <AuditLogs isOpen={showAuditLogs} onClose={() => setShowAuditLogs(false)} />
    </div>
  );
}

export default GroupPage;
