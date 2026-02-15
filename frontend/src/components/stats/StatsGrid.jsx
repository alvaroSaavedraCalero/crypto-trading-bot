import React from 'react';

function StatsGrid({ stats = [] }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
      gap: '1rem',
    }}>
      {stats.map((stat, i) => (
        <div key={i} style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          padding: '1.25rem',
          borderLeft: `3px solid ${stat.color || 'var(--accent)'}`,
        }}>
          <p style={{
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '0.5rem',
          }}>
            {stat.label}
          </p>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
            <span style={{
              fontSize: '1.5rem',
              fontWeight: 700,
              color: stat.valueColor || 'var(--text-primary)',
            }}>
              {stat.value}
            </span>
            {stat.trend != null && (
              <span style={{
                fontSize: '0.8rem',
                fontWeight: 600,
                color: stat.trend >= 0 ? 'var(--profit)' : 'var(--loss)',
              }}>
                {stat.trend >= 0 ? '+' : ''}{stat.trend}%
              </span>
            )}
          </div>
          {stat.subtitle && (
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              {stat.subtitle}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

export default StatsGrid;
