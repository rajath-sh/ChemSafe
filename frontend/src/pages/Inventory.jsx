import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { FlaskConical, MapPin, Plus, Trash2, Edit2, AlertTriangle, Search } from 'lucide-react';
import './Inventory.css';

export const Inventory = () => {
  const { apiFetch, currentUser } = useAuth();
  
  // Locations State
  const [locations, setLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [locSearchQuery, setLocSearchQuery] = useState('');
  
  // Chemicals State
  const [chemicals, setChemicals] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);

  // Modal States
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [showChemicalModal, setShowChemicalModal] = useState(false);

  // Forms
  const [newLocationName, setNewLocationName] = useState('');
  const [newLocationDesc, setNewLocationDesc] = useState('');

  const [newChem, setNewChem] = useState({
    name: '', cas_number: '', hazard_class: 'non_hazardous', quantity: 0, unit: 'mL', image_url: ''
  });
  const [imageFile, setImageFile] = useState(null);
  const [viewingImage, setViewingImage] = useState(null);

  const hazardClasses = [
    'flammable', 'toxic', 'corrosive', 'oxidizer', 'explosive',
    'radioactive', 'biohazard', 'irritant', 'compressed_gas',
    'environmental', 'non_hazardous'
  ];

  // ── Fetching Data ──────────────────────────────────────────────────────────

  const fetchLocations = async () => {
    try {
      const data = await apiFetch('/api/inventory/locations');
      setLocations(data);
      if (data.length > 0 && !selectedLocation) {
        setSelectedLocation(data[0]);
      } else if (data.length === 0) {
        setSelectedLocation(null);
      }
    } catch (err) {
      console.error('Failed to fetch locations:', err);
    }
  };

  const fetchChemicals = async (locId) => {
    setLoading(true);
    try {
      const data = await apiFetch(`/api/inventory?location_id=${locId}`);
      setChemicals(data);
    } catch (err) {
      console.error('Failed to fetch chemicals:', err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchLocations();
  }, []);

  useEffect(() => {
    if (selectedLocation) {
      fetchChemicals(selectedLocation.location_id);
    } else {
      setChemicals([]);
    }
  }, [selectedLocation]);

  // ── Location Actions ────────────────────────────────────────────────────────

  const handleAddLocation = async (e) => {
    e.preventDefault();
    try {
      await apiFetch('/api/inventory/locations', {
        method: 'POST',
        body: JSON.stringify({ name: newLocationName, description: newLocationDesc })
      });
      setShowLocationModal(false);
      setNewLocationName('');
      setNewLocationDesc('');
      fetchLocations();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteLocation = async (locId, e) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this location? Ensure it has no chemicals first.")) return;
    try {
      await apiFetch(`/api/inventory/locations/${locId}`, { method: 'DELETE' });
      if (selectedLocation?.location_id === locId) setSelectedLocation(null);
      fetchLocations();
    } catch (err) {
      alert(err.message);
    }
  };

  // ── Chemical Actions ────────────────────────────────────────────────────────

  const handleAddChemical = async (e) => {
    e.preventDefault();
    if (!selectedLocation) return;
    
    let uploadedUrl = '';
    if (imageFile) {
      try {
        const formData = new FormData();
        formData.append('file', imageFile);
        
        const token = localStorage.getItem('chemsafe_token');
        const uploadRes = await fetch('http://localhost:8000/api/inventory/upload', {
          method: 'POST',
          headers: token ? { 'Authorization': `Bearer ${token}` } : {},
          body: formData
        });
        
        if (!uploadRes.ok) throw new Error('Image upload failed');
        const uploadData = await uploadRes.json();
        uploadedUrl = uploadData.url;
      } catch (err) {
        alert(err.message);
        return;
      }
    }

    try {
      await apiFetch('/api/inventory', {
        method: 'POST',
        body: JSON.stringify({
          ...newChem,
          location_id: selectedLocation.location_id,
          quantity: parseFloat(newChem.quantity),
          image_url: uploadedUrl || newChem.image_url
        })
      });
      setShowChemicalModal(false);
      setNewChem({ name: '', cas_number: '', hazard_class: 'non_hazardous', quantity: 0, unit: 'mL', image_url: '' });
      setImageFile(null);
      fetchChemicals(selectedLocation.location_id);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteChemical = async (chemId) => {
    if (!window.confirm("Delete this chemical record?")) return;
    try {
      await apiFetch(`/api/inventory/${chemId}`, { method: 'DELETE' });
      fetchChemicals(selectedLocation.location_id);
    } catch (err) {
      alert(err.message);
    }
  };

  // ── UI Helpers ──────────────────────────────────────────────────────────────

  const getHazardBadgeVariant = (hazard) => {
    const critical = ['explosive', 'toxic', 'radioactive', 'biohazard'];
    const warning = ['flammable', 'corrosive', 'oxidizer', 'compressed_gas'];
    
    if (critical.includes(hazard)) return 'critical';
    if (warning.includes(hazard)) return 'warning';
    return 'safe';
  };

  const filteredChemicals = chemicals.filter(c => {
    const q = searchQuery.toLowerCase();
    return (
      c.name.toLowerCase().includes(q) ||
      (c.cas_number && c.cas_number.toLowerCase().includes(q)) ||
      c.hazard_class.toLowerCase().includes(q) ||
      c.quantity.toString().includes(q) ||
      c.unit.toLowerCase().includes(q)
    );
  });

  const filteredLocations = locations.filter(loc => 
    loc.name.toLowerCase().includes(locSearchQuery.toLowerCase()) ||
    (loc.description && loc.description.toLowerCase().includes(locSearchQuery.toLowerCase()))
  );

  return (
    <div className="inventory-page">
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <h2>Chemical Inventory Management</h2>
        <p>Manage storage locations and chemical stock dynamically.</p>
      </div>

      <div className="inventory-layout">
        
        {/* LEFT PANE: LOCATIONS */}
        <div className="inventory-sidebar">
          <div className="sidebar-header">
            <h3><MapPin size={18} style={{marginRight: '8px'}} /> Storage Locations</h3>
            {currentUser?.role === 'admin' && (
              <button className="icon-btn" onClick={() => setShowLocationModal(true)}>
                <Plus size={18} />
              </button>
            )}
          </div>
          
          <div style={{ padding: '8px 12px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <div className="search-box" style={{ background: 'rgba(0,0,0,0.4)', borderRadius: '6px' }}>
              <Search size={14} style={{ color: 'var(--text-muted)' }} />
              <input 
                type="text" 
                placeholder="Find location..." 
                value={locSearchQuery}
                onChange={e => setLocSearchQuery(e.target.value)}
                style={{ padding: '6px', fontSize: '0.85rem', width: '100%' }}
              />
            </div>
          </div>
          
          <div className="location-list">
            {filteredLocations.length === 0 ? (
              <div className="empty-state">No locations found.</div>
            ) : (
              filteredLocations.map(loc => (
                <div 
                  key={loc.location_id}
                  className={`location-item ${selectedLocation?.location_id === loc.location_id ? 'active' : ''}`}
                  onClick={() => setSelectedLocation(loc)}
                >
                  <div className="loc-info">
                    <strong>{loc.name}</strong>
                    <span>{loc.description || 'No description'}</span>
                  </div>
                  {currentUser?.role === 'admin' && (
                    <button className="del-loc-btn" onClick={(e) => handleDeleteLocation(loc.location_id, e)}>
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* RIGHT PANE: CHEMICALS */}
        <div className="inventory-main">
          {!selectedLocation ? (
            <div className="empty-main">
              <FlaskConical size={48} />
              <h3>Select a Location</h3>
              <p>Choose a storage location from the left to view its inventory.</p>
            </div>
          ) : (
            <>
              <div className="main-header">
                <div>
                  <h3>Inventory: {selectedLocation.name}</h3>
                  <p className="subtitle">{selectedLocation.description}</p>
                </div>
                <div className="main-actions">
                  <div className="search-box">
                    <Search size={16} />
                    <input 
                      type="text" 
                      placeholder="Search chemicals..." 
                      value={searchQuery}
                      onChange={e => setSearchQuery(e.target.value)}
                    />
                  </div>
                  {currentUser?.role !== 'viewer' && (
                    <Button onClick={() => setShowChemicalModal(true)}>
                      <Plus size={16} style={{marginRight: '8px'}}/> Add Chemical
                    </Button>
                  )}
                </div>
              </div>

              {loading ? (
                <div className="loading-state">Loading chemicals...</div>
              ) : (
                <Card>
                  <div className="table-responsive">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th style={{ width: '80px' }}></th>
                          <th>Chemical Name</th>
                          <th>CAS Number</th>
                          <th>Hazard Class</th>
                          <th>Quantity</th>
                          {currentUser?.role === 'admin' && <th>Actions</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {filteredChemicals.length === 0 ? (
                          <tr><td colSpan="6" style={{textAlign: 'center', padding: '20px'}}>No chemicals found.</td></tr>
                        ) : (
                          filteredChemicals.map(chem => (
                            <tr key={chem.chemical_id}>
                              <td>
                                {chem.image_url ? (
                                  <img 
                                    src={chem.image_url} 
                                    alt={chem.name} 
                                    className="chem-thumb clickable" 
                                    onClick={() => setViewingImage(chem.image_url)}
                                  />
                                ) : (
                                  <div className="chem-thumb-placeholder"><FlaskConical size={16} /></div>
                                )}
                              </td>
                              <td><strong>{chem.name}</strong></td>
                              <td>{chem.cas_number || 'N/A'}</td>
                              <td>
                                <Badge variant={getHazardBadgeVariant(chem.hazard_class)}>
                                  {chem.hazard_class.replace('_', ' ').toUpperCase()}
                                </Badge>
                              </td>
                              <td>{chem.quantity} {chem.unit}</td>
                              {currentUser?.role === 'admin' && (
                                <td>
                                  <button className="icon-btn danger" onClick={() => handleDeleteChemical(chem.chemical_id)}>
                                    <Trash2 size={16} />
                                  </button>
                                </td>
                              )}
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}
            </>
          )}
        </div>
      </div>

      {/* Modals */}
      {showLocationModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Add New Location</h3>
            <form onSubmit={handleAddLocation}>
              <div className="form-group">
                <label>Location Name</label>
                <input required value={newLocationName} onChange={e => setNewLocationName(e.target.value)} placeholder="e.g. Acid Cabinet 1" />
              </div>
              <div className="form-group">
                <label>Description</label>
                <input value={newLocationDesc} onChange={e => setNewLocationDesc(e.target.value)} placeholder="Optional details..." />
              </div>
              <div className="modal-actions">
                <Button type="button" variant="secondary" onClick={() => setShowLocationModal(false)}>Cancel</Button>
                <Button type="submit">Create Location</Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showChemicalModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Add Chemical to {selectedLocation?.name}</h3>
            <form onSubmit={handleAddChemical}>
              <div className="form-group">
                <label>Chemical Name</label>
                <input required value={newChem.name} onChange={e => setNewChem({...newChem, name: e.target.value})} />
              </div>
              <div className="form-group">
                <label>CAS Number</label>
                <input value={newChem.cas_number} onChange={e => setNewChem({...newChem, cas_number: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Hazard Class</label>
                <select value={newChem.hazard_class} onChange={e => setNewChem({...newChem, hazard_class: e.target.value})}>
                  {hazardClasses.map(hc => <option key={hc} value={hc}>{hc.replace('_', ' ').toUpperCase()}</option>)}
                </select>
              </div>
              <div style={{display: 'flex', gap: '16px'}}>
                <div className="form-group" style={{flex: 1}}>
                  <label>Quantity</label>
                  <input type="number" step="0.01" required value={newChem.quantity} onChange={e => setNewChem({...newChem, quantity: e.target.value})} />
                </div>
                <div className="form-group" style={{flex: 1}}>
                  <label>Unit</label>
                  <select value={newChem.unit} onChange={e => setNewChem({...newChem, unit: e.target.value})}>
                    <option value="mL">mL</option>
                    <option value="L">L</option>
                    <option value="g">g</option>
                    <option value="kg">kg</option>
                    <option value="units">units</option>
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>Chemical Photo</label>
                <input type="file" accept="image/*" onChange={e => setImageFile(e.target.files[0])} style={{padding: '8px'}} />
                {imageFile && <span style={{fontSize: '0.8rem', color: 'var(--color-primary)'}}>File selected: {imageFile.name}</span>}
              </div>
              <div className="modal-actions">
                <Button type="button" variant="secondary" onClick={() => {setShowChemicalModal(false); setImageFile(null);}}>Cancel</Button>
                <Button type="submit">Add Chemical</Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {viewingImage && (
        <div className="modal-overlay" onClick={() => setViewingImage(null)}>
          <div className="modal-content" style={{maxWidth: '800px', background: 'transparent', border: 'none', boxShadow: 'none', display: 'flex', justifyContent: 'center'}}>
            <img src={viewingImage} alt="Full size" style={{maxWidth: '100%', maxHeight: '80vh', borderRadius: '8px', objectFit: 'contain', boxShadow: '0 20px 40px rgba(0,0,0,0.5)'}} />
          </div>
        </div>
      )}

    </div>
  );
};
