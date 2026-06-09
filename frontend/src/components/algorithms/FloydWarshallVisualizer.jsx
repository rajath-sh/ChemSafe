import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipForward, SkipBack, RotateCcw } from 'lucide-react';

export const FloydWarshallVisualizer = () => {
  const INF = 999;
  
  const generateRandomMatrix = (n) => {
    const graph = Array.from({ length: n }, () => Array(n).fill(INF));
    for (let i = 0; i < n; i++) graph[i][i] = 0;
    for(let i=0; i<n; i++) {
      for(let j=0; j<n; j++) {
        if (i !== j && Math.random() > 0.5) {
          graph[i][j] = Math.floor(Math.random() * 20) + 1;
        }
      }
    }
    return graph;
  };

  const [nodesCount, setNodesCount] = useState(4);
  const [initialMatrix, setInitialMatrix] = useState(() => generateRandomMatrix(4));
  const [steps, setSteps] = useState([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [metrics, setMetrics] = useState({ timeMs: 0, spaceBytes: 0 });
  const timerRef = useRef(null);

  useEffect(() => {
    return () => clearInterval(timerRef.current);
  }, []);

  const generateSteps = (initialGraph) => {
    const n = initialGraph.length;
    const newSteps = [];
    
    let spaceUsed = n * n * 8; // matrix size
    const dist = initialGraph.map(row => [...row]);
    
    const t0 = performance.now();

    newSteps.push({ dist: dist.map(row => [...row]), k: -1, i: -1, j: -1 });

    for (let k = 0; k < n; k++) {
      for (let i = 0; i < n; i++) {
        for (let j = 0; j < n; j++) {
          if (dist[i][k] + dist[k][j] < dist[i][j]) {
            dist[i][j] = dist[i][k] + dist[k][j];
            newSteps.push({ dist: dist.map(row => [...row]), k, i, j, updated: true });
          } else {
            newSteps.push({ dist: dist.map(row => [...row]), k, i, j, updated: false });
          }
        }
      }
    }

    const t1 = performance.now();
    const timeTaken = t1 - t0;

    setMetrics({
      timeMs: timeTaken === 0 ? "< 0.0001" : timeTaken.toFixed(4),
      spaceBytes: spaceUsed
    });

    setSteps(newSteps);
    setCurrentStepIndex(0);
    setIsPlaying(false);
  };

  const handleNodesChange = (e) => {
    const val = parseInt(e.target.value, 10);
    setNodesCount(e.target.value);
    if (!isNaN(val) && val >= 3 && val <= 8) {
      setInitialMatrix(generateRandomMatrix(val));
      setSteps([]);
    }
  };

  const handleMatrixChange = (i, j, value) => {
    const newMatrix = [...initialMatrix];
    newMatrix[i] = [...newMatrix[i]];
    if (value.trim() === '' || value === '∞') {
      newMatrix[i][j] = INF;
    } else {
      const parsed = parseInt(value, 10);
      newMatrix[i][j] = isNaN(parsed) ? INF : parsed;
    }
    setInitialMatrix(newMatrix);
  };

  const handleStart = () => {
    generateSteps(initialMatrix);
  };

  useEffect(() => {
    if (isPlaying && steps.length > 0) {
      timerRef.current = setInterval(() => {
        setCurrentStepIndex(prev => {
          if (prev >= steps.length - 1) {
            clearInterval(timerRef.current);
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 50); // fast animation because O(N^3)
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [isPlaying, steps]);

  const togglePlay = () => setIsPlaying(!isPlaying);
  const stepForward = () => {
    if (currentStepIndex < steps.length - 1) setCurrentStepIndex(currentStepIndex + 1);
    setIsPlaying(false);
  };
  const stepBack = () => {
    if (currentStepIndex > 0) setCurrentStepIndex(currentStepIndex - 1);
    setIsPlaying(false);
  };
  const reset = () => {
    setIsPlaying(false);
    setCurrentStepIndex(0);
  };

  const currentStep = steps[currentStepIndex] || { dist: [], k: -1, i: -1, j: -1 };

  return (
    <>
      <div className="metrics-panel">
        <div className="metric-card">
          <div className="metric-label">Execution Time (ms)</div>
          <div className="metric-value">{metrics.timeMs} ms</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Approx. Extra Space (Bytes)</div>
          <div className="metric-value">{metrics.spaceBytes} B</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Time Complexity</div>
          <div className="metric-value">Θ(n³)</div>
        </div>
      </div>

      <div className="control-panel">
        <div className="input-group" style={{ maxWidth: '150px' }}>
          <label>Nodes (3-8)</label>
          <input type="number" min="3" max="8" value={nodesCount} onChange={handleNodesChange} />
        </div>
        <button className="view-syllabus-btn" onClick={handleStart} style={{ height: '42px' }}>Initialize / Run</button>
        
        <div className="button-group" style={{ marginLeft: 'auto' }}>
          <button className="btn-icon" onClick={reset} disabled={steps.length === 0}><RotateCcw size={18}/></button>
          <button className="btn-icon" onClick={stepBack} disabled={currentStepIndex <= 0}><SkipBack size={18}/></button>
          <button className="btn-icon active" onClick={togglePlay} disabled={steps.length === 0 || currentStepIndex >= steps.length - 1}>
            {isPlaying ? <Pause size={18}/> : <Play size={18}/>}
          </button>
          <button className="btn-icon" onClick={stepForward} disabled={currentStepIndex >= steps.length - 1}><SkipForward size={18}/></button>
        </div>
      </div>

      <div className="visualization-area" style={{ flexDirection: 'column', gap: '20px' }}>
        
        {steps.length === 0 && (
          <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center', background: 'var(--bg-surface-alt)', borderRadius: '8px', border: '1px solid #374151' }}>
            <h3 style={{ color: 'var(--text-secondary)', margin: '0 0 5px 0' }}>Edit Initial Graph Matrix</h3>
            <p style={{ color: '#9ca3af', fontSize: '13px', margin: '0 0 15px 0' }}>Diagonal is 0. Leave empty for ∞ (no edge).</p>
            <table style={{ borderCollapse: 'collapse' }}>
              <tbody>
                {initialMatrix.map((row, i) => (
                  <tr key={i}>
                    {row.map((val, j) => (
                      <td key={j} style={{ padding: '3px' }}>
                        <input 
                          type="text" 
                          value={val === INF ? '' : val}
                          onChange={(e) => handleMatrixChange(i, j, e.target.value)}
                          disabled={i === j}
                          style={{ 
                            width: '45px', height: '45px', textAlign: 'center', 
                            background: i === j ? '#1f2937' : '#374151', 
                            border: '1px solid #4b5563', color: i === j ? '#6b7280' : 'white', 
                            borderRadius: '4px', fontWeight: 'bold'
                          }}
                          placeholder={i === j ? '0' : '∞'}
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {currentStep.dist.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{ marginBottom: '16px', fontWeight: 'bold', color: 'var(--color-primary)' }}>
              k = {currentStep.k !== -1 ? currentStep.k : '-'}, 
              i = {currentStep.i !== -1 ? currentStep.i : '-'}, 
              j = {currentStep.j !== -1 ? currentStep.j : '-'}
            </div>
            
            <table style={{ borderCollapse: 'collapse', background: 'var(--bg-surface-alt)', color: 'var(--text-primary)' }}>
              <thead>
                <tr>
                  <th style={{ padding: '10px', border: '1px solid var(--border-light)', background: '#1f2937' }}></th>
                  {currentStep.dist.map((_, colIdx) => (
                    <th key={colIdx} style={{ padding: '10px', border: '1px solid var(--border-light)', background: '#1f2937', color: colIdx === currentStep.k ? '#f59e0b' : 'var(--text-primary)' }}>{colIdx}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {currentStep.dist.map((row, rowIdx) => (
                  <tr key={rowIdx}>
                    <th style={{ padding: '10px', border: '1px solid var(--border-light)', background: '#1f2937', color: rowIdx === currentStep.k ? '#f59e0b' : 'var(--text-primary)' }}>{rowIdx}</th>
                    {row.map((val, colIdx) => {
                      let bgColor = 'transparent';
                      let color = 'var(--text-primary)';
                      
                      if (rowIdx === currentStep.i && colIdx === currentStep.j) {
                        bgColor = currentStep.updated ? '#10b981' : '#ef4444';
                        color = '#fff';
                      } else if (rowIdx === currentStep.i && colIdx === currentStep.k) {
                        bgColor = '#3b82f6';
                        color = '#fff';
                      } else if (rowIdx === currentStep.k && colIdx === currentStep.j) {
                        bgColor = '#3b82f6';
                        color = '#fff';
                      }

                      return (
                        <td key={colIdx} style={{ 
                          padding: '10px 15px', 
                          border: '1px solid var(--border-light)', 
                          textAlign: 'center',
                          backgroundColor: bgColor,
                          color: color,
                          fontWeight: bgColor !== 'transparent' ? 'bold' : 'normal',
                          transition: 'background-color 0.2s ease'
                        }}>
                          {val === 999 ? '∞' : val}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {currentStepIndex === steps.length - 1 && steps.length > 1 && (
          <div style={{ marginTop: '20px', padding: '16px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid #10b981', borderRadius: '8px', width: '100%' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#10b981' }}>Final Output</h3>
            <p style={{ margin: 0, color: 'var(--text-primary)', fontSize: '16px' }}>
              All-Pairs Shortest Path matrix has been fully computed.
            </p>
          </div>
        )}
      </div>
    </>
  );
};
