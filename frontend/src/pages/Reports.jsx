import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { FileText, Printer, Calendar, MapPin, ShieldAlert, FlaskConical, Bot } from 'lucide-react';
import './Reports.css';

export const Reports = () => {
  const { apiFetch, currentUser } = useAuth();
  const navigate = useNavigate();
  
  // Form State
  const [reportType, setReportType] = useState('inventory'); // 'inventory' | 'safety'
  const [timeframe, setTimeframe] = useState(30);
  const [selectedTarget, setSelectedTarget] = useState(''); // location_id or lab_id
  
  // Data State
  const [locations, setLocations] = useState([]);
  const [facilities, setFacilities] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [reportData, setReportData] = useState(null);

  // Hardcoded labs for safety reports (since labs aren't dynamically tracked yet)
  const labs = [
    { id: 'LAB-1', name: 'Main Laboratory (LAB-1)' },
    { id: 'LAB-2', name: 'Bio-Hazard Facility (LAB-2)' },
    { id: 'LAB-3', name: 'Chemical Storage (LAB-3)' }
  ];

  useEffect(() => {
    // Fetch inventory locations for the dropdown
    const fetchData = async () => {
      try {
        const [locData, facData] = await Promise.all([
          apiFetch('/api/inventory/locations'),
          apiFetch('/api/reports/facilities')
        ]);
        setLocations(locData);
        setFacilities(facData);
      } catch (err) {
        console.error("Failed to load dropdown data", err);
      }
    };
    fetchData();
  }, []);

  const handleGenerate = async (e) => {
    e.preventDefault();
    setIsGenerating(true);
    setReportData(null);
    
    try {
      const payload = {
        report_type: reportType,
        days: timeframe,
        location_id: reportType === 'inventory' ? (selectedTarget === 'all' ? null : selectedTarget) : null,
        lab_id: reportType === 'safety' ? selectedTarget : null
      };

      const data = await apiFetch('/api/reports/generate', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      
      setReportData(data);
    } catch (err) {
      alert(err.message);
    }
    setIsGenerating(false);
  };

  const handlePrint = () => {
    window.print();
  };

  const handleGoToAI = () => {
    if (!reportData) return;
    const reportText = JSON.stringify(reportData.data, null, 2);
    const initialText = `${reportText}\n\n`;
    navigate('/ai-assistant', { state: { initialText } });
  };

  return (
    <div className="reports-page">
      <div className="page-header no-print">
        <h2>Report Generation</h2>
        <p>Generate downloadable compliance, safety, and inventory summaries.</p>
      </div>

      <div className="reports-layout">
        
        {/* REPORT BUILDER CONTROLS */}
        <div className="reports-sidebar no-print">
          <Card>
            <h3 style={{marginTop: 0, marginBottom: '20px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px'}}>
              Report Configuration
            </h3>
            
            <form onSubmit={handleGenerate}>
              <div className="form-group">
                <label>Report Type</label>
                <div className="type-toggles">
                  <div 
                    className={`type-toggle ${reportType === 'inventory' ? 'active' : ''}`}
                    onClick={() => { setReportType('inventory'); setSelectedTarget(''); }}
                  >
                    <FlaskConical size={18}/> Inventory
                  </div>
                  <div 
                    className={`type-toggle ${reportType === 'safety' ? 'active' : ''}`}
                    onClick={() => { setReportType('safety'); setSelectedTarget(facilities[0]?.id || ''); }}
                  >
                    <ShieldAlert size={18}/> Safety & Alerts
                  </div>
                </div>
              </div>

              {reportType === 'safety' && (
                <div className="form-group">
                  <label><Calendar size={14}/> Timeframe</label>
                  <select value={timeframe} onChange={e => setTimeframe(Number(e.target.value))}>
                    <option value={7}>Last 7 Days</option>
                    <option value={30}>Last 30 Days</option>
                    <option value={90}>Last 90 Days</option>
                    <option value={365}>Last 1 Year</option>
                  </select>
                </div>
              )}

              <div className="form-group">
                <label><MapPin size={14}/> Target Location / Facility</label>
                {reportType === 'inventory' ? (
                  <select value={selectedTarget} onChange={e => setSelectedTarget(e.target.value)} required>
                    <option value="" disabled>Select Storage Location...</option>
                    <option value="all">All Locations (Global Inventory)</option>
                    {locations.map(loc => (
                      <option key={loc.location_id} value={loc.location_id}>{loc.name}</option>
                    ))}
                  </select>
                ) : (
                  <select value={selectedTarget} onChange={e => setSelectedTarget(e.target.value)} required>
                    {facilities.length === 0 && <option value="" disabled>No facilities found</option>}
                    {facilities.map(fac => (
                      <option key={fac.id} value={fac.id}>{fac.name}</option>
                    ))}
                  </select>
                )}
              </div>

              <Button type="submit" style={{width: '100%', marginTop: '16px'}} disabled={isGenerating || (reportType === 'inventory' && !selectedTarget)}>
                {isGenerating ? 'Compiling Data...' : 'Generate Report'}
              </Button>
            </form>
          </Card>
        </div>

        {/* REPORT PREVIEW PANEL */}
        <div className="reports-preview">
          {!reportData ? (
            <div className="empty-report no-print">
              <FileText size={48} />
              <h3>No Report Generated</h3>
              <p>Select your parameters on the left and click Generate.</p>
            </div>
          ) : (
            <div className="report-document printable-report">
              <div className="report-doc-header">
                <div className="brand">
                  <h2>ChemSafe IoT</h2>
                  <span>Official System Report</span>
                </div>
                <div className="meta">
                  <div><strong>ID:</strong> {reportData.report_id}</div>
                  <div><strong>Date:</strong> {new Date(reportData.generated_at).toLocaleString()}</div>
                  <div><strong>Generated By:</strong> {reportData.generated_by}</div>
                </div>
              </div>

              <div className="report-title">
                <h1>{reportData.data.summary}</h1>
                <p>
                  Target: {reportData.report_type === 'inventory' 
                    ? (reportData.location_id === null ? 'All Global Locations' : locations.find(l => l.location_id === reportData.location_id)?.name || 'Unknown Location')
                    : (facilities.find(f => f.id === reportData.lab_id)?.name || reportData.lab_id)
                  }
                  {reportData.report_type === 'safety' && ` | Period: Last ${reportData.data.period_days} Days`}
                </p>
              </div>

              <div className="report-stats">
                {reportData.report_type === 'safety' ? (
                  <>
                    <div className="stat-box">
                      <div className="stat-val">{reportData.data.total_alerts}</div>
                      <div className="stat-label">Total Sensor Alerts</div>
                    </div>
                    <div className="stat-box warning">
                      <div className="stat-val">{reportData.data.critical_alerts}</div>
                      <div className="stat-label">Critical Alerts</div>
                    </div>
                    <div className="stat-box">
                      <div className="stat-val">{reportData.data.total_incidents}</div>
                      <div className="stat-label">Total Incidents</div>
                    </div>
                    <div className="stat-box danger">
                      <div className="stat-val">{reportData.data.critical_incidents}</div>
                      <div className="stat-label">Critical Incidents</div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="stat-box">
                      <div className="stat-val">{reportData.data.total_chemicals}</div>
                      <div className="stat-label">Registered Chemicals</div>
                    </div>
                    {/* Render Hazard Counts */}
                    {Object.entries(reportData.data.hazard_distribution || {}).map(([hazard, count]) => (
                      <div key={hazard} className="stat-box outline">
                        <div className="stat-val">{count}</div>
                        <div className="stat-label" style={{textTransform: 'capitalize'}}>{hazard.replace('_', ' ')}</div>
                      </div>
                    ))}
                  </>
                )}
              </div>

              <div className="report-tables">
                {reportData.report_type === 'safety' ? (
                  <>
                    <h3>Incident Log</h3>
                    <table className="doc-table">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Incident Details</th>
                          <th>Resolution</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {!reportData.data.incident_details || reportData.data.incident_details.length === 0 ? (
                          <tr><td colSpan="4">No incidents recorded in this timeframe.</td></tr>
                        ) : (
                          reportData.data.incident_details.map(inc => (
                            <tr key={inc.id}>
                              <td style={{whiteSpace: 'nowrap'}}>{new Date(inc.date).toLocaleDateString()}</td>
                              <td>
                                <strong>{inc.title}</strong><br/>
                                <span style={{fontSize: '0.85rem', color: '#64748b'}}>{inc.id}</span>
                                <div style={{marginTop: '4px', fontSize: '0.9rem'}}>{inc.description}</div>
                              </td>
                              <td>
                                {inc.status === 'resolved' || inc.status === 'closed' ? (
                                  <>
                                    <div style={{fontSize: '0.9rem'}}><strong>Notes:</strong> {inc.resolution_summary || 'No notes provided.'}</div>
                                    <div style={{fontSize: '0.85rem', color: '#64748b', marginTop: '4px'}}>
                                      Resolved By: {inc.resolved_by_name} <br/>
                                      On: {inc.resolved_at ? new Date(inc.resolved_at).toLocaleString() : 'Unknown'}
                                    </div>
                                  </>
                                ) : (
                                  <span style={{color: '#94a3b8', fontStyle: 'italic'}}>Pending Resolution</span>
                                )}
                              </td>
                              <td style={{textTransform: 'uppercase'}}><strong>{inc.status}</strong></td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </>
                ) : (
                  <>
                    <h3>Chemical Register</h3>
                    <table className="doc-table">
                      <thead>
                        <tr>
                          <th>Chemical Name</th>
                          <th>Hazard Class</th>
                          <th style={{textAlign: 'right'}}>Stock Quantity</th>
                        </tr>
                      </thead>
                      <tbody>
                        {!reportData.data.inventory_list || reportData.data.inventory_list.length === 0 ? (
                          <tr><td colSpan="3">No chemicals stored in this location.</td></tr>
                        ) : (
                          reportData.data.inventory_list.map((chem, idx) => (
                            <tr key={idx}>
                              <td><strong>{chem.name}</strong></td>
                              <td style={{textTransform: 'capitalize'}}>{(chem.hazard || 'Unknown').replace('_', ' ')}</td>
                              <td style={{textAlign: 'right'}}>{chem.quantity} {chem.unit}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </>
                )}
              </div>

              <div className="report-footer">
                <p>CONFIDENTIAL — DO NOT DISTRIBUTE WITHOUT AUTHORIZATION</p>
                <div className="no-print print-btn-container" style={{ display: 'flex', gap: '12px' }}>
                  <Button onClick={handlePrint}><Printer size={16} style={{marginRight: '8px'}} /> Print / Save as PDF</Button>
                  <Button onClick={handleGoToAI} style={{ backgroundColor: 'var(--color-primary)' }}><Bot size={16} style={{marginRight: '8px'}} /> Ask AI</Button>
                </div>
              </div>

            </div>
          )}
        </div>

      </div>
    </div>
  );
};
