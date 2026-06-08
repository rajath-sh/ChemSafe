import React from 'react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export const Layout = ({ children }) => {
  return (
    <div className="app-container">
      <Sidebar />
      <main className="main-content">
        <TopBar />
        <div className="page-content">
          {children}
        </div>
      </main>
    </div>
  );
};
