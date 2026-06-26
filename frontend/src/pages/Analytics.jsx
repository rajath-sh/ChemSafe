import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { 
  Activity, MapPin, AlertCircle, Thermometer, Droplets, Wind, Sun, Vibrate, Info
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';
import './Analytics.css';

const SENSOR_ICONS = {
  temperature: <Thermometer size={18} />,
  humidity: <Droplets size={18} />,
  gas: <Wind size={18} />,
  light: <Sun size={18} />,
  vibration: <Vibrate size={18} />
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="custom-tooltip">
        <div className="label">{new Date(data.timestamp).toLocaleTimeString()}</div>
        <div className="value">{payload[0].value.toFixed(2)}</div>
      </div>
    );
  }
  return null;
};

export const Analytics = () => {
  const { apiFetch } = useAuth();
  const [nodes, setNodes] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Analytics State
  const [analyticsData, setAnalyticsData] = useState([]);
  const [nodeSensors, setNodeSensors] = useState([]);
  const [nodeThresholds, setNodeThresholds] = useState([]);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);

  // 1. Fetch Node List on Mount
  useEffect(() => {
    const fetchNodes = async () => {
      try {
        const data = await apiFetch('/api/sensors/labs');
        setNodes(data);
      } catch (err) {
        console.error("Failed to fetch nodes:", err);
      }
    };
    fetchNodes();
  }, [apiFetch]);

  // 2. Fetch Analytics when a Node is selected
  useEffect(() => {
    const fetchAnalytics = async (showSpinner = true) => {
      if (!selectedNode) return;
      if (showSpinner) setLoadingAnalytics(true);
      try {
        // Fetch historical readings for charts (210 readings * 2s = 420s = 7 minutes)
        const readings = await apiFetch(`/api/sensors/readings/${selectedNode.lab_id}?limit=210`);
        
        // Fetch actual sensor configurations for this node to check availability
        const sensors = await apiFetch(`/api/sensors?lab_id=${selectedNode.lab_id}`);
        
        // Fetch thresholds to determine good/bad state
        const thresholds = await apiFetch(`/api/sensors/thresholds/${selectedNode.lab_id}`);
        
        // Data usually comes back newest first, reverse for chronological chart plotting
        setAnalyticsData(readings.reverse());
        setNodeSensors(sensors);
        setNodeThresholds(thresholds);
      } catch (err) {
        console.error("Failed to fetch analytics:", err);
      }
      if (showSpinner) setLoadingAnalytics(false);
    };

    fetchAnalytics();
    
    const interval = setInterval(() => {
      fetchAnalytics(false);
    }, 2000);
    
    return () => clearInterval(interval);
  }, [selectedNode, apiFetch]);

  const filteredNodes = nodes.filter(node => 
    node.lab_name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    (node.location && node.location.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const renderChart = (sensorType, dataKey, color, title, unit) => {
    const sensorConfig = nodeSensors.find(s => s.sensor_type === sensorType);
    
    // If not configured, or explicitly offline/error, or no readings exist
    if (!sensorConfig) {
      return (
        <Card className="chart-card">
          <div className="chart-header">
            <h4>{title}</h4>
            <span style={{color: 'var(--text-muted)', fontSize: '0.8rem'}}>{unit}</span>
          </div>
          <div className="not-available-state"><Info size={24}/><span>Not Configured</span></div>
        </Card>
      );
    }
    
    if (sensorConfig.status !== 'online') {
      return (
        <Card className="chart-card">
          <div className="chart-header">
            <h4>{title}</h4>
            <span style={{color: 'var(--text-muted)', fontSize: '0.8rem'}}>{unit}</span>
          </div>
          <div className="not-available-state">
            <AlertCircle size={24} style={{color: sensorConfig.status === 'error' ? 'var(--color-critical)' : 'var(--color-warning)'}}/>
            <span style={{marginTop: '8px'}}>Data Not Available - {sensorConfig.status.toUpperCase()}</span>
          </div>
        </Card>
      );
    }

    if (analyticsData.length === 0) {
      return (
        <Card className="chart-card">
          <div className="chart-header">
            <h4>{title}</h4>
            <span style={{color: 'var(--text-muted)', fontSize: '0.8rem'}}>{unit}</span>
          </div>
          <div className="not-available-state"><Activity size={24}/><span>Waiting for ESP32 data...</span></div>
        </Card>
      );
    }

    const latestReading = analyticsData[analyticsData.length - 1][dataKey];
    const threshold = nodeThresholds.find(t => t.sensor_type === sensorType);
    
    // Calculate Analytics
    const validReadings = analyticsData.map(d => d[dataKey]).filter(v => v !== undefined && v !== null);
    let maxVal = '--';
    let minVal = '--';
    let avgVal = '--';
    let trend = 'Stable';
    
    if (validReadings.length > 0) {
      maxVal = Math.max(...validReadings).toFixed(2);
      minVal = Math.min(...validReadings).toFixed(2);
      const sum = validReadings.reduce((a, b) => a + b, 0);
      const numericAvg = sum / validReadings.length;
      avgVal = numericAvg.toFixed(2);
      
      if (validReadings.length > 1) {
        const variance = validReadings.reduce((a, b) => a + Math.pow(b - numericAvg, 2), 0) / validReadings.length;
        const stdDev = Math.sqrt(variance);
        // Calculate a 0-100 score based on coefficient of variation
        const score = Math.min(100, Math.round((stdDev / (Math.abs(numericAvg) || 1)) * 100));
        trend = score + '%';
      }
    }

    let statusBadge = null;
    let valueColor = 'var(--text-primary)';
    
    if (latestReading !== undefined && latestReading !== null) {
      if (threshold) {
        if (latestReading >= threshold.critical_value) {
          statusBadge = <Badge variant="critical">CRITICAL</Badge>;
          valueColor = 'var(--color-critical)';
        } else if (latestReading >= threshold.warning_value) {
          statusBadge = <Badge variant="warning">WARNING</Badge>;
          valueColor = 'var(--color-warning)';
        } else {
          statusBadge = <Badge variant="safe">GOOD</Badge>;
          valueColor = 'var(--color-safe)';
        }
      } else {
        statusBadge = <Badge variant="safe">GOOD</Badge>;
      }
    }

    return (
      <Card className="chart-card">
        <div className="chart-header">
          <div>
            <h4>{title}</h4>
            <div style={{display: 'flex', alignItems: 'center', gap: '12px', marginTop: '4px'}}>
              <span style={{fontSize: '1.5rem', fontWeight: 'bold', color: valueColor}}>
                {latestReading !== undefined && latestReading !== null ? latestReading.toFixed(2) : '--'}
              </span>
              <span style={{color: 'var(--text-muted)', fontSize: '0.9rem'}}>{unit}</span>
              {statusBadge}
            </div>
          </div>
        </div>
        
        {/* Analytics Summary Bar */}
        {validReadings.length > 0 && (
          <div style={{display: 'flex', gap: '16px', marginBottom: '16px', padding: '8px 12px', background: 'rgba(0,0,0,0.2)', borderRadius: '6px', fontSize: '0.8rem'}}>
            <div><span style={{color: 'var(--text-muted)'}}>Max:</span> <strong>{maxVal}</strong></div>
            <div><span style={{color: 'var(--text-muted)'}}>Min:</span> <strong>{minVal}</strong></div>
            <div><span style={{color: 'var(--text-muted)'}}>Avg:</span> <strong>{avgVal}</strong></div>
            <div><span style={{color: 'var(--text-muted)'}}>Anomaly Score:</span> <strong style={{color: parseInt(trend) > 25 ? 'var(--color-warning)' : 'var(--color-safe)'}}>{trend}</strong></div>
          </div>
        )}

        <div className="chart-container">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={analyticsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={(tick) => new Date(tick).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} 
                stroke="rgba(255,255,255,0.4)" 
                fontSize={12} 
              />
              <YAxis stroke="rgba(255,255,255,0.4)" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Line 
                type="monotone" 
                dataKey={dataKey} 
                stroke={color} 
                strokeWidth={3} 
                dot={false}
                activeDot={{ r: 6, fill: color, stroke: '#1e293b', strokeWidth: 2 }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>
    );
  };

  return (
    <div className="dashboard-page">
      <div>
        <h2>Facility Analytics</h2>
        <p>Select a node to view its complete historical analytics and current health status.</p>
      </div>

      <div className="dashboard-layout">
        
        {/* LEFT PANEL: Master List */}
        <div className="nodes-master-list">
          <div style={{marginBottom: '12px'}}>
            <input 
              type="text" 
              placeholder="Search by Node Name or Location..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-input"
              style={{width: '100%', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)'}}
            />
          </div>
          {filteredNodes.length === 0 ? (
            <div className="not-available-state">No Nodes Found</div>
          ) : (
            filteredNodes.map(node => (
              <Card 
                key={node.lab_id} 
                className={`node-list-item ${selectedNode?.lab_id === node.lab_id ? 'selected' : ''}`}
                onClick={() => setSelectedNode(node)}
              >
                <h3>{node.lab_name}</h3>
                {node.location && (
                  <div className="location">
                    <MapPin size={14} /> {node.location}
                  </div>
                )}
              </Card>
            ))
          )}
        </div>

        {/* RIGHT PANEL: Analytics Detail */}
        <div className="analytics-detail">
          {!selectedNode ? (
            <div className="empty-analytics glass-panel">
              <Activity size={48} />
              <h3>No Node Selected</h3>
              <p>Select a node from the list to view its complete analytics.</p>
            </div>
          ) : (
            <div className="glass-panel" style={{padding: '24px', flex: 1, display: 'flex', flexDirection: 'column'}}>
              <div className="analytics-header flex-between">
                <div>
                  <h2>{selectedNode.lab_name} Analytics</h2>
                  <span style={{color: 'var(--text-muted)'}}>{selectedNode.lab_id} • {selectedNode.location}</span>
                </div>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  {loadingAnalytics && <Badge variant="neutral">Loading Data...</Badge>}
                  <button 
                    className="btn" 
                    style={{ backgroundColor: 'white', color: 'black', fontWeight: 'bold' }}
                    onClick={async () => {
                      try {
                        const userStr = localStorage.getItem('chemsafe_user');
                        const headers = {};
                        if (userStr) {
                          const user = JSON.parse(userStr);
                          headers['X-Dev-Role'] = user.role;
                          headers['X-Dev-User-Id'] = user.user_id;
                        } else {
                          headers['X-Dev-Role'] = 'admin';
                          headers['X-Dev-User-Id'] = 'DEV-admin-001';
                        }
                        
                        const response = await fetch(`http://127.0.0.1:8000/api/sensors/readings/${selectedNode.lab_id}/export?days=1`, { headers });
                        if (!response.ok) throw new Error("Failed to export data");
                        
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `node_${selectedNode.lab_id}_1day_data.csv`;
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        window.URL.revokeObjectURL(url);
                      } catch (err) {
                        alert("Error downloading data: " + err.message);
                      }
                    }}
                  >
                    Export 1-Day CSV
                  </button>
                </div>
              </div>

              <div className="charts-grid">
                {renderChart('temperature', 'temperature', 'var(--color-critical)', <><Thermometer size={18} /> Temperature</>, '°C')}
                {renderChart('humidity', 'humidity', '#3b82f6', <><Droplets size={18} /> Humidity</>, '%')}
                {renderChart('gas', 'gas', 'var(--color-warning)', <><Wind size={18} /> Air Quality (Gas)</>, 'PPM')}
                {/* {renderChart('vibration', 'vibration', '#8b5cf6', <><Vibrate size={18} /> Vibration</>, 'g')} */}
                {renderChart('light', 'light', '#f59e0b', <><Sun size={18} /> Ambient Light</>, 'Lux')}
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
