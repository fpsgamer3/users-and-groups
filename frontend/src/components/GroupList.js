import React, { useState, useRef } from 'react';
import ReactDOM from 'react-dom';
import './GroupList.css';
import { getCsrfToken } from '../utils/csrf';
import { useLanguage } from '../LanguageContext';

function GroupList({ groups, selectedGroupId, onSelectGroup, onRefresh, currentUserRole, currentUserId }) {
    const { t } = useLanguage();
    const [hoveredGroupId, setHoveredGroupId] = useState(null);
    const [groupCardPos, setGroupCardPos] = useState({ top: 0, left: 0 });
    const groupButtonRefs = useRef({});
    const hoverTimeoutRef = useRef(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupDesc, setNewGroupDesc] = useState('');
  const [selectedTeacherId, setSelectedTeacherId] = useState('');
  const [createError, setCreateError] = useState('');
  const [creating, setCreating] = useState(false);
  const [teachers, setTeachers] = useState([]);
  const [loadingTeachers, setLoadingTeachers] = useState(false);

  const getAvatarColor = (index) => {
    const colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe', '#43e97b'];
    return colors[index % colors.length];
  };

  const getAvatarLetter = (name) => {
    return name.charAt(0).toUpperCase();
  };

  const canManageGroups = currentUserRole === 'admin' || currentUserRole === 'teacher';

  const fetchTeachers = async () => {
    setLoadingTeachers(true);
    try {
      const response = await fetch('http://localhost:8000/api/auth/users/', {
        credentials: 'include',
      });
      if (response.ok) {
        const users = await response.json();
        const teachersList = users.filter(user => user.role === 'teacher');
        setTeachers(teachersList);
      }
    } catch (err) {
      console.error('Error fetching teachers:', err);
    } finally {
      setLoadingTeachers(false);
    }
  };

  const handleOpenCreateModal = () => {
    setShowCreateModal(true);
    if (currentUserRole === 'admin') {
      fetchTeachers();
    }
  };

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) {
      setCreateError('Group name is required');
      return;
    }

    // Admins must select a teacher
    if (currentUserRole === 'admin' && !selectedTeacherId) {
      setCreateError('Please select a teacher to manage this group');
      return;
    }

    setCreating(true);
    setCreateError('');

    try {
      const body = {
        name: newGroupName,
        description: newGroupDesc,
      };

      // Add teacher_id if admin is creating
      if (currentUserRole === 'admin') {
        body.teacher_id = parseInt(selectedTeacherId);
      }

      const response = await fetch('http://localhost:8000/api/auth/groups/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        credentials: 'include',
        body: JSON.stringify(body),
      });

      if (response.ok) {
        setNewGroupName('');
        setNewGroupDesc('');
        setSelectedTeacherId('');
        setShowCreateModal(false);
        onRefresh();
      } else {
        const data = await response.json();
        setCreateError(data.error || 'Failed to create group');
      }
    } catch (err) {
      setCreateError('Error creating group');
      console.error('Error:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteGroup = async (groupId) => {
    if (!window.confirm('Delete this group? This action cannot be undone.')) return;

    try {
      const response = await fetch(
        `http://localhost:8000/api/auth/groups/${groupId}/`,
        {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
          },
          credentials: 'include',
        }
      );

      if (response.ok) {
        onRefresh();
      } else {
        alert('Failed to delete group');
      }
    } catch (err) {
      alert('Error deleting group');
      console.error('Error:', err);
    }
  };

  return (
    <div className="group-list">
      <div className="group-list-header">
        <h3>{t('groups')}</h3>
        <div className="header-actions">
          <button className="btn-refresh" onClick={onRefresh} title="Refresh groups">🔄</button>
          {canManageGroups && (
            <button
              className="btn-create"
              onClick={handleOpenCreateModal}
              title="Create new group"
            >
              {t('grouplist_create_group')}
            </button>
          )}
        </div>
      </div>

      <div className="group-buttons">
        {groups.map((group, index) => (
          (() => {
            const currentUserGroupRole = group.members.find((m) => m.user === currentUserId)?.role;
            const canDeleteGroup = group.is_teacher_group
              ? currentUserRole === 'admin' || currentUserGroupRole === 'teacher_moderator'
              : currentUserRole === 'admin' || group.created_by === currentUserId;
            const isActive = String(selectedGroupId) === String(group.id);
            return (
          <div
            key={group.id}
            className="group-button-wrapper"
            ref={el => groupButtonRefs.current[group.id] = el}
            onMouseEnter={() => {
              const el = groupButtonRefs.current[group.id];
              if (el) {
                const rect = el.getBoundingClientRect();
                setGroupCardPos({
                  top: rect.top + rect.height / 2,
                  left: rect.left
                });
              }
              if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
              setHoveredGroupId(group.id);
            }}
            onMouseLeave={() => {
              hoverTimeoutRef.current = setTimeout(() => {
                setHoveredGroupId(null);
              }, 200);
            }}
          >
            <button
              className={`group-button ${isActive ? 'active' : ''}`}
              onClick={() => onSelectGroup(group.id)}
            >
              <div className="group-avatar" style={{ backgroundColor: getAvatarColor(index) }}>
                {getAvatarLetter(group.name)}
              </div>
              <div className="group-info">
                <p className="group-name">{group.name}</p>
                <p className="group-members">{group.members.length} {t('groups_members').toLowerCase()}</p>
              </div>
            </button>
            {/* Delete button removed from group list, only available in hover menu */}
            {hoveredGroupId === group.id && ReactDOM.createPortal(
              <div
                className="group-info-card"
                style={{
                  position: 'fixed',
                  top: `${groupCardPos.top}px`,
                  left: `${groupCardPos.left + 220}px`,
                  transform: 'translateY(-50%)',
                  zIndex: 99999,
                  minWidth: 260,
                  maxWidth: 340,
                  background: 'white',
                  border: '1px solid #e0e0e0',
                  borderRadius: 10,
                  boxShadow: '0 4px 16px rgba(0,0,0,0.13)',
                  padding: 18,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                }}
                onMouseEnter={() => {
                  if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
                  setHoveredGroupId(group.id);
                }}
                onMouseLeave={() => {
                  hoverTimeoutRef.current = setTimeout(() => {
                    setHoveredGroupId(null);
                  }, 200);
                }}
              >
                <div style={{display:'flex',alignItems:'center',gap:14,marginBottom:8}}>
                  <div className="group-avatar" style={{ backgroundColor: getAvatarColor(index), width:44, height:44, fontSize:22 }}>
                    {getAvatarLetter(group.name)}
                  </div>
                  <div style={{flex:1}}>
                    <h4 style={{margin:'0 0 2px 0',fontSize:15,fontWeight:700}}>{group.name}</h4>
                    <div style={{fontSize:12,color:'#888'}}>{group.members.length} {t('groups_members').toLowerCase()}</div>
                  </div>
                </div>
                <div style={{fontSize:13,marginBottom:6}}><b>{t('group_description')}:</b> {group.description || <span style={{color:'#bbb'}}>—</span>}</div>
                <div style={{fontSize:13,marginBottom:6}}><b>{t('group_created_by')}:</b> {group.created_by_username}</div>
                <div style={{fontSize:13,marginBottom:6}}><b>{t('group_created')}:</b> {group.created_at ? new Date(group.created_at).toLocaleDateString() : <span style={{color:'#bbb'}}>—</span>}</div>
                <div style={{fontSize:13,marginBottom:6}}><b>{t('group_message_count')}:</b> {group.message_count}</div>
                {canDeleteGroup && (
                  <button
                    className="btn-delete-group hover-menu-delete"
                    style={{
                      marginTop: 12,
                      alignSelf: 'flex-end',
                      background: '#ff4d4f',
                      color: 'white',
                      border: 'none',
                      borderRadius: 6,
                      padding: '7px 16px',
                      fontWeight: 600,
                      fontSize: 14,
                      cursor: 'pointer',
                      boxShadow: '0 2px 8px rgba(255,77,79,0.10)',
                      transition: 'background 0.2s',
                    }}
                    onClick={() => handleDeleteGroup(group.id)}
                    onMouseEnter={e => e.target.style.background = '#d9363e'}
                    onMouseLeave={e => e.target.style.background = '#ff4d4f'}
                  >
                    Delete Group
                  </button>
                )}
              </div>,
              document.body
            )}
          </div>
            );
          })()
        ))}
      </div>

      {groups.length === 0 && (
        <div className="no-groups">
          <p>No groups available</p>
        </div>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{t('grouplist_create_new_group')}</h2>
              <button className="btn-close" onClick={() => setShowCreateModal(false)}>×</button>
            </div>

            {createError && <div className="modal-error">{createError}</div>}

            <div className="modal-body">
              <div className="form-group">
                <label>{t('grouplist_group_name')}</label>
                <input
                  type="text"
                  placeholder={t('grouplist_enter_group_name')}
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  disabled={creating}
                />
              </div>

              <div className="form-group">
                <label>{t('grouplist_description')}</label>
                <textarea
                  placeholder={t('grouplist_enter_group_description')}
                  value={newGroupDesc}
                  onChange={(e) => setNewGroupDesc(e.target.value)}
                  disabled={creating}
                  rows="3"
                />
              </div>

              {currentUserRole === 'admin' && (
                <div className="form-group">
                  <label>{t('grouplist_select_teacher')}</label>
                  <select
                    value={selectedTeacherId}
                    onChange={(e) => setSelectedTeacherId(e.target.value)}
                    disabled={creating || loadingTeachers}
                    className="teacher-select"
                  >
                    <option value="">
                      {loadingTeachers ? t('grouplist_loading_teachers') : t('grouplist_choose_teacher')}
                    </option>
                    {teachers.map(teacher => (
                      <option key={teacher.id} value={teacher.id}>
                        {teacher.first_name} {teacher.last_name} ({teacher.username})
                      </option>
                    ))}
                  </select>
                  <small style={{ color: '#666', marginTop: '4px', display: 'block' }}>
                    {t('grouplist_required_teacher')}
                  </small>
                </div>
              )}

              <div className="modal-actions">
                <button
                  className="btn-cancel"
                  onClick={() => setShowCreateModal(false)}
                  disabled={creating}
                >
                  {t('grouplist_button_cancel')}
                </button>
                <button
                  className="btn-create-submit"
                  onClick={handleCreateGroup}
                  disabled={creating}
                >
                  {creating ? t('grouplist_creating') : t('grouplist_button_create')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default GroupList;
