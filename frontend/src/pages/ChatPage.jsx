import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  User,
  Bot,
  FileText,
  AlertTriangle,
  Lightbulb,
  ExternalLink,
  BookOpen
} from 'lucide-react';
import { sendChatMessage } from '../services/api';

export default function ChatPage({ documents = [] }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: "Hello! I am your AI study assistant. Ask me questions about your uploaded course material, and I'll provide concise explanations with exact page and slide citations.",
      sources: []
    }
  ]);
  const [inputQuestion, setInputQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (questionToSend) => {
    const q = (questionToSend || inputQuestion).trim();
    if (!q || loading) return;

    const userMessageId = `user_${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { id: userMessageId, sender: 'user', text: q }
    ]);
    setInputQuestion('');
    setLoading(true);

    try {
      const data = await sendChatMessage(q);
      const assistantMessageId = `ai_${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        {
          id: assistantMessageId,
          sender: 'assistant',
          text: data.answer,
          sources: data.sources || []
        }
      ]);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error communicating with AI tutor.';
      setMessages((prev) => [
        ...prev,
        {
          id: `err_${Date.now()}`,
          sender: 'assistant',
          isError: true,
          text: `Error: ${errorMsg}`,
          sources: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Render citation highlights in assistant text
  const renderFormattedText = (text) => {
    if (!text) return null;
    // Regex for [Page X] or [Slide Y]
    const parts = text.split(/(\[(?:Page|Slide)\s+\d+\])/gi);
    return parts.map((part, i) => {
      if (/^\[(?:Page|Slide)\s+\d+\]$/i.test(part)) {
        return (
          <span key={i} className="citation-pill" style={{ margin: '0 3px' }}>
            {part}
          </span>
        );
      }
      return part;
    });
  };

  const sampleQuestions = [
    "What is TCP?",
    "Explain the difference between TCP and UDP",
    "What is the capital of France?",
    "Summarize the main concepts from the notes"
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 128px)', gap: '1rem' }}>
      {/* Chat Messages Box */}
      <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '1rem' }}>
        <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            const isRefusal = msg.text?.includes('outside the scope') || msg.text?.includes("couldn't find enough information");

            return (
              <div
                key={msg.id}
                style={{
                  display: 'flex',
                  gap: '0.75rem',
                  alignSelf: isUser ? 'flex-end' : 'flex-start',
                  maxWidth: isUser ? '75%' : '85%',
                }}
              >
                {!isUser && (
                  <div style={{
                    width: '36px', height: '36px', borderRadius: '50%',
                    background: isRefusal ? '#fffbeb' : '#ede9fe',
                    color: isRefusal ? '#d97706' : 'var(--primary)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    {isRefusal ? <AlertTriangle size={18} /> : <Bot size={20} />}
                  </div>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <div style={{
                    padding: '0.9rem 1.2rem',
                    borderRadius: '14px',
                    fontSize: '0.925rem',
                    lineHeight: '1.55',
                    background: isUser ? 'var(--primary)' : isRefusal ? '#fffbeb' : '#f8fafc',
                    color: isUser ? '#fff' : isRefusal ? '#92400e' : 'var(--text-main)',
                    border: isUser ? 'none' : `1px solid ${isRefusal ? '#fde68a' : 'var(--border)'}`,
                    boxShadow: '0 1px 2px rgba(0,0,0,0.04)',
                    whiteSpace: 'pre-wrap'
                  }}>
                    {isUser ? msg.text : renderFormattedText(msg.text)}
                  </div>

                  {/* Sources List for Assistant Answers */}
                  {!isUser && msg.sources && msg.sources.length > 0 && (
                    <div style={{
                      padding: '0.65rem 0.9rem',
                      background: '#f1f5f9',
                      borderRadius: '8px',
                      border: '1px solid #e2e8f0',
                      fontSize: '0.8rem'
                    }}>
                      <div style={{ fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <BookOpen size={13} /> GROUNDED SOURCES:
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                        {msg.sources.map((src, idx) => {
                          const loc = src.page !== undefined && src.page !== null
                            ? `Page ${src.page}`
                            : src.slide !== undefined && src.slide !== null
                            ? `Slide ${src.slide}`
                            : 'Course Material';
                          return (
                            <div
                              key={idx}
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '0.35rem',
                                padding: '0.2rem 0.5rem',
                                background: '#fff',
                                borderRadius: '6px',
                                border: '1px solid #cbd5e1',
                                fontWeight: 500,
                                color: 'var(--text-main)'
                              }}
                            >
                              <FileText size={12} color="var(--primary)" />
                              <span>{src.filename}</span>
                              <span style={{ color: 'var(--text-muted)' }}>—</span>
                              <strong style={{ color: '#4338ca' }}>{loc}</strong>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>

                {isUser && (
                  <div style={{
                    width: '36px', height: '36px', borderRadius: '50%',
                    background: 'var(--primary)', color: '#fff',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    <User size={18} />
                  </div>
                )}
              </div>
            );
          })}

          {loading && (
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
              <div style={{
                width: '36px', height: '36px', borderRadius: '50%',
                background: '#ede9fe', color: 'var(--primary)',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}>
                <Bot size={20} />
              </div>
              <div style={{
                padding: '0.75rem 1rem', background: '#f8fafc',
                borderRadius: '12px', border: '1px solid var(--border)',
                fontSize: '0.875rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.5rem'
              }}>
                <Sparkles size={16} className="animate-spin" color="var(--primary)" />
                <span>Searching vector store & verifying course citations...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestion Chips */}
        <div style={{ padding: '0.5rem 0.75rem', borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '0.5rem', overflowX: 'auto' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <Lightbulb size={12} /> Suggestions:
          </span>
          {sampleQuestions.map((sq, i) => (
            <button
              key={i}
              onClick={() => handleSend(sq)}
              disabled={loading}
              style={{
                fontSize: '0.75rem',
                padding: '0.25rem 0.65rem',
                borderRadius: '999px',
                background: '#f1f5f9',
                border: '1px solid #e2e8f0',
                color: 'var(--text-main)',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s'
              }}
              onMouseEnter={(e) => e.target.style.background = '#e2e8f0'}
              onMouseLeave={(e) => e.target.style.background = '#f1f5f9'}
            >
              {sq}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          style={{ display: 'flex', gap: '0.75rem', padding: '0.75rem 0 0 0' }}
        >
          <input
            type="text"
            value={inputQuestion}
            onChange={(e) => setInputQuestion(e.target.value)}
            placeholder="Ask anything grounded in your course materials..."
            disabled={loading}
            style={{
              flex: 1,
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              border: '1px solid var(--border)',
              fontSize: '0.925rem',
              outline: 'none',
              transition: 'border 0.2s',
            }}
            onFocus={(e) => e.target.style.borderColor = 'var(--primary)'}
            onBlur={(e) => e.target.style.borderColor = 'var(--border)'}
          />
          <button
            type="submit"
            disabled={!inputQuestion.trim() || loading}
            className="btn btn-primary"
            style={{ padding: '0 1.5rem' }}
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
