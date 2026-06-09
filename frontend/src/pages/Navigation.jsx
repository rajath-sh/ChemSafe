import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Plus, Trash2, Map, Play, ArrowRight, ArrowLeft } from 'lucide-react';
import './Navigation.css';

export const Navigation = () => {
  const { apiFetch } = useAuth();
  
  const [nodes, setNodes] = useState(() => {
    const saved = localStorage.getItem('chemSafe_nav_nodes');
    return saved ? JSON.parse(saved) : [];
  });
  const [edges, setEdges] = useState(() => {
    const saved = localStorage.getItem('chemSafe_nav_edges');
    return saved ? JSON.parse(saved) : [];
  });
  
  // Builder state
  const [newNodeName, setNewNodeName] = useState('');
  const [newNodeType, setNewNodeType] = useState('sensor');
  const [newNodeLocation, setNewNodeLocation] = useState('');
  
  const [newEdgeSource, setNewEdgeSource] = useState('');
  const [newEdgeTarget, setNewEdgeTarget] = useState('');
  const [newEdgeWeight, setNewEdgeWeight] = useState(1.0);

  // Pathfinding state
  const [sourceNode, setSourceNode] = useState('');
  const [targetNode, setTargetNode] = useState('');
  const [currentPath, setCurrentPath] = useState([]);
  const [pathDistance, setPathDistance] = useState(0);
  const [stepIndex, setStepIndex] = useState(-1);
  const [errorMsg, setErrorMsg] = useState('');

  // Canvas ref for simple drawing
  const canvasRef = useRef(null);
  
  // Force simple positions for visualization
  const [nodePositions, setNodePositions] = useState(() => {
    const saved = localStorage.getItem('chemSafe_nav_positions');
    return saved ? JSON.parse(saved) : {};
  });
  const [draggingNode, setDraggingNode] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  
  const [unit, setUnit] = useState(() => {
    return localStorage.getItem('chemSafe_nav_unit') || 'm';
  });

  // Dry run state
  const [showDryRun, setShowDryRun] = useState(false);
  const [dryRunData, setDryRunData] = useState(null);
  const [dryRunStep, setDryRunStep] = useState(0);

  useEffect(() => {
    localStorage.setItem('chemSafe_nav_nodes', JSON.stringify(nodes));
  }, [nodes]);

  useEffect(() => {
    localStorage.setItem('chemSafe_nav_edges', JSON.stringify(edges));
  }, [edges]);

  useEffect(() => {
    localStorage.setItem('chemSafe_nav_positions', JSON.stringify(nodePositions));
  }, [nodePositions]);

  useEffect(() => {
    localStorage.setItem('chemSafe_nav_unit', unit);
  }, [unit]);

  useEffect(() => {
    // Generate random positions for new nodes to display on a simple canvas
    const newPositions = { ...nodePositions };
    let changed = false;
    nodes.forEach(n => {
      if (!newPositions[n.id]) {
        newPositions[n.id] = {
          x: 50 + Math.random() * 500,
          y: 50 + Math.random() * 300
        };
        changed = true;
      }
    });
    if (changed) setNodePositions(newPositions);
  }, [nodes]);

  useEffect(() => {
    drawGraph();
  }, [nodes, edges, nodePositions, currentPath, stepIndex, selectedNode, selectedEdge]);

  const drawGraph = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw edges
    edges.forEach(edge => {
      const sourcePos = nodePositions[edge.source];
      const targetPos = nodePositions[edge.target];
      if (!sourcePos || !targetPos) return;

      // Check if edge is part of current step path
      let isPath = false;
      let isCurrentStep = false;
      
      if (currentPath.length > 0 && stepIndex >= 0) {
        for (let i = 0; i < currentPath.length - 1; i++) {
          if ((currentPath[i] === edge.source && currentPath[i+1] === edge.target) || 
              (currentPath[i] === edge.target && currentPath[i+1] === edge.source)) {
            
            // Only highlight up to current step
            if (i < stepIndex) {
              isPath = true;
            }
            if (i === stepIndex - 1) {
              isCurrentStep = true;
            }
            break;
          }
        }
      }

      ctx.beginPath();
      ctx.moveTo(sourcePos.x, sourcePos.y);
      ctx.lineTo(targetPos.x, targetPos.y);
      
      if (edge.id === selectedEdge) {
        ctx.strokeStyle = '#ef4444'; // Highlight selected edge in red
        ctx.lineWidth = 5;
      } else if (isCurrentStep) {
        ctx.strokeStyle = '#fca311'; // highlight current step
        ctx.lineWidth = 4;
      } else if (isPath) {
        ctx.strokeStyle = '#14b8a6'; // path traveled
        ctx.lineWidth = 3;
      } else {
        ctx.strokeStyle = 'rgba(255,255,255,0.2)';
        ctx.lineWidth = 2;
      }
      ctx.stroke();

      // Draw weight text
      const midX = (sourcePos.x + targetPos.x) / 2;
      const midY = (sourcePos.y + targetPos.y) / 2;
      ctx.fillStyle = 'white';
      ctx.font = '12px Arial';
      ctx.fillText(edge.weight.toString() + unit, midX, midY - 5);
    });

    // Draw nodes
    nodes.forEach(node => {
      const pos = nodePositions[node.id];
      if (!pos) return;

      const isStart = currentPath.length > 0 && node.id === currentPath[0];
      const isEnd = currentPath.length > 0 && node.id === currentPath[currentPath.length - 1];
      const isCurrentLocation = currentPath.length > 0 && stepIndex >= 0 && node.id === currentPath[stepIndex];

      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 15, 0, 2 * Math.PI);
      
      if (isCurrentLocation) {
        ctx.fillStyle = '#fca311'; // active location
      } else if (isStart) {
        ctx.fillStyle = '#10b981'; // green for start
      } else if (isEnd) {
        ctx.fillStyle = '#ef4444'; // red for end
      } else {
        ctx.fillStyle = node.type === 'sensor' ? '#3b82f6' : '#8b5cf6';
      }
      
      ctx.fill();
      
      if (node.id === selectedNode) {
        ctx.strokeStyle = '#fca311'; // Highlight selected node
        ctx.lineWidth = 4;
      } else {
        ctx.strokeStyle = 'rgba(255,255,255,0.8)';
        ctx.lineWidth = 2;
      }
      
      ctx.stroke();

      // Node label
      ctx.fillStyle = 'white';
      ctx.font = '12px Arial';
      ctx.fillText(node.name, pos.x - 10, pos.y + 25);
    });
  };

  const getMousePos = (e) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };
  };

  const distToSegmentSquared = (p, v, w) => {
    const l2 = Math.pow(v.x - w.x, 2) + Math.pow(v.y - w.y, 2);
    if (l2 === 0) return Math.pow(p.x - v.x, 2) + Math.pow(p.y - v.y, 2);
    let t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
    t = Math.max(0, Math.min(1, t));
    return Math.pow(p.x - (v.x + t * (w.x - v.x)), 2) + Math.pow(p.y - (v.y + t * (w.y - v.y)), 2);
  };

  const handleMouseDown = (e) => {
    const pos = getMousePos(e);
    let clickedNode = null;
    let clickedEdge = null;
    
    // Check nodes first
    for (let i = nodes.length - 1; i >= 0; i--) {
      const node = nodes[i];
      const nPos = nodePositions[node.id];
      if (!nPos) continue;
      const dist = Math.sqrt(Math.pow(pos.x - nPos.x, 2) + Math.pow(pos.y - nPos.y, 2));
      if (dist <= 15) {
        clickedNode = node.id;
        setDraggingNode(node.id);
        setDragOffset({ x: pos.x - nPos.x, y: pos.y - nPos.y });
        break;
      }
    }
    
    // If no node clicked, check edges
    if (!clickedNode) {
      for (const edge of edges) {
        const sourcePos = nodePositions[edge.source];
        const targetPos = nodePositions[edge.target];
        if (!sourcePos || !targetPos) continue;
        const d2 = distToSegmentSquared(pos, sourcePos, targetPos);
        if (d2 <= 25) { // within 5 pixels
          clickedEdge = edge.id;
          break;
        }
      }
    }
    
    setSelectedNode(clickedNode);
    setSelectedEdge(clickedEdge);
  };

  const handleMouseMove = (e) => {
    if (!draggingNode) return;
    const pos = getMousePos(e);
    setNodePositions(prev => ({
      ...prev,
      [draggingNode]: {
        x: pos.x - dragOffset.x,
        y: pos.y - dragOffset.y
      }
    }));
  };

  const handleMouseUp = () => {
    setDraggingNode(null);
  };

  const handleAddNode = (e) => {
    e.preventDefault();
    if (!newNodeName) return;
    
    const newNode = {
      id: `node_${Date.now()}`,
      name: newNodeName,
      type: newNodeType,
      location: newNodeLocation
    };
    
    setNodes([...nodes, newNode]);
    setNewNodeName('');
    setNewNodeLocation('');
  };

  const handleDeleteNode = (id) => {
    setNodes(nodes.filter(n => n.id !== id));
    setEdges(edges.filter(e => e.source !== id && e.target !== id));
    resetPath();
  };

  const handleAddEdge = (e) => {
    e.preventDefault();
    if (!newEdgeSource || !newEdgeTarget || newEdgeSource === newEdgeTarget) return;
    
    // Check if edge already exists
    const exists = edges.find(e => 
      (e.source === newEdgeSource && e.target === newEdgeTarget) ||
      (e.source === newEdgeTarget && e.target === newEdgeSource)
    );
    if (exists) return;

    const newEdge = {
      id: `edge_${Date.now()}`,
      source: newEdgeSource,
      target: newEdgeTarget,
      weight: parseFloat(newEdgeWeight) || 1.0
    };
    
    setEdges([...edges, newEdge]);
  };

  const handleDeleteEdge = (id) => {
    setEdges(edges.filter(e => e.id !== id));
    resetPath();
  };

  const resetPath = () => {
    setCurrentPath([]);
    setPathDistance(0);
    setStepIndex(-1);
    setErrorMsg('');
  };

  const computePath = async () => {
    if (!sourceNode || !targetNode) {
      setErrorMsg("Select both source and target.");
      return;
    }
    
    resetPath();
    
    try {
      const graphData = { nodes, edges };
      const response = await apiFetch('/api/navigation/shortest-path', {
        method: 'POST',
        body: JSON.stringify({
          graph: graphData,
          source_id: sourceNode,
          target_id: targetNode
        })
      });
      
      setCurrentPath(response.path_nodes);
      setPathDistance(response.total_distance);
      setStepIndex(0); // Start at index 0
    } catch (err) {
      setErrorMsg(err.message || "No path found");
    }
  };

  const fetchDryRun = async () => {
    if (nodes.length === 0) {
      setErrorMsg("Graph is empty. Build a graph first.");
      return;
    }
    try {
      const graphData = { nodes, edges };
      const response = await apiFetch('/api/navigation/dry-run', {
        method: 'POST',
        body: JSON.stringify(graphData)
      });
      setDryRunData(response);
      setDryRunStep(0);
      setShowDryRun(true);
    } catch (err) {
      setErrorMsg(err.message || "Failed to fetch dry run");
    }
  };

  return (
    <div className="navigation-page">
      <div className="page-header" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start'}}>
        <div>
          <h2>Laboratory Navigation Network</h2>
          <p>Emergency response navigation system mapping sensors and transit routes via Floyd-Warshall.</p>
        </div>
        <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
          <span style={{color: 'var(--text-muted)'}}>Distance Unit:</span>
          <select value={unit} onChange={e => setUnit(e.target.value)} style={{background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', padding: '0.25rem 0.5rem', borderRadius: '4px'}}>
            <option value="m">Meters (m)</option>
            <option value="km">Kilometers (km)</option>
          </select>
        </div>
      </div>

      <div className="navigation-grid">
        <div className="nav-sidebar">
          {/* Node Builder */}
          <Card className="builder-card">
            <h3><Map size={18} /> Graph Builder</h3>
            <form onSubmit={handleAddNode} className="builder-form">
              <input 
                type="text" 
                placeholder="Node Name" 
                value={newNodeName} 
                onChange={e => setNewNodeName(e.target.value)} 
                required 
              />
              <select value={newNodeType} onChange={e => setNewNodeType(e.target.value)}>
                <option value="sensor">Sensor Node</option>
                <option value="transit">Transit Node</option>
              </select>
              <input 
                type="text" 
                placeholder="Location Info (Optional)" 
                value={newNodeLocation} 
                onChange={e => setNewNodeLocation(e.target.value)} 
              />
              <Button type="submit" size="sm" variant="primary">Add Node</Button>
            </form>

            {/* Edge Builder */}
            <h4 style={{marginTop:'1rem'}}>Connections</h4>
            <form onSubmit={handleAddEdge} className="builder-form">
              <select value={newEdgeSource} onChange={e => setNewEdgeSource(e.target.value)} required>
                <option value="">Source...</option>
                {nodes.map(n => <option key={n.id} value={n.id}>{n.name}</option>)}
              </select>
              <select value={newEdgeTarget} onChange={e => setNewEdgeTarget(e.target.value)} required>
                <option value="">Target...</option>
                {nodes.map(n => <option key={n.id} value={n.id}>{n.name}</option>)}
              </select>
              <input 
                type="number" 
                step="0.1" 
                min="0.1"
                placeholder={`Distance (${unit})`} 
                value={newEdgeWeight} 
                onChange={e => setNewEdgeWeight(e.target.value)} 
                required 
              />
              <Button type="submit" size="sm" variant="secondary">Link Nodes</Button>
            </form>

          </Card>
        </div>

        <div className="nav-main">
          {/* Visual Canvas */}
          <Card className="canvas-card">
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', marginBottom: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem'}}>
              <span>Tip: Click a node or edge to select it, or drag to move!</span>
              <div>
                {selectedNode && (
                  <Button 
                    type="button"
                    variant="danger" 
                    size="sm" 
                    onClick={() => {
                      handleDeleteNode(selectedNode);
                      setSelectedNode(null);
                    }}
                  >
                    Delete Selected Node
                  </Button>
                )}
                {selectedEdge && (
                  <Button 
                    type="button"
                    variant="danger" 
                    size="sm" 
                    onClick={() => {
                      handleDeleteEdge(selectedEdge);
                      setSelectedEdge(null);
                    }}
                  >
                    Delete Selected Edge
                  </Button>
                )}
              </div>
            </div>
            <canvas 
              ref={canvasRef} 
              width={600} 
              height={400} 
              className="nav-canvas" 
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              style={{ cursor: draggingNode ? 'grabbing' : 'grab' }}
            />
          </Card>

          {/* Route Explorer */}
          <Card className="explorer-card">
            <h3>Route Explorer</h3>
            <div className="explorer-controls">
              <select value={sourceNode} onChange={e => setSourceNode(e.target.value)}>
                <option value="">Start from...</option>
                {nodes.map(n => <option key={n.id} value={n.id}>{n.name}</option>)}
              </select>
              <ArrowRight size={18} style={{color: 'var(--text-muted)'}} />
              <select value={targetNode} onChange={e => setTargetNode(e.target.value)}>
                <option value="">Destination...</option>
                {nodes.map(n => <option key={n.id} value={n.id}>{n.name}</option>)}
              </select>
              <Button onClick={computePath} variant="primary"><Play size={16}/> Show Route</Button>
              <Button onClick={fetchDryRun} variant="secondary">Visualize Matrix Updates</Button>
            </div>

            {errorMsg && <div className="text-danger" style={{marginTop:'1rem'}}>{errorMsg}</div>}

            {currentPath.length > 0 && (
              <div className="path-display">
                <div className="path-stats">
                  <strong>Total Distance:</strong> {pathDistance}{unit} | <strong>Stops:</strong> {currentPath.length}
                </div>
                
                <div className="step-navigator">
                  <Button 
                    variant="secondary" 
                    size="sm"
                    disabled={stepIndex <= 0} 
                    onClick={() => setStepIndex(stepIndex - 1)}
                  >
                    <ArrowLeft size={16} /> Backward
                  </Button>
                  
                  <div className="current-step-info" style={{textAlign: 'center'}}>
                    {stepIndex >= 0 && stepIndex < currentPath.length - 1 ? (
                      (() => {
                        const currNode = nodes.find(n => n.id === currentPath[stepIndex])?.name;
                        const nextNode = nodes.find(n => n.id === currentPath[stepIndex+1])?.name;
                        const edge = edges.find(e => 
                          (e.source === currentPath[stepIndex] && e.target === currentPath[stepIndex+1]) ||
                          (e.target === currentPath[stepIndex] && e.source === currentPath[stepIndex+1])
                        );
                        return (
                          <>
                            <span style={{color: '#fca311', fontWeight: 'bold', display: 'block'}}>
                              Step {stepIndex + 1}: {currNode}
                            </span>
                            <small style={{color: 'white', fontSize: '0.85rem'}}>
                              Next: {nextNode} ({edge?.weight}{unit} away)
                            </small>
                          </>
                        );
                      })()
                    ) : (
                      <span style={{color: '#10b981', fontWeight: 'bold'}}>
                        Arrived at {nodes.find(n => n.id === currentPath[currentPath.length - 1])?.name}!
                      </span>
                    )}
                  </div>

                  <Button 
                    variant="secondary" 
                    size="sm"
                    disabled={stepIndex >= currentPath.length - 1} 
                    onClick={() => setStepIndex(stepIndex + 1)}
                  >
                    Forward <ArrowRight size={16} />
                  </Button>
                </div>

                <div className="full-route">
                  {currentPath.map((nodeId, idx) => {
                    const node = nodes.find(n => n.id === nodeId);
                    let nextDist = "";
                    if (idx < currentPath.length - 1) {
                      const nextId = currentPath[idx+1];
                      const edge = edges.find(e => (e.source === nodeId && e.target === nextId) || (e.target === nodeId && e.source === nextId));
                      if (edge) nextDist = edge.weight;
                    }
                    return (
                      <span key={`${nodeId}-${idx}`} className={`path-node ${idx === stepIndex ? 'active' : ''}`}>
                        {node?.name} {idx < currentPath.length - 1 && <span style={{color: 'var(--text-muted)'}}> → ({nextDist}{unit}) → </span>}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
          </Card>
        </div>
      </div>

      {showDryRun && dryRunData && (
        <div className="dry-run-modal">
          <div className="dry-run-content glass-panel">
            <div className="dry-run-header">
              <h3>Floyd-Warshall Matrix Visualization</h3>
              <Button variant="danger" size="sm" onClick={() => setShowDryRun(false)}>Close</Button>
            </div>
            
            <div className="dry-run-controls">
              <Button variant="secondary" disabled={dryRunStep <= 0} onClick={() => setDryRunStep(dryRunStep - 1)}>Previous Step</Button>
              <span style={{fontWeight: 'bold', color: '#fca311'}}>
                {dryRunData.history[dryRunStep].step} 
                <span style={{color:'white', marginLeft:'10px'}}>({dryRunStep + 1} of {dryRunData.history.length})</span>
              </span>
              <Button variant="secondary" disabled={dryRunStep >= dryRunData.history.length - 1} onClick={() => setDryRunStep(dryRunStep + 1)}>Next Step</Button>
            </div>

            <div className="dry-run-matrix-container">
              <table className="dry-run-matrix">
                <thead>
                  <tr>
                    <th>Src \ Dst</th>
                    {dryRunData.nodes.map(n => <th key={n.id} title={n.name}>{n.name.substring(0,8)}..</th>)}
                  </tr>
                </thead>
                <tbody>
                  {dryRunData.nodes.map(rowNode => (
                    <tr key={rowNode.id}>
                      <th title={rowNode.name} style={{textAlign:'left'}}>{rowNode.name.substring(0,8)}..</th>
                      {dryRunData.nodes.map(colNode => {
                        const val = dryRunData.history[dryRunStep].matrix[rowNode.id]?.[colNode.id];
                        const displayVal = val === -1.0 ? "∞" : val;
                        return (
                          <td key={colNode.id} className={val !== -1.0 && val !== 0 ? 'has-path' : ''}>
                            {displayVal}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
