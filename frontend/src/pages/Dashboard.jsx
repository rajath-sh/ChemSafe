import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { 
  Activity, 
  ShieldAlert, 
  Users, 
  FlaskConical, 
  AlertTriangle,
  ArrowRight,
  Clock,
  CheckCircle2,
  FileText
} from 'lucide-react';
import './Dashboard.css';

export const Dashboard = () => {
  const { apiFetch, currentUser } = useAuth();
  const navigate = useNavigate();
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        // Fetch snapshot for ALL labs
        const snapshot = await apiFetch('/api/dashboard/ALL');
        setData(snapshot);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
    
    // Poll every 10 seconds for real-time feel
    const interval = setInterval(fetchDashboard, 10000);
    return () => clearInterval(interval);
  }, [apiFetch]);

  if (loading && !data) {
    return <div className="dashboard-loading">Initializing Command Center...</div>;
  }

  if (!data) {
    return <div className="dashboard-error">Failed to connect to Command Center. Please check network.</div>;
  }

  const hasCritical = 
    data.active_alerts.some(a => a.severity === 'critical') || 
    data.open_incidents.some(i => i.severity === 'critical');

  // Combine alerts and incidents into a single unified chronological feed, capped at 5 total items
  const combinedFeed = [
    ...data.open_incidents.map(i => ({ ...i, isIncident: true, sortTime: i.created_at || i.incident_id })),
    ...data.active_alerts.map(a => ({ ...a, isAlert: true, sortTime: a.created_at || a.alert_id }))
  ]
  .sort((a, b) => {
    // If they have created_at strings, we can sort by Date
    if (a.sortTime && b.sortTime && new Date(a.sortTime).getTime() && new Date(b.sortTime).getTime()) {
      return new Date(b.sortTime) - new Date(a.sortTime);
    }
    return 0; // Fallback
  })
  .slice(0, 5);

  return (
    <div className="dashboard-page">
      
      {/* GLOBAL STATUS BANNER */}
      <div className={`global-status-banner ${hasCritical ? 'critical' : 'secure'}`}>
        <div className="banner-content">
          {hasCritical ? (
            <><AlertTriangle size={32} /> <div><strong>SYSTEM ALERT</strong><br/>Critical Incidents Require Immediate Attention</div></>
          ) : (
            <><CheckCircle2 size={32} /> <div><strong>SYSTEM STATUS: SECURE</strong><br/>All monitored locations are operating within normal parameters.</div></>
          )}
        </div>
        <div className="banner-time">
          {new Date().toLocaleString()}
        </div>
      </div>

      {/* QUICK KPI CARDS */}
      <div className="kpi-grid">
        <Card className="kpi-card">
          <div className="kpi-icon"><Activity size={24} color="var(--color-primary)" /></div>
          <div className="kpi-data">
            <h3>{data.total_active_sensors}</h3>
            <p>Active Sensors</p>
          </div>
        </Card>
        
        <Card className="kpi-card">
          <div className="kpi-icon"><FlaskConical size={24} color="var(--color-safe)" /></div>
          <div className="kpi-data">
            <h3>{data.total_chemicals}</h3>
            <p>Registered Chemicals</p>
          </div>
        </Card>

        <Card className="kpi-card">
          <div className="kpi-icon"><Users size={24} color="#a855f7" /></div>
          <div className="kpi-data">
            <h3>{data.available_staff}</h3>
            <p>Available Staff</p>
          </div>
        </Card>

        <Card className="kpi-card" style={data.active_alerts.length > 0 ? { borderLeft: '4px solid var(--color-warning)' } : {}}>
          <div className="kpi-icon"><ShieldAlert size={24} color="var(--color-warning)" /></div>
          <div className="kpi-data">
            <h3>{data.active_alerts.length}</h3>
            <p>Active Alerts</p>
          </div>
        </Card>
      </div>

      {/* QUICK ACTIONS ROW */}
      <div className="quick-actions-row">
        <button className="action-btn-row" onClick={() => navigate('/alerts')}>
          <ShieldAlert size={18}/> Log Incident
        </button>
        <button className="action-btn-row" onClick={() => navigate('/inventory')}>
          <FlaskConical size={18}/> Manage Chemicals
        </button>
        <button className="action-btn-row" onClick={() => navigate('/reports')}>
          <FileText size={18}/> Generate Report
        </button>
        {currentUser.role === 'admin' && (
          <button className="action-btn-row" onClick={() => navigate('/staff')}>
            <Users size={18}/> Assign Staff
          </button>
        )}
      </div>

      {/* SPLIT PANEL FEEDS */}
      <div className="dashboard-split">
        
        {/* Priority Action Feed */}
        <div className="panel priority-feed">
          <div className="panel-header">
            <h3>Priority Action Feed</h3>
            <button className="btn-text" onClick={() => navigate('/alerts')}>View All <ArrowRight size={14}/></button>
          </div>
          
          <div className="feed-list">
            {data.open_incidents.length === 0 && data.active_alerts.length === 0 ? (
              <div className="empty-state">No active incidents or alerts. Everything is quiet.</div>
            ) : (
              <>
                {combinedFeed.map((item, idx) => {
                  if (item.isIncident) {
                    return (
                      <div key={`inc-${item.incident_id}-${idx}`} className="feed-item incident-item">
                        <div className="feed-item-top">
                          <Badge variant={item.severity === 'critical' ? 'critical' : 'warning'}>INCIDENT</Badge>
                          <span className="time-badge"><Clock size={12}/> {item.incident_id}</span>
                        </div>
                        <h4>{item.title}</h4>
                        <div className="feed-meta">Assigned to: {item.assigned_staff_name || 'Unassigned'}</div>
                      </div>
                    );
                  } else {
                    return (
                      <div key={`alr-${item.alert_id}-${idx}`} className="feed-item alert-item">
                        <div className="feed-item-top">
                          <Badge variant="neutral">ALERT</Badge>
                          <span className="time-badge"><AlertTriangle size={12}/> {item.type.toUpperCase()}</span>
                        </div>
                        <h4>{item.message || `Anomaly detected in ${item.type} readings.`}</h4>
                      </div>
                    );
                  }
                })}
              </>
            )}
          </div>
        </div>

        {/* Right Side: Sensors & Quick Actions */}
        <div className="panel-column">
          
          <div className="panel sensor-pulse">
            <div className="panel-header">
              <h3>Sensor Pulse</h3>
              <button className="btn-text" onClick={() => navigate('/sensors')}>Manage <ArrowRight size={14}/></button>
            </div>
            <div className="sensor-list">
              {data.sensors.length === 0 ? (
                <div className="empty-state" style={{padding: '20px 0'}}>No sensors provisioned.</div>
              ) : (
                data.sensors.slice(0, 5).map(sensor => (
                  <div key={sensor.sensor_id} className="sensor-row">
                    <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                      <div className={`status-dot ${sensor.status}`}></div>
                      <div>
                        <strong>{sensor.type.toUpperCase()} SENSOR</strong> <span style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>({sensor.location_name})</span>
                        <div style={{fontSize: '0.8rem', color: 'var(--color-primary)', marginTop: '2px', fontFamily: 'monospace'}}>{sensor.sensor_id}</div>
                      </div>
                    </div>
                    <div className="sensor-value">
                      {sensor.last_reading !== null ? sensor.last_reading : '--'}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};
