import React from 'react';
import {
  TrendingUp,
  Award,
  Sparkles,
  BookOpen,
  Calendar,
  CheckCircle,
  AlertCircle,
  HelpCircle
} from 'lucide-react';

export default function MasteryPage({ masteryTopics = [], onNavigate }) {
  const getMasteryColor = (pct) => {
    if (pct >= 85) return { color: '#059669', bg: '#ecfdf5', label: 'Mastered' };
    if (pct >= 70) return { color: '#4f46e5', bg: '#eef2ff', label: 'Proficient' };
    if (pct >= 50) return { color: '#d97706', bg: '#fffbeb', label: 'Developing' };
    return { color: '#dc2626', bg: '#fef2f2', label: 'Needs Focus' };
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Mastery Header Card */}
      <div className="card" style={{ background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 100%)', color: '#fff' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
          <TrendingUp size={24} color="#a5b4fc" />
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Adaptive Mastery Tracking</h2>
        </div>
        <p style={{ color: '#c7d2fe', fontSize: '0.925rem', maxWidth: '700px', lineHeight: '1.5' }}>
          Our adaptive system updates your mastery level after each quiz attempt using an exponential moving average:
        </p>

        {/* Formula Box */}
        <div style={{
          marginTop: '1.25rem',
          padding: '0.85rem 1.25rem',
          background: 'rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          display: 'inline-flex',
          flexDirection: 'column',
          gap: '0.25rem'
        }}>
          <span style={{ fontSize: '0.75rem', color: '#a5b4fc', fontWeight: 700, textTransform: 'uppercase' }}>
            Adaptive Learning Formula
          </span>
          <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.95rem', color: '#fff', fontWeight: 600 }}>
            new_mastery = (old_mastery × 0.70) + (quiz_score × 0.30)
          </code>
          <span style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>
            First attempt: mastery = quiz_score (clamped strictly between 0% and 100%)
          </span>
        </div>
      </div>

      {/* Topic Mastery Grid */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 800 }}>Topic Mastery Breakdown</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Current calculated student mastery across all evaluated topics.
            </p>
          </div>
          <button onClick={() => onNavigate('quiz')} className="btn btn-primary" style={{ fontSize: '0.85rem' }}>
            Take New Quiz
          </button>
        </div>

        {masteryTopics.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
            <BookOpen size={40} style={{ opacity: 0.3, marginBottom: '0.75rem' }} />
            <p style={{ fontSize: '1rem', fontWeight: 600 }}>No mastery records yet.</p>
            <p style={{ fontSize: '0.85rem', marginTop: '0.25rem' }}>
              Complete a topic quiz to start tracking your personalized learning curve.
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
            {masteryTopics.map((topicItem) => {
              const pct = Math.round(topicItem.mastery || 0);
              const tier = getMasteryColor(pct);

              return (
                <div
                  key={topicItem.topic}
                  style={{
                    padding: '1.25rem',
                    borderRadius: '10px',
                    border: '1px solid var(--border)',
                    background: '#f8fafc',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.85rem'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <h4 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)' }}>
                        {topicItem.topic}
                      </h4>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                        <Calendar size={12} />
                        <span>Last quiz: {topicItem.last_attempted_at?.split('.')[0] || 'Recently'}</span>
                      </div>
                    </div>

                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: '999px',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        background: tier.bg,
                        color: tier.color,
                        border: `1px solid ${tier.color}33`
                      }}
                    >
                      {tier.label}
                    </span>
                  </div>

                  {/* Percentage Display & Progress Bar */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.35rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Mastery Level</span>
                      <span style={{ color: tier.color, fontSize: '1.2rem' }}>{pct}%</span>
                    </div>
                    <div className="progress-track" style={{ height: '10px' }}>
                      <div
                        className="progress-fill"
                        style={{ width: `${pct}%`, background: tier.color }}
                      />
                    </div>
                  </div>

                  {/* Quiz Count & Previous Score */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    paddingTop: '0.65rem',
                    borderTop: '1px solid #e2e8f0',
                    fontSize: '0.8rem',
                    color: 'var(--text-muted)'
                  }}>
                    <span>Quizzes: <strong>{topicItem.quiz_count || 1}</strong></span>
                    {topicItem.previous_mastery !== null && (
                      <span>Prev: <strong>{Math.round(topicItem.previous_mastery)}%</strong></span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
