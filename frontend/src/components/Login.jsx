import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, Stethoscope, User, ArrowRight, Activity, Shield } from 'lucide-react';

export default function Login() {
  const [role, setRole] = useState('patient');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    setIsLoading(true);
    setTimeout(() => {
      localStorage.setItem('epichat_role', role);
      localStorage.setItem('epichat_email', email || 'demo@epichat.ai');
      if (role === 'clinician') {
        navigate('/clinician/dashboard');
      } else {
        navigate('/patient/home');
      }
      setIsLoading(false);
    }, 800);
  };

  return (
    <div className="app-canvas flex-center">
      <div className="orb orb-pink"></div>
      <div className="orb orb-blue"></div>

      <div className="glass-panel premium-card">
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', marginBottom: '0.5rem' }}>
            <Activity size={28} style={{ color: 'var(--med-safe)', filter: 'drop-shadow(0 0 8px var(--med-safe-glow))' }} />
            <h1 className="title neon-text" style={{ fontSize: '2.5rem', margin: 0 }}>EpiChat</h1>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--med-accent)', textTransform: 'uppercase', letterSpacing: '3px' }}>
            Clinical Seizure Intelligence
          </p>
        </div>

        <div className="role-selector">
          <button className={`role-btn ${role === 'patient' ? 'active' : ''}`} onClick={() => setRole('patient')} type="button">
            <User size={18} /> Patient
          </button>
          <button
            className={`role-btn ${role === 'clinician' ? 'active' : ''}`}
            onClick={() => setRole('clinician')}
            type="button"
            style={role === 'clinician' ? { color: 'var(--med-accent)' } : {}}
          >
            <Stethoscope size={18} /> Clinician
          </button>
        </div>

        <div style={{
          textAlign: 'center', marginBottom: '1.5rem', padding: '8px 16px',
          background: role === 'clinician' ? 'rgba(56,189,248,0.08)' : 'rgba(16,185,129,0.08)',
          border: `1px solid ${role === 'clinician' ? 'rgba(56,189,248,0.2)' : 'rgba(16,185,129,0.2)'}`,
          borderRadius: '10px', fontSize: '0.8rem',
          color: role === 'clinician' ? 'var(--med-accent)' : 'var(--med-safe)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px'
        }}>
          <Shield size={14} />
          {role === 'clinician'
            ? 'Access Level: Full Clinical Analytics & EEG Viewer'
            : 'Access Level: Personal Health Dashboard'}
        </div>

        <form onSubmit={handleLogin} className="login-form">
          <div className="input-group">
            <input type="text" value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder={role === 'clinician' ? 'Doctor ID or Email' : 'Patient Email'} className="premium-input" />
          </div>
          <div className="input-group">
            <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
              placeholder="Password" className="premium-input" />
          </div>
          <button type="submit" className="btn-primary login-submit-btn" disabled={isLoading}
            style={role === 'clinician' ? { background: 'linear-gradient(135deg, #0ea5e9, #38bdf8)' } : {}}>
            {isLoading ? 'Authenticating...' : (
              <>{role === 'clinician' ? 'Enter Command Center' : 'Enter Health Tracker'} <ArrowRight size={18} style={{ marginLeft: '8px' }} /></>
            )}
          </button>
        </form>

        <div className="divider"><span>OR</span></div>
        <button className="btn-secondary gmail-btn" type="button" onClick={handleLogin}>
          <Mail size={18} style={{ marginRight: '10px' }} /> Continue with Google
        </button>
      </div>
    </div>
  );
}
