import React from 'react';
import './Badge.css';

export const Badge = ({ children, variant = 'neutral', className = '' }) => {
  return (
    <span className={`badge-tag badge-${variant} ${className}`}>
      {children}
    </span>
  );
};
