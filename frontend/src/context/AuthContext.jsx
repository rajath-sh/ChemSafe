import React, { createContext, useState, useEffect, useContext } from 'react';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load user from local storage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('chemsafe_user');
    if (storedUser) {
      setCurrentUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  // Standard API fetch wrapper that automatically includes the X-Dev-Role header
  const apiFetch = async (endpoint, options = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    // Inject the dev role so the backend knows who we are pretending to be
    if (currentUser) {
      headers['X-Dev-Role'] = currentUser.role;
      headers['X-Dev-User-Id'] = currentUser.user_id;
    } else {
      // For public endpoints like the initial user fetch
      headers['X-Dev-Role'] = 'admin'; 
      headers['X-Dev-User-Id'] = 'DEV-admin-001';
    }

    const baseUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
    const response = await fetch(`${baseUrl}${endpoint}`, {
      ...options,
      headers,
    });
    
    // If not okay and not specifically handled, throw
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      let errorMessage = `HTTP error! status: ${response.status}`;
      
      if (errorData.detail) {
        if (Array.isArray(errorData.detail)) {
          // FastAPI 422 Validation Error
          errorMessage = errorData.detail.map(err => `${err.loc.join('.')} - ${err.msg}`).join(', ');
        } else if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        }
      }
      
      throw new Error(errorMessage);
    }
    
    return await response.json();
  };

  const login = async (email, password) => {
    try {
      // In a real app we'd send password to /login. Here we just lookup by email to simulate auth since backend is in dev mode.
      const users = await apiFetch('/api/users');
      const user = users.find(u => u.email === email);
      
      if (user) {
        localStorage.setItem('chemsafe_user', JSON.stringify(user));
        setCurrentUser(user);
        return { success: true };
      } else {
        return { success: false, error: 'User not found. Please register.' };
      }
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const register = async (name, email, password) => {
    try {
      // 1. Check if any admins exist to determine role
      const users = await apiFetch('/api/users');
      const hasAdmin = users.some(u => u.role === 'admin');
      
      // If no admin exists in the system, this user becomes the Admin
      const role = !hasAdmin ? 'admin' : 'viewer';
      
      // 2. Create the user
      const newUser = await apiFetch('/api/users', {
        method: 'POST',
        body: JSON.stringify({
          name,
          email,
          role,
          department: 'General',
          phone: '',
          status: 'active',
          availability: 'available'
        })
      });
      
      // 3. Auto-login
      localStorage.setItem('chemsafe_user', JSON.stringify(newUser));
      setCurrentUser(newUser);
      
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const logout = () => {
    localStorage.removeItem('chemsafe_user');
    setCurrentUser(null);
  };

  return (
    <AuthContext.Provider value={{ currentUser, loading, login, register, logout, apiFetch }}>
      {children}
    </AuthContext.Provider>
  );
};
