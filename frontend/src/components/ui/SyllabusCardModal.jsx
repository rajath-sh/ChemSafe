import React from 'react';
import { X, BookOpen, Sigma, LineChart } from 'lucide-react';
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

export const SyllabusCardModal = ({ isOpen, onClose, algorithmDetails }) => {
  if (!isOpen || !algorithmDetails) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{algorithmDetails.title} - Algorithm Details</h2>
          <button className="close-btn" onClick={onClose}>
            <X size={24} />
          </button>
        </div>
        
        <div className="modal-body">
          <div className="syllabus-section">
            <h3><BookOpen size={18} /> Pseudocode</h3>
            <div className="pseudocode">
              {algorithmDetails.pseudocode}
            </div>
          </div>
          
          <div className="syllabus-section">
            <h3><Sigma size={18} /> Time & Space Complexity Derivation</h3>
            <div className="math-derivation">
              {algorithmDetails.derivation.map((p, i) => <p key={i}>{p}</p>)}
            </div>
          </div>
          
          <div className="syllabus-section">
            <h3><LineChart size={18} /> Growth Function Curves</h3>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
              Comparison of actual function f(n) vs Bounds (c*g(n))
            </p>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsLineChart
                  data={algorithmDetails.chartData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                  <XAxis dataKey="n" stroke="#888" label={{ value: 'Input Size (n)', position: 'insideBottomRight', offset: -10 }} />
                  <YAxis stroke="#888" label={{ value: 'Time / Operations', angle: -90, position: 'insideLeft' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e1e1e', border: '1px solid #333' }} />
                  <Legend />
                  <Line type="monotone" dataKey="fn" name="f(n) (Actual)" stroke="#3b82f6" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="gn" name="c*g(n) (Upper Bound)" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                  {algorithmDetails.chartData[0]?.hn !== undefined && (
                    <Line type="monotone" dataKey="hn" name="c*h(n) (Lower Bound)" stroke="#10b981" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                  )}
                </RechartsLineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
