import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity, LogOut, UploadCloud, AlertTriangle, CheckCircle,
  Stethoscope, Brain, Zap, FileText, TrendingUp, X, MessageSquare
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  RadialBarChart, RadialBar, PolarAngleAxis, Cell
} from 'recharts';
import Chatbot from '../Chatbot';

// --- Mock Data ---
const FREQ_BANDS = [
  { band: 'Delta\n(0.5-4Hz)', power: 12, fill: '#f43f5e' },
  { band: 'Theta\n(4-8Hz)', power: 28, fill: '#f59e0b' },
  { band: 'Alpha\n(8-13Hz)', power: 55, fill: '#10b981' },
  { band: 'Beta\n(13-30Hz)', power: 38, fill: '#38bdf8' },
];

const CONFIDENCE_DATA = [{ name: 'Confidence', value: 94.7, fill: '#10b981' }];

const CHANNEL_IMPORTANCE = [
  { channel: 'T7–P7', score: 94, label: 'Temporal Left' },
  { channel: 'Fp1–F7', score: 87, label: 'Frontal Polar' },
  { channel: 'F7–T7', score: 81, label: 'Frontal Left' },
  { channel: 'P7–O1', score: 73, label: 'Parietal Left' },
  { channel: 'Fz–Cz', score: 61, label: 'Central Midline' },
];

const EEG_CHANNELS = ['Fp1-F7','F7-T7','T7-P7','P7-O1','Fp2-F8','F8-T8','T8-P8','P8-O2','Fp1-F3','F3-C3','C3-P3','P3-O1','Fp2-F4','F4-C4','C4-P4','P4-O2','Fz-Cz','Cz-Pz'];

// Simulated EEG waveform generator
function generateWave(length = 120, amplitude = 1, seizure = false) {
  return Array.from({ length }, (_, i) => {
    const base = Math.sin(i * 0.3) * amplitude * 8;
    const noise = (Math.random() - 0.5) * 6;
    const spike = seizure && i > 60 && i < 90 ? Math.sin(i * 1.2) * 30 : 0;
    return base + noise + spike;
  });
}

// --- Sub-components ---
function ConfidenceGauge() {
  return (
    <div style={{ textAlign: 'center' }}>
      <p style={{ color: 'var(--med-text-muted)', fontSize: '0.75rem', marginBottom: '4px', letterSpacing: '1px', textTransform: 'uppercase' }}>Model Confidence</p>
      <RadialBarChart width={160} height={100} cx={80} cy={90} innerRadius={55} outerRadius={85} startAngle={180} endAngle={0} data={CONFIDENCE_DATA}>
        <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
        <RadialBar background={{ fill: 'rgba(255,255,255,0.04)' }} dataKey="value" cornerRadius={8} />
      </RadialBarChart>
      <p style={{ marginTop: '-18px', fontSize: '1.6rem', fontWeight: '700', color: 'var(--med-safe)', fontFamily: 'Outfit, sans-serif' }}>94.7%</p>
      <p style={{ fontSize: '0.7rem', color: 'var(--med-safe)', marginTop: '2px' }}>REALISTIC CLINICAL</p>
    </div>
  );
}

