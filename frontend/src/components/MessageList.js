import React, { useState } from 'react';
import './MessageList.css';
import { useLanguage } from '../LanguageContext';

function MessageList({ messages, currentUserId, currentUserRole, currentUserGroupRole, onDeleteMessage, onEditMessage }) {
  const { t } = useLanguage();
  const [openMenuId, setOpenMenuId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editContent, setEditContent] = useState('');
  const canDeleteMessage = (message) => {
    return currentUserRole === 'admin' || 
           currentUserRole === 'teacher' || 
           currentUserGroupRole === 'moderator' ||
           message.sender === currentUserId;
  };

  const canEditMessage = (message) => {
    return currentUserRole === 'admin' || currentUserGroupRole === 'moderator' || message.sender === currentUserId;
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getAvatarColor = (username) => {
    const colors = ['#2dd46f', '#10b981', '#06d6a0', '#22a447', '#059669', '#0d8659'];
    let hash = 0;
    for (let i = 0; i < username.length; i++) {
      hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  };

  const getFirstLetter = (firstName) => {
    return firstName ? firstName.charAt(0).toUpperCase() : '?';
  };

  return (
    <div className="message-list">
      {messages.length === 0 ? (
        <div className="no-messages">
          <p>{t('message_no_messages')}</p>
        </div>
      ) : (
        messages.map((message) => (
          <div 
            key={message.id} 
            className={`message ${message.sender === currentUserId ? 'own-message' : ''}`}
          >
            <div className="message-avatar" style={{ backgroundColor: getAvatarColor(message.sender_username) }}>
              {getFirstLetter(message.sender_first_name)}
            </div>
            <div className="message-header">
              <span className="message-sender">
                {message.sender_first_name} {message.sender_last_name} ({message.sender_username})
              </span>
              <span className="message-time">{formatTime(message.created_at)}</span>
            </div>
            <div className="message-content">
              {editingId === message.id ? (
                <div className="edit-message-form">
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="edit-message-input"
                    autoFocus
                  />
                  <div className="edit-message-actions">
                    <button
                      className="btn-save-edit"
                      onClick={() => {
                        if (editContent.trim()) {
                          onEditMessage(message.id, editContent);
                          setEditingId(null);
                          setEditContent('');
                        }
                      }}
                      disabled={!editContent.trim()}
                    >
                      {t('msg_save')}
                    </button>
                    <button
                      className="btn-cancel-edit"
                      onClick={() => {
                        setEditingId(null);
                        setEditContent('');
                      }}
                    >
                      {t('msg_cancel')}
                    </button>
                  </div>
                </div>
              ) : (
                <p>{message.content}</p>
              )}
            </div>
            {canDeleteMessage(message) && (
              <div className="message-menu-container">
                <button 
                  className="btn-message-menu"
                  onClick={() => setOpenMenuId(openMenuId === message.id ? null : message.id)}
                  title="Message options"
                >
                  ⋯
                </button>
                {openMenuId === message.id && (
                  <div className="message-menu-dropdown">
                    {canEditMessage(message) && (
                      <button 
                        className="menu-option"
                        onClick={() => {
                          setEditingId(message.id);
                          setEditContent(message.content);
                          setOpenMenuId(null);
                        }}
                      >
                        {t('msg_edit')}
                      </button>
                    )}
                    <button 
                      className="menu-option menu-option-delete"
                      onClick={() => {
                        onDeleteMessage(message.id);
                        setOpenMenuId(null);
                      }}
                    >
                      {t('msg_delete')}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}

export default MessageList;
