import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Badge } from '../components/ui/Badge';
import { 
  AlertTriangle, 
  ShieldAlert, 
  Activity, 
  CheckCircle2, 
  ArrowRight,
  Clock
} from 'lucide-react';
import './AlertsIncidents.css';

export const AlertsIncidents = () => {
  const { apiFetch, currentUser } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [staffUsers, setStaffUsers] = useState([]);
  const [labs, setLabs] = useState([]);
  
  const [loading, setLoading] = useState(true);

  const fetchData = async (showSpinner = true) => {
    if (showSpinner) setLoading(true);
    try {
      // 1. Fetch Alerts
      const alertsData = await apiFetch('/api/alerts');
      // 2. Fetch Anomalies
      const anomaliesData = await apiFetch('/api/alerts/anomalies');
      
      // Combine them for the feed
      const combinedFeed = [
        ...alertsData.map(a => ({ ...a, feed_type: 'alert' })),
        ...anomaliesData.map(a => ({ ...a, feed_type: 'anomaly', created_at: a.timestamp }))
      ].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      
      setAlerts(combinedFeed);

      // 3. Fetch Incidents
      const incidentsData = await apiFetch('/api/incidents');
      setIncidents(incidentsData);

      // 4. Fetch Staff for Assignment Dropdown
      const staffData = await apiFetch('/api/staff');
      setStaffUsers(staffData);

      // 5. Fetch Labs/Nodes
      const labsData = await apiFetch('/api/sensors/labs');
      setLabs(labsData);

    } catch (err) {
      console.error("Failed to fetch data:", err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => {
      // Fetch without triggering the full loading state spinner
      fetchData(false);
    }, 2000);
    return () => clearInterval(interval);
  }, [apiFetch]);

  const handleConvert = async (item) => {
    try {
      // 1. Create Incident
      const response = await apiFetch('/api/incidents', {
        method: 'POST',
        body: JSON.stringify({
          lab_id: item.lab_id,
          title: `Escalated: ${item.feed_type === 'alert' ? item.alert_type : 'Anomaly'} Issue`,
          description: item.message || item.description || `Converted from ${item.feed_type}`,
          severity: item.severity,
          alert_id: item.alert_id || item.anomaly_id
        })
      });
      
      // 2. Update Alert Status (if it's a standard alert)
      if (item.feed_type === 'alert' && response) {
        await apiFetch(`/api/alerts/${item.alert_id}/convert`, { method: 'PATCH' });
      }

      // Refresh data
      fetchData();
    } catch (err) {
      console.error("Failed to convert:", err);
      alert("Failed to convert to incident. Please check the console.");
    }
  };

  const handleDismiss = async (item) => {
    try {
      if (item.feed_type === 'alert') {
        await apiFetch(`/api/alerts/${item.alert_id}/close`, { method: 'PATCH' });
      } else {
        // Temporarily, just remove anomalies from UI state or call backend if implemented
        // We will filter it out of the UI locally for now
        setAlerts(alerts.filter(a => a !== item));
      }
      fetchData();
    } catch (err) {
      console.error("Failed to dismiss:", err);
    }
  };

  const handleClearAll = async () => {
    try {
      const now = new Date().toISOString();
      await apiFetch(`/api/alerts/history?before=${now}`, { method: 'DELETE' });
      setAlerts([]); // Clear UI immediately
      fetchData();
    } catch (err) {
      console.error("Failed to clear alerts:", err);
    }
  };

  const handleAssignStaff = async (incidentId, staffId) => {
    try {
      await apiFetch(`/api/incidents/${incidentId}`, {
        method: 'PATCH',
        body: JSON.stringify({ assigned_staff_id: staffId })
      });
      fetchData();
    } catch (err) {
      console.error("Failed to assign staff:", err);
    }
  };

  const handleUpdateIncidentStatus = async (incidentId, status) => {
    let payload = { status };
    if (status === 'resolved') {
      const summary = window.prompt("Please provide a brief description of how you resolved this incident:");
      if (summary === null) return; // User cancelled
      if (summary.trim() === '') {
        alert("A resolution summary is required to mark the incident as resolved.");
        return;
      }
      payload.resolution_summary = summary;
    }

    try {
      await apiFetch(`/api/incidents/${incidentId}`, {
        method: 'PATCH',
        body: JSON.stringify(payload)
      });
      fetchData();
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  };

  const handleClearIncidents = async () => {
    try {
      const now = new Date().toISOString();
      await apiFetch(`/api/incidents/history?before=${now}`, { method: 'DELETE' });
      setIncidents([]);
      fetchData();
    } catch (err) {
      console.error("Failed to clear incidents:", err);
    }
  };

  const handleDeleteIncident = async (incidentId) => {
    try {
      await apiFetch(`/api/incidents/${incidentId}`, { method: 'DELETE' });
      fetchData();
    } catch (err) {
      console.error("Failed to delete incident:", err);
    }
  };

  const handleUpdateDescription = async (incidentId, newDescription) => {
    try {
      await apiFetch(`/api/incidents/${incidentId}`, {
        method: 'PATCH',
        body: JSON.stringify({ description: newDescription })
      });
      fetchData();
    } catch (err) {
      console.error("Failed to update description:", err);
    }
  };

  const handleRejectIncident = async (incidentId) => {
    const reason = window.prompt("Please provide a reason for rejecting this assignment:");
    if (!reason) return; // User cancelled
    
    try {
      await apiFetch(`/api/incidents/${incidentId}`, {
        method: 'PATCH',
        body: JSON.stringify({ 
          status: 'open',
          assigned_staff_id: null,
          rejection_reason: `${currentUser.name}|${reason}`
        })
      });
      fetchData();
    } catch (err) {
      console.error("Failed to reject incident:", err);
    }
  };

  return (
    <div className="alerts-incidents-page">
      <div>
        <h2>Command Center: Alerts & Incidents</h2>
        <p>Monitor real-time machine signals and manage human response workflows.</p>
      </div>

      <div className="ai-layout">
        
        {/* LEFT PANEL: 30% Alert Feed */}
        <div className="alerts-feed">
          <div className="feed-header">
            <h3><Activity size={20} color="var(--color-warning)" /> Live Alert Feed</h3>
            <div style={{display: 'flex', gap: '8px', alignItems: 'center'}}>
              <Badge variant="neutral">{alerts.filter(a => a.status !== 'closed' && a.status !== 'converted_to_incident').length}</Badge>
              {currentUser.role === 'admin' && (
                <button className="btn-secondary" style={{padding: '2px 8px', fontSize: '0.75rem'}} onClick={handleClearAll}>
                  Clear All
                </button>
              )}
            </div>
          </div>
          
          <div className="feed-content">
            {loading ? (
              <div style={{color: 'var(--text-muted)', textAlign: 'center', marginTop: '20px'}}>Loading Feed...</div>
            ) : alerts.filter(a => a.status !== 'closed' && a.status !== 'converted_to_incident').length === 0 ? (
              <div style={{color: 'var(--text-muted)', textAlign: 'center', marginTop: '20px'}}>No alerts found.</div>
            ) : (
              alerts.filter(a => a.status !== 'closed' && a.status !== 'converted_to_incident').map((item, idx) => {
                const isAnomaly = item.feed_type === 'anomaly';
                // Calculated False Alert Logic
                const isFalseAlert = isAnomaly && item.confidence < 40;

                return (
                  <div key={idx} className={`alert-item ${isFalseAlert ? 'false-alert' : ''}`}>
                    <div className="alert-header">
                      <span><strong>{item.lab_id}</strong> {labs.find(l => l.lab_id === item.lab_id)?.lab_name ? `(${labs.find(l => l.lab_id === item.lab_id).lab_name})` : ''} • {new Date(item.created_at).toLocaleTimeString()}</span>
                      {isFalseAlert && <Badge variant="neutral">Calculated False Alert</Badge>}
                      {!isFalseAlert && (
                        <Badge variant={item.severity === 'critical' ? 'critical' : 'warning'}>
                          {item.severity.toUpperCase()}
                        </Badge>
                      )}
                    </div>
                    
                    <div className="alert-message">
                      {isAnomaly ? item.description : item.message}
                      {isAnomaly && <div style={{fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px'}}>
                        Confidence Score: {item.confidence}%
                      </div>}
                    </div>

                    {(item.status === 'active' || isAnomaly) && (
                      <div className="alert-actions">
                        {currentUser.role === 'admin' && (
                          <>
                            <button 
                              className="btn-secondary" 
                              onClick={() => handleDismiss(item)}
                            >
                              Dismiss
                            </button>
                            {!isFalseAlert && (
                              <button 
                                className="btn-primary" 
                                style={{display: 'flex', alignItems: 'center', gap: '4px'}}
                                onClick={() => handleConvert(item)}
                              >
                                Convert to Incident <ArrowRight size={14} />
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* RIGHT PANEL: 70% Incident Board */}
        <div className="incidents-board">
          <div className="board-header">
            <h3><ShieldAlert size={20} color="var(--color-primary)" /> Incident Board</h3>
            <div style={{display: 'flex', gap: '8px'}}>
              <button className="btn-secondary" onClick={fetchData}>Refresh Board</button>
              {currentUser.role === 'admin' && (
                <button className="btn-secondary" onClick={handleClearIncidents}>Clear All Incidents</button>
              )}
            </div>
          </div>

          <div className="board-content">
            {loading ? (
              <div style={{color: 'var(--text-muted)', textAlign: 'center', marginTop: '20px'}}>Loading Incidents...</div>
            ) : incidents.length === 0 ? (
              <div style={{color: 'var(--text-muted)', textAlign: 'center', marginTop: '40px'}}>
                <CheckCircle2 size={48} style={{opacity: 0.2, marginBottom: '16px'}} />
                <div>No active incidents requiring attention.</div>
              </div>
            ) : (
              incidents.map(inc => {
                // Find users currently assigned to an active incident
                const assignedStaffIds = incidents
                  .filter(i => i.status !== 'resolved' && i.assigned_staff_id)
                  .map(i => i.assigned_staff_id);

                return (
                  <div key={inc.incident_id} className="incident-card" style={inc.rejection_reason ? { borderLeft: '4px solid var(--color-critical)' } : {}}>
                    
                    <div className="incident-card-top">
                      <div>
                        <div className="incident-title">{inc.title}</div>
                        <div className="incident-meta">
                          <span><Clock size={14}/> {new Date(inc.created_at).toLocaleString()}</span>
                          <span>Loc: <strong>{inc.lab_id}</strong> {labs.find(l => l.lab_id === inc.lab_id)?.lab_name ? `(${labs.find(l => l.lab_id === inc.lab_id).lab_name})` : ''}</span>
                        </div>
                      </div>
                      <div style={{display: 'flex', gap: '8px'}}>
                        <Badge variant={inc.severity === 'critical' ? 'critical' : 'warning'}>
                          {inc.severity.toUpperCase()}
                        </Badge>
                        <Badge variant={inc.status === 'resolved' ? 'safe' : 'neutral'}>
                          {inc.status.toUpperCase()}
                        </Badge>
                        {currentUser.role === 'admin' && (
                          <button className="btn-secondary" style={{padding: '2px 8px'}} onClick={() => handleDeleteIncident(inc.incident_id)}>
                            Delete
                          </button>
                        )}
                      </div>
                    </div>

                    {inc.rejection_reason && (
                      <div style={{background: 'rgba(239, 68, 68, 0.1)', padding: '12px', borderRadius: '6px', border: '1px solid var(--color-critical)'}}>
                        <strong style={{color: 'var(--color-critical)'}}>Rejected by {inc.rejection_reason.includes('|') ? inc.rejection_reason.split('|')[0] : 'previous assignee'}:</strong> {inc.rejection_reason.includes('|') ? inc.rejection_reason.split('|')[1] : inc.rejection_reason}
                      </div>
                    )}

                    <div className="incident-description" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {currentUser.role === 'admin' ? (
                        <textarea 
                          style={{width: '100%', background: 'transparent', color: 'white', border: '1px solid rgba(255,255,255,0.2)', padding: '8px', borderRadius: '4px', minHeight: '60px'}}
                          defaultValue={inc.description || ""}
                          placeholder="Add instructions for staff here..."
                          onBlur={(e) => handleUpdateDescription(inc.incident_id, e.target.value)}
                        />
                      ) : (
                        <div>{inc.description || "No description provided."}</div>
                      )}
                      
                      {inc.resolution_summary && (
                        <div style={{background: 'rgba(59, 130, 246, 0.1)', padding: '8px 12px', borderRadius: '6px', borderLeft: '3px solid var(--color-primary)', marginTop: '8px', fontSize: '0.9rem'}}>
                          <strong>Resolution Notes:</strong> {inc.resolution_summary}
                        </div>
                      )}
                    </div>

                    <div className="incident-controls">
                      {/* Staff Assignment */}
                      <div className="staff-assignment">
                        <span style={{fontSize: '0.85rem', color: 'var(--text-muted)'}}>Assignee:</span>
                        {currentUser.role === 'admin' ? (
                          <select 
                            value={inc.assigned_staff_id || ''} 
                            onChange={(e) => handleAssignStaff(inc.incident_id, e.target.value)}
                            disabled={inc.status === 'resolved'}
                          >
                            <option value="">-- Unassigned --</option>
                            {staffUsers.filter(u => u.availability === 'available' || u.user_id === inc.assigned_staff_id).map(u => {
                              // If this user is assigned to ANOTHER active incident, disable them
                              const isBusy = assignedStaffIds.includes(u.user_id) && inc.assigned_staff_id !== u.user_id;
                              return (
                                <option key={u.user_id} value={u.user_id} disabled={isBusy}>
                                  {u.name} ({u.role || u.department || 'Staff'}) {isBusy ? '- BUSY' : ''}
                                </option>
                              );
                            })}
                          </select>
                        ) : (
                          <span style={{fontWeight: '500', color: 'white'}}>
                            {staffUsers.find(u => u.user_id === inc.assigned_staff_id)?.name || 'Unassigned'}
                          </span>
                        )}
                      </div>

                      {/* Status Controls */}
                      <div className="status-controls">
                        {/* Only the ASSIGNED staff member can change status */}
                        {currentUser.role !== 'admin' && currentUser.user_id === inc.assigned_staff_id && inc.status !== 'resolved' && (
                          <>
                            {inc.status === 'open' ? (
                              <>
                                <button className="btn-secondary" onClick={() => handleRejectIncident(inc.incident_id)} style={{color: 'var(--color-critical)'}}>
                                  Reject
                                </button>
                                <button className="btn-primary" onClick={() => handleUpdateIncidentStatus(inc.incident_id, 'in_progress')}>
                                  Accept & Start
                                </button>
                              </>
                            ) : (
                              <button 
                                className="btn-primary"
                                onClick={() => handleUpdateIncidentStatus(inc.incident_id, 'resolved')}
                              >
                                Mark Resolved
                              </button>
                            )}
                          </>
                        )}
                        {currentUser.role === 'admin' && inc.assigned_staff_id && inc.status === 'open' && (
                          <span style={{color: 'var(--text-muted)', fontSize: '0.85rem'}}>Waiting for staff to accept...</span>
                        )}
                      </div>
                    </div>

                  </div>
                );
              })
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
