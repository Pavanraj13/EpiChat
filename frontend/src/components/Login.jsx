import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Stethoscope, User, ArrowRight } from 'lucide-react';

export default function Login() {
  const [role, setRole] = useState('patient');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    navigate('/dashboard');
  };

  return (
    <div className="app-canvas flex-center">
      {/* Decorative Orbs for WOW factor */}
      <div className="orb orb-pink"></div>
      <div className="orb orb-blue"></div>
      
      <div className="glass-panel premium-card">
        <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          <h1 className="title neon-text" style={{ fontSize: '3rem', margin: 0, paddingBottom: '10px' }}>EpiChat</h1>
          <p className="subtitle" style={{ fontSize: '1rem', color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '2px' }}>Neural Net OS</p>
        </div>

        <div className="role-selector">
          <button 
            className={`role-btn ${role === 'patient' ? 'active' : ''}`}
            onClick={() => setRole('patient')}
          >
            <User size={18} /> Patient
          </button>
          <button 
            className={`role-btn ${role === 'doctor' ? 'active' : ''}`}
            onClick={() => setRole('doctor')}
          >
            <Stethoscope size={18} /> Doctor
          </button>
        </div>

        <form onSubmit={handleLogin} className="login-form">
          <div className="input-group">
            <input 
              type="text" 
              required 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Username or Email" 
              className="premium-input"
            />
          </div>
          <div className="input-group">
            <input 
              type="password" 
              required 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password" 
              className="premium-input"
            />
          </div>
          <button type="submit" className="btn-primary login-submit-btn">
            Initialize <ArrowRight size={18} style={{marginLeft: '8px'}}/>
          </button>
        </form>

        <div className="divider">
          <span>OR</span>
        </div>

        <button className="btn-secondary gmail-btn" type="button" onClick={handleLogin}>
          <Mail size={18} style={{ marginRight: '10px' }}/> 
          Continue with Google
        </button>
      </div>
    </div>
  );
}
