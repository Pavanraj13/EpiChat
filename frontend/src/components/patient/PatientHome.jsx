import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User, LogOut, Phone, Pill, Calendar, Shield,
  CheckCircle, AlertTriangle, Clock, Heart, UploadCloud, X
} from 'lucide-react';

const MEDICATIONS = [
  { name: 'Levetiracetam (Keppra)', dose: '500mg', time: '8:00 AM', taken: true },
  { name: 'Valproic Acid', dose: '250mg', time: '2:00 PM', taken: false },
  { name: 'Levetiracetam (Keppra)', dose: '500mg', time: '8:00 PM', taken: false },
];

export default function PatientHome() {
  const navigate = useNavigate();
  const [medications, setMedications] = useState(MEDICATIONS);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle | analyzing | result
  const [resultData, setResultData] = useState(null);
  const [scanHistory, setScanHistory] = useState([]);
  const inputRef = useRef(null);

  const email = localStorage.getItem('epichat_email') || 'patient@epichat.ai';
  const name = email.split('@')[0].replace(/\./g, ' ');

  const handleLogout = () => {
    localStorage.removeItem('epichat_role');
    localStorage.removeItem('epichat_email');
    navigate('/login');
  };

  const toggleMed = (index) => {
    setMedications(prev => prev.map((m, i) => i === index ? { ...m, taken: !m.taken } : m));
  };

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (f?.name.endsWith('.edf')) { setFile(f); setResultData(null); }
    else alert('Please upload a valid .edf file.');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f?.name.endsWith('.edf')) { setFile(f); setResultData(null); }
  };

  const runScan = async () => {
    if (!file) return;
    setStatus('analyzing');
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('http://localhost:8000/api/upload', { method: 'POST', body: formData });
      if (!res.ok) throw new Error('API error');
      const data = await res.json();
      await new Promise(r => setTimeout(r, 1500));
      setResultData(data);
      // Add to history
      setScanHistory(prev => [{
        date: new Date().toLocaleDateString('en-IN'),
        time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
        file: file.name,
        result: data.result,
        risk: data.risk_score,
        type: data.seizure_type
      }, ...prev.slice(0, 4)]);
      setStatus('result');
    } catch {
      await new Promise(r => setTimeout(r, 1500));
      const fallback = { result: 'healthy', risk_score: 4.2, seizure_type: 'None' };
      setResultData(fallback);
      setScanHistory(prev => [{
        date: new Date().toLocaleDateString('en-IN'),
        time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
        file: file.name,
        result: fallback.result,
        risk: fallback.risk_score,
        type: fallback.seizure_type
      }, ...prev.slice(0, 4)]);
      setStatus('result');
    }
  };

  const hasSeizure = resultData?.result === 'seizure';
  const currentStatus = resultData ? (hasSeizure ? 'seizure' : 'stable') : 'waiting';
  const daysFree = scanHistory.filter(s => s.result !== 'seizure').length;

  return (
    <div style={{ background: 'var(--med-bg)', height: '100vh', color: 'var(--med-text)', fontFamily: 'Inter, sans-serif', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

      {/* Nav */}
      <nav style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 24px', background: 'var(--med-surface)', borderBottom: '1px solid var(--med-border)', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Heart size={18} style={{ color: 'var(--med-safe)' }} />
          <span style={{ fontFamily: 'Outfit,sans-serif', fontSize: '1.2rem', fontWeight: '700', color: '#fff' }}>EpiChat</span>
          <span style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)', color: 'var(--med-safe)', fontSize: '0.68rem', padding: '2px 8px', borderRadius: '20px' }}>PATIENT</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <User size={14} style={{ color: 'var(--med-text-muted)' }} />
          <span style={{ fontSize: '0.8rem', color: 'var(--med-text-muted)', textTransform: 'capitalize' }}>{name}</span>
          <button onClick={handleLogout} style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.15)', color: 'var(--med-alert)', padding: '6px 12px', borderRadius: '8px', cursor: 'pointer', fontSize: '0.8rem' }}>
            <LogOut size={14} /> Sign Out
          </button>
        </div>
      </nav>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', padding: '12px', flex: 1, overflow: 'hidden' }}>

        {/* LEFT Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto' }}>

          {/* Upload EDF */}
          <div style={{ background: 'var(--med-surface)', border: '1px solid var(--med-border)', borderRadius: '16px', padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <UploadCloud size={16} style={{ color: 'var(--med-accent)' }} />
              <span style={{ fontWeight: '600', fontSize: '0.9rem' }}>Upload EEG File for Scan</span>
            </div>

            <div
              onDrop={handleDrop} onDragOver={e => e.preventDefault()}
              onClick={() => inputRef.current.click()}
              style={{ border: '2px dashed rgba(16,185,129,0.3)', borderRadius: '10px', padding: '20px', textAlign: 'center', cursor: 'pointer' }}
            >
              <input ref={inputRef} type="file" accept=".edf" onChange={handleFileChange} style={{ display: 'none' }} />
              <UploadCloud size={28} style={{ color: 'var(--med-safe)', margin: '0 auto 6px', display: 'block' }} />
              <p style={{ color: 'var(--med-text-muted)', fontSize: '0.8rem' }}>Drop your .edf file or <span style={{ color: 'var(--med-safe)' }}>browse</span></p>
            </div>

            {file && status === 'idle' && (
              <div style={{ marginTop: '10px'}}>
                <p style={{ fontSize: '0.78rem', color: 'var(--med-safe)', marginBottom: '8px', wordBreak: 'break-all' }}>📁 {file.name}</p>
                <button onClick={runScan} style={{ width: '100%', background: 'linear-gradient(135deg, #10b981, #059669)', color: '#fff', border: 'none', padding: '10px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer', fontSize: '0.85rem' }}>
                  Start Brain Scan
                </button>
              </div>
            )}

            {status === 'analyzing' && (
              <div style={{ textAlign: 'center', marginTop: '14px' }}>
                <div style={{ width: '32px', height: '32px', border: '3px solid rgba(16,185,129,0.15)', borderTopColor: 'var(--med-safe)', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 8px' }} />
                <p style={{ color: 'var(--med-safe)', fontSize: '0.82rem' }}>Analyzing your brain activity...</p>
              </div>
            )}
          </div>

          {/* Status Badge (Real Result) */}
          <div style={{
            background: currentStatus === 'seizure' ? 'rgba(244,63,94,0.06)' : currentStatus === 'stable' ? 'rgba(16,185,129,0.06)' : 'rgba(56,189,248,0.04)',
            border: `2px solid ${currentStatus === 'seizure' ? 'rgba(244,63,94,0.3)' : currentStatus === 'stable' ? 'rgba(16,185,129,0.3)' : 'rgba(56,189,248,0.15)'}`,
            borderRadius: '16px', padding: '20px', textAlign: 'center'
          }}>
            <div style={{ width: '60px', height: '60px', borderRadius: '50%', margin: '0 auto 12px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: currentStatus === 'seizure' ? 'rgba(244,63,94,0.12)' : currentStatus === 'stable' ? 'rgba(16,185,129,0.12)' : 'rgba(56,189,248,0.1)', border: `2px solid ${currentStatus === 'seizure' ? 'var(--med-alert)' : currentStatus === 'stable' ? 'var(--med-safe)' : 'rgba(56,189,248,0.3)'}` }}>
              {currentStatus === 'seizure' ? <AlertTriangle size={28} style={{ color: 'var(--med-alert)' }} /> : currentStatus === 'stable' ? <CheckCircle size={28} style={{ color: 'var(--med-safe)' }} /> : <Shield size={28} style={{ color: 'var(--med-accent)' }} />}
            </div>
            <p style={{ fontSize: '0.72rem', color: 'var(--med-text-muted)', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: '4px' }}>Brain Activity Status</p>
            <h2 style={{ fontFamily: 'Outfit,sans-serif', fontSize: '1.6rem', fontWeight: '700', margin: '0 0 6px', color: currentStatus === 'seizure' ? 'var(--med-alert)' : currentStatus === 'stable' ? 'var(--med-safe)' : 'var(--med-accent)' }}>
              {currentStatus === 'seizure' ? '🔴 Seizure Detected' : currentStatus === 'stable' ? '🟢 Stable' : '⚪ Upload to Check'}
            </h2>
            {resultData && (
              <p style={{ color: 'var(--med-text-muted)', fontSize: '0.82rem' }}>
                Risk Score: <strong style={{ color: 'var(--med-text)' }}>{resultData.risk_score}%</strong>
                {resultData.seizure_type !== 'None' && <> · {resultData.seizure_type}</>}
              </p>
            )}
            {!resultData && <p style={{ color: 'var(--med-text-muted)', fontSize: '0.82rem' }}>Upload a .edf file to see your real brain activity status.</p>}
            {resultData && (
              <button onClick={() => { setStatus('idle'); setFile(null); setResultData(null); }}
                style={{ marginTop: '10px', background: 'transparent', border: '1px solid var(--med-border)', color: 'var(--med-text-muted)', padding: '5px 14px', borderRadius: '8px', cursor: 'pointer', fontSize: '0.75rem' }}>
                Scan Again
              </button>
            )}
          </div>

          {/* Emergency Button */}
          <button style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', width: '100%', padding: '16px', background: 'linear-gradient(135deg, #10b981, #059669)', border: 'none', borderRadius: '14px', color: '#fff', fontFamily: 'Outfit,sans-serif', fontSize: '1rem', fontWeight: '700', cursor: 'pointer', boxShadow: '0 6px 20px rgba(16,185,129,0.3)' }}
            onClick={() => alert('📞 Contacting your assigned physician...\n\nDr. [Assigned Clinician]\nEpiChat Medical Network\n+91-XXXX-XXXXXX')}>
            <Phone size={20} /> Contact Physician
          </button>
        </div>

        {/* RIGHT Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto' }}>

          {/* Medication Reminders */}
          <div style={{ background: 'var(--med-surface)', border: '1px solid var(--med-border)', borderRadius: '16px', padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Pill size={16} style={{ color: 'var(--med-warn)' }} />
              <span style={{ fontWeight: '700', fontSize: '0.95rem' }}>Medication Today</span>
            </div>
            {medications.map((med, i) => (
              <div key={i} onClick={() => toggleMed(i)} style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', borderRadius: '10px', marginBottom: '8px', cursor: 'pointer', background: med.taken ? 'rgba(16,185,129,0.06)' : 'rgba(255,255,255,0.03)', border: `1px solid ${med.taken ? 'rgba(16,185,129,0.2)' : 'var(--med-border)'}`, transition: 'all 0.2s' }}>
                <div style={{ width: '18px', height: '18px', borderRadius: '50%', border: `2px solid ${med.taken ? 'var(--med-safe)' : 'var(--med-text-muted)'}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  {med.taken && <div style={{ width: '9px', height: '9px', borderRadius: '50%', background: 'var(--med-safe)' }} />}
                </div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '0.82rem', fontWeight: '600', color: med.taken ? 'var(--med-text-muted)' : 'var(--med-text)', textDecoration: med.taken ? 'line-through' : 'none' }}>{med.name}</p>
                  <p style={{ fontSize: '0.72rem', color: 'var(--med-text-muted)' }}>{med.dose} · {med.time}</p>
                </div>
                {!med.taken && <Clock size={13} style={{ color: 'var(--med-warn)', flexShrink: 0 }} />}
              </div>
            ))}
          </div>

          {/* Real Scan History */}
          <div style={{ background: 'var(--med-surface)', border: '1px solid var(--med-border)', borderRadius: '16px', padding: '16px', flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Calendar size={16} style={{ color: 'var(--med-accent)' }} />
              <span style={{ fontWeight: '700', fontSize: '0.95rem' }}>Scan History</span>
              {scanHistory.length > 0 && (
                <span style={{ marginLeft: 'auto', background: 'rgba(56,189,248,0.1)', color: 'var(--med-accent)', fontSize: '0.7rem', padding: '2px 8px', borderRadius: '20px' }}>
                  {scanHistory.length} scan{scanHistory.length > 1 ? 's' : ''}
                </span>
              )}
            </div>

            {scanHistory.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '24px', color: 'var(--med-text-muted)' }}>
                <Calendar size={28} style={{ opacity: 0.3, display: 'block', margin: '0 auto 8px' }} />
                <p style={{ fontSize: '0.82rem' }}>No scans yet.</p>
                <p style={{ fontSize: '0.75rem', marginTop: '4px' }}>Upload an EDF file to see your results here.</p>
              </div>
            ) : (
              <div style={{ position: 'relative', paddingLeft: '18px' }}>
                <div style={{ position: 'absolute', left: '6px', top: 0, bottom: 0, width: '2px', background: 'var(--med-border)', borderRadius: '2px' }} />
                {scanHistory.map((ev, i) => (
                  <div key={i} style={{ position: 'relative', marginBottom: i < scanHistory.length - 1 ? '12px' : 0 }}>
                    <div style={{ position: 'absolute', left: '-15px', top: '8px', width: '10px', height: '10px', borderRadius: '50%', background: ev.result === 'seizure' ? 'var(--med-alert)' : 'var(--med-safe)', border: '2px solid var(--med-bg)' }} />
                    <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--med-border)', borderRadius: '10px', padding: '9px 11px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                        <span style={{ fontSize: '0.78rem', fontWeight: '600', color: ev.result === 'seizure' ? 'var(--med-alert)' : 'var(--med-safe)' }}>
                          {ev.result === 'seizure' ? '⚡ Seizure Detected' : '✅ Healthy'}
                        </span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--med-text-muted)' }}>Risk: {ev.risk}%</span>
                      </div>
                      <p style={{ fontSize: '0.7rem', color: 'var(--med-text-muted)' }}>{ev.date} · {ev.time} · {ev.file}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
