import React, { useState } from 'react';
import {
  BookOpenCheck,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle,
  HelpCircle,
  Loader2,
  FileText
} from 'lucide-react';
import { generateQuiz, gradeQuiz } from '../services/api';

export default function QuizPage({ documents = [], onQuizFinished }) {
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [numberOfQuestions, setNumberOfQuestions] = useState(5);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isGrading, setIsGrading] = useState(false);
  const [error, setError] = useState(null);

  // Active quiz state
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});

  const handleStartQuiz = async (e) => {
    e?.preventDefault();
    if (!topic.trim()) {
      setError('Please provide a topic for the quiz.');
      return;
    }

    setError(null);
    setIsGenerating(true);

    try {
      const data = await generateQuiz(topic.trim(), difficulty, numberOfQuestions);
      setActiveQuiz(data);
      setCurrentQuestionIndex(0);
      setUserAnswers({});
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to generate quiz.';
      setError(`Generation error: ${msg}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSelectOption = (questionIndex, optionIndex) => {
    setUserAnswers((prev) => ({
      ...prev,
      [questionIndex]: optionIndex,
    }));
  };

  const handleSubmitQuiz = async () => {
    if (!activeQuiz) return;
    
    // Map answers array in question order
    const answersList = activeQuiz.questions.map((_, idx) => (
      userAnswers[idx] !== undefined ? userAnswers[idx] : -1
    ));

    setIsGrading(true);
    setError(null);

    try {
      const result = await gradeQuiz(activeQuiz.quiz_id, answersList);
      if (onQuizFinished) {
        onQuizFinished({
          quiz: activeQuiz,
          results: result,
        });
      }
    } catch (err) {
      setError(`Grading error: ${err.response?.data?.detail || err.message}`);
      setIsGrading(false);
    }
  };

  // 1. Generation Form Mode
  if (!activeQuiz) {
    return (
      <div style={{ maxWidth: '640px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
            <div style={{
              width: '42px', height: '42px', borderRadius: '10px',
              background: '#eef2ff', color: 'var(--primary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <BookOpenCheck size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800 }}>Create Topic Quiz</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Test your understanding with source-grounded multiple choice questions.
              </p>
            </div>
          </div>

          <form onSubmit={handleStartQuiz} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.4rem' }}>
                Quiz Topic
              </label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. TCP, UDP, Routing Protocols, DNS..."
                style={{
                  width: '100%',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  border: '1px solid var(--border)',
                  fontSize: '0.925rem',
                  outline: 'none',
                }}
              />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem', display: 'block' }}>
                Gemini will extract relevant chunks from your uploaded documents to build questions.
              </span>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                Difficulty Level
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
                {['easy', 'medium', 'hard'].map((level) => (
                  <button
                    type="button"
                    key={level}
                    onClick={() => setDifficulty(level)}
                    style={{
                      padding: '0.65rem 0.5rem',
                      borderRadius: '8px',
                      border: `1.5px solid ${difficulty === level ? 'var(--primary)' : 'var(--border)'}`,
                      background: difficulty === level ? 'var(--primary-light)' : '#fff',
                      color: difficulty === level ? 'var(--primary)' : 'var(--text-main)',
                      fontWeight: 700,
                      textTransform: 'capitalize',
                      cursor: 'pointer',
                      transition: 'all 0.15s'
                    }}
                  >
                    {level}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.4rem' }}>
                Number of Questions
              </label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {[3, 5, 8].map((num) => (
                  <button
                    type="button"
                    key={num}
                    onClick={() => setNumberOfQuestions(num)}
                    style={{
                      flex: 1,
                      padding: '0.5rem',
                      borderRadius: '6px',
                      border: `1.5px solid ${numberOfQuestions === num ? 'var(--primary)' : 'var(--border)'}`,
                      background: numberOfQuestions === num ? 'var(--primary-light)' : '#fff',
                      color: numberOfQuestions === num ? 'var(--primary)' : 'var(--text-main)',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    {num} Questions
                  </button>
                ))}
              </div>
            </div>

            {error && (
              <div style={{
                padding: '0.75rem', borderRadius: '8px',
                background: 'var(--danger-light)', border: '1px solid #fecaca',
                color: 'var(--danger)', fontSize: '0.85rem'
              }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isGenerating || !topic.trim()}
              className="btn btn-primary"
              style={{ marginTop: '0.5rem', padding: '0.8rem' }}
            >
              {isGenerating ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Generating Grounded Quiz with Gemini...
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  Generate Quiz
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // 2. Active Quiz Taking Mode
  const currentQuestion = activeQuiz.questions[currentQuestionIndex];
  const totalQ = activeQuiz.questions.length;
  const isAnswered = userAnswers[currentQuestionIndex] !== undefined;
  const isLast = currentQuestionIndex === totalQ - 1;
  const answeredCount = Object.keys(userAnswers).length;

  return (
    <div style={{ maxWidth: '720px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Quiz Top Status Bar */}
      <div className="card" style={{ padding: '1rem 1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <span className="badge badge-primary" style={{ textTransform: 'uppercase', marginBottom: '0.25rem' }}>
            {activeQuiz.topic} • {activeQuiz.difficulty}
          </span>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800 }}>
            Question {currentQuestionIndex + 1} of {totalQ}
          </h3>
        </div>

        {/* Stepper Pills */}
        <div style={{ display: 'flex', gap: '0.4rem' }}>
          {activeQuiz.questions.map((_, i) => {
            const hasAns = userAnswers[i] !== undefined;
            const isCurrent = currentQuestionIndex === i;
            return (
              <button
                key={i}
                onClick={() => setCurrentQuestionIndex(i)}
                style={{
                  width: '32px', height: '32px', borderRadius: '50%',
                  border: isCurrent ? '2px solid var(--primary)' : '1px solid var(--border)',
                  background: isCurrent ? 'var(--primary)' : hasAns ? '#ecfdf5' : '#fff',
                  color: isCurrent ? '#fff' : hasAns ? 'var(--success)' : 'var(--text-muted)',
                  fontWeight: 700, fontSize: '0.8rem', cursor: 'pointer'
                }}
              >
                {i + 1}
              </button>
            );
          })}
        </div>
      </div>

      {/* Question Card */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <p style={{ fontSize: '1.1rem', fontWeight: 700, lineHeight: '1.45', color: 'var(--text-main)' }}>
          {currentQuestion.question}
        </p>

        {/* Options */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {currentQuestion.options.map((opt, optIndex) => {
            const isSelected = userAnswers[currentQuestionIndex] === optIndex;
            const letter = String.fromCharCode(65 + optIndex);

            return (
              <div
                key={optIndex}
                onClick={() => handleSelectOption(currentQuestionIndex, optIndex)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.85rem',
                  padding: '1rem',
                  borderRadius: '10px',
                  border: `2px solid ${isSelected ? 'var(--primary)' : 'var(--border)'}`,
                  background: isSelected ? 'var(--primary-light)' : '#f8fafc',
                  cursor: 'pointer',
                  transition: 'all 0.15s'
                }}
              >
                <div style={{
                  width: '30px', height: '30px', borderRadius: '50%',
                  background: isSelected ? 'var(--primary)' : '#fff',
                  color: isSelected ? '#fff' : 'var(--text-muted)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 700, fontSize: '0.85rem', border: '1px solid #cbd5e1'
                }}>
                  {letter}
                </div>
                <div style={{ fontSize: '0.95rem', fontWeight: 500, color: 'var(--text-main)' }}>
                  {opt}
                </div>
              </div>
            );
          })}
        </div>

        {/* Source ground note */}
        {currentQuestion.source && (
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <FileText size={13} />
            <span>Grounded in: {currentQuestion.source.filename || 'Uploaded Document'}</span>
            {(currentQuestion.source.page !== undefined && currentQuestion.source.page !== null) && (
              <span className="citation-pill">Page {currentQuestion.source.page}</span>
            )}
            {(currentQuestion.source.slide !== undefined && currentQuestion.source.slide !== null) && (
              <span className="citation-pill">Slide {currentQuestion.source.slide}</span>
            )}
          </div>
        )}

        {error && (
          <div style={{
            padding: '0.75rem', borderRadius: '8px',
            background: 'var(--danger-light)', color: 'var(--danger)', fontSize: '0.85rem'
          }}>
            {error}
          </div>
        )}

        {/* Actions Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border)', paddingTop: '1.25rem' }}>
          <button
            onClick={() => setCurrentQuestionIndex((prev) => Math.max(0, prev - 1))}
            disabled={currentQuestionIndex === 0 || isGrading}
            className="btn btn-secondary"
          >
            <ArrowLeft size={16} /> Previous
          </button>

          {!isLast ? (
            <button
              onClick={() => setCurrentQuestionIndex((prev) => Math.min(totalQ - 1, prev + 1))}
              disabled={isGrading}
              className="btn btn-primary"
            >
              Next <ArrowRight size={16} />
            </button>
          ) : (
            <button
              onClick={handleSubmitQuiz}
              disabled={isGrading}
              className="btn"
              style={{ background: 'var(--success)', color: '#fff' }}
            >
              {isGrading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Grading Answers...
                </>
              ) : (
                <>
                  <CheckCircle size={16} />
                  Submit Quiz ({answeredCount}/{totalQ} Answered)
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
