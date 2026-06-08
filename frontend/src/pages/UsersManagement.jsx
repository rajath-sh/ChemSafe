import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Shield, ShieldAlert, User as UserIcon, UserMinus } from 'lucide-react';
import './UsersManagement.css';

export const UsersManagement = () => {
  const { currentUser, apiFetch } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  const [searchQuery, setSearchQuery] = useState('');

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await apiFetch('/api/users');
      setUsers(data);
    } catch (err) {
      console.error("Failed to fetch users:", err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleUpdateRole = async (userId, newRole) => {
    try {
      await apiFetch(`/api/users/${userId}`, {
        method: 'PATCH',
        body: JSON.stringify({ role: newRole })
      });
      fetchUsers();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeactivate = async (userId) => {
    if (window.confirm("Are you sure you want to deactivate this user?")) {
      try {
        await apiFetch(`/api/users/${userId}`, {
          method: 'PATCH',
          body: JSON.stringify({ status: 'inactive' })
        });
        fetchUsers();
      } catch (err) {
        alert(err.message);
      }
    }
  };

  if (currentUser?.role !== 'admin') {
    return (
      <div className="page-header">
        <h2>Access Denied</h2>
        <p>You must be an administrator to view this page.</p>
      </div>
    );
  }

  const filteredUsers = users.filter(user => {
    const q = searchQuery.toLowerCase();
    return user.name.toLowerCase().includes(q) || 
           user.email.toLowerCase().includes(q) || 
           user.role.toLowerCase().includes(q);
  });

  return (
    <div className="users-page">
      <div className="page-header">
        <h2>User Management</h2>
        <p>Manage system access, roles, and staff assignments.</p>
      </div>
      
      <div style={{ marginBottom: '24px' }}>
        <input 
          type="text" 
          placeholder="Search users by name, email, or role..." 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            width: '100%',
            maxWidth: '400px',
            padding: '10px 16px',
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.2)',
            background: 'rgba(0,0,0,0.2)',
            color: 'white',
            outline: 'none',
            fontSize: '1rem'
          }}
        />
      </div>

      <Card>
        {loading ? (
          <div className="loading-state">Loading users...</div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map(user => (
                  <tr key={user.user_id} className={user.status === 'inactive' ? 'inactive-row' : ''}>
                    <td>
                      <div className="user-cell">
                        <div className="user-avatar">
                          {user.role === 'admin' ? <Shield size={16} /> : 
                           user.role === 'staff' ? <ShieldAlert size={16} /> : 
                           <UserIcon size={16} />}
                        </div>
                        <div className="user-info">
                          <span className="user-name">{user.name}</span>
                          <span className="user-email">{user.email}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <Badge variant={
                        user.role === 'admin' ? 'critical' : 
                        user.role === 'staff' ? 'warning' : 'neutral'
                      }>
                        {user.role}
                      </Badge>
                    </td>
                    <td>
                      <Badge variant={user.status === 'active' ? 'safe' : 'neutral'}>
                        {user.status}
                      </Badge>
                    </td>
                    <td>
                      <div className="action-buttons">
                        {user.role !== 'staff' && user.role !== 'admin' && (
                          <Button size="sm" variant="secondary" onClick={() => handleUpdateRole(user.user_id, 'staff')}>
                            Make Staff
                          </Button>
                        )}
                        {user.role !== 'viewer' && user.role !== 'admin' && (
                          <Button size="sm" variant="secondary" onClick={() => handleUpdateRole(user.user_id, 'viewer')}>
                            Make Viewer
                          </Button>
                        )}
                        {user.status === 'active' && user.user_id !== currentUser.user_id && (
                          <Button size="sm" variant="danger" onClick={() => handleDeactivate(user.user_id)}>
                            <UserMinus size={14} />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};
