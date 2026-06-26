import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Activity, Thermometer, Droplets, Wind, Sun, Vibrate, Plus, Trash2, Settings, Search } from 'lucide-react';
import RemoteAlarmToggle from '../components/ui/RemoteAlarmToggle';
import './NodesManagement.css';

const SENSOR_TYPES = ['temperature', 'humidity', 'gas', 'light', 'vibration'];

const SENSOR_ICONS = {
  temperature: <Thermometer size={18} />,
  humidity: <Droplets size={18} />,
  gas: <Wind size={18} />,
  light: <Sun size={18} />,
  vibration: <Vibrate size={18} />
};

export const NodesManagement = () => {
  const { apiFetch, currentUser } = useAuth();
  const [nodes, setNodes] = useState([]);
  const [sensors, setSensors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [hideStaleData, setHideStaleData] = useState(true);

  // Periodic refresh to keep stale checks updated visually
  useEffect(() => {
    const interval = setInterval(() => {
      // Force re-render to update the stale checks
      setSensors(prev => [...prev]);
    }, 5000);
    return () => clearInterval(interval);
  }, []);
  
  // Modal State
  const [showAddModal, setShowAddModal] = useState(false);
  const [newNodeName, setNewNodeName] = useState('');
  const [newNodeLocation, setNewNodeLocation] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchData = async (showSpinner = true) => {
    if (showSpinner) setLoading(true);
    try {
      // In the backend, 'Laboratories' are conceptually our physical ESP32 Nodes
      const [labsData, sensorsData] = await Promise.all([
        apiFetch('/api/sensors/labs'),
        apiFetch('/api/sensors')
      ]);
      setNodes(labsData);
      setSensors(sensorsData);
    } catch (err) {
      console.error("Failed to fetch nodes data:", err);
    }
    if (showSpinner) setLoading(false);
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => {
      fetchData(false);
    }, 2000);
    return () => clearInterval(interval);
  }, [apiFetch]);

  const handleAddNode = async (e) => {
    e.preventDefault();
    if (!newNodeName) return;
    
    setIsSubmitting(true);
    try {
      // 1. Create the physical Node (Lab)
      const newNode = await apiFetch('/api/sensors/labs', {
        method: 'POST',
        body: JSON.stringify({
          lab_name: newNodeName,
          location: newNodeLocation,
          description: 'ESP32 Sensor Node'
        })
      });

      // 2. Automatically provision all 5 mandatory sensors to this node (default offline until hardware posts data)
      await Promise.all(SENSOR_TYPES.map(type => 
        apiFetch('/api/sensors', {
          method: 'POST',
          body: JSON.stringify({
            lab_id: newNode.lab_id,
            sensor_type: type,
            status: 'online'
          })
        })
      ));

      // Close modal and refresh
      setShowAddModal(false);
      setNewNodeName('');
      setNewNodeLocation('');
      fetchData();
      
    } catch (err) {
      alert(err.message);
    }
    setIsSubmitting(false);
  };

  // Group sensors by Node (lab_id)
  const getSensorsForNode = (labId) => {
    return sensors.filter(s => s.lab_id === labId);
  };

  // Update all sensors for a node
  const handleUpdateNodeStatus = async (labId, newStatus) => {
    try {
      const nodeSensors = getSensorsForNode(labId);
      await Promise.all(nodeSensors.map(sensor => 
        apiFetch(`/api/sensors/${sensor.sensor_id}`, {
          method: 'PATCH',
          body: JSON.stringify({ status: newStatus })
        })
      ));
      fetchData();
    } catch (err) {
      alert(err.message);
    }
  };

  // Config Modal State
  const [configNode, setConfigNode] = useState(null);
  const [configThresholds, setConfigThresholds] = useState({});
  const [configActiveSensor, setConfigActiveSensor] = useState('temperature');
  const [isLoadingConfig, setIsLoadingConfig] = useState(false);

  const openConfigModal = async (node) => {
    setConfigNode(node);
    setConfigActiveSensor('temperature');
    setIsLoadingConfig(true);
    
    try {
      const thresholdsData = await apiFetch(`/api/sensors/thresholds/${node.lab_id}`);
      // Convert array to object keyed by sensor_type
      const thresholdsMap = {};
      thresholdsData.forEach(t => {
        thresholdsMap[t.sensor_type] = t;
      });
      setConfigThresholds(thresholdsMap);
    } catch (err) {
      console.error("Failed to fetch thresholds:", err);
    }
    
    setIsLoadingConfig(false);
  };

  const handleSaveSensorConfig = async (e) => {
    e.preventDefault();
    if (!configNode) return;
    
    // Viewers cannot save
    if (currentUser?.role === 'viewer') {
      alert("Viewers do not have permission to modify configuration.");
      return;
    }

    setIsSubmitting(true);
    try {
      // 1. Update Threshold (Admin Only)
      if (currentUser?.role === 'admin') {
        const warningVal = parseFloat(e.target.warning_value.value);
        const criticalVal = parseFloat(e.target.critical_value.value);
        const minValStr = e.target.min_value?.value;
        const maxValStr = e.target.max_value?.value;
        
        if (!isNaN(warningVal) && !isNaN(criticalVal)) {
          await apiFetch('/api/sensors/thresholds', {
            method: 'POST',
            body: JSON.stringify({
              lab_id: configNode.lab_id,
              sensor_type: configActiveSensor,
              warning_value: warningVal,
              critical_value: criticalVal,
              min_value: minValStr ? parseFloat(minValStr) : null,
              max_value: maxValStr ? parseFloat(maxValStr) : null
            })
          });
        }
      }

      // 2. Update Sensor Status (Admin & Staff)
      if (['admin', 'staff'].includes(currentUser?.role)) {
        const newStatus = e.target.sensor_status.value;
        const nodeSensors = getSensorsForNode(configNode.lab_id);
        const targetSensor = nodeSensors.find(s => s.sensor_type === configActiveSensor);
        
        if (targetSensor && targetSensor.status !== newStatus) {
          await apiFetch(`/api/sensors/${targetSensor.sensor_id}`, {
            method: 'PATCH',
            body: JSON.stringify({ status: newStatus })
          });
        }
      }

      // Re-fetch to update UI
      await openConfigModal(configNode);
      await fetchData();
      alert(`Configuration saved for ${configActiveSensor}`);
    } catch (err) {
      alert(err.message);
    }
    setIsSubmitting(false);
  };

  const handleRemoveNode = async (labId) => {
    if (window.confirm("WARNING: Hard deletion will permanently erase this Node and all its historical sensor data. Proceed?")) {
      try {
        await apiFetch(`/api/sensors/labs/${labId}`, { method: 'DELETE' });
        fetchData();
      } catch (err) {
        alert("Failed to delete node: " + err.message);
      }
    }
  };

  const handleGlobalVibration = async (status) => {
    if (window.confirm(`This will turn ${status.toUpperCase()} ALL physical vibration sensors across every ESP32 node simultaneously. Proceed?`)) {
      try {
        await apiFetch(`/api/sensors/vibration/global?status=${status}`, { method: 'POST' });
        await fetchData(); // Refresh UI
      } catch (err) {
        alert("Failed to toggle global vibration: " + err.message);
      }
    }
  };

  // Determine global vibration state
  const vibrationSensors = sensors.filter(s => s.sensor_type === 'vibration');
  const isGlobalVibrationOn = vibrationSensors.length > 0 && vibrationSensors.some(s => s.status === 'online');

  return (
    <div className="nodes-page">
      <div className="page-header flex-between">
        <div>
          <h2>Sensor Nodes</h2>
          <p>Manage ESP32 hardware nodes and their sensors.</p>
        </div>
        <div style={{display: 'flex', gap: '16px', alignItems: 'center'}}>
          <div className="local-search" style={{display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.2)', padding: '6px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)'}}>
            <Search size={16} color="var(--text-muted)" style={{marginRight: '8px'}} />
            <input 
              type="text" 
              placeholder="Search Name or Location..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{background: 'transparent', border: 'none', color: 'white', outline: 'none', fontSize: '0.9rem', width: '200px'}}
            />
          </div>
          {/* <div className="stale-toggle" style={{display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(0,0,0,0.2)', padding: '6px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)'}}>
            <span style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>Hide Disconnected Data</span>
            <div 
              className={`switch ${hideStaleData ? 'active' : ''}`} 
              onClick={() => setHideStaleData(!hideStaleData)}
              style={{ transform: 'scale(0.8)', cursor: 'pointer' }}
            >
              <div className="switch-thumb"></div>
            </div>
          </div> */}
          {/* currentUser?.role === 'admin' && (
            <div className="global-controls" style={{display: 'flex', background: 'rgba(255,255,255,0.05)', padding: '6px 12px', borderRadius: '8px', alignItems: 'center', gap: '12px'}}>
              <span style={{fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px'}}>Master Vibration:</span>
              <Button 
                size="sm" 
                variant={isGlobalVibrationOn ? "danger" : "safe"} 
                onClick={() => handleGlobalVibration(isGlobalVibrationOn ? 'offline' : 'online')}
              >
                {isGlobalVibrationOn ? 'Deactivate All' : 'Activate All'}
              </Button>
            </div>
          ) */ }
          {currentUser?.role === 'admin' && (
            <Button onClick={() => setShowAddModal(true)} variant="primary">
              <Plus size={18} /> Add ESP32 Node
            </Button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="loading-state">Scanning for hardware nodes...</div>
      ) : (
        <div className="nodes-grid">
          {nodes.length === 0 ? (
            <div className="empty-state glass-panel">
              <Activity size={48} className="empty-icon" />
              <h3>No Nodes Configured</h3>
              <p>Click the button above to provision your first ESP32 node.</p>
            </div>
          ) : (
            nodes
              .filter(n => {
                if (!searchQuery) return true;
                const query = searchQuery.toLowerCase();
                const nameMatch = n.lab_name?.toLowerCase().includes(query);
                const locMatch = n.location?.toLowerCase().includes(query);
                return nameMatch || locMatch;
              })
              .map(node => {
              const nodeSensors = getSensorsForNode(node.lab_id);
              // Check if node is completely offline
              const isOffline = nodeSensors.length > 0 && nodeSensors.every(s => s.status === 'offline');
              
              return (
                <Card key={node.lab_id} className={`node-card`}>
                  <div className="node-header">
                    <div>
                      <h3>{node.lab_name}</h3>
                      <div className="node-id-row" style={{display: 'flex', alignItems: 'center', gap: '12px', marginTop: '4px'}}>
                        <span className="node-id" title="Hardware ID">{node.lab_id}</span>
                        <span className="mqtt-topic" style={{fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'monospace', background: 'rgba(0,0,0,0.2)', padding: '2px 6px', borderRadius: '4px'}}>
                          MQTT Topic: lab/{node.lab_id}/sensorData
                        </span>
                      </div>
                      {node.location && <span className="node-location" style={{display: 'block', marginTop: '6px'}}>• {node.location}</span>}
                    </div>
                    <div className="node-actions" style={{display: 'flex', gap: '8px', flexWrap: 'wrap'}}>
                      <RemoteAlarmToggle labId={node.lab_id} />
                      <Button size="sm" variant="secondary" title="View/Configure Thresholds" onClick={() => openConfigModal(node)}>
                        <Settings size={14} />
                      </Button>

                      {currentUser?.role === 'admin' && (
                        <Button size="sm" variant="danger" title="Remove Node" onClick={() => handleRemoveNode(node.lab_id)}>
                          <Trash2 size={14} />
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  <div className="sensor-array">

                    <div className="sensor-list">
                      {SENSOR_TYPES.map(type => {
                        if (type === 'vibration') return null; // Vibration commented out for now
                        const sensor = nodeSensors.find(s => s.sensor_type === type);
                        return (
                          <div key={type} className={`sensor-item ${!sensor ? 'missing' : ''}`}>
                            <div className="sensor-icon">
                              {SENSOR_ICONS[type]}
                            </div>
                            <div className="sensor-details">
                              <span className="sensor-type">{type}</span>
                              {sensor ? (
                                <div className="sensor-status-row">
                                  <Badge variant={
                                    sensor.status === 'online' ? 'safe' : 
                                    sensor.status === 'error' ? 'critical' : 'warning'
                                  }>
                                    {sensor.status}
                                  </Badge>
                                  <span className="sensor-reading">
                                    {(() => {
                                      const isStale = sensor.last_updated && (new Date() - new Date(sensor.last_updated)) > 15000;
                                      
                                      if (sensor.status !== 'online') {
                                        return <span style={{ color: 'var(--text-muted)' }}>--</span>;
                                      }
                                      if (hideStaleData && isStale) {
                                        return <span style={{ color: 'var(--text-muted)' }} title="Disconnected or unresponsive">--</span>;
                                      }
                                      if (sensor.last_reading !== null && sensor.last_reading !== undefined) {
                                        return (
                                          <>
                                            {sensor.last_reading.toFixed(2)}
                                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '4px' }}>
                                              {type === 'temperature' ? '°C' : 
                                               type === 'humidity' ? '%' : 
                                               type === 'gas' ? 'PPM' : 
                                               type === 'light' ? 'Lux' : ''}
                                            </span>
                                          </>
                                        );
                                      }
                                      return <span style={{color: 'var(--text-muted)'}}>--</span>;
                                    })()}
                                  </span>
                                </div>
                              ) : (
                                <span className="error-text">Provisioning...</span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </Card>
              );
            })
          )}
        </div>
      )}

      {/* Add Node Modal */}
      {showAddModal && (
        <div className="modal-backdrop">
          <Card className="modal-content">
            <h3>Provision New ESP32 Node</h3>
            <p className="modal-desc">
              This will register a new hardware node and automatically initialize the sensors.
            </p>
            <form onSubmit={handleAddNode}>
              <div className="form-group">
                <label>Node Identifier / Name</label>
                <input 
                  type="text" 
                  value={newNodeName} 
                  onChange={e => setNewNodeName(e.target.value)} 
                  placeholder="e.g. Node-Alpha-01"
                  className="form-input"
                  required
                />
              </div>
              <div className="form-group" style={{marginTop: '16px'}}>
                <label>Physical Location (Optional)</label>
                <input 
                  type="text" 
                  value={newNodeLocation} 
                  onChange={e => setNewNodeLocation(e.target.value)} 
                  placeholder="e.g. North Wing, Sector 4"
                  className="form-input"
                />
              </div>
              
              <div className="modal-actions" style={{marginTop: '24px', display: 'flex', gap: '12px', justifyContent: 'flex-end'}}>
                <Button type="button" variant="secondary" onClick={() => setShowAddModal(false)} disabled={isSubmitting}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Provisioning...' : 'Provision Node'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Sensor Configuration Modal */}
      {configNode && (
        <div className="modal-backdrop">
          <Card className="modal-content config-modal">
            <div className="config-header">
              <div>
                <h3>Configure Sensor Array</h3>
                <p className="modal-desc" style={{margin: '4px 0 0 0'}}>Node: {configNode.lab_name}</p>
              </div>
              <Button variant="secondary" size="sm" onClick={() => setConfigNode(null)}>Close</Button>
            </div>
            
            {isLoadingConfig ? (
              <div className="loading-state">Loading sensor configurations...</div>
            ) : (
              <div className="config-layout">
                <div className="config-sidebar">
                  {SENSOR_TYPES.map(type => {
                    if (type === 'vibration') return null; // Vibration commented out for now
                    return (
                      <button 
                        key={type}
                        type="button"
                        className={`config-tab ${configActiveSensor === type ? 'active' : ''}`}
                        onClick={() => setConfigActiveSensor(type)}
                      >
                        {SENSOR_ICONS[type]} <span style={{textTransform: 'capitalize'}}>{type}</span>
                      </button>
                    );
                  })}
                </div>
                
                <div className="config-body">
                  <form onSubmit={handleSaveSensorConfig} key={configActiveSensor}>
                    <h4 style={{textTransform: 'capitalize', marginBottom: '16px', color: 'var(--color-primary)'}}>
                      {configActiveSensor} Sensor Settings
                    </h4>
                    
                    <div className="form-group">
                      <label>Operational Status</label>
                      <select 
                        name="sensor_status" 
                        className="form-input"
                        defaultValue={getSensorsForNode(configNode.lab_id).find(s => s.sensor_type === configActiveSensor)?.status || 'offline'}
                        disabled={currentUser?.role === 'viewer'}
                      >
                        <option value="online">Online (Active)</option>
                        <option value="offline">Offline (Standby)</option>
                        <option value="error">Error State</option>
                      </select>
                    </div>

                    <div className="form-row" style={{display: 'flex', gap: '16px', marginTop: '16px'}}>
                      <div className="form-group" style={{flex: 1}}>
                        <label>Warning Threshold</label>
                        <input 
                          type="number" 
                          step="0.01"
                          name="warning_value" 
                          defaultValue={configThresholds[configActiveSensor]?.warning_value || ''}
                          placeholder="e.g. 25.5"
                          className="form-input"
                          required
                          disabled={currentUser?.role !== 'admin'}
                        />
                      </div>
                      <div className="form-group" style={{flex: 1}}>
                        <label>Critical Threshold</label>
                        <input 
                          type="number" 
                          step="0.01"
                          name="critical_value" 
                          defaultValue={configThresholds[configActiveSensor]?.critical_value || ''}
                          placeholder="e.g. 30.0"
                          className="form-input"
                          required
                          disabled={currentUser?.role !== 'admin'}
                        />
                      </div>
                    </div>
                    <div className="form-row" style={{display: 'flex', gap: '16px', marginTop: '16px'}}>
                      <div className="form-group" style={{flex: 1}}>
                        <label>Minimum Value</label>
                        <input 
                          type="number" 
                          step="0.01"
                          name="min_value" 
                          defaultValue={configThresholds[configActiveSensor]?.min_value !== null ? configThresholds[configActiveSensor]?.min_value : ''}
                          placeholder="e.g. 20.0"
                          className="form-input"
                          disabled={currentUser?.role !== 'admin'}
                        />
                      </div>
                      <div className="form-group" style={{flex: 1}}>
                        <label>Maximum Value</label>
                        <input 
                          type="number" 
                          step="0.01"
                          name="max_value" 
                          defaultValue={configThresholds[configActiveSensor]?.max_value !== null ? configThresholds[configActiveSensor]?.max_value : ''}
                          placeholder="e.g. 80.0"
                          className="form-input"
                          disabled={currentUser?.role !== 'admin'}
                        />
                      </div>
                    </div>
                    
                    <div style={{marginTop: '8px', fontSize: '0.8rem', color: 'var(--text-muted)'}}>
                      If the sensor reading exceeds the Critical Threshold, an automatic Incident will be generated for staff action.
                      {currentUser?.role !== 'admin' && <div style={{color: 'var(--color-warning)', marginTop: '4px'}}>Note: Only Administrators can modify threshold values.</div>}
                    </div>

                    {currentUser?.role !== 'viewer' && (
                      <div className="modal-actions" style={{marginTop: '24px', display: 'flex', justifyContent: 'flex-end'}}>
                        <Button type="submit" variant="primary" disabled={isSubmitting}>
                          {isSubmitting ? 'Saving...' : 'Save Configuration'}
                        </Button>
                      </div>
                    )}
                  </form>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
};
