import React, { useState, useEffect, useRef } from 'react';
import { Bell, User, LogOut, Trash2, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './TopBar.css';

export const TopBar = () => {
  const { currentUser, logout, apiFetch } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const fetchNotifications = async () => {
    try {
      const data = await apiFetch('/api/notifications?unread_only=false');
      setNotifications(data);
    } catch (err) {
      console.error("Failed to fetch notifications:", err);
    }
  };

  useEffect(() => {
    fetchNotifications();
    // Poll every 2 seconds for new notifications
    const interval = setInterval(fetchNotifications, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleClearAll = async () => {
    if (currentUser?.role !== 'admin') return;
    try {
      const now = new Date().toISOString();
      await apiFetch(`/api/notifications/history?before=${now}`, { method: 'DELETE' });
      fetchNotifications();
      setIsDropdownOpen(false);
    } catch (err) {
      console.error("Failed to clear notifications:", err);
    }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    try {
      await apiFetch(`/api/notifications/${id}`, { method: 'DELETE' });
      fetchNotifications();
    } catch (err) {
      console.error("Failed to delete notification:", err);
    }
  };

  const handleMarkRead = async (id, isRead) => {
    if (isRead) return;
    try {
      await apiFetch(`/api/notifications/${id}/read`, { method: 'PATCH' });
      fetchNotifications();
    } catch (err) {
      console.error("Failed to mark as read:", err);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <header className="topbar glass-panel">
      <div className="search-container" style={{visibility: 'hidden'}}>
        {/* Removed global search as per user request */}
      </div>
      
      <div className="topbar-actions">
        <div className="notification-wrapper" ref={dropdownRef}>
          <button 
            className={`icon-button notification-btn ${isDropdownOpen ? 'active' : ''}`}
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          >
            <Bell size={20} />
            {unreadCount > 0 && <span className="badge">{unreadCount}</span>}
          </button>
          
          {isDropdownOpen && (
            <div className="notification-dropdown glass-panel">
              <div className="dropdown-header">
                <h4>Notifications</h4>
                {currentUser?.role === 'admin' && notifications.length > 0 && (
                  <button className="clear-all-btn" onClick={handleClearAll}>
                    Clear All
                  </button>
                )}
              </div>
              <div className="dropdown-content">
                {notifications.length === 0 ? (
                  <div className="empty-notifications">
                    <CheckCircle2 size={32} opacity={0.3} />
                    <p>All caught up!</p>
                  </div>
                ) : (
                  notifications.map(notif => (
                    <div 
                      key={notif.notification_id} 
                      className={`notification-item ${notif.is_read ? 'read' : 'unread'}`}
                      onClick={() => handleMarkRead(notif.notification_id, notif.is_read)}
                    >
                      <div className="notification-item-content">
                        <strong>{notif.title}</strong>
                        <p>{notif.message}</p>
                        <span className="notification-time">
                          {new Date(notif.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <button 
                        className="delete-notif-btn"
                        onClick={(e) => handleDelete(e, notif.notification_id)}
                        title="Delete"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
        
        <div className="user-profile">
          <div className="avatar">
            <User size={18} />
          </div>
          <div className="user-info">
            <span className="user-name">{currentUser?.name || 'User'}</span>
            <span className="user-role">{currentUser?.role?.toUpperCase() || 'ROLE'}</span>
          </div>
        </div>

        <button className="icon-button" onClick={logout} title="Logout">
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
};
