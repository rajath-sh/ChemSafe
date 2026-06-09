import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipForward, SkipBack, RotateCcw } from 'lucide-react';

export const BoyerMooreVisualizer = () => {
  const [text, setText] = useState('FINDINAHAYSTACKNEEDLE');
  const [pattern, setPattern] = useState('NEEDLE');
  const [steps, setSteps] = useState([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [metrics, setMetrics] = useState({ timeMs: 0, spaceBytes: 0 });
  const timerRef = useRef(null);

  useEffect(() => {
    return () => clearInterval(timerRef.current);
  }, []);

    const generateSteps = (t, p) => {
    const newSteps = [];
    let spaceUsed = 0;
    
    const t0 = performance.now();
    
    const m = p.length;
    const n = t.length;
    
    // Bad Character (Shift) table
    const badChar = {};
    spaceUsed += 256 * 4; 
    
    for (let i = 0; i < m - 1; i++) {
      badChar[p[i]] = m - 1 - i;
    }

    // Good Suffix table
    const goodSuffix = new Array(m).fill(m); // Initialize with m
    const border = new Array(m + 1).fill(0);
    spaceUsed += (m * 2) * 4;
    
    let i = m, j = m + 1;
    border[i] = j;
    while (i > 0) {
      while (j <= m && p[i - 1] !== p[j - 1]) {
        if (goodSuffix[j - 1] === m) goodSuffix[j - 1] = j - i;
        j = border[j];
      }
      i--; j--;
      border[i] = j;
    }
    j = border[0];
    for (i = 0; i < m; i++) {
      if (goodSuffix[i] === m) goodSuffix[i] = j;
      if (i === j) j = border[j];
    }
    
    let tIdx = m - 1;
    let found = false;
    
    while (tIdx <= n - 1) {
      let k = 0;
      while (k < m && p[m - 1 - k] === t[tIdx - k]) {
        newSteps.push({ textIdx: tIdx - k, patIdx: m - 1 - k, match: true, shift: tIdx - m + 1, badChar: { ...badChar }, goodSuffix: [...goodSuffix] });
        k++;
      }
      
      if (k === m) {
        newSteps.push({ found: true, index: tIdx - m + 1, shift: tIdx - m + 1, badChar: { ...badChar }, goodSuffix: [...goodSuffix] });
        found = true;
        break; // Stop at first match for visualization
      } else {
        newSteps.push({ textIdx: tIdx - k, patIdx: m - 1 - k, match: false, shift: tIdx - m + 1, badChar: { ...badChar }, goodSuffix: [...goodSuffix] });
        
        const mismatchedChar = t[tIdx - k];
        // Horspool bad char shift from the end of the window
        const windowEndChar = t[tIdx];
        const bcShift = badChar[windowEndChar] !== undefined ? badChar[windowEndChar] : m;
        
        // Good suffix shift (based on the mismatched pattern index m - 1 - k)
        // Wait, goodSuffix array is indexed 0 to m-1.
        const gsShift = goodSuffix[m - 1 - k] || m; 
        
        const s = Math.max(bcShift, gsShift); // Use max of both heuristics
        tIdx += s;
      }
    }
    
    if (!found) {
      newSteps.push({ found: false, index: -1, shift: -1, badChar: { ...badChar }, goodSuffix: [...goodSuffix] });
    }
    
    const t1 = performance.now();
    
    setMetrics({
      timeMs: (t1 - t0).toFixed(4),
      spaceBytes: spaceUsed
    });

    setSteps([{ shift: 0 }, ...newSteps]);
    setCurrentStepIndex(0);
    setIsPlaying(false);
  };

  const handleStart = () => {
    if (!text || !pattern || pattern.length > text.length) return;
    generateSteps(text, pattern);
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
      }, 800);
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

  const currentStep = steps[currentStepIndex] || { shift: 0 };

  return (
    <>
      {/* Moved Metrics to the top to avoid scrolling */}
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
          <div className="metric-value">Θ(n/m) Best | O(nm) Worst</div>
        </div>
      </div>

      <div className="control-panel">
        <div className="input-group">
          <label>Text</label>
          <input type="text" value={text} onChange={(e) => setText(e.target.value.toUpperCase())} />
        </div>
        <div className="input-group">
          <label>Pattern</label>
          <input type="text" value={pattern} onChange={(e) => setPattern(e.target.value.toUpperCase())} />
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

      <div className="visualization-area" style={{ flexDirection: 'column', gap: '20px', alignItems: 'flex-start', minHeight: '200px' }}>
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
          {text.split('').map((char, idx) => {
            let bgColor = '#374151'; // default gray
            if (currentStep.found && idx >= currentStep.index && idx < currentStep.index + pattern.length) bgColor = '#10b981'; // green found
            else if (idx === currentStep.textIdx) bgColor = currentStep.match ? '#10b981' : '#ef4444';
            
            return (
              <div key={'t'+idx} style={{ 
                width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                backgroundColor: bgColor, color: 'white', fontWeight: 'bold', borderRadius: '4px',
                border: '1px solid #4b5563'
              }}>
                {char}
              </div>
            );
          })}
        </div>
        
        <div style={{ display: 'flex', gap: '4px', marginLeft: `${Math.max(0, currentStep.shift) * 44}px`, transition: 'margin 0.3s ease' }}>
          {pattern.split('').map((char, idx) => {
            let bgColor = '#4f46e5'; // default blue
            if (idx === currentStep.patIdx) bgColor = currentStep.match ? '#10b981' : '#ef4444';
            
            return (
              <div key={'p'+idx} style={{ 
                width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                backgroundColor: bgColor, color: 'white', fontWeight: 'bold', borderRadius: '4px',
                border: '1px solid #4b5563'
              }}>
                {char}
              </div>
            );
          })}
        </div>

        {currentStep.badChar && (
          <div style={{ display: 'flex', gap: '20px', width: '100%' }}>
            <div style={{ marginTop: '20px', padding: '16px', background: 'var(--bg-surface-alt)', borderRadius: '8px', flex: 1 }}>
              <h4 style={{ margin: '0 0 10px 0', color: 'var(--text-secondary)' }}>Bad Character (Shift) Table</h4>
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                {Object.entries(currentStep.badChar).map(([char, val]) => (
                  <div key={char} style={{ background: '#1f2937', padding: '4px 8px', borderRadius: '4px', border: '1px solid #374151' }}>
                    <strong style={{ color: '#60a5fa' }}>{char}</strong>: {val}
                  </div>
                ))}
                <div style={{ background: '#1f2937', padding: '4px 8px', borderRadius: '4px', border: '1px solid #374151' }}>
                  <strong style={{ color: '#9ca3af' }}>*</strong>: {pattern.length}
                </div>
              </div>
            </div>

            <div style={{ marginTop: '20px', padding: '16px', background: 'var(--bg-surface-alt)', borderRadius: '8px', flex: 1 }}>
              <h4 style={{ margin: '0 0 10px 0', color: 'var(--text-secondary)' }}>Good Suffix Table</h4>
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                {currentStep.goodSuffix.map((val, idx) => (
                  <div key={idx} style={{ background: '#1f2937', padding: '4px 8px', borderRadius: '4px', border: '1px solid #374151', textAlign: 'center' }}>
                    <div style={{ fontSize: '10px', color: '#9ca3af' }}>idx {idx}</div>
                    <strong>{val}</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        {currentStepIndex === steps.length - 1 && steps.length > 1 && (
          <div style={{ marginTop: '20px', padding: '16px', background: currentStep.found ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', border: `1px solid ${currentStep.found ? '#10b981' : '#ef4444'}`, borderRadius: '8px', width: '100%' }}>
            <h3 style={{ margin: '0 0 10px 0', color: currentStep.found ? '#10b981' : '#ef4444' }}>Final Output</h3>
            <p style={{ margin: 0, color: 'var(--text-primary)', fontSize: '16px' }}>
              {currentStep.found 
                ? `Pattern found starting at index ${currentStep.index}.` 
                : 'Pattern not found in the text.'}
            </p>
          </div>
        )}
      </div>
    </>
  );
};
