import React from 'react';
import {
  LayoutDashboard,
  UploadCloud,
  MessageSquare,
  BookOpenCheck,
  TrendingUp,
  Sparkles,
  Award
} from 'lucide-react';

export default function Sidebar({ activePage, setActivePage, hasResults }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'upload', label: 'Upload Materials', icon: UploadCloud },
    { id: 'chat', label: 'AI Tutor', icon: MessageSquare },
    { id: 'quiz', label: 'Take Quiz', icon: BookOpenCheck },
    ...(hasResults ? [{ id: 'results', label: 'Quiz Results', icon: Award }] : []),
    { id: 'mastery', label: 'Topic Mastery', icon: TrendingUp },
  ];

  return (
    <aside className="sidebar">
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2rem', padding: '0 0.5rem' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #6366f1, #a855f7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          boxShadow: '0 4px 12px rgba(99, 102, 241, 0.4)'
        }}>
          <Sparkles size={20} />
        </div>
        <div>
          <h1 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            StudySmart
          </h1>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 500 }}>
            Adaptive AI Portal
          </span>
        </div>
      </div>

      {/* Nav List */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', flex: 1 }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActivePage(item.id)}
              className={`nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={19} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Track & System Badge */}
      <div style={{
        padding: '1rem',
        borderRadius: '10px',
        background: 'rgba(255, 255, 255, 0.05)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        marginTop: 'auto'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>TRACK D</span>
          <span style={{
            fontSize: '0.7rem',
            padding: '2px 6px',
            background: 'rgba(16, 185, 129, 0.2)',
            color: '#34d399',
            borderRadius: '4px',
            fontWeight: 600
          }}>
            Gemini RAG
          </span>
        </div>
        <p style={{ fontSize: '0.775rem', color: '#cbd5e1', lineHeight: '1.3' }}>
          Personalized Tutoring & Adaptive Learning
        </p>
      </div>
    </aside>
  );
}
