import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot } from 'lucide-react';

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { id: 1, sender: 'ai', text: "Hello! I'm the EpiChat AI assistant. I can help interpret EEG results or provide general information about epilepsy. How can I help you today?" }
  ]);
  const [inputVal, setInputVal] = useState('');
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!inputVal.trim()) return;

    const newMsg = { id: Date.now(), sender: 'user', text: inputVal };
    setMessages(prev => [...prev, newMsg]);
    setInputVal('');

    // Mock AI response
    setTimeout(() => {
      setMessages(prev => [
        ...prev, 
        { id: Date.now()+1, sender: 'ai', text: "That's a great question! Our AI model analyzes the uploaded EEG signals searching for specific waveform spikes that indicate seizures. Based on your current session data, we are ready for the next test." }
      ]);
    }, 1200);
  };

  return (
    <div className="glass-panel chatbot-container">
      <div className="chatbot-header">
        <Bot size={24} style={{ marginRight: '10px', color: 'var(--text-primary)' }} />
        <h3 style={{ margin: 0 }}>EpiChat AI Assistant</h3>
      </div>
      
      <div className="chatbot-messages">
        {messages.map(msg => (
          <div key={msg.id} className={`chat-message-row ${msg.sender}`}>
            <div className={`chat-bubble ${msg.sender}-bubble`}>
              {msg.text}
            </div>
          </div>
        ))}
        <div ref={endRef} />
      </div>

      <form onSubmit={handleSend} className="chatbot-input-container">
        <input 
          type="text" 
          value={inputVal} 
          onChange={(e) => setInputVal(e.target.value)} 
          placeholder="Message EpiChat AI..." 
          className="chat-input"
        />
        <button type="submit" className="chat-send-btn">
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}
