import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipForward, SkipBack, RotateCcw } from 'lucide-react';

export const MergeSortVisualizer = () => {
  const [array, setArray] = useState([38, 27, 43, 3, 9, 82, 10]);
  const [inputVal, setInputVal] = useState('38, 27, 43, 3, 9, 82, 10');
  const [steps, setSteps] = useState([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [metrics, setMetrics] = useState({ timeMs: 0, spaceBytes: 0 });
  const timerRef = useRef(null);

  useEffect(() => {
    return () => clearInterval(timerRef.current);
  }, []);

  const generateSteps = (arr) => {
    const newSteps = [];
    let spaceUsed = arr.length * 8; 
    let visited = [];

    const mergeSort = (arr, l, r) => {
      if (l >= r) {
        if (!visited.includes(`${l}-${r}`)) visited.push(`${l}-${r}`);
        return;
      }
      const m = l + Math.floor((r - l) / 2);
      mergeSort(arr, l, m);
      mergeSort(arr, m + 1, r);
      if (!visited.includes(`${l}-${r}`)) visited.push(`${l}-${r}`);
      merge(arr, l, m, r);
    };

    const merge = (arr, l, m, r) => {
      const n1 = m - l + 1;
      const n2 = r - m;
      const L = new Array(n1);
      const R = new Array(n2);
      spaceUsed += (n1 + n2) * 8; 

      for (let i = 0; i < n1; i++) L[i] = arr[l + i];
      for (let j = 0; j < n2; j++) R[j] = arr[m + 1 + j];

      let i = 0, j = 0, k = l;
      while (i < n1 && j < n2) {
        newSteps.push({ array: [...arr], comparing: [l + i, m + 1 + j], merging: [], activeRange: [l, r], visited: [...visited] });
        if (L[i] <= R[j]) {
          arr[k] = L[i];
          i++;
        } else {
          arr[k] = R[j];
          j++;
        }
        newSteps.push({ array: [...arr], comparing: [], merging: [k], activeRange: [l, r], visited: [...visited] });
        k++;
      }

      while (i < n1) {
        arr[k] = L[i];
        newSteps.push({ array: [...arr], comparing: [], merging: [k], activeRange: [l, r], visited: [...visited] });
        i++;
        k++;
      }

      while (j < n2) {
        arr[k] = R[j];
        newSteps.push({ array: [...arr], comparing: [], merging: [k], activeRange: [l, r], visited: [...visited] });
        j++;
        k++;
      }
    };

    const arrCopy = [...arr];
    
    const t0 = performance.now();
    
    // Push an initial step where nothing is visited yet (except maybe the root conceptually, but we build bottom up)
    newSteps.push({ array: [...arrCopy], comparing: [], merging: [], activeRange: null, visited: [] });
    
    mergeSort(arrCopy, 0, arrCopy.length - 1);
    const t1 = performance.now();
    
    newSteps.push({ array: [...arrCopy], comparing: [], merging: [], sorted: true, visited: [...visited] });

    setMetrics({
      timeMs: (t1 - t0).toFixed(4),
      spaceBytes: spaceUsed
    });

    setSteps(newSteps);
    setCurrentStepIndex(0);
    setIsPlaying(false);
  };

  const handleStart = () => {
    const newArr = inputVal.split(',').map(n => parseInt(n.trim(), 10)).filter(n => !isNaN(n));
    setArray(newArr);
    generateSteps(newArr);
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
      }, 500);
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

  const currentStep = steps[currentStepIndex] || { array, comparing: [], merging: [] };
  const maxVal = Math.max(...array, 1); // Avoid 0 division

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
          <div className="metric-value">Θ(n log n)</div>
        </div>
      </div>

      <div className="control-panel">
        <div className="input-group">
          <label>Array Input (comma separated)</label>
          <input 
            type="text" 
            value={inputVal} 
            onChange={(e) => setInputVal(e.target.value)} 
            placeholder="e.g. 5, 2, 9, 1"
          />
        </div>
        <button className="view-syllabus-btn" onClick={handleStart} style={{ height: '42px' }}>Initialize</button>
        
        <div className="button-group" style={{ marginLeft: 'auto' }}>
          <button className="btn-icon" onClick={reset} disabled={steps.length === 0}><RotateCcw size={18}/></button>
          <button className="btn-icon" onClick={stepBack} disabled={currentStepIndex <= 0}><SkipBack size={18}/></button>
          <button className="btn-icon active" onClick={togglePlay} disabled={steps.length === 0 || currentStepIndex >= steps.length - 1}>
            {isPlaying ? <Pause size={18}/> : <Play size={18}/>}
          </button>
          <button className="btn-icon" onClick={stepForward} disabled={currentStepIndex >= steps.length - 1}><SkipForward size={18}/></button>
        </div>
      </div>

      <div className="visualization-area" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '40px' }}>
        
        {/* Bars Section */}
        <div style={{ width: '100%' }}>
          <h3 style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>Array State</h3>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '8px', minHeight: '150px' }}>
            {currentStep.array.map((val, idx) => {
              let bgColor = '#4b5563'; // default gray
              if (currentStep.sorted) bgColor = '#10b981'; // green sorted
              else if (currentStep.comparing?.includes(idx)) bgColor = '#ef4444'; // red comparing
              else if (currentStep.merging?.includes(idx)) bgColor = '#3b82f6'; // blue merging

              const heightPct = Math.max((val / maxVal) * 100, 5);

              return (
                <div 
                  key={idx} 
                  style={{ 
                    height: `${heightPct}%`, 
                    width: '40px', 
                    flexShrink: 0,
                    backgroundColor: bgColor,
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'center',
                    color: 'white',
                    fontWeight: 'bold',
                    paddingTop: '8px',
                    borderRadius: '4px 4px 0 0',
                    transition: 'height 0.3s ease, background-color 0.3s ease'
                  }}
                >
                  {val}
                </div>
              );
            })}
          </div>
        </div>

        {/* Tree Section */}
        <div style={{ width: '100%', overflowX: 'auto', paddingBottom: '20px' }}>
          <h3 style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>Recursion Tree (Splits)</h3>
          <div style={{ display: 'flex', justifyContent: 'center', minWidth: 'fit-content' }}>
            {(() => {
              const buildTree = (arr, l, r) => {
                if (l >= r) return { val: [arr[l]], left: null, right: null, l, r };
                const m = l + Math.floor((r - l) / 2);
                const left = buildTree(arr, l, m);
                const right = buildTree(arr, m + 1, r);
                return { val: arr.slice(l, r + 1), left, right, l, r };
              };
              
              if (array.length === 0) return null;
              // Build initial tree based on input array
              const treeRoot = buildTree(array, 0, array.length - 1);

              const renderNode = (node) => {
                if (!node) return null;
                
                // Determine if this node is active or sorted
                const isActive = currentStep.activeRange && currentStep.activeRange[0] === node.l && currentStep.activeRange[1] === node.r;
                const isSorted = currentStep.sorted;
                
                // Determine if this node is visible (dynamically created)
                const isVisible = isSorted || (currentStep.visited && currentStep.visited.includes(`${node.l}-${node.r}`));
                
                const bgColor = isActive ? 'rgba(59, 130, 246, 0.2)' : 'var(--bg-surface-alt)';
                const borderColor = isSorted ? '#10b981' : (isActive ? '#3b82f6' : '#4b5563');
                const textColor = isSorted ? '#10b981' : (isActive ? '#fff' : '#66fcf1');
                
                return (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', margin: '0 10px' }}>
                    <div style={{
                      padding: '8px 12px', background: bgColor, border: `2px solid ${borderColor}`,
                      borderRadius: '6px', color: textColor, fontWeight: 'bold', fontSize: '14px',
                      whiteSpace: 'nowrap', transition: 'all 0.3s ease',
                      boxShadow: isActive ? '0 0 10px rgba(59, 130, 246, 0.5)' : 'none',
                      opacity: isVisible ? 1 : 0
                    }}>
                      [{currentStep.array.slice(node.l, node.r + 1).join(', ')}]
                    </div>
                    {(node.left || node.right) && (
                      <div style={{ display: 'flex', marginTop: '15px', position: 'relative' }}>
                        <div style={{ 
                          position: 'absolute', top: '-15px', left: '25%', width: '50%', height: '15px', 
                          borderTop: '2px solid #4b5563', borderLeft: '2px solid #4b5563', borderRight: '2px solid #4b5563',
                          opacity: isVisible ? 1 : 0, transition: 'opacity 0.3s ease'
                        }} />
                        <div>{renderNode(node.left)}</div>
                        <div>{renderNode(node.right)}</div>
                      </div>
                    )}
                  </div>
                );
              };

              return renderNode(treeRoot);
            })()}
          </div>
        </div>

        {currentStepIndex === steps.length - 1 && steps.length > 1 && (
          <div style={{ marginTop: '20px', padding: '16px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid #10b981', borderRadius: '8px', width: '100%' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#10b981' }}>Final Output</h3>
            <p style={{ margin: 0, color: 'var(--text-primary)', fontSize: '16px' }}>
              Array successfully sorted: <strong>{currentStep.array.join(', ')}</strong>
            </p>
          </div>
        )}
      </div>
    </>
  );
};
