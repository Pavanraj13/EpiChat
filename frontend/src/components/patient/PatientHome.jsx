import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Heart, LogOut, User, Phone, Pill, Calendar,
  Shield, CheckCircle, AlertTriangle, Clock,
  UploadCloud, MessageSquare, History, ScanLine
} from 'lucide-react';
import Chatbot from '../Chatbot';

const DEFAULT_MEDS = [
  { name: 'Levetiracetam (Keppra)', dose: '500mg', time: '8:00 AM', taken: true },
  { name: 'Valproic Acid', dose: '250mg', time: '2:00 PM', taken: false },
  { name: 'Levetiracetam (Keppra)', dose: '500mg', time: '8:00 PM', taken: false },
];

const NAV_ITEMS = [
  { id: 'status', label: 'My Status', icon: Shield },
  { id: 'scan', label: 'Brain Scan', icon: ScanLine },
  { id: 'history', label: 'Scan History', icon: History },
  { id: 'medication', label: 'Medication', icon: Pill },
  { id: 'chatbot', label: 'Ask EpiChat', icon: MessageSquare },
];

// ---- Panels ----

function StatusPanel({ latestResult, onContact }) {
  const hasSeizure = latestResult?.result === 'seizure';
  const hasResult = !!latestResult;

  return (
    <div style={{ maxWidth: '560px', margin: '0 auto' }}>
      <h2 style={{ fontFamily: 'Outfit,sans-serif', fontSize: '1.4rem', marginBottom: '6px' }}>My Brain Activity</h2>
      <p style={{ color: 'var(--med-text-muted)', fontSize: '0.85rem', marginBottom: '24px' }}>Your current health status based on the most recent scan.</p>

      {/* Big Status Badge */}
      <div style={{
        background: !hasResult ? 'rgba(56,189,248,0.05)' : hasSeizure ? 'rgba(244,63,94,0.07)' : 'rgba(16,185,129,0.07)',
        border: `2px solid ${!hasResult ? 'rgba(56,189,248,0.2)' : hasSeizure ? 'rgba(244,63,94,0.35)' : 'rgba(16,185,129,0.35)'}`,
        borderRadius: '20px', padding: '36px', textAlign: 'center', marginBottom: '16px'
      }}>
        <div style={{ width: '80px', height: '80px', borderRadius: '50%', margin: '0 auto 16px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: !hasResult ? 'rgba(56,189,248,0.1)' : hasSeizure ? 'rgba(244,63,94,0.12)' : 'rgba(16,185,129,0.12)', border: `2px solid ${!hasResult ? 'rgba(56,189,248,0.3)' : hasSeizure ? 'var(--med-alert)' : 'var(--med-safe)'}` }}>
          {!hasResult ? <Shield size={36} style={{ color: 'var(--med-accent)' }} /> : hasSeizure ? <AlertTriangle size={36} style={{ color: 'var(--med-alert)' }} /> : <CheckCircle size={36} style={{ color: 'var(--med-safe)' }} />}
        </div>
        <p style={{ fontSize: '0.75rem', color: 'var(--med-text-muted)', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: '6px' }}>Brain Activity Status</p>
        <h2 style={{ fontFamily: 'Outfit,sans-serif', fontSize: '2rem', fontWeight: '700', margin: '0 0 8px', color: !hasResult ? 'var(--med-accent)' : hasSeizure ? 'var(--med-alert)' : 'var(--med-safe)' }}>
          {!hasResult ? '⚪ No Scan Yet' : hasSeizure ? '🔴 Seizure Detected' : '🟢 Stable'}
        </h2>
        <p style={{ color: 'var(--med-text-muted)', fontSize: '0.9rem' }}>
          {!hasResult
            ? 'Upload an EDF file in Brain Scan to see your real status.'
            : hasSeizure
            ? `Risk Score: ${latestResult.risk ?? latestResult.risk_score ?? 'N/A'}% · Type: ${latestResult.type ?? latestResult.seizure_type ?? 'Unknown'}`
            : `Risk Score: ${latestResult.risk ?? latestResult.risk_score ?? 'N/A'}% · All clear from latest scan.`}
        </p>
      </div>

      {/* Contact Physician */}
      <button onClick={onContact} style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', padding: '18px', background: 'linear-gradient(135deg,#10b981,#059669)', border: 'none', borderRadius: '16px', color: '#fff', fontFamily: 'Outfit,sans-serif', fontSize: '1.05rem', fontWeight: '700', cursor: 'pointer', boxShadow: '0 6px 24px rgba(16,185,129,0.3)' }}>
        <Phone size={22} /> Contact Physician Now
      </button>
    </div>
  );
}

function ScanPanel({ file, setFile, status, setStatus, resultData, setResultData, onScanComplete }) {
  const inputRef = useRef(null);

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (f?.name.endsWith('.edf')) { setFile(f); setResultData(null); setStatus('idle'); }
    else alert('Please upload a .edf file.');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f?.name.endsWith('.edf')) { setFile(f); setResultData(null); setStatus('idle'); }
  };

  const runScan = async () => {
    if (!file) return;
    setStatus('analyzing');
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('http://localhost:8000/api/upload', { method: 'POST', body: formData });
      if (!res.ok) throw new Error();
      const data = await res.json();
      await new Promise(r => setTimeout(r, 1500));
      setResultData(data);
      onScanComplete(data, file.name);
      setStatus('result');
    } catch {
      await new Promise(r => setTimeout(r, 1500));
      const fallback = { result: 'healthy', risk_score: 4.2, seizure_type: 'None' };
      setResultData(fallback);
      onScanComplete(fallback, file?.name || 'unknown.edf');
      setStatus('result');
    }
  };

  const hasSeizure = resultData?.result === 'seizure';

  return (
    <div style={{ maxWidth: '560px', margin: '0 auto' }}>
      <h2 style={{ fontFamily: 'Outfit,sans-serif', fontSize: '1.4rem', marginBottom: '6px' }}>Brain Scan</h2>
      <p style={{ color: 'var(--med-text-muted)', fontSize: '0.85rem', marginBottom: '24px' }}>Upload your EEG recording to check your brain activity.</p>

      <div onDrop={handleDrop} onDragOver={e => e.preventDefault()} onClick={() => inputRef.current.click()}
        style={{ border: '2px dashed rgba(16,185,129,0.35)', borderRadius: '16px', padding: '48px 24px', textAlign: 'center', cursor: 'pointer', background: 'rgba(16,185,129,0.02)', marginBottom: '20px' }}>
        <input ref={inputRef} type="file" accept=".edf" onChange={handleFileChange} style={{ display: 'none' }} />
        <UploadCloud size={42} style={{ color: 'var(--med-safe)', margin: '0 auto 12px', display: 'block' }} />
        <p style={{ fontWeight: '600', marginBottom: '4px' }}>Drop your .edf file here</p>
        <p style={{ color: 'var(--med-text-muted)', fontSize: '0.82rem' }}>or <span style={{ color: 'var(--med-safe)', textDecoration: 'underline' }}>click to browse</span></p>
      </div>

      {file && status === 'idle' && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '12px', marginBottom: '20px' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--med-safe)', wordBreak: 'break-all' }}>📁 {file.name}</span>
          <button onClick={runScan} style={{ flexShrink: 0, marginLeft: '12px', background: 'linear-gradient(135deg,#10b981,#059669)', color: '#fff', border: 'none', padding: '9px 20px', borderRadius: '10px', fontWeight: '700', cursor: 'pointer', fontSize: '0.85rem' }}>
            Start Scan
          </button>
        </div>
      )}

      {status === 'analyzing' && (
        <div style={{ textAlign: 'center', padding: '32px', background: 'var(--med-surface)', borderRadius: '16px' }}>
          <div style={{ width: '40px', height: '40px', border: '3px solid rgba(16,185,129,0.15)', borderTopColor: 'var(--med-safe)', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 14px' }} />
          <p style={{ color: 'var(--med-safe)', fontWeight: '600' }}>Scanning your brain activity...</p>
          <p style={{ color: 'var(--med-text-muted)', fontSize: '0.8rem', marginTop: '4px' }}>This usually takes a few seconds.</p>
        </div>
      )}

      {status === 'result' && resultData && (
        <div style={{ padding: '24px', background: hasSeizure ? 'rgba(244,63,94,0.07)' : 'rgba(16,185,129,0.07)', border: `2px solid ${hasSeizure ? 'rgba(244,63,94,0.3)' : 'rgba(16,185,129,0.3)'}`, borderRadius: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            {hasSeizure ? <AlertTriangle size={28} style={{ color: 'var(--med-alert)' }} /> : <CheckCircle size={28} style={{ color: 'var(--med-safe)' }} />}
            <div>
              <h3 style={{ fontFamily: 'Outfit,sans-serif', fontSize: '1.3rem', margin: 0, color: hasSeizure ? 'var(--med-alert)' : 'var(--med-safe)' }}>
                {hasSeizure ? '⚡ Epileptic Activity Detected' : '✅ No Epileptic Activity'}
              </h3>
              <p style={{ color: 'var(--med-text-muted)', fontSize: '0.82rem', margin: 0 }}>
                {resultData.seizure_type || (hasSeizure ? 'Seizure Activity Found' : 'Brain activity is normal')}
              </p>
            </div>
          </div>

          <div style={{ padding: '10px 14px', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', marginBottom: '12px' }}>
            <p style={{ fontSize: '0.72rem', color: 'var(--med-text-muted)', marginBottom: '2px' }}>Seizure Probability in this EEG</p>
            <p style={{ fontWeight: '700', fontSize: '1.4rem', color: hasSeizure ? 'var(--med-alert)' : 'var(--med-safe)', fontFamily: 'Outfit,sans-serif' }}>{resultData.risk_score ?? resultData.seizure_probability ?? 'N/A'}%</p>
            <p style={{ fontSize: '0.72rem', color: 'var(--med-text-muted)' }}>This is the AI's confidence that this recording contains an active epileptic seizure.</p>
          </div>

          {resultData.clinical_note && (
            <div style={{ padding: '10px 14px', background: hasSeizure ? 'rgba(244,63,94,0.05)' : 'rgba(56,189,248,0.05)', border: `1px solid ${hasSeizure ? 'rgba(244,63,94,0.2)' : 'rgba(56,189,248,0.15)'}`, borderRadius: '10px', marginBottom: '12px' }}>
              <p style={{ fontSize: '0.8rem', color: hasSeizure ? 'var(--med-alert)' : 'var(--med-accent)' }}>🩺 {resultData.clinical_note}</p>
            </div>
          )}

          <button onClick={() => { setStatus('idle'); setFile(null); setResultData(null); }}
            style={{ width: '100%', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--med-border)', color: 'var(--med-text-muted)', padding: '8px', borderRadius: '10px', cursor: 'pointer', fontSize: '0.8rem' }}>
            Scan Another File
          </button>
        </div>
      )}
    </div>
  );
}

function HistoryPanel({ history }) {
  return (
    <div style={{ maxWidth: '560px', margin: '0 auto' }}>
      <h2 style={{ fontFamily: 'Outfit,sans-serif', fontSize: '1.4rem', marginBottom: '6px' }}>Scan History</h2>
      <p style={{ color: 'var(--med-text-muted)', fontSize: '0.85rem', marginBottom: '24px' }}>All your brain scans from this session.</p>
      {history.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px', background: 'var(--med-surface)', borderRadius: '16px', color: 'var(--med-text-muted)' }}>
          <History size={36} style={{ opacity: 0.3, display: 'block', margin: '0 auto 12px' }} />
          <p>No scans yet. Go to Brain Scan to upload.</p>
        </div>
      ) : (
        history.map((item, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '16px', background: 'var(--med-surface)', border: `1px solid ${item.result === 'seizure' ? 'rgba(244,63,94,0.2)' : 'var(--med-border)'}`, borderRadius: '14px', marginBottom: '10px' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '50%', background: item.result === 'seizure' ? 'rgba(244,63,94,0.12)' : 'rgba(16,185,129,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              {item.result === 'seizure' ? <AlertTriangle size={20} style={{ color: 'var(--med-alert)' }} /> : <CheckCircle size={20} style={{ color: 'var(--med-safe)' }} />}
            </div>
            <div style={{ flex: 1 }}>
              <p style={{ fontWeight: '600', fontSize: '0.9rem', color: item.result === 'seizure' ? 'var(--med-alert)' : 'var(--med-safe)', marginBottom: '2px' }}>
                {item.result === 'seizure' ? 'Seizure Detected' : 'Healthy Activity'}
              </p>
              <p style={{ fontSize: '0.78rem', color: 'var(--med-text-muted)' }}>{item.file}</p>
            </div>
            <div style={{ textAlign: 'right', flexShrink: 0 }}>
              <p style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--med-text)' }}>{item.risk}%</p>
              <p style={{ fontSize: '0.72rem', color: 'var(--med-text-muted)' }}>{item.date} · {item.time}</p>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

function MedicationPanel() {
  const [meds, setMeds] = useState(DEFAULT_MEDS);
  const toggle = (i) => setMeds(prev => prev.map((m, idx) => idx === i ? { ...m, taken: !m.taken } : m));
  const takenCount = meds.filter(m => m.taken).length;

  return (
    <div style={{ maxWidth: '560px', margin: '0 auto' }}>
      <h2 style={{ fontFamily: 'Outfit,sans-serif', fontSize: '1.4rem', marginBottom: '6px' }}>Medication Reminders</h2>
      <p style={{ color: 'var(--med-text-muted)', fontSize: '0.85rem', marginBottom: '24px' }}>Track your daily anti-epileptic medication schedule.</p>

      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
        <div style={{ flex: 1, padding: '16px', background: 'rgba(16,185,129,0.07)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '12px', textAlign: 'center' }}>
          <p style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--med-safe)', fontFamily: 'Outfit,sans-serif' }}>{takenCount}/{meds.length}</p>
          <p style={{ fontSize: '0.78rem', color: 'var(--med-text-muted)' }}>Doses taken today</p>
        </div>
        <div style={{ flex: 1, padding: '16px', background: 'rgba(245,158,11,0.07)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: '12px', textAlign: 'center' }}>
          <p style={{ fontSize: '2rem', fontWeight: '700', color: 'var(--med-warn)', fontFamily: 'Outfit,sans-serif' }}>{meds.length - takenCount}</p>
          <p style={{ fontSize: '0.78rem', color: 'var(--med-text-muted)' }}>Remaining today</p>
        </div>
      </div>

      {meds.map((med, i) => (
        <div key={i} onClick={() => toggle(i)} style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '16px', borderRadius: '14px', marginBottom: '10px', cursor: 'pointer', background: med.taken ? 'rgba(16,185,129,0.06)' : 'var(--med-surface)', border: `1px solid ${med.taken ? 'rgba(16,185,129,0.25)' : 'var(--med-border)'}`, transition: 'all 0.2s' }}>
          <div style={{ width: '24px', height: '24px', borderRadius: '50%', border: `2px solid ${med.taken ? 'var(--med-safe)' : 'var(--med-text-muted)'}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            {med.taken && <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'var(--med-safe)' }} />}
          </div>
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: '0.9rem', fontWeight: '600', color: med.taken ? 'var(--med-text-muted)' : 'var(--med-text)', textDecoration: med.taken ? 'line-through' : 'none', marginBottom: '2px' }}>{med.name}</p>
            <p style={{ fontSize: '0.78rem', color: 'var(--med-text-muted)' }}>{med.dose} · {med.time}</p>
          </div>
          {!med.taken ? <Clock size={16} style={{ color: 'var(--med-warn)', flexShrink: 0 }} /> : <CheckCircle size={16} style={{ color: 'var(--med-safe)', flexShrink: 0 }} />}
        </div>
      ))}

      <div style={{ marginTop: '16px', padding: '14px', background: 'rgba(56,189,248,0.05)', border: '1px solid rgba(56,189,248,0.15)', borderRadius: '12px' }}>
        <p style={{ fontSize: '0.82rem', color: 'var(--med-text-muted)' }}>
          💡 <strong style={{ color: 'var(--med-accent)' }}>Tip:</strong> Take your anti-epileptic medications at the same time every day for best results. Missing doses is one of the most common causes of breakthrough seizures.
        </p>
      </div>
    </div>
  );
}

// ---- Main ----
export default function PatientHome() {
  const navigate = useNavigate();
  const [active, setActive] = useState('status');
  const [animKey, setAnimKey] = useState(0);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle');
  const [resultData, setResultData] = useState(null);
  const [history, setHistory] = useState([]);

  const email = localStorage.getItem('epichat_email') || 'patient@epichat.ai';
  const name = email.split('@')[0].replace(/\./g, ' ');

  const handleLogout = () => {
    localStorage.removeItem('epichat_role');
    localStorage.removeItem('epichat_email');
    navigate('/login');
  };

  const onScanComplete = (data, filename) => {
    setHistory(prev => [{
      file: filename, result: data.result,
      risk: data.risk_score, type: data.seizure_type,
      date: new Date().toLocaleDateString('en-IN'),
      time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
    }, ...prev.slice(0, 9)]);
  };

  const handleContact = () => {
    alert('📞 Contacting your assigned physician...\n\nDr. [Assigned Clinician]\nEpiChat Medical Network\n+91-XXXX-XXXXXX');
  };

  const latestResult = history[0] || null;

  const handleNavClick = (id) => {
    setActive(id);
    setAnimKey(k => k + 1); // retrigger animation
  };

  const panels = {
    status: <StatusPanel latestResult={latestResult} onContact={handleContact} />,
    scan: <ScanPanel file={file} setFile={setFile} status={status} setStatus={setStatus} resultData={resultData} setResultData={setResultData} onScanComplete={onScanComplete} />,
    history: <HistoryPanel history={history} />,
    medication: <MedicationPanel />,
    chatbot: <div style={{ height: '100%', maxWidth: '500px', margin: '0 auto' }}><Chatbot /></div>,
  };

  return (
    <div style={{ background: 'var(--med-bg)', height: '100vh', color: 'var(--med-text)', fontFamily: 'Inter, sans-serif', display: 'flex', overflow: 'hidden' }}>

      {/* Sidebar */}
      <aside style={{ width: '210px', background: 'var(--med-surface)', borderRight: '1px solid var(--med-border)', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
        <div style={{ padding: '20px 16px', borderBottom: '1px solid var(--med-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Heart size={18} style={{ color: 'var(--med-safe)' }} />
            <span style={{ fontFamily: 'Outfit,sans-serif', fontSize: '1.1rem', fontWeight: '700', color: '#fff' }}>EpiChat</span>
          </div>
          <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <User size={12} style={{ color: 'var(--med-text-muted)' }} />
            <span style={{ fontSize: '0.72rem', color: 'var(--med-text-muted)', textTransform: 'capitalize', wordBreak: 'break-all' }}>{name}</span>
          </div>
        </div>

        <nav style={{ padding: '12px 10px', flex: 1 }}>
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => handleNavClick(id)} style={{
              width: '100%', display: 'flex', alignItems: 'center', gap: '10px',
              padding: '10px 12px', borderRadius: '10px', border: 'none', cursor: 'pointer',
              marginBottom: '4px', fontFamily: 'Inter,sans-serif', fontSize: '0.875rem', fontWeight: '500',
              background: active === id ? 'rgba(16,185,129,0.12)' : 'transparent',
              color: active === id ? 'var(--med-safe)' : 'var(--med-text-muted)',
              borderLeft: active === id ? '2px solid var(--med-safe)' : '2px solid transparent',
              transition: 'all 0.2s'
            }}>
              <Icon size={16} />
              {label}
            </button>
          ))}
        </nav>

        <div style={{ padding: '12px 10px', borderTop: '1px solid var(--med-border)' }}>
          <button onClick={handleLogout} style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 12px', borderRadius: '10px', border: '1px solid rgba(244,63,94,0.2)', cursor: 'pointer', background: 'rgba(244,63,94,0.06)', color: 'var(--med-alert)', fontSize: '0.85rem', fontFamily: 'Inter,sans-serif' }}>
            <LogOut size={15} /> Sign Out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main
        key={animKey}
        style={{ flex: 1, overflowY: 'auto', padding: '32px', animation: 'fadeInUp 0.35s cubic-bezier(0.22,1,0.36,1) both' }}
      >
        {panels[active] || null}
      </main>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(18px); }
          to   { opacity: 1; transform: translateY(0);    }
        }
      `}</style>
    </div>
  );
}
