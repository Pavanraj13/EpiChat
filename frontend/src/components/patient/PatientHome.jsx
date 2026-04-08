import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User, LogOut, Phone, Pill, Calendar, Shield,
  CheckCircle, AlertTriangle, Clock, Heart
} from 'lucide-react';

// --- Mock Data ---
const SEIZURE_LOG = [
  { date: '2026-04-05', time: '03:12 AM', type: 'Generalized', duration: '45s', severity: 'High' },
  { date: '2026-03-28', time: '11:40 PM', type: 'Focal', duration: '28s', severity: 'Moderate' },
  { date: '2026-03-14', time: '07:15 AM', type: 'Generalized', duration: '62s', severity: 'High' },
];

const MEDICATIONS = [
  { name: 'Levetiracetam (Keppra)', dose: '500mg', time: '8:00 AM', taken: true },
  { name: 'Valproic Acid', dose: '250mg', time: '2:00 PM', taken: false },
  { name: 'Levetiracetam (Keppra)', dose: '500mg', time: '8:00 PM', taken: false },
];

const DAYS_SEIZURE_FREE = 3;
const STATUS_STABLE = true;

export default function PatientHome() {
  const navigate = useNavigate();
  const [medications, setMedications] = useState(MEDICATIONS);
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

  return (
    <div style={{ background: 'var(--med-bg)', minHeight: '100vh', color: 'var(--med-text)', fontFamily: 'Inter, sans-serif', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

      {/* Nav */}
      <nav style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 24px', background: 'var(--med-surface)', borderBottom: '1px solid var(--med-border)', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Heart size={20} style={{ color: 'var(--med-safe)' }} />
          <span style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.2rem', fontWeight: '700', color: '#fff' }}>EpiChat</span>
          <span style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)', color: 'var(--med-safe)', fontSize: '0.7rem', padding: '2px 10px', borderRadius: '20px' }}>PATIENT</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <User size={15} style={{ color: 'var(--med-text-muted)' }} />
            <span style={{ fontSize: '0.85rem', color: 'var(--med-text-muted)', textTransform: 'capitalize' }}>{name}</span>
          </div>
          <button onClick={handleLogout} style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.15)', color: 'var(--med-alert)', padding: '6px 12px', borderRadius: '8px', cursor: 'pointer', fontSize: '0.8rem' }}>
            <LogOut size={14} /> Sign Out
          </button>
        </div>
      </nav>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', padding: '16px', flex: 1, overflowY: 'auto' }}>

        {/* LEFT column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* Big Status Card */}
          <div style={{
            background: STATUS_STABLE ? 'rgba(16,185,129,0.06)' : 'rgba(244,63,94,0.06)',
            border: `2px solid ${STATUS_STABLE ? 'rgba(16,185,129,0.3)' : 'rgba(244,63,94,0.4)'}`,
            borderRadius: '20px', padding: '28px', textAlign: 'center',
            boxShadow: `0 0 40px ${STATUS_STABLE ? 'rgba(16,185,129,0.08)' : 'rgba(244,63,94,0.12)'}`
          }}>
            <div style={{ width: '80px', height: '80px', borderRadius: '50%', margin: '0 auto 16px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: STATUS_STABLE ? 'rgba(16,185,129,0.15)' : 'rgba(244,63,94,0.15)', border: `2px solid ${STATUS_STABLE ? 'var(--med-safe)' : 'var(--med-alert)'}` }}>
              {STATUS_STABLE
                ? <CheckCircle size={36} style={{ color: 'var(--med-safe)' }} />
                : <AlertTriangle size={36} style={{ color: 'var(--med-alert)' }} />}
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--med-text-muted)', textTransform: 'uppercase', letterSpacing: '2px', marginBottom: '6px' }}>Brain Activity Status</p>
            <h2 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '2rem', fontWeight: '700', color: STATUS_STABLE ? 'var(--med-safe)' : 'var(--med-alert)', margin: '0 0 8px' }}>
              {STATUS_STABLE ? '🟢 Stable' : '🔴 Alert'}
            </h2>
            <p style={{ color: 'var(--med-text-muted)', fontSize: '0.9rem' }}>
              {STATUS_STABLE ? 'Your brain activity is within normal ranges.' : 'A seizure event has been recently detected. Contact your physician.'}
            </p>
          </div>

          {/* Days Seizure Free */}
          <div style={{ background: 'var(--med-surface)', border: '1px solid var(--med-border)', borderRadius: '16px', padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'rgba(56,189,248,0.1)', border: '2px solid rgba(56,189,248,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <Shield size={24} style={{ color: 'var(--med-accent)' }} />
            </div>
            <div>
              <p style={{ fontSize: '0.75rem', color: 'var(--med-text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>Days Seizure Free</p>
              <p style={{ fontFamily: 'Outfit, sans-serif', fontSize: '2.4rem', fontWeight: '700', color: 'var(--med-accent)', lineHeight: 1 }}>{DAYS_SEIZURE_FREE}</p>
              <p style={{ fontSize: '0.75rem', color: 'var(--med-text-muted)' }}>Keep it up! Last event: April 5, 2026</p>
            </div>
          </div>

          {/* Emergency - Contact Physician */}
          <button style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px',
            width: '100%', padding: '18px',
            background: 'linear-gradient(135deg, #10b981, #059669)',
            border: 'none', borderRadius: '16px',
            color: '#fff', fontFamily: 'Outfit, sans-serif', fontSize: '1.1rem', fontWeight: '700',
            cursor: 'pointer', boxShadow: '0 8px 30px rgba(16,185,129,0.35)',
            transition: 'transform 0.2s, box-shadow 0.2s'
          }}
            onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.02)'}
            onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
            onClick={() => alert('📞 Contacting your assigned physician...\n\nDr. [Assigned Clinician]\nEpiChat Medical Network\n+91-XXXX-XXXXXX')}
          >
            <Phone size={22} /> Contact Physician Now
          </button>
        </div>

        {/* RIGHT column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* Medication Reminders */}
          <div style={{ background: 'var(--med-surface)', border: '1px solid var(--med-border)', borderRadius: '16px', padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <Pill size={18} style={{ color: 'var(--med-warn)' }} />
              <span style={{ fontWeight: '700', fontSize: '1rem' }}>Medication Today</span>
            </div>
            {medications.map((med, i) => (
              <div key={i} onClick={() => toggleMed(i)} style={{
                display: 'flex', alignItems: 'center', gap: '12px', padding: '12px',
                borderRadius: '12px', marginBottom: '8px', cursor: 'pointer',
                background: med.taken ? 'rgba(16,185,129,0.06)' : 'rgba(255,255,255,0.03)',
                border: `1px solid ${med.taken ? 'rgba(16,185,129,0.2)' : 'var(--med-border)'}`,
                transition: 'all 0.2s'
              }}>
                <div style={{ width: '20px', height: '20px', borderRadius: '50%', border: `2px solid ${med.taken ? 'var(--med-safe)' : 'var(--med-text-muted)'}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  {med.taken && <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--med-safe)' }} />}
                </div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: '0.85rem', fontWeight: '600', color: med.taken ? 'var(--med-text-muted)' : 'var(--med-text)', textDecoration: med.taken ? 'line-through' : 'none' }}>{med.name}</p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--med-text-muted)' }}>{med.dose} · {med.time}</p>
                </div>
                {!med.taken && <Clock size={14} style={{ color: 'var(--med-warn)', flexShrink: 0 }} />}
              </div>
            ))}
          </div>

          {/* Seizure Event Timeline */}
          <div style={{ background: 'var(--med-surface)', border: '1px solid var(--med-border)', borderRadius: '16px', padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
              <Calendar size={18} style={{ color: 'var(--med-alert)' }} />
              <span style={{ fontWeight: '700', fontSize: '1rem' }}>Seizure History</span>
            </div>
            <div style={{ position: 'relative', paddingLeft: '20px' }}>
              <div style={{ position: 'absolute', left: '7px', top: 0, bottom: 0, width: '2px', background: 'var(--med-border)', borderRadius: '2px' }} />
              {SEIZURE_LOG.map((ev, i) => (
                <div key={i} style={{ position: 'relative', marginBottom: i < SEIZURE_LOG.length - 1 ? '16px' : 0 }}>
                  <div style={{ position: 'absolute', left: '-16px', top: '6px', width: '10px', height: '10px', borderRadius: '50%', background: ev.severity === 'High' ? 'var(--med-alert)' : 'var(--med-warn)', border: '2px solid var(--med-bg)' }} />
                  <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--med-border)', borderRadius: '10px', padding: '10px 12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                      <span style={{ fontSize: '0.8rem', fontWeight: '600', color: ev.severity === 'High' ? 'var(--med-alert)' : 'var(--med-warn)' }}>{ev.type} Seizure</span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--med-text-muted)' }}>{ev.duration}</span>
                    </div>
                    <p style={{ fontSize: '0.72rem', color: 'var(--med-text-muted)' }}>{ev.date} · {ev.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
