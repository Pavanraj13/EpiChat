import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, ShieldAlert } from 'lucide-react';

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { 
      id: 1, 
      sender: 'ai', 
      text: "Hello! I'm the EpiChat AI assistant. I can help interpret EEG results or provide general information about epilepsy. How can I help you today?",
      isDisclaimer: false
    },
    {
      id: 2,
      sender: 'ai',
      text: "Medical Disclaimer: This AI is an educational tool and does not provide clinical diagnoses. In case of a medical emergency, please contact 108 (in India) or your local emergency services immediately.",
      isDisclaimer: true
    }
  ]);
  const [inputVal, setInputVal] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputVal.trim() || isTyping) return;

    const userMsg = { id: Date.now(), sender: 'user', text: inputVal };
    setMessages(prev => [...prev, userMsg]);
    setInputVal('');
    setIsTyping(true);

    try {
      const response = await fetch('http://localhost:8000/api/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: inputVal })
      });

      if (!response.ok) throw new Error('API Error');
      
      const data = await response.json();
      
      setTimeout(() => {
        setMessages(prev => [...prev, { id: Date.now(), sender: 'ai', text: data.text }]);
        setIsTyping(false);
      }, 600); // Slight delay for natural feel

    } catch (err) {
      console.error("Chat Error:", err);
      setMessages(prev => [...prev, { id: Date.now(), sender: 'ai', text: "I'm having trouble connecting to my brain right now. Please ensure the server is running." }]);
      setIsTyping(false);
    }
  };

  return (
    <div className="glass-panel chatbot-container" style={{ display: 'flex', flexDirection: 'column', height: '100%', borderRadius: '24px', overflow: 'hidden', background: 'rgba(15,23,42,0.85)', border: '1px solid var(--med-border)' }}>
      <div className="chatbot-header" style={{ padding: '16px 20px', background: 'rgba(0,0,0,0.3)', borderBottom: '1px solid var(--med-border)', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ padding: '8px', background: 'rgba(56,189,248,0.1)', borderRadius: '12px' }}>
          <Bot size={22} style={{ color: 'var(--med-accent)' }} />
        </div>
        <div>
          <h3 style={{ margin: 0, fontSize: '1rem', fontFamily: 'Outfit,sans-serif', color: '#fff' }}>EpiChat Assistant</h3>
          <p style={{ margin: 0, fontSize: '0.7rem', color: 'var(--med-text-muted)' }}>Online · Clinical AI Engine</p>
        </div>
      </div>
      
      <div className="chatbot-messages" style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {messages.map(msg => (
          <div key={msg.id} style={{ alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start', maxWidth: '85%' }}>
            <div style={{ display: 'flex', gap: '8px', flexDirection: msg.sender === 'user' ? 'row-reverse' : 'row' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: msg.sender === 'user' ? 'var(--med-accent)' : 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                {msg.sender === 'user' ? <User size={14} color="#0f172a" /> : <Bot size={14} color="var(--med-accent)" />}
              </div>
              <div style={{ 
                padding: '12px 16px', 
                borderRadius: '16px', 
                fontSize: '0.88rem', 
                lineHeight: '1.5',
                background: msg.isDisclaimer ? 'rgba(244,63,94,0.08)' : msg.sender === 'user' ? 'var(--med-accent)' : 'rgba(255,255,255,0.05)',
                color: msg.sender === 'user' ? '#0f172a' : msg.isDisclaimer ? 'var(--med-alert)' : '#e2e8f0',
                border: msg.isDisclaimer ? '1px solid rgba(244,63,94,0.2)' : 'none',
                fontWeight: msg.sender === 'user' ? '600' : '400'
              }}>
                {msg.isDisclaimer && <ShieldAlert size={14} style={{ marginBottom: '4px', display: 'block' }} />}
                {msg.text}
              </div>
            </div>
          </div>
        ))}
        {isTyping && (
          <div style={{ alignSelf: 'flex-start', display: 'flex', gap: '8px' }}>
            <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bot size={14} color="var(--med-accent)" />
            </div>
            <div style={{ padding: '12px 16px', background: 'rgba(255,255,255,0.05)', borderRadius: '16px', display: 'flex', gap: '4px', alignItems: 'center' }}>
               <div className="dot" style={{ width: '4px', height: '4px', background: '#94a3b8', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out' }}></div>
               <div className="dot" style={{ width: '4px', height: '4px', background: '#94a3b8', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out 0.2s' }}></div>
               <div className="dot" style={{ width: '4px', height: '4px', background: '#94a3b8', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out 0.4s' }}></div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form onSubmit={handleSend} style={{ padding: '16px', background: 'rgba(0,0,0,0.2)', borderTop: '1px solid var(--med-border)', display: 'flex', gap: '10px' }}>
        <input 
          type="text" 
          value={inputVal} 
          onChange={(e) => setInputVal(e.target.value)} 
          placeholder="Ask about seizure types, EEG, or meds..." 
          style={{ flex: 1, background: 'rgba(255,255,255,0.03)', border: '1px solid var(--med-border)', borderRadius: '12px', padding: '10px 16px', color: '#fff', fontSize: '0.9rem' }}
        />
        <button type="submit" disabled={isTyping} style={{ background: 'var(--med-accent)', color: '#0f172a', border: 'none', padding: '10px', borderRadius: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: isTyping ? 0.5 : 1 }}>
          <Send size={18} />
        </button>
      </form>

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1.0); }
        }
      `}</style>
    </div>
  );
}
