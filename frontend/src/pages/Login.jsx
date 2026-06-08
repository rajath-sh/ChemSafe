import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { FlaskConical } from 'lucide-react';
import './Login.css';

export const Login = () => {
  const { login, register } = useAuth();
  const [isRegistering, setIsRegistering] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    let result;
    if (isRegistering) {
      if (!name || !email || !password) {
        setError("Please fill in all fields");
        setLoading(false);
        return;
      }
      result = await register(name, email, password);
    } else {
      if (!email || !password) {
        setError("Please enter your email and password");
        setLoading(false);
        return;
      }
      result = await login(email, password);
    }

    if (!result.success) {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="login-container">
      <div className="login-brand">
        <div className="login-logo">
          <FlaskConical size={48} color="var(--color-primary)" />
        </div>
        <h1>ChemSafe IoT</h1>
        <p>Laboratory Environment & Safety Platform</p>
      </div>

      <Card className="login-card">
        <h2 className="login-title">{isRegistering ? 'Create Account' : 'Welcome Back'}</h2>
        
        {error && <div className="login-error">{error}</div>}

        <form onSubmit={handleSubmit} className="login-form">
          {isRegistering && (
            <div className="form-group">
              <label>Full Name</label>
              <input 
                type="text" 
                value={name} 
                onChange={(e) => setName(e.target.value)} 
                placeholder="Dr. Jane Doe"
                className="form-input"
              />
            </div>
          )}
          
          <div className="form-group">
            <label>Email Address</label>
            <input 
              type="email" 
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              placeholder="jane@chemsafe.local"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              placeholder="••••••••"
              className="form-input"
            />
          </div>

          <Button type="submit" variant="primary" className="login-submit" disabled={loading}>
            {loading ? 'Processing...' : (isRegistering ? 'Register' : 'Login')}
          </Button>
        </form>

        <div className="login-toggle">
          <button onClick={() => { setIsRegistering(!isRegistering); setError(''); setPassword(''); }}>
            {isRegistering ? 'Already have an account? Login' : "Don't have an account? Register"}
          </button>
        </div>
      </Card>
    </div>
  );
};
