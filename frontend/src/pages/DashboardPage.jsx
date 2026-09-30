import React from 'react';
import {
  FileText,
  TrendingUp,
  Award,
  BookOpen,
  ArrowRight,
  UploadCloud,
  MessageSquare,
  Sparkles,
  CheckCircle2
} from 'lucide-react';

export default function DashboardPage({
  documents = [],
  masteryTopics = [],
  recentScore,
  onNavigate
}) {
  // Compute average mastery
  const avgMastery = masteryTopics.length > 0
    ? Math.round(masteryTopics.reduce((acc, t) => acc + (t.mastery || 0), 0) / masteryTopics.length)
    : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Welcome Banner */}
      <div style={{
        background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
        borderRadius: '16px',
        padding: '2rem',
        color: '#fff',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 10px 25px -5px rgba(79, 70, 229, 0.3)'
      }}>
        <div style={{ maxWidth: '650px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            background: 'rgba(255, 255, 255, 0.15)',
            padding: '0.25rem 0.75rem',
            borderRadius: '999px',
            fontSize: '0.8rem',
            fontWeight: 600,
            marginBottom: '0.75rem'
          }}>
            <Sparkles size={14} /> Adaptive Tutoring Active
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '0.5rem', letterSpacing: '-0.02em' }}>
            Welcome to Your Smart Study Portal
          </h2>
          <p style={{ color: '#e0e7ff', fontSize: '0.95rem', lineHeight: '1.5' }}>
            Upload your lecture slides, notes, or PDFs. Our RAG engine extracts knowledge,
            provides page-grounded citations, and tracks your mastery topic-by-topic.
          </p>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '1.25rem' }}>
            <button
              onClick={() => onNavigate('upload')}
              className="btn"
              style={{ background: '#fff', color: 'var(--primary)', fontWeight: 700 }}
            >
              <UploadCloud size={16} /> Upload Notes
            </button>
            <button
              onClick={() => onNavigate('chat')}
              className="btn"
              style={{ background: 'rgba(255,255,255,0.2)', color: '#fff', border: '1px solid rgba(255,255,255,0.3)' }}
            >
              <MessageSquare size={16} /> Ask AI Tutor
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid-4">
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '48px', height: '48px', borderRadius: '12px',
            background: '#eef2ff', display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--primary)'
          }}>
            <FileText size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>
              UPLOADED MATERIALS
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>
              {documents.length}
            </div>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '48px', height: '48px', borderRadius: '12px',
            background: '#ecfdf5', display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--success)'
          }}>
            <Award size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>
              RECENT QUIZ SCORE
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--success)' }}>
              {recentScore !== null && recentScore !== undefined ? `${recentScore}%` : 'N/A'}
            </div>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '48px', height: '48px', borderRadius: '12px',
            background: '#f0f9ff', display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--secondary)'
          }}>
            <TrendingUp size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>
              AVERAGE MASTERY
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>
              {avgMastery}%
            </div>
          </div>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '48px', height: '48px', borderRadius: '12px',
            background: '#fffbeb', display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--warning)'
          }}>
            <BookOpen size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>
              ACTIVE TOPICS
            </div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>
              {masteryTopics.length}
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Topic Mastery & Uploaded Docs Preview */}
      <div className="grid-2">
        {/* Topic Mastery Summary */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Topic Mastery</h3>
            <button
              onClick={() => onNavigate('mastery')}
              style={{
                background: 'none', border: 'none', color: 'var(--primary)',
                fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem'
              }}
            >
              View details <ArrowRight size={14} />
            </button>
          </div>

          {masteryTopics.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)' }}>
              <p style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>No topic mastery recorded yet.</p>
              <button onClick={() => onNavigate('quiz')} className="btn btn-primary" style={{ fontSize: '0.8rem' }}>
                Take a Quiz to Assess Mastery
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {masteryTopics.slice(0, 5).map((t) => {
                const pct = Math.round(t.mastery || 0);
                const color = pct >= 80 ? 'var(--success)' : pct >= 60 ? 'var(--secondary)' : pct >= 40 ? 'var(--warning)' : 'var(--danger)';
                return (
                  <div key={t.topic}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                      <span>{t.topic}</span>
                      <span style={{ color }}>{pct}%</span>
                    </div>
                    <div className="progress-track">
                      <div className="progress-fill" style={{ width: `${pct}%`, background: color }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Uploaded Materials Preview */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Course Materials</h3>
            <button
              onClick={() => onNavigate('upload')}
              style={{
                background: 'none', border: 'none', color: 'var(--primary)',
                fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem'
              }}
            >
              Manage all <ArrowRight size={14} />
            </button>
          </div>

          {documents.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'var(--text-muted)' }}>
              <p style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>No materials uploaded yet.</p>
              <button onClick={() => onNavigate('upload')} className="btn btn-primary" style={{ fontSize: '0.8rem' }}>
                Upload PDF / Slides
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {documents.slice(0, 4).map((doc) => (
                <div
                  key={doc.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.75rem',
                    background: '#f8fafc',
                    borderRadius: '8px',
                    border: '1px solid var(--border)'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{
                      padding: '0.35rem 0.6rem',
                      borderRadius: '6px',
                      background: doc.source_type === 'pdf' ? '#fee2e2' : doc.source_type === 'pptx' ? '#ffedd5' : '#e0e7ff',
                      color: doc.source_type === 'pdf' ? '#dc2626' : doc.source_type === 'pptx' ? '#ea580c' : '#4338ca',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      textTransform: 'uppercase'
                    }}>
                      {doc.source_type}
                    </div>
                    <div>
                      <div style={{ fontSize: '0.875rem', fontWeight: 600, maxWidth: '220px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {doc.filename}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {doc.total_sections} sections / pages indexed
                      </div>
                    </div>
                  </div>

                  <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
                    <CheckCircle2 size={12} /> Indexed
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
