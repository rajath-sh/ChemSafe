import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Badge } from '../components/ui/Badge';
import { Mail, Phone, ShieldAlert, User, Briefcase, Edit, Check, X } from 'lucide-react';
import './Staff.css';

export const Staff = () => {
  const { apiFetch, currentUser } = useAuth();
  const [staffList, setStaffList] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);

  const [searchQuery, setSearchQuery] = useState('');
  const [editingPhoneId, setEditingPhoneId] = useState(null);
  const [tempPhone, setTempPhone] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const [staffData, incidentsData] = await Promise.all([
        apiFetch('/api/staff'),
        apiFetch('/api/incidents')
      ]);
      setStaffList(staffData);
      setIncidents(incidentsData.filter(i => i.status !== 'resolved' && i.status !== 'closed'));
    } catch (err) {
      console.error("Failed to fetch staff data:", err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [apiFetch]);

  const handleUpdateAvailability = async (userId, newAvailability) => {
    try {
      await apiFetch(`/api/staff/${userId}`, {
        method: 'PATCH',
        body: JSON.stringify({ availability: newAvailability })
      });
      fetchData(); // Refresh to ensure data is synced
    } catch (err) {
      console.error("Failed to update availability:", err);
      alert("Failed to update status. Check permissions.");
    }
  };

  const handleSavePhone = async (userId, availability, department) => {
    try {
      await apiFetch(`/api/staff/${userId}`, {
        method: 'PATCH',
        body: JSON.stringify({ 
          availability: availability,
          department: department,
          phone: tempPhone 
        })
      });
      setEditingPhoneId(null);
      fetchData();
    } catch (err) {
      console.error("Failed to update phone number:", err);
      alert("Failed to update phone number. Check permissions.");
    }
  };

  const getInitials = (name) => {
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  };

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading Personnel Data...</div>;
  }

  // Calculate dynamic statuses for all staff
  const staffWithStatus = staffList.map(staff => {
    const activeIncident = incidents.find(i => i.assigned_staff_id === staff.user_id);
    let visualStatus = staff.availability;
    if (activeIncident && staff.availability === 'available') {
      visualStatus = 'busy';
    }
    return { ...staff, visualStatus, activeIncident };
  });

  // Calculate Stats
  const stats = {
    total: staffWithStatus.length,
    available: staffWithStatus.filter(s => s.visualStatus === 'available').length,
    busy: staffWithStatus.filter(s => s.visualStatus === 'busy').length,
    offline: staffWithStatus.filter(s => s.visualStatus === 'offline').length,
    onLeave: staffWithStatus.filter(s => s.visualStatus === 'on_leave').length,
  };

  // Filter staff based on search query
  const filteredStaff = staffWithStatus.filter(staff => {
    const query = searchQuery.toLowerCase();
    return (
      staff.name.toLowerCase().includes(query) ||
      (staff.department && staff.department.toLowerCase().includes(query)) ||
      staff.visualStatus.toLowerCase().includes(query)
    );
  });

  return (
    <div className="staff-page">
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Workforce Management</h2>
          <p style={{ color: 'var(--text-muted)' }}>View live personnel status and manage active incident responders.</p>
        </div>
      </div>

      {/* Stats Row */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <div className="glass-panel" style={{ padding: '16px', flex: 1, minWidth: '150px', textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--color-primary)' }}>{stats.total}</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Total Staff</div>
        </div>
        <div className="glass-panel" style={{ padding: '16px', flex: 1, minWidth: '150px', textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--color-safe)' }}>{stats.available}</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Available</div>
        </div>
        <div className="glass-panel" style={{ padding: '16px', flex: 1, minWidth: '150px', textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--color-warning)' }}>{stats.busy}</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Busy / Responding</div>
        </div>
        <div className="glass-panel" style={{ padding: '16px', flex: 1, minWidth: '150px', textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--text-muted)' }}>{stats.offline}</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Offline</div>
        </div>
        <div className="glass-panel" style={{ padding: '16px', flex: 1, minWidth: '150px', textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--color-critical)' }}>{stats.onLeave}</div>
          <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>On Leave</div>
        </div>
      </div>

      {/* Search Bar */}
      <div style={{ marginBottom: '24px' }}>
        <input 
          type="text" 
          placeholder="Search by name, department, or status (e.g. 'available', 'busy')..." 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            width: '100%',
            maxWidth: '500px',
            padding: '12px 16px',
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.2)',
            background: 'rgba(0,0,0,0.2)',
            color: 'white',
            outline: 'none',
            fontSize: '1rem'
          }}
        />
      </div>

      <div className="staff-grid">
        {filteredStaff.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', padding: '20px' }}>No personnel match your search.</div>
        ) : (
          filteredStaff.map(staff => {
            const { visualStatus, activeIncident } = staff;

            return (
              <div key={staff.user_id} className={`staff-card status-${visualStatus}`}>
              
              <div className="staff-header">
                <div className="staff-avatar">
                  {getInitials(staff.name)}
                </div>
                <div className="staff-info">
                  <h3>{staff.name}</h3>
                  <p><Briefcase size={12} style={{marginRight: '4px', verticalAlign: 'middle'}}/> {staff.department || 'General Staff'}</p>
                </div>
                <div>
                  <Badge variant={
                    visualStatus === 'available' ? 'safe' : 
                    visualStatus === 'busy' ? 'warning' : 
                    visualStatus === 'offline' ? 'neutral' : 'critical'
                  }>
                    {visualStatus.toUpperCase()}
                  </Badge>
                </div>
              </div>

              <div className="staff-contact">
                <div className="contact-item">
                  <Mail size={14} /> {staff.email}
                </div>
                {(staff.phone || currentUser?.role === 'admin' || currentUser?.user_id === staff.user_id) && (
                  <div className="contact-item" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', minHeight: '28px' }}>
                    {editingPhoneId === staff.user_id ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', width: '100%' }}>
                        <Phone size={14} style={{ flexShrink: 0 }} />
                        <input 
                          type="text" 
                          value={tempPhone} 
                          onChange={(e) => setTempPhone(e.target.value)} 
                          placeholder="Phone number"
                          style={{
                            background: 'rgba(0,0,0,0.4)',
                            border: '1px solid rgba(255,255,255,0.2)',
                            borderRadius: '4px',
                            color: 'white',
                            padding: '2px 6px',
                            fontSize: '0.85rem',
                            width: '120px',
                            outline: 'none'
                          }}
                          autoFocus
                        />
                        <button 
                          onClick={() => handleSavePhone(staff.user_id, staff.availability, staff.department)}
                          style={{ background: 'none', border: 'none', color: '#10b981', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: '2px' }}
                          title="Save"
                        >
                          <Check size={14} />
                        </button>
                        <button 
                          onClick={() => setEditingPhoneId(null)}
                          style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: '2px' }}
                          title="Cancel"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ) : (
                      <>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Phone size={14} /> 
                          <span style={{ color: staff.phone ? 'inherit' : 'var(--text-muted)', fontStyle: staff.phone ? 'normal' : 'italic' }}>
                            {staff.phone || 'No phone number'}
                          </span>
                        </div>
                        {(currentUser?.role === 'admin' || currentUser?.user_id === staff.user_id) && (
                          <button 
                            onClick={() => {
                              setEditingPhoneId(staff.user_id);
                              setTempPhone(staff.phone || '');
                            }}
                            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', opacity: 0.7 }}
                            title="Edit Phone Number"
                          >
                            <Edit size={12} />
                          </button>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>

              {activeIncident && (
                <div className="staff-active-incident">
                  <div className="incident-badge">
                    <ShieldAlert size={14} /> Actively Responding
                  </div>
                  <div><strong>{activeIncident.title}</strong> in {activeIncident.lab_id}</div>
                </div>
              )}

              {/* Admin Controls */}
              {currentUser?.role === 'admin' && (
                <div className="staff-controls">
                  <label>Override Status:</label>
                  <select 
                    value={staff.availability}
                    onChange={(e) => handleUpdateAvailability(staff.user_id, e.target.value)}
                  >
                    <option value="available">Available</option>
                    <option value="offline">Offline</option>
                    <option value="on_leave">On Leave</option>
                    <option value="busy">Busy</option>
                  </select>
                </div>
              )}

            </div>
          );
        })
        )}
      </div>
    </div>
  );
};
