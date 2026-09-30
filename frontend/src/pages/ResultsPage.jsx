import React from 'react';
import {
  Award,
  CheckCircle2,
  XCircle,
  FileText,
  TrendingUp,
  RotateCcw,
  Sparkles,
  BookOpen,
  AlertCircle
} from 'lucide-react';

export default function ResultsPage({ resultsData, onRetake, onNavigate }) {
  if (!resultsData || !resultsData.results) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <p>No recent quiz results found.</p>
        <button onClick={() => onNavigate('quiz')} className="btn btn-primary" style={{ marginTop: '1rem' }}>
          Take a Quiz
        </button>
      </div>
    );
  }

  const { quiz, results } = resultsData;
  const { score, total, percentage, questions = [], feedback, updated_mastery } = results;

  const isPassing = percentage >= 60;
  const isHighMastery = percentage >= 80;

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Score Banner */}
      <div style={{
        background: isHighMastery
          ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
          : isPassing
          ? 'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)'
          : 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
        borderRadius: '16px',
        padding: '2.5rem 2rem',
        color: '#fff',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.15)'
      }}>
        <div>
          <span style={{
            fontSize: '0.8rem',
            padding: '3px 10px',
            background: 'rgba(255,255,255,0.2)',
            borderRadius: '999px',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            Quiz Completed • {quiz?.topic || results.topic}
          </span>
          <h2 style={{ fontSize: '2rem', fontWeight: 800, marginTop: '0.5rem', marginBottom: '0.25rem' }}>
            {percentage}% Score
          </h2>
          <p style={{ color: 'rgba(255,255,255,0.9)', fontSize: '0.95rem' }}>
            You answered <strong>{score}</strong> out of <strong>{total}</strong> questions correctly.
          </p>
        </div>

        {/* Updated Mastery Pill */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.15)',
          backdropFilter: 'blur(8px)',
          borderRadius: '12px',
          padding: '1.25rem',
          textAlign: 'center',
          minWidth: '150px',
          border: '1px solid rgba(255,255,255,0.3)'
        }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Topic Mastery
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, margin: '0.25rem 0' }}>
            {updated_mastery !== undefined ? `${updated_mastery}%` : `${percentage}%`}
          </div>
          <div style={{ fontSize: '0.7rem', color: 'rgba(255,255,255,0.85)' }}>
            Adaptive Weight: 70/30
          </div>
        </div>
      </div>

      {/* AI Diagnostic Feedback */}
      {feedback && (
        <div className="card" style={{ borderLeft: '4px solid var(--primary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <Sparkles size={20} color="var(--primary)" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800 }}>AI Personalized Tutor Feedback</h3>
          </div>

          <p style={{ fontSize: '0.925rem', lineHeight: '1.5', color: 'var(--text-main)', marginBottom: '1rem' }}>
            {feedback.summary}
          </p>

          {/* Weak Topics */}
          {feedback.weak_topics && feedback.weak_topics.length > 0 && (
            <div style={{ marginBottom: '1rem' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Areas Needing Review:
              </span>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.35rem' }}>
                {feedback.weak_topics.map((wt, i) => (
                  <span key={i} className="badge badge-warning">
                    <AlertCircle size={12} /> {wt}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Study Recommendations */}
          {feedback.study_recommendations && feedback.study_recommendations.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Grounded Study Plan:
              </span>
              {feedback.study_recommendations.map((rec, i) => (
                <div
                  key={i}
                  style={{
                    padding: '0.65rem 0.85rem',
                    borderRadius: '8px',
                    background: '#f8fafc',
                    border: '1px solid var(--border)',
                    fontSize: '0.85rem',
                    display: 'flex',
                    alignItems: 'baseline',
                    gap: '0.5rem'
                  }}
                >
                  <span className="citation-pill">{rec.source_citation || '[Material]'}</span>
                  <span>{rec.advice}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Question by Question Review */}
      <div className="card">
        <h3 style={{ fontSize: '1.15rem', fontWeight: 800, marginBottom: '1.25rem' }}>
          Question Breakdown & Answer Keys
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {questions.map((q, idx) => {
            const isCorrect = q.correct;
            const originalQuestionObj = quiz?.questions?.find((orig) => orig.id === q.question_id) || quiz?.questions?.[idx];

            return (
              <div
                key={q.question_id || idx}
                style={{
                  padding: '1.25rem',
                  borderRadius: '10px',
                  background: isCorrect ? '#f0fdf4' : '#fef2f2',
                  border: `1.5px solid ${isCorrect ? '#bbf7d0' : '#fecaca'}`,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {isCorrect ? (
                      <CheckCircle2 size={20} color="var(--success)" />
                    ) : (
                      <XCircle size={20} color="var(--danger)" />
                    )}
                    <span style={{ fontWeight: 800, fontSize: '0.95rem' }}>
                      Question {idx + 1}
                    </span>
                  </div>

                  <span className={`badge ${isCorrect ? 'badge-success' : 'badge-danger'}`}>
                    {isCorrect ? 'Correct' : 'Incorrect'}
                  </span>
                </div>

                <p style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--text-main)', marginBottom: '0.75rem' }}>
                  {originalQuestionObj?.question || `Question ${idx + 1}`}
                </p>

                {/* Options display */}
                {originalQuestionObj?.options && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '0.75rem' }}>
                    {originalQuestionObj.options.map((opt, optIdx) => {
                      const isUserSelected = q.selected_answer === optIdx;
                      const isActualCorrect = q.correct_answer === optIdx;

                      let optBg = '#fff';
                      let optBorder = 'var(--border)';
                      let optColor = 'var(--text-main)';

                      if (isActualCorrect) {
                        optBg = '#dcfce7';
                        optBorder = '#86efac';
                        optColor = '#14532d';
                      } else if (isUserSelected && !isCorrect) {
                        optBg = '#fee2e2';
                        optBorder = '#fca5a5';
                        optColor = '#7f1d1d';
                      }

                      return (
                        <div
                          key={optIdx}
                          style={{
                            padding: '0.5rem 0.75rem',
                            borderRadius: '6px',
                            background: optBg,
                            border: `1px solid ${optBorder}`,
                            color: optColor,
                            fontSize: '0.875rem',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between'
                          }}
                        >
                          <span><strong>{String.fromCharCode(65 + optIdx)}.</strong> {opt}</span>
                          {isActualCorrect && <span style={{ fontSize: '0.75rem', fontWeight: 700 }}>✓ Correct Key</span>}
                          {isUserSelected && !isCorrect && <span style={{ fontSize: '0.75rem', fontWeight: 700 }}>✗ Your Choice</span>}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Explanation and Citation */}
                <div style={{
                  padding: '0.75rem',
                  borderRadius: '6px',
                  background: '#fff',
                  border: '1px solid rgba(0,0,0,0.06)',
                  fontSize: '0.85rem',
                  color: 'var(--text-main)'
                }}>
                  <div style={{ fontWeight: 700, marginBottom: '0.25rem', color: 'var(--text-muted)' }}>
                    Explanation:
                  </div>
                  <p>{q.explanation}</p>

                  {q.source && (
                    <div style={{ marginTop: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      <FileText size={12} />
                      <span>{q.source.filename || 'Document'}</span>
                      {q.source.page !== undefined && <span className="citation-pill">Page {q.source.page}</span>}
                      {q.source.slide !== undefined && <span className="citation-pill">Slide {q.source.slide}</span>}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', marginTop: '1rem' }}>
        <button onClick={onRetake} className="btn btn-secondary">
          <RotateCcw size={16} /> Retake / New Quiz
        </button>
        <button onClick={() => onNavigate('mastery')} className="btn btn-primary">
          <TrendingUp size={16} /> View Mastery Progress
        </button>
      </div>
    </div>
  );
}
