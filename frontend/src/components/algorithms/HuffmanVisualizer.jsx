import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipForward, SkipBack, RotateCcw } from 'lucide-react';

export const HuffmanVisualizer = () => {
  const [inputVal, setInputVal] = useState('CHEMSAFEALERTS');
  const [steps, setSteps] = useState([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [metrics, setMetrics] = useState({ timeMs: 0, spaceBytes: 0 });
  const timerRef = useRef(null);

  useEffect(() => {
    return () => clearInterval(timerRef.current);
  }, []);

  const generateSteps = (str) => {
    const newSteps = [];
    let spaceUsed = 0;
    
    const t0 = performance.now();
    
    // Frequency map
    const freq = {};
    for (let char of str) {
      freq[char] = (freq[char] || 0) + 1;
    }
    spaceUsed += Object.keys(freq).length * 16; 
    
    // Priority Queue (Nodes)
    let nodes = Object.keys(freq).map(char => ({ char, freq: freq[char], left: null, right: null }));
    spaceUsed += nodes.length * 32; 
    
    nodes.sort((a, b) => a.freq - b.freq);
    
    newSteps.push({ nodes: [...nodes], processing: null, stage: 'build' });
    
    while (nodes.length > 1) {
      const left = nodes.shift();
      const right = nodes.shift();
      
      const newNode = {
        char: left.char + right.char,
        freq: left.freq + right.freq,
        left,
        right
      };
      
      spaceUsed += 32;
      
      newSteps.push({ nodes: [left, right, ...nodes], processing: newNode, stage: 'build' });
      
      nodes.push(newNode);
      nodes.sort((a, b) => a.freq - b.freq);
      
      newSteps.push({ nodes: [...nodes], processing: null, stage: 'build' });
    }
    
    const root = nodes[0];
    const codes = {};
    
    const traverse = (node, code) => {
      if (!node) return;
      if (!node.left && !node.right) {
        codes[node.char] = code;
      }
      traverse(node.left, code + '0');
      traverse(node.right, code + '1');
    };
    
    if (root) {
      if (!root.left && !root.right) traverse(root, '0');
      else traverse(root, '');
    }
    
    // Add encode steps
    let encodedStr = '';
    for (let i = 0; i < str.length; i++) {
      const char = str[i];
      const code = codes[char];
      encodedStr += code;
      newSteps.push({ 
        nodes: [root], 
        codes, 
        stage: 'encode', 
        textIdx: i, 
        char: char, 
        code: code,
        currentEncoded: encodedStr 
      });
    }
    
    const t1 = performance.now();
    
    newSteps.push({ nodes: [root], codes, stage: 'done', finalEncoded: encodedStr, textIdx: -1 });
    
    setMetrics({
      timeMs: (t1 - t0).toFixed(4),
      spaceBytes: spaceUsed
    });

    setSteps([{ nodes: Object.keys(freq).map(char => ({ char, freq: freq[char] })), stage: 'init' }, ...newSteps]);
    setCurrentStepIndex(0);
    setIsPlaying(false);
  };

  const handleStart = () => {
    if (!inputVal) return;
    generateSteps(inputVal.toUpperCase());
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

  const currentStep = steps[currentStepIndex] || { nodes: [], stage: 'init' };

  // Recursive render for the tree
  const renderTree = (node) => {
    if (!node) return null;
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <div style={{
          width: '40px', height: '40px', borderRadius: '50%', background: 'var(--color-primary)',
          color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 'bold', border: '2px solid #fff', zIndex: 2
        }}>
          {node.freq}
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
          {node.char.length === 1 ? node.char : '*'}
        </div>
        
        {(node.left || node.right) && (
          <div style={{ display: 'flex', marginTop: '20px', position: 'relative' }}>
            <div style={{ position: 'absolute', top: '-20px', left: '25%', width: '50%', height: '20px', borderTop: '2px solid #4b5563', borderLeft: '2px solid #4b5563', borderRight: '2px solid #4b5563' }} />
            <div style={{ margin: '0 20px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <span style={{ fontSize: '10px', color: '#66fcf1', marginBottom: '2px' }}>0</span>
              {renderTree(node.left)}
            </div>
            <div style={{ margin: '0 20px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <span style={{ fontSize: '10px', color: '#66fcf1', marginBottom: '2px' }}>1</span>
              {renderTree(node.right)}
            </div>
          </div>
        )}
      </div>
    );
  };

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
          <label>String Input</label>
          <input type="text" value={inputVal} onChange={(e) => setInputVal(e.target.value)} />
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

      <div className="visualization-area" style={{ flexDirection: 'column', gap: '30px', alignItems: 'flex-start' }}>
        
        <div style={{ display: 'flex', flexDirection: 'row', gap: '30px', width: '100%', alignItems: 'flex-start' }}>
          {/* Left Side: Text and Encoding */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <h3 style={{ color: 'var(--text-secondary)', margin: 0 }}>Input String</h3>
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
              {inputVal.split('').map((char, idx) => {
                const isProcessing = currentStep.textIdx === idx;
                return (
                  <div key={idx} style={{ 
                    width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    backgroundColor: isProcessing ? '#10b981' : '#374151', 
                    color: 'white', fontWeight: 'bold', borderRadius: '4px',
                    border: isProcessing ? '2px solid #fff' : '1px solid #4b5563',
                    transition: 'all 0.2s ease'
                  }}>
                    {char}
                  </div>
                );
              })}
            </div>

            {(currentStep.stage === 'encode' || currentStep.stage === 'done') && (
              <>
                <h3 style={{ color: 'var(--text-secondary)', margin: '20px 0 0 0' }}>Encoded Bitstream</h3>
                <div style={{ padding: '16px', background: '#1a202c', border: '1px solid #2d3748', borderRadius: '8px', wordBreak: 'break-all', fontFamily: 'monospace', color: '#66fcf1', fontSize: '18px', letterSpacing: '2px' }}>
                  {currentStep.stage === 'done' ? currentStep.finalEncoded : currentStep.currentEncoded}
                </div>
              </>
            )}
          </div>

          {/* Right Side: Tree Building */}
          <div style={{ flex: 2, display: 'flex', flexDirection: 'column', gap: '20px', borderLeft: '1px solid #2d3748', paddingLeft: '30px', minHeight: '400px' }}>
            <h3 style={{ color: 'var(--text-secondary)', margin: 0 }}>Huffman Forest / Tree</h3>
            <div style={{ display: 'flex', gap: '40px', flexWrap: 'wrap', overflowX: 'auto', paddingBottom: '20px', alignItems: 'flex-start' }}>
              {currentStep.nodes?.map((node, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'center' }}>
                  {renderTree(node)}
                </div>
              ))}
            </div>

            {currentStep.processing && (
              <div style={{ marginTop: 'auto', padding: '15px', background: '#312e81', borderRadius: '8px', color: '#c7d2fe', textAlign: 'center' }}>
                Merging <strong>{currentStep.processing.left.char}</strong> ({currentStep.processing.left.freq}) and <strong>{currentStep.processing.right.char}</strong> ({currentStep.processing.right.freq})
              </div>
            )}
          </div>
        </div>

        {/* Bottom Section: Codes and Final Output */}
        {currentStep.codes && (
          <div style={{ width: '100%', marginTop: '10px' }}>
            <h3 style={{ color: 'var(--text-secondary)', margin: '0 0 10px 0' }}>Character Codes</h3>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              {Object.entries(currentStep.codes).map(([char, code]) => (
                <div key={char} style={{ background: '#1f2937', padding: '8px 16px', borderRadius: '6px', border: '1px solid #374151', fontSize: '16px' }}>
                  <strong style={{ color: '#60a5fa' }}>{char}</strong>: <span style={{ fontFamily: 'monospace', color: '#a0aec0' }}>{code}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {currentStep.stage === 'done' && (
          <div style={{ padding: '16px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid #10b981', borderRadius: '8px', width: '100%' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#10b981' }}>Final Output</h3>
            <p style={{ margin: 0, color: 'var(--text-primary)', fontSize: '16px' }}>
              Huffman Encoding complete. The string is fully compressed.
            </p>
          </div>
        )}
      </div>
    </>
  );
};
