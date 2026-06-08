import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Server, Bell, Shield, Database, Save, CheckCircle2 } from 'lucide-react';
import './Settings.css';

export const Settings = () => {
  const { apiFetch, currentUser } = useAuth();
  
  const [settings, setSettings] = useState({
    mqtt_broker_url: '',
    global_notifications_enabled: true,
    strict_mode_enabled: false,
    data_retention_days: 30
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await apiFetch('/api/settings');
        setSettings(data);
      } catch (err) {
        console.error("Failed to load settings:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, [apiFetch]);

  const handleToggle = (field) => {
    setSettings(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveSuccess(false);
    try {
      await apiFetch('/api/settings', {
        method: 'PATCH',
        body: JSON.stringify(settings)
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      alert("Failed to save settings: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  if (currentUser?.role !== 'admin') {
    return (
      <div className="page-header">
        <h2>Access Denied</h2>
        <p>You do not have permission to view system settings.</p>
      </div>
    );
  }

  if (loading) {
    return <div style={{padding: '24px'}}>Loading configuration...</div>;
  }

  return (
    <div className="settings-page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>System Settings</h2>
          <p>Global configuration for ChemSafe IoT. Changes apply immediately across the entire network.</p>
        </div>
        <Button 
          onClick={handleSave} 
          disabled={saving}
          style={{ display: 'flex', alignItems: 'center', gap: '8px', transition: '0.3s' }}
        >
          {saving ? 'Saving...' : saveSuccess ? <><CheckCircle2 size={16}/> Saved</> : <><Save size={16}/> Save Changes</>}
        </Button>
      </div>

      <div className="settings-grid">
        
        {/* Network Configuration */}
        <Card className="settings-card">
          <div className="card-icon-header">
            <Server size={24} color="var(--color-primary)" />
            <h3>IoT Network</h3>
          </div>
          <p className="settings-desc">Configure the connection to the MQTT message broker responsible for ingesting live sensor data.</p>
          
          <div className="form-group">
            <label>MQTT Broker URL</label>
            <input 
              type="text" 
              value={settings.mqtt_broker_url} 
              onChange={e => setSettings({...settings, mqtt_broker_url: e.target.value})}
              placeholder="e.g., broker.hivemq.com or localhost"
              className="settings-input"
            />
          </div>
        </Card>

        {/* Global Operations */}
        <Card className="settings-card">
          <div className="card-icon-header">
            <Bell size={24} color="var(--color-warning)" />
            <h3>System Operations</h3>
          </div>
          <p className="settings-desc">Manage global behavior, including emergency broadcast overrides and strict compliance protocols.</p>
          
          <div className="setting-toggle-row" onClick={() => handleToggle('global_notifications_enabled')}>
            <div className="toggle-info">
              <h4>Global Push Notifications</h4>
              <p>When disabled, all push alerts to staff devices are paused (useful for maintenance).</p>
            </div>
            <div className={`switch ${settings.global_notifications_enabled ? 'active' : ''}`}>
              <div className="switch-thumb"></div>
            </div>
          </div>

          <div className="setting-toggle-row" onClick={() => handleToggle('strict_mode_enabled')}>
            <div className="toggle-info">
              <h4>Strict Compliance Mode <Shield size={14} style={{display:'inline', marginLeft: '4px', verticalAlign: 'text-bottom'}}/></h4>
              <p>Enforces maximum security rules (e.g., disables anonymous alert dismissal).</p>
            </div>
            <div className={`switch ${settings.strict_mode_enabled ? 'active-critical' : ''}`}>
              <div className="switch-thumb"></div>
            </div>
          </div>
        </Card>

        {/* Data Management */}
        <Card className="settings-card">
          <div className="card-icon-header">
            <Database size={24} color="var(--color-safe)" />
            <h3>Data Management</h3>
          </div>
          <p className="settings-desc">Configure how long historical logs and non-critical data are kept before automatic pruning.</p>
          
          <div className="form-group">
            <label>Incident & Alert Retention (Days)</label>
            <div className="retention-slider-container">
              <input 
                type="range" 
                min="7" 
                max="365" 
                value={settings.data_retention_days} 
                onChange={e => setSettings({...settings, data_retention_days: parseInt(e.target.value)})}
                className="retention-slider"
              />
              <div className="retention-value">{settings.data_retention_days} Days</div>
            </div>
            <div className="slider-labels">
              <span>7 Days</span>
              <span>1 Year</span>
            </div>
          </div>
        </Card>

      </div>
    </div>
  );
};
