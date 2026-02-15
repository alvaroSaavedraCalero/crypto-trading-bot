import React from 'react';

function MetricsPanel({ metrics = {} }) {
  const sections = [
    {
      title: 'Rendimiento',
      items: [
        { label: 'Retorno Total', value: `${(metrics.total_return_pct || 0).toFixed(2)}%`, positive: (metrics.total_return_pct || 0) >= 0 },
        { label: 'Ganancia Neta', value: `$${(metrics.net_profit || 0).toFixed(2)}` },
        { label: 'Profit Factor', value: (metrics.profit_factor || 0).toFixed(2) },
        { label: 'Expectativa', value: `$${(metrics.expectancy || 0).toFixed(2)}` },
      ],
    },
    {
      title: 'Riesgo',
      items: [
        { label: 'Max Drawdown', value: `${(metrics.max_drawdown_pct || 0).toFixed(2)}%`, negative: true },
        { label: 'Sharpe Ratio', value: (metrics.sharpe_ratio || 0).toFixed(2) },
        { label: 'Sortino Ratio', value: (metrics.sortino_ratio || 0).toFixed(2) },
        { label: 'Calmar Ratio', value: (metrics.calmar_ratio || 0).toFixed(2) },
      ],
    },
    {
      title: 'Trades',
      items: [
        { label: 'Total Trades', value: metrics.num_trades || 0 },
        { label: 'Win Rate', value: `${(metrics.winrate_pct || 0).toFixed(1)}%` },
        { label: 'Ganadores', value: metrics.winning_trades || 0 },
        { label: 'Perdedores', value: metrics.losing_trades || 0 },
      ],
    },
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
      gap: '1rem',
    }}>
      {sections.map((section) => (
        <div key={section.title} style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          padding: '1.25rem',
        }}>
          <h4 style={{
            fontSize: '0.8rem',
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '1rem',
            paddingBottom: '0.5rem',
            borderBottom: '1px solid var(--border)',
          }}>
            {section.title}
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {section.items.map((item) => (
              <div key={item.label} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {item.label}
                </span>
                <span style={{
                  fontSize: '0.95rem',
                  fontWeight: 600,
                  color: item.positive === true ? 'var(--profit)'
                       : item.positive === false ? 'var(--loss)'
                       : item.negative ? 'var(--loss)'
                       : 'var(--text-primary)',
                }}>
                  {item.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default MetricsPanel;
