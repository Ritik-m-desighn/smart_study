import React from 'react';
import { Activity, ShieldCheck, Cpu } from 'lucide-react';

export default function Header({ title, healthInfo }) {
  return (
    <header className="header">
      <div>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)' }}>
          {title}
        </h2>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {/* Model Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          padding: '0.35rem 0.75rem',
          background: '#f1f5f9',
          borderRadius: '999px',
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
          fontWeight: 500
        }}>
          <Cpu size={14} color="var(--primary)" />
          <span>{healthInfo?.models?.gemini_model || 'gemini-3.8-flash'}</span>
        </div>

        {/* Security Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          padding: '0.35rem 0.75rem',
          background: '#ecfdf5',
          borderRadius: '999px',
          fontSize: '0.8rem',
          color: '#059669',
          fontWeight: 600
        }}>
          <ShieldCheck size={15} color="#059669" />
          <span>Backend Secured</span>
        </div>
      </div>
    </header>
  );
}