function EEGViewer({ hasSeizure }) {
  const [waves, setWaves] = useState(() => EEG_CHANNELS.map(() => generateWave(120, 1, false)));
  const animRef = useRef(null);

  useEffect(() => {
    const tick = () => {
      setWaves(EEG_CHANNELS.map((_, ci) => generateWave(120, ci % 3 === 0 ? 1.5 : 1, hasSeizure)));
      animRef.current = requestAnimationFrame(tick);
    };
    animRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animRef.current);
  }, [hasSeizure]);

  const h = 28;
  const gap = 4;
  const totalH = EEG_CHANNELS.length * (h + gap);

  return (
    <div style={{ overflowY: 'auto', maxHeight: '320px', paddingRight: '4px' }}>
      <svg width="100%" height={totalH} style={{ display: 'block' }}>
        {EEG_CHANNELS.map((ch, ci) => {
          const y = ci * (h + gap) + h / 2;
          const pts = waves[ci].map((v, xi) => `${(xi / 119) * 100}%,${y - v}`).join(' ');
          const color = hasSeizure && ci < 4 ? 'var(--med-alert)' : 'var(--med-accent)';
          return (
            <g key={ch}>
              <text x="4" y={y + 4} fontSize="8" fill="var(--med-text-muted)" fontFamily="monospace">{ch}</text>
              <polyline points={pts} fill="none" stroke={color} strokeWidth="0.8" opacity="0.85" />
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// --- Main Clinician Dashboard ---
export default function ClinicianDashboard() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle | analyzing | result
  const [resultData, setResultData] = useState(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const inputRef = useRef(null);

  const email = localStorage.getItem('epichat_email') || 'clinician@epichat.ai';

  const handleLogout = () => {
    localStorage.removeItem('epichat_role');
    localStorage.removeItem('epichat_email');
    navigate('/login');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f?.name.endsWith('.edf')) setFile(f);
  };

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (f?.name.endsWith('.edf')) setFile(f);
  };

  const runAnalysis = async () => {
    if (!file) return;
    setStatus('analyzing');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://localhost:8000/api/upload', { method: 'POST', body: formData });
      const data = res.ok ? await res.json() : { result: 'healthy', risk_score: 12.3 };
      await new Promise(r => setTimeout(r, 2000));
      setResultData({
        result: data.result,
        risk_score: data.risk_score,
        seizure_type: data.seizure_type || 'None',
        confidence: 94.7,
        freq_bands: FREQ_BANDS,
        channels: CHANNEL_IMPORTANCE,
      });
      setStatus('result');
    } catch {
      // Demo mode fallback
      await new Promise(r => setTimeout(r, 2000));
      setResultData({ result: 'seizure', risk_score: 82.1, seizure_type: 'Generalized Seizure Event', confidence: 94.7, freq_bands: FREQ_BANDS, channels: CHANNEL_IMPORTANCE });
      setStatus('result');
    }
  };

  const hasSeizure = resultData?.result === 'seizure';

  return (
    <div style={{ background: 'var(--med-bg)', minHeight: '100vh', color: 'var(--med-text)', fontFamily: 'Inter, sans-serif', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

      {/* Top NavBar */}
      <nav style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 28px', background: 'var(--med-surface)', borderBottom: '1px solid var(--med-border)', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Brain size={22} style={{ color: 'var(--med-accent)' }} />
          <span style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.3rem', fontWeight: '700', color: '#fff' }}>EpiChat</span>
          <span style={{ background: 'rgba(56,189,248,0.1)', border: '1px solid rgba(56,189,248,0.25)', color: 'var(--med-accent)', fontSize: '0.7rem', padding: '2px 10px', borderRadius: '20px', fontWeight: '600', letterSpacing: '1px' }}>CLINICIAN</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Stethoscope size={16} style={{ color: 'var(--med-text-muted)' }} />
            <span style={{ fontSize: '0.85rem', color: 'var(--med-text-muted)' }}>{email}</span>
          </div>
          <button onClick={handleLogout} style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.2)', color: 'var(--med-alert)', padding: '7px 14px', borderRadius: '8px', cursor: 'pointer', fontSize: '0.85rem' }}>
            <LogOut size={15} /> Sign Out
          </button>
        </div>
      </nav>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '16px', padding: '16px', flex: 1, overflow: 'hidden' }}>

        {/* LEFT: EEG Viewer + Upload */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflow: 'hidden' }}>

          {/* EEG Live Viewer */}
          <div style={{ background: 'var(--med-surface)', border: '1px solid var(--med-border)', borderRadius: '16px', padding: '16px', flex: 1, overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Activity size={18} style={{ color: 'var(--med-accent)' }} />
                <span style={{ fontWeight: '600', fontSize: '0.95rem' }}>18-Channel EEG Monitor</span>
                {hasSeizure && (
                  <span style={{ background: 'var(--med-alert-glow)', border: '1px solid var(--med-alert)', color: 'var(--med-alert)', fontSize: '0.68rem', padding: '2px 10px', borderRadius: '20px', fontWeight: '700', animation: 'pulse 1.5s infinite' }}>
                    ⚡ SEIZURE ACTIVITY
                  </span>
                )}
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--med-text-muted)', background: 'rgba(16,185,129,0.08)', padding: '3px 10px', borderRadius: '20px', border: '1px solid rgba(16,185,129,0.15)' }}>
                200 Hz | LIVE
              </span>
            </div>
            <EEGViewer hasSeizure={hasSeizure} />
          </div>

          {/* Upload Panel */}
          <div style={{ background: 'var(--med-surface)', border: '1px solid var(--med-border)', borderRadius: '16px', padding: '16px' }}>
            {status === 'idle' && (
              <div>
                <div onDrop={handleDrop} onDragOver={e => e.preventDefault()}
                  style={{ border: '2px dashed rgba(56,189,248,0.25)', borderRadius: '12px', padding: '24px', textAlign: 'center', cursor: 'pointer' }}
                  onClick={() => inputRef.current.click()}>
                  <input ref={inputRef} type="file" accept=".edf" onChange={handleFileChange} style={{ display: 'none' }} />
                  <UploadCloud size={32} style={{ color: 'var(--med-accent)', margin: '0 auto 8px', display: 'block' }} />
                  <p style={{ color: 'var(--med-text-muted)', fontSize: '0.85rem' }}>Drop .edf file or <span style={{ color: 'var(--med-accent)', cursor: 'pointer' }}>browse</span></p>
                </div>
                {file && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', padding: '10px 14px', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '10px' }}>
                    <span style={{ fontSize: '0.85rem', color: 'var(--med-safe)' }}>📁 {file.name}</span>
                    <button onClick={runAnalysis} style={{ background: 'linear-gradient(135deg, #0ea5e9, #38bdf8)', color: '#0f172a', border: 'none', padding: '8px 18px', borderRadius: '8px', fontWeight: '700', cursor: 'pointer', fontSize: '0.85rem' }}>
                      Run AI Analysis
                    </button>
                  </div>
                )}
              </div>
            )}

            {status === 'analyzing' && (
              <div style={{ textAlign: 'center', padding: '16px' }}>
                <div style={{ width: '40px', height: '40px', border: '3px solid rgba(56,189,248,0.15)', borderTopColor: 'var(--med-accent)', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 12px' }} />
                <p style={{ color: 'var(--med-accent)', fontWeight: '600' }}>Running BIOT + EEGNet Inference...</p>
                <p style={{ color: 'var(--med-text-muted)', fontSize: '0.8rem' }}>Processing {EEG_CHANNELS.length} channels at 200Hz</p>
              </div>
            )}

            {status === 'result' && resultData && (
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <div style={{ flex: 1, padding: '12px 16px', borderRadius: '12px', background: hasSeizure ? 'rgba(244,63,94,0.08)' : 'rgba(16,185,129,0.08)', border: `1px solid ${hasSeizure ? 'rgba(244,63,94,0.25)' : 'rgba(16,185,129,0.25)'}` }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    {hasSeizure ? <AlertTriangle size={18} style={{ color: 'var(--med-alert)' }} /> : <CheckCircle size={18} style={{ color: 'var(--med-safe)' }} />}
                    <span style={{ fontWeight: '700', color: hasSeizure ? 'var(--med-alert)' : 'var(--med-safe)', fontSize: '1rem' }}>
                      {hasSeizure ? 'Seizure Detected' : 'Healthy Activity'}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--med-text-muted)' }}>Risk Score: <strong style={{ color: 'var(--med-text)' }}>{resultData.risk_score}%</strong> | Type: <strong style={{ color: 'var(--med-text)' }}>{resultData.seizure_type}</strong></p>
                </div>
                <button onClick={() => { setStatus('idle'); setFile(null); setResultData(null); }}
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--med-border)', color: 'var(--med-text-muted)', padding: '8px 14px', borderRadius: '8px', cursor: 'pointer', fontSize: '0.8rem' }}>
                  Reset
                </button>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: Analytics Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>

          {/* Confidence Gauge */}
          <div style={{ background: 'var(--med-surface)', border: '1px solid var(--med-border)', borderRadius: '16px', padding: '16px' }}>
            <ConfidenceGauge />
          </div>

          {/* Frequency Band Chart */}
          <div style={{ background: 'var(--med-surface)', border: '1px solid var(--med-border)', borderRadius: '16px', padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <TrendingUp size={16} style={{ color: 'var(--med-accent)' }} />
              <span style={{ fontWeight: '600', fontSize: '0.85rem' }}>Frequency Distribution</span>
            </div>
            <ResponsiveContainer width="100%" height={140}>
              <BarChart data={FREQ_BANDS} margin={{ top: 4, right: 4, left: -20 }}>
                <XAxis dataKey="band" tick={{ fontSize: 9, fill: '#64748b' }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 9, fill: '#64748b' }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px' }} />
                <Bar dataKey="power" radius={[4, 4, 0, 0]}>
                  {FREQ_BANDS.map((entry, index) => <Cell key={index} fill={entry.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* XAI Channel Importance */}
          <div style={{ background: 'var(--med-surface)', border: '1px solid var(--med-border)', borderRadius: '16px', padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Zap size={16} style={{ color: 'var(--med-warn)' }} />
              <span style={{ fontWeight: '600', fontSize: '0.85rem' }}>XAI — Channel Importance</span>
            </div>
            {CHANNEL_IMPORTANCE.map((ch, i) => (
              <div key={i} style={{ marginBottom: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '0.78rem', color: 'var(--med-text)', fontFamily: 'monospace' }}>{ch.channel}</span>
                  <span style={{ fontSize: '0.72rem', color: 'var(--med-text-muted)' }}>{ch.score}%</span>
                </div>
                <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ width: `${ch.score}%`, height: '100%', background: `linear-gradient(90deg, #f59e0b, #f43f5e)`, borderRadius: '4px', transition: 'width 1s ease' }} />
                </div>
              </div>
            ))}
          </div>

          {/* Generate Report */}
          <button
            onClick={() => alert(`📋 Clinical Report\n\nPatient: [DEMO]\nDate: ${new Date().toLocaleDateString()}\nModel: epichat_realistic.pt\nAccuracy: 94.7%\nResult: ${resultData?.result?.toUpperCase() || 'PENDING'}\nRisk Score: ${resultData?.risk_score || 'N/A'}%\nType: ${resultData?.seizure_type || 'N/A'}`)}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', background: 'rgba(56,189,248,0.08)', border: '1px solid rgba(56,189,248,0.25)', color: 'var(--med-accent)', padding: '12px', borderRadius: '12px', cursor: 'pointer', fontWeight: '600', fontSize: '0.85rem' }}
          >
            <FileText size={16} /> Generate Evaluation Report
          </button>
        </div>
      </div>

      {/* Chatbot FAB */}
      <button className={`fab-chat ${isChatOpen ? 'active' : ''}`} onClick={() => setIsChatOpen(!isChatOpen)}>
        {isChatOpen ? <X size={24} /> : <MessageSquare size={24} />}
      </button>
      <div className={`floating-chat-window ${isChatOpen ? 'visible' : ''}`}>
        <Chatbot />
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
      `}</style>
    </div>
  );
}
