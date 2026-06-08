import React, { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Bot, Send, Loader2 } from 'lucide-react';
import './AiAssistant.css';

export const AiAssistant = () => {
  const { apiFetch } = useAuth();
  const location = useLocation();
  const [messages, setMessages] = useState([
    { id: 1, type: 'ai', text: 'Hello! I am the ChemSafe AI Assistant. How can I help you today?' }
  ]);
  const [inputValue, setInputValue] = useState(location.state?.initialText || '');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Clear the location state so that reloading the page doesn't keep the initial text
  useEffect(() => {
    if (location.state?.initialText) {
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Auto-focus input and move cursor to end on mount
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
      const length = inputRef.current.value.length;
      inputRef.current.setSelectionRange(length, length);
    }
  }, []);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    
    // Add user message to UI
    const newUserMsg = { id: Date.now(), type: 'user', text: userMessage };
    setMessages(prev => [...prev, newUserMsg]);
    setIsLoading(true);

    try {
      // Call backend AI endpoint
      const response = await apiFetch('/api/ai/chat', {
        method: 'POST',
        body: JSON.stringify({ message: userMessage })
      });
      
      const aiReply = { id: Date.now() + 1, type: 'ai', text: response.reply };
      setMessages(prev => [...prev, aiReply]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        type: 'ai', 
        text: "Sorry, I couldn't connect to the AI service. Please ensure the GEMINI_API_KEY is configured in the backend." 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="ai-assistant-page">
      <div>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Bot size={28} color="var(--color-primary)" />
          ChemSafe AI Assistant
        </h2>
        <p style={{ color: 'var(--text-muted)' }}>Ask questions about chemical safety, system usage, or general inquiries.</p>
      </div>

      <div className="chat-container">
        <div className="chat-messages">
          {messages.map(msg => (
            <div key={msg.id} className={`chat-bubble ${msg.type}`}>
              {msg.text}
            </div>
          ))}
          {isLoading && (
            <div className="chat-bubble ai" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Loader2 size={16} className="spin" /> Thinking...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSendMessage} className="chat-input-container">
          <input
            ref={inputRef}
            type="text"
            className="chat-input"
            placeholder="Type your message here..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isLoading}
          />
          <button type="submit" className="chat-send-btn" disabled={!inputValue.trim() || isLoading}>
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};
