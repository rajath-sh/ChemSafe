import React, { useState } from 'react';
import { Cpu, BookOpen } from 'lucide-react';
import './AlgorithmsDashboard.css';
import { SyllabusCardModal } from '../components/ui/SyllabusCardModal';

// Placeholder imports for visualizers
import { BoyerMooreVisualizer } from '../components/algorithms/BoyerMooreVisualizer';
import { HuffmanVisualizer } from '../components/algorithms/HuffmanVisualizer';
import { MergeSortVisualizer } from '../components/algorithms/MergeSortVisualizer';
import { PriorityQueueVisualizer } from '../components/algorithms/PriorityQueueVisualizer';
import { FloydWarshallVisualizer } from '../components/algorithms/FloydWarshallVisualizer';

// Import syllabus details
import { ALGORITHM_SYLLABUS_DATA } from '../components/algorithms/SyllabusData';

const ALGORITHMS = [
  { id: 'boyer-moore', name: 'Boyer-Moore String Matching', component: BoyerMooreVisualizer },
  { id: 'huffman', name: 'Huffman Coding', component: HuffmanVisualizer },
  { id: 'merge-sort', name: 'Merge Sort', component: MergeSortVisualizer },
  { id: 'priority-queue', name: 'Priority Queue (Heap)', component: PriorityQueueVisualizer },
  { id: 'floyd-warshall', name: 'Floyd-Warshall', component: FloydWarshallVisualizer }
];

export const AlgorithmsDashboard = () => {
  const [activeAlgoId, setActiveAlgoId] = useState(ALGORITHMS[0].id);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const activeAlgo = ALGORITHMS.find(a => a.id === activeAlgoId);
  const ActiveComponent = activeAlgo.component;

  const handleOpenSyllabus = () => {
    setIsModalOpen(true);
  };

  return (
    <div className="algorithms-dashboard">
      <div className="dashboard-header">
        <h1><Cpu size={28} color="var(--color-primary)" /> Algorithms Dashboard</h1>
      </div>

      <div className="dashboard-content">
        <aside className="algorithm-selector">
          {ALGORITHMS.map(algo => (
            <button
              key={algo.id}
              className={`algo-tab ${activeAlgoId === algo.id ? 'active' : ''}`}
              onClick={() => setActiveAlgoId(algo.id)}
            >
              {algo.name}
            </button>
          ))}
        </aside>

        <main className="algorithm-viewer">
          <div className="viewer-header">
            <h2>{activeAlgo.name}</h2>
            <button className="view-syllabus-btn" onClick={handleOpenSyllabus}>
              <BookOpen size={18} />
              Algorithm Details
            </button>
          </div>
          
          <div className="viewer-body">
            <ActiveComponent />
          </div>
        </main>
      </div>

      <SyllabusCardModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        algorithmDetails={ALGORITHM_SYLLABUS_DATA[activeAlgoId]} 
      />
    </div>
  );
};
