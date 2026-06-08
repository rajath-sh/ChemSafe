import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { Layout } from './components/layout/Layout';
import { Login } from './pages/Login';
import { UsersManagement } from './pages/UsersManagement';
import { NodesManagement } from './pages/NodesManagement';
import { Analytics } from './pages/Analytics';
import { AlertsIncidents } from './pages/AlertsIncidents';
import { Staff } from './pages/Staff';
import { Inventory } from './pages/Inventory';

import { Reports } from './pages/Reports';

// Placeholder Pages for routing
import { Activity, AlertTriangle, ShieldAlert, Users } from 'lucide-react';
import { Dashboard } from './pages/Dashboard';
import { Settings } from './pages/Settings';
import { AiAssistant } from './pages/AiAssistant';

function App() {
  const { currentUser, loading } = useAuth();

  if (loading) {
    return <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading ChemSafe...</div>;
  }

  if (!currentUser) {
    return <Login />;
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/sensors" element={<NodesManagement />} />
        <Route path="/alerts" element={<AlertsIncidents />} />
        <Route path="/incidents" element={<Navigate to="/alerts" replace />} />
        <Route path="/staff" element={<Staff />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/users" element={<UsersManagement />} />
        <Route path="/ai-assistant" element={<AiAssistant />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;
