import React, { useState, useEffect } from 'react';
import './AuditLogs.css';
import { useLanguage } from '../LanguageContext';

const AuditLogs = ({ isOpen, onClose }) => {
  const { t } = useLanguage();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsClosing(false);
      fetchAuditLogs();
    }
  }, [isOpen, filter]);

  const handleClose = () => {
    setIsClosing(true);
    // Wait for animation to complete before calling onClose
    setTimeout(() => {
      onClose();
      setIsClosing(false);
    }, 400);
  };

  const fetchAuditLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = filter === 'all' 
        ? '/api/auth/admin/audit-logs/'
        : `/api/auth/admin/audit-logs/?action=${filter}`;
      
      const response = await fetch(url, {
        credentials: 'include',
      });

      if (!response.ok) {
        if (response.status === 403) {
          setError(t('audit_access_denied'));
        } else {
          setError(t('audit_fetch_error'));
        }
        return;
      }

      const data = await response.json();
      setLogs(data.logs || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatDescription = (log) => {
    const key = `audit_desc_${log.action}`;
    const template = t(key);
    if (template === key) return log.description; // fallback to raw if key missing
    return template
      .replace('{user}', log.user_username || log.target_user_username || '')
      .replace('{group}', log.group_name || '');
  };

  const getActionColor = (action) => {
    const colors = {
      'login': '#10b981',
      'logout': '#ef4444',
      'account_create': '#3b82f6',
      'account_delete': '#ef4444',
      'account_update': '#f59e0b',
      'message_send': '#8b5cf6',
      'message_delete': '#ef4444',
      'group_create': '#06b6d4',
      'group_delete': '#ef4444',
      'group_update': '#f59e0b',
      'member_join': '#10b981',
      'member_leave': '#ef4444',
      'member_remove': '#ef4444',
      'role_change': '#f59e0b',
    };
    return colors[action] || '#6b7280';
  };

  if (!isOpen) return null;

  return (
    <div 
      className={`audit-logs-overlay ${isClosing ? 'closing' : ''}`} 
      onClick={handleClose}
    >
      <div 
        className={`audit-logs-modal ${isClosing ? 'closing' : ''}`} 
        onClick={(e) => e.stopPropagation()}
      >
        <div className="audit-logs-header">
          <h2>{t('audit_records')}</h2>
          <button className="close-btn" onClick={handleClose}>×</button>
        </div>

        <div className="audit-logs-filters">
          <label>{t('audit_filter_label')}</label>
          <select 
            value={filter} 
            onChange={(e) => setFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">{t('filter_all_actions')}</option>
            <option value="login">{t('filter_action_login')}</option>
            <option value="logout">{t('filter_action_logout')}</option>
            <option value="account_create">{t('filter_action_account_create')}</option>
            <option value="account_delete">{t('filter_action_account_delete')}</option>
            <option value="account_update">{t('filter_action_account_update')}</option>
            <option value="message_send">{t('filter_action_message_send')}</option>
            <option value="group_create">{t('filter_action_group_create')}</option>
            <option value="member_join">{t('filter_action_member_join')}</option>
            <option value="role_change">{t('filter_action_role_change')}</option>
          </select>
        </div>

        <div className="audit-logs-content">
          {loading ? (
            <div className="loading">{t('audit_loading')}</div>
          ) : error ? (
            <div className="error-message">{error}</div>
          ) : logs.length === 0 ? (
            <div className="empty-state">{t('audit_empty')}</div>
          ) : (
            <div className="logs-list">
              {logs.map((log) => (
                <div key={log.id} className="log-entry">
                  <div className="log-timestamp">{formatTimestamp(log.timestamp)}</div>
                  <div className="log-body">
                    <span 
                      className="log-action" 
                      style={{ backgroundColor: getActionColor(log.action) }}
                    >
                      {t(`audit_action_${log.action}`)}
                    </span>
                    <div className="log-description">{formatDescription(log)}</div>
                    <div className="log-meta">
                      {log.user_username && (
                        <span className="log-user">👤 {log.user_username}</span>
                      )}
                      {log.group_name && (
                        <span className="log-group">{log.group_name}</span>
                      )}
                      {log.target_user_username && (
                        <span className="log-target">⎯→ {log.target_user_username}</span>
                      )}
                      {log.ip_address && (
                        <span className="log-ip">🔗 {log.ip_address}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuditLogs;
