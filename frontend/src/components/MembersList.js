import React, { useState, useRef } from 'react';
import ReactDOM from 'react-dom';
import './MembersList.css';
import { getCsrfToken } from '../utils/csrf';
import { useLanguage } from '../LanguageContext';

function MembersList({ members, groupId, currentUserRole, currentUserId, isTeacherGroup, onMembersChange }) {
  const { t } = useLanguage();
  const [showManageModal, setShowManageModal] = useState(false);
  const [allUsers, setAllUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [modalError, setModalError] = useState('');
  const [hoveredMemberId, setHoveredMemberId] = useState(null);
  const [togglingModerator, setTogglingModerator] = useState(null);
  const [togglingMute, setTogglingMute] = useState(null);
  const [cardPosition, setCardPosition] = useState({ top: 0, left: 0 });
  const memberItemRefs = useRef({});
  const hoverTimeoutRef = useRef(null);
  const [searchName, setSearchName] = useState('');
  const [filterGrade, setFilterGrade] = useState('');
  const [filterClass, setFilterClass] = useState('');

  const getRoleColor = (role) => {
    switch(role) {
      case 'admin': return '#ef4444';
      case 'teacher': return '#f59e0b';
      case 'teacher_moderator': return '#2563eb';
      case 'moderator': return '#8b5cf6';
      case 'student': return '#06d6a0';
      default: return '#cccccc';
    }
  };

  const formatRoleName = (role) => {
    return t(`role_${role}`) || role.replace(/_/g, ' ');
  };

  const getFirstLetter = (firstName) => {
    return firstName ? firstName.charAt(0).toUpperCase() : '?';
  };

  const currentUserGroupRole = members.find((m) => m.user === currentUserId)?.role;
  const canManage = isTeacherGroup
    ? currentUserRole === 'admin' || currentUserGroupRole === 'teacher_moderator'
    : currentUserRole === 'admin' || currentUserRole === 'teacher';
  const canMute = isTeacherGroup
    ? currentUserRole === 'admin' || currentUserGroupRole === 'teacher_moderator'
    : currentUserRole === 'admin' || currentUserRole === 'teacher' || currentUserGroupRole === 'moderator';
  const canKick = isTeacherGroup
    ? currentUserRole === 'admin' || currentUserGroupRole === 'teacher_moderator'
    : currentUserRole === 'admin' || currentUserRole === 'teacher' || currentUserGroupRole === 'moderator';
  const canAddMembers = !isTeacherGroup && (currentUserRole === 'admin' || currentUserRole === 'teacher');

  const openManageModal = async () => {
    setLoadingUsers(true);
    setModalError('');
    try {
      const response = await fetch('http://localhost:8000/api/auth/users/', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setAllUsers(data);
        setShowManageModal(true);
      } else {
        setModalError('Failed to load users');
      }
    } catch (err) {
      setModalError('Error loading users');
      console.error('Error:', err);
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleAddMember = async (userId) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/auth/groups/${groupId}/members/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
          },
          credentials: 'include',
          body: JSON.stringify({ user_id: userId }),
        }
      );

      if (response.ok) {
        // Refresh members
        if (onMembersChange) onMembersChange();
        setModalError('');
      } else {
        const data = await response.json();
        setModalError(data.error || 'Failed to add member');
      }
    } catch (err) {
      setModalError('Error adding member');
      console.error('Error:', err);
    }
  };

  const handleRemoveMember = async (userId) => {
    if (!window.confirm('Remove this member from the group?')) return;

    try {
      const response = await fetch(
        `http://localhost:8000/api/auth/groups/${groupId}/members/${userId}/`,
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
        if (onMembersChange) onMembersChange();
        setModalError('');
      } else {
        setModalError('Failed to remove member');
      }
    } catch (err) {
      setModalError('Error removing member');
      console.error('Error:', err);
    }
  };

  const handleToggleModerator = async (userId) => {
    setTogglingModerator(userId);
    try {
      const response = await fetch(
        `http://localhost:8000/api/auth/groups/${groupId}/members/${userId}/moderator/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
          },
          credentials: 'include',
        }
      );

      if (response.ok) {
        if (onMembersChange) onMembersChange();
      } else {
        const data = await response.json();
        console.error('Failed to toggle moderator:', data.error);
      }
    } catch (err) {
      console.error('Error toggling moderator:', err);
    } finally {
      setTogglingModerator(null);
    }
  };

  const handleToggleMute = async (userId) => {
    setTogglingMute(userId);
    try {
      const response = await fetch(
        `http://localhost:8000/api/auth/groups/${groupId}/members/${userId}/mute/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
          },
          credentials: 'include',
        }
      );

      if (response.ok) {
        if (onMembersChange) onMembersChange();
      } else {
        const data = await response.json();
        console.error('Failed to toggle mute:', data.error);
      }
    } catch (err) {
      console.error('Error toggling mute:', err);
    } finally {
      setTogglingMute(null);
    }
  };

  const memberUserIds = members.map((m) => m.user);
  const nonMembers = allUsers.filter((u) => !memberUserIds.includes(u.id));
  const addableUsers = nonMembers.filter((u) => u.role !== 'teacher' && u.role !== 'admin');

  // Filter members by name, grade, and class
  const filteredMembers = members.filter((member) => {
    const fullName = `${member.first_name} ${member.last_name}`.toLowerCase();
    const matchesName = fullName.includes(searchName.toLowerCase());
    const matchesGrade = !filterGrade || member.grade === filterGrade;
    const matchesClass = !filterClass || member.class_number === parseInt(filterClass);
    return matchesName && matchesGrade && matchesClass;
  });

  return (
    <div className="members-list">
      <div className="members-header">
        <h3>{t('groups_members')} ({members.length})</h3>
        {canAddMembers && (
          <button className="btn-manage" onClick={openManageModal} disabled={loadingUsers}>
            <img src="/cog-wheel.png" alt="Manage" className="manage-icon" />
            {t('groups_manage')}
          </button>
        )}
      </div>

      <div className="members-content">
        {members.length === 0 ? (
          <p className="no-members">{t('groups_no_members')}</p>
        ) : (
          members.map((member) => (
            <div 
              key={member.id} 
              className="member-item"
              ref={(el) => memberItemRefs.current[member.id] = el}
              onMouseEnter={() => {
                const el = memberItemRefs.current[member.id];
                if (el) {
                  const rect = el.getBoundingClientRect();
                  setCardPosition({
                    top: rect.top + rect.height / 2,
                    left: rect.left
                  });
                }
                if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
                setHoveredMemberId(member.id);
              }}
              onMouseLeave={() => {
                hoverTimeoutRef.current = setTimeout(() => {
                  setHoveredMemberId(null);
                }, 200);
              }}
            >
              <div className="member-avatar" style={{ backgroundColor: getRoleColor(member.role) }}>
                {getFirstLetter(member.first_name)}
              </div>
              <div className="member-info">
                <p className="member-name">
                  {member.first_name} {member.last_name}
                </p>
                <p className="member-username">@{member.username} {(member.role === 'student' || member.role === 'moderator') && member.grade && `• ${t('member_grade')} ${member.grade}`} {(member.role === 'student' || member.role === 'moderator') && member.class_number && `• #${member.class_number}`}</p>
              </div>
              <div className="member-role-badge" 
                style={{ backgroundColor: getRoleColor(member.role) }}
              >
                {formatRoleName(member.role)}
              </div>

              {hoveredMemberId === member.id && ReactDOM.createPortal(
                <div 
                  className="member-info-card"
                  style={{
                    position: 'fixed',
                    top: `${cardPosition.top}px`,
                    left: `${cardPosition.left - 292}px`,
                    transform: 'translateY(-50%)',
                    zIndex: 99999,
                  }}
                  onMouseEnter={() => {
                    if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
                    setHoveredMemberId(member.id);
                  }}
                  onMouseLeave={() => {
                    hoverTimeoutRef.current = setTimeout(() => {
                      setHoveredMemberId(null);
                    }, 200);
                  }}
                >

                  <div className="card-header">
                    <div className="card-avatar" style={{ backgroundColor: getRoleColor(member.role) }}>
                      {getFirstLetter(member.first_name)}
                    </div>
                    <div className="card-name-section">
                      <h4>{member.first_name} {member.last_name}</h4>
                      <p className="card-username">@{member.username}</p>
                      <p className="card-role" style={{ color: getRoleColor(member.role), fontWeight: 600, margin: 0 }}>{formatRoleName(member.role)}</p>
                    </div>
                  </div>

                  <div className="card-details">
                    <div className="detail-row">
                      <span className="detail-label">{t('member_email')}:</span>
                      <span className="detail-value">{member.email}</span>
                    </div>
                    {(member.role === 'student' || member.role === 'moderator') && (
                      <>
                        <div className="detail-row">
                          <span className="detail-label">{t('member_grade')}:</span>
                          <span className="detail-value">{member.grade || <span style={{color:'#bbb'}}>—</span>}</span>
                        </div>
                        <div className="detail-row">
                          <span className="detail-label">{t('member_class_number')}:</span>
                          <span className="detail-value">{member.class_number || <span style={{color:'#bbb'}}>—</span>}</span>
                        </div>
                      </>
                    )}
                    <div className="detail-row">
                      <span className="detail-label">{t('member_joined')}:</span>
                      <span className="detail-value">{member.joined_at ? new Date(member.joined_at).toLocaleDateString() : <span style={{color:'#bbb'}}>—</span>}</span>
                    </div>
                  </div>

                  {(canManage || canMute || canKick) && (
                    <div className="card-actions">
                      {canManage && (
                        <>
                          {!isTeacherGroup && (currentUserRole === 'admin' || currentUserRole === 'teacher') && member.role !== 'teacher' && member.user !== currentUserId && (
                            <button
                              className="btn-moderator-toggle"
                              onClick={() => handleToggleModerator(member.user)}
                              disabled={togglingModerator === member.user}
                            >
                              {member.role === 'moderator' ? t('btn_remove_moderator') : t('btn_make_moderator')}
                            </button>
                          )}
                          {isTeacherGroup && (currentUserRole === 'admin' || currentUserGroupRole === 'teacher_moderator') && member.role !== 'admin' && member.user !== currentUserId && (
                            <button
                              className="btn-moderator-toggle"
                              onClick={() => handleToggleModerator(member.user)}
                              disabled={togglingModerator === member.user}
                            >
                              {member.role === 'teacher_moderator' ? t('btn_remove_teacher_moderator') : t('btn_make_teacher_moderator')}
                            </button>
                          )}
                        </>
                      )}
                      {canKick && member.user !== currentUserId && member.role !== 'teacher' && member.role !== 'teacher_moderator' && (
                        <button
                          className="btn-remove-member"
                          onClick={() => handleRemoveMember(member.user)}
                        >
                          {t('btn_remove_member')}
                        </button>
                      )}
                      {canMute && member.role === 'student' && member.user !== currentUserId && (
                        <button
                          className="btn-mute-toggle"
                          onClick={() => handleToggleMute(member.user)}
                          disabled={togglingMute === member.user}
                        >
                          {member.is_muted ? t('groups_unmute_member') : t('groups_mute_member')}
                        </button>
                      )}
                    </div>
                  )}
                </div>,
                document.body
              )}
            </div>
          ))
        )}
      </div>

      {showManageModal && (
        <div className="modal-overlay" onClick={() => setShowManageModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{t('modal_manage_members')}</h2>
              <button className="btn-close" onClick={() => setShowManageModal(false)}>×</button>
            </div>

            {modalError && <div className="modal-error">{modalError}</div>}

            <div className="modal-body">
              {/* Search and Filters */}
              <div style={{ marginBottom: '20px', borderBottom: '1px solid #eee', paddingBottom: '15px' }}>
                <input
                  type="text"
                  placeholder={t('search_by_name')}
                  value={searchName}
                  onChange={(e) => setSearchName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    marginBottom: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '14px',
                  }}
                />
                <div style={{ display: 'flex', gap: '10px' }}>
                  <select
                    value={filterGrade}
                    onChange={(e) => setFilterGrade(e.target.value)}
                    style={{
                      flex: 1,
                      padding: '8px 12px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontSize: '14px',
                    }}
                  >
                    <option value="">{t('filter_all_grades')}</option>
                    <option value="12A">12A</option>
                    <option value="12B">12B</option>
                  </select>
                  <select
                    value={filterClass}
                    onChange={(e) => setFilterClass(e.target.value)}
                    style={{
                      flex: 1,
                      padding: '8px 12px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontSize: '14px',
                    }}
                  >
                    <option value="">{t('filter_all_class_numbers')}</option>
                    {[...new Set(members.map(m => m.class_number).filter(Boolean))].sort((a, b) => a - b).map((num) => (
                      <option key={num} value={num}>{num}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Current Members with Edit Capability */}
              {filteredMembers.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                  <h3 style={{ marginTop: 0, marginBottom: '10px', fontSize: '14px', color: '#666' }}>{t('modal_add_members')} ({filteredMembers.length})</h3>
                  <div className="user-list">
                    {filteredMembers.map((member) => (
                      <div key={member.id} className="user-item">
                        <div className="user-info">
                          <span className="user-name">{member.first_name} {member.last_name}</span>
                          {(member.role === 'student' || member.role === 'moderator') && (
                            <span className="user-grade">{t('member_grade')}: {member.grade || 'N/A'} | {t('member_class_number')}: {member.class_number || 'N/A'}</span>
                          )}
                          <span className="user-role">@{member.username} • {t(`role_${member.role}`)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Add New Members Section */}
              {addableUsers.length > 0 && (
                <div>
                  <h3 style={{ marginTop: 0, marginBottom: '10px', fontSize: '14px', color: '#666' }}>{t('modal_add_members')}</h3>
                  {addableUsers.length === 0 ? (
                    <p>{t('modal_all_users_added')}</p>
                  ) : (
                    <div className="user-list">
                      {addableUsers.map((user) => (
                        <div key={user.id} className="user-item">
                          <div className="user-info">
                            <span className="user-name">{user.first_name} {user.last_name}</span>
                            <span className="user-role">@{user.username} • {t(`role_${user.role}`)}</span>
                          </div>
                          <div className="user-btn-col">
                            <button
                              className="btn-add"
                              onClick={() => handleAddMember(user.id)}
                            >
                              {t('btn_add_member')}
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default MembersList;
