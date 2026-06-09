import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  LayoutDashboard, 
  Activity, 
  AlertTriangle, 
  ClipboardList, 
  FlaskConical, 
  Bell, 
  BarChart3, 
  ShieldAlert, 
  Settings,
  FileText,
  Bot,
  Map,
  Cpu
} from 'lucide-react';
import './Sidebar.css';

const navItems = [
  { path: '/', icon: <LayoutDashboard size={20} />, label: 'Dashboard', roles: ['admin', 'staff', 'viewer'] },
  { path: '/navigation', icon: <Map size={20} />, label: 'Navigation', roles: ['admin', 'staff', 'viewer'] },
  { path: '/sensors', icon: <Activity size={20} />, label: 'Sensors', roles: ['admin', 'staff', 'viewer'] },
  { path: '/alerts', icon: <AlertTriangle size={20} />, label: 'Alerts & Incidents', roles: ['admin', 'staff', 'viewer'] },
  { path: '/analytics', icon: <BarChart3 size={20} />, label: 'Analytics', roles: ['admin', 'staff', 'viewer'] },
  { path: '/staff', icon: <ClipboardList size={20} />, label: 'Staff', roles: ['admin', 'staff', 'viewer'] },
  { path: '/inventory', icon: <FlaskConical size={20} />, label: 'Inventory', roles: ['admin', 'staff', 'viewer'] },
  { path: '/reports', icon: <FileText size={20} />, label: 'Reports', roles: ['admin', 'staff'] },
  { path: '/ai-assistant', icon: <Bot size={20} />, label: 'AI Assistant', roles: ['admin', 'staff', 'viewer'] },
  { path: '/settings', icon: <Settings size={20} />, label: 'Settings', roles: ['admin'] },
  { path: '/users', icon: <ClipboardList size={20} />, label: 'Users', roles: ['admin'] },
  { path: '/algorithms', icon: <Cpu size={20} />, label: 'Algorithms Dashboard', roles: ['admin', 'staff', 'viewer'] },
];

export const Sidebar = () => {
  const { currentUser } = useAuth();
  
  // Filter nav items based on user role
  const visibleNavItems = navItems.filter(item => 
    !item.roles || (currentUser && item.roles.includes(currentUser.role))
  );
  return (
    <aside className="sidebar glass-panel">
      <div className="sidebar-brand">
        <div className="brand-logo">
          <FlaskConical size={24} color="var(--color-primary)" />
        </div>
        <h2>ChemSafe</h2>
      </div>
      
      <nav className="sidebar-nav">
        {visibleNavItems.map((item) => (
          <NavLink 
            key={item.path} 
            to={item.path} 
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>
      
      <div className="sidebar-footer">
        <div className="system-status">
          <div className="status-dot"></div>
          <span>System Online</span>
        </div>
      </div>
    </aside>
  );
};
