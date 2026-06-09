import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, SkipForward, SkipBack, RotateCcw } from 'lucide-react';

export const PriorityQueueVisualizer = () => {
  const [inputVal, setInputVal] = useState('45, 20, 14, 12, 31, 7, 11, 13, 7');
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
    const heap = [];
    const processed = [];
    
    const t0 = performance.now();

    const swap = (i, j) => {
      const temp = heap[i];
      heap[i] = heap[j];
      heap[j] = temp;
    };

    const heapifyUp = (index) => {
      let currentIndex = index;
      while (currentIndex > 0) {
        const parentIndex = Math.floor((currentIndex - 1) / 2);
        newSteps.push({ heap: [...heap], processed: [...processed], comparing: [currentIndex, parentIndex] });
        if (heap[currentIndex] > heap[parentIndex]) { // Max Heap condition
          swap(currentIndex, parentIndex);
          newSteps.push({ heap: [...heap], processed: [...processed], swapped: [currentIndex, parentIndex] });
          currentIndex = parentIndex;
        } else {
          break;
        }
      }
    };

    const heapifyDown = (index) => {
      let currentIndex = index;
      while (true) {
        let leftChildIndex = 2 * currentIndex + 1;
        let rightChildIndex = 2 * currentIndex + 2;
        let largestIndex = currentIndex;

        if (leftChildIndex < heap.length) {
          newSteps.push({ heap: [...heap], processed: [...processed], comparing: [largestIndex, leftChildIndex] });
          if (heap[leftChildIndex] > heap[largestIndex]) largestIndex = leftChildIndex;
        }

        if (rightChildIndex < heap.length) {
          newSteps.push({ heap: [...heap], processed: [...processed], comparing: [largestIndex, rightChildIndex] });
          if (heap[rightChildIndex] > heap[largestIndex]) largestIndex = rightChildIndex;
        }

        if (largestIndex !== currentIndex) {
          swap(currentIndex, largestIndex);
          newSteps.push({ heap: [...heap], processed: [...processed], swapped: [currentIndex, largestIndex] });
          currentIndex = largestIndex;
        } else {
          break;
        }
      }
    };

    // Build Max-Heap
    for (let i = 0; i < arr.length; i++) {
      heap.push(arr[i]);
      newSteps.push({ heap: [...heap], processed: [...processed], inserting: i });
      heapifyUp(heap.length - 1);
    }
    
    newSteps.push({ heap: [...heap], processed: [...processed], phase: 'build_done' });

    // Extract all elements (simulate Priority Queue processing)
    while(heap.length > 0) {
      newSteps.push({ heap: [...heap], processed: [...processed], extracting: 0 });
      const max = heap[0];
      
      if (heap.length > 1) {
        heap[0] = heap.pop();
        processed.push(max);
        newSteps.push({ heap: [...heap], processed: [...processed], swapped: [0] });
        heapifyDown(0);
      } else {
        heap.pop();
        processed.push(max);
      }
    }

    const t1 = performance.now();

    setMetrics({
      timeMs: (t1 - t0).toFixed(4),
      spaceBytes: spaceUsed
    });

    setSteps([{ heap: [], processed: [] }, ...newSteps, { heap: [], processed: [...processed], done: true }]);
    setCurrentStepIndex(0);
    setIsPlaying(false);
  };

  const handleStart = () => {
    const newArr = inputVal.split(',').map(n => parseInt(n.trim(), 10)).filter(n => !isNaN(n));
    if (newArr.length === 0) return;
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
      }, 600);
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

  const currentStep = steps[currentStepIndex] || { heap: [], processed: [] };

  const renderHeapTree = (index, level) => {
    if (!currentStep.heap || index >= currentStep.heap.length) return null;
    
    let bgColor = '#4b5563';
    if (currentStep.comparing?.includes(index)) bgColor = '#eab308'; // yellow comparing
    if (currentStep.swapped?.includes(index)) bgColor = '#3b82f6'; // blue swapped
    if (currentStep.extracting === index) bgColor = '#ef4444'; // red extracting
    if (currentStep.done) bgColor = '#10b981'; // green done

    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <div style={{
          width: '40px', height: '40px', borderRadius: '50%', background: bgColor,
          color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 'bold', border: '2px solid #fff', zIndex: 2, transition: 'all 0.3s ease'
        }}>
          {currentStep.heap[index]}
        </div>
        
        {(2 * index + 1 < currentStep.heap.length) && (
          <div style={{ display: 'flex', marginTop: '20px', position: 'relative' }}>
            <div style={{ position: 'absolute', top: '-20px', left: '25%', width: '50%', height: '20px', borderTop: '2px solid #4b5563', borderLeft: '2px solid #4b5563', borderRight: '2px solid #4b5563' }} />
            <div style={{ margin: `0 ${20 / (level+1)}px` }}>{renderHeapTree(2 * index + 1, level + 1)}</div>
            <div style={{ margin: `0 ${20 / (level+1)}px` }}>{renderHeapTree(2 * index + 2, level + 1)}</div>
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
          <div className="metric-value">O(n log n) Process</div>
        </div>
      </div>

      <div className="control-panel">
        <div className="input-group">
          <label>Alert Priorities (comma separated)</label>
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

      <div className="visualization-area" style={{ flexDirection: 'column', gap: '30px' }}>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '100%' }}>
          {currentStep.heap && currentStep.heap.length > 0 && (
            <>
              <div style={{ color: 'var(--text-secondary)', fontSize: '14px', fontWeight: 'bold' }}>Priority Queue (Max-Heap Array)</div>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {currentStep.heap.map((val, idx) => {
                  let bgColor = '#374151'; 
                  if (currentStep.comparing?.includes(idx)) bgColor = '#eab308';
                  if (currentStep.swapped?.includes(idx)) bgColor = '#3b82f6';
                  if (currentStep.extracting === idx) bgColor = '#ef4444';
                  if (currentStep.done) bgColor = '#10b981';
                  
                  return (
                    <div key={idx} style={{ 
                      width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                      backgroundColor: bgColor, color: 'white', fontWeight: 'bold', borderRadius: '4px',
                      border: '1px solid #4b5563', transition: 'all 0.3s ease'
                    }}>
                      {val}
                    </div>
                  );
                })}
              </div>
            </>
          )}

          {currentStep.processed && currentStep.processed.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <div style={{ color: 'var(--text-secondary)', fontSize: '14px', fontWeight: 'bold', marginBottom: '10px' }}>Processed Alerts (Extracted Max)</div>
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {currentStep.processed.map((val, idx) => (
                  <div key={'p'+idx} style={{ 
                    width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    backgroundColor: '#8b5cf6', color: 'white', fontWeight: 'bold', borderRadius: '4px',
                    border: '1px solid #7c3aed', transition: 'all 0.3s ease'
                  }}>
                    {val}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div style={{ width: '100%', overflowX: 'auto', display: 'flex', justifyContent: 'center', flex: 1, alignItems: 'center' }}>
          {currentStep.heap && currentStep.heap.length > 0 && renderHeapTree(0, 0)}
        </div>

        {currentStepIndex === steps.length - 1 && steps.length > 1 && (
          <div style={{ marginTop: '20px', padding: '16px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid #10b981', borderRadius: '8px', width: '100%' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#10b981' }}>Final Output</h3>
            <p style={{ margin: 0, color: 'var(--text-primary)', fontSize: '16px' }}>
              All alerts processed successfully by priority: <strong>[{currentStep.processed.join(', ')}]</strong>
            </p>
          </div>
        )}
      </div>
    </>
  );
};
