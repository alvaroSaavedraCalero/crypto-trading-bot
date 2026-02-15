import React, { useState, useEffect } from 'react';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { dashboardAPI, paperTradingAPI } from '../services/api';
import StatsGrid from '../components/stats/StatsGrid';

ChartJS.register(ArcElement, Tooltip, Legend);

function Portfolio() {
  const [stats, setStats] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const results = await Promise.allSettled([
        dashboardAPI.getStats(),
        paperTradingAPI.listSessions(),
      ]);
      if (results[0].status === 'fulfilled') setStats(results[0].value.data);
      if (results[1].status === 'fulfilled') setSessions(results[1].value.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const activeSessions = sessions.filter(s => s.is_active);
  const totalPnl = sessions.reduce((sum, s) => sum + (s.total_return_pct || 0), 0);

  const allocationData = {
    labels: activeSessions.length > 0 ? activeSessions.map(s => `${s.name} (${s.pair})`) : ['Sin posiciones'],
    datasets: [{
      data: activeSessions.length > 0
        ? activeSessions.map(s => s.current_capital || s.initial_capital || 0)
        : [1],
      backgroundColor: activeSessions.length > 0
        ? ['#2196f3', '#00c853', '#ff9800', '#e040fb', '#ff1744', '#00bcd4']
        : ['#2d3748'],
      borderColor: '#1e2d3d',
      borderWidth: 2,
    }],
  };

  const statsCards = [
    {
      label: 'Valor Total',
      value: `$${(stats?.portfolio_value ?? 10000).toLocaleString()}`,
      color: 'var(--accent)',
    },
    {
      label: 'Sesiones Activas',
      value: activeSessions.length,
      color: 'var(--profit)',
    },
    {
      label: 'PnL Total',
      value: `${totalPnl >= 0 ? '+' : ''}${totalPnl.toFixed(2)}%`,
      valueColor: totalPnl >= 0 ? 'var(--profit)' : 'var(--loss)',
      color: totalPnl >= 0 ? 'var(--profit)' : 'var(--loss)',
    },
    {
      label: 'Total Trades',
      value: stats?.total_trades ?? 0,
      color: 'var(--warning)',
    },
  ];

  if (loading) {
    return (
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <h1 style={{ color: 'var(--text-primary)', fontSize: '1.6rem', marginBottom: '1.5rem' }}>Portafolio</h1>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
          {[1, 2, 3, 4].map(i => <div key={i} className="skeleton skeleton-card" />)}
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <h1 style={{ color: 'var(--text-primary)', fontSize: '1.6rem', marginBottom: '1.5rem' }}>Portafolio</h1>

      <StatsGrid stats={statsCards} />

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))',
        gap: '1.25rem',
        marginTop: '1.5rem',
      }}>
        {/* Allocation chart */}
        <div style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          padding: '1.25rem',
          border: '1px solid var(--border)',
        }}>
          <h3 style={{
            fontSize: '0.8rem',
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '1rem',
          }}>
            Asignacion de Capital
          </h3>
          <div style={{ maxWidth: 300, margin: '0 auto' }}>
            <Doughnut
              data={allocationData}
              options={{
                responsive: true,
                plugins: {
                  legend: {
                    position: 'bottom',
                    labels: { color: '#8899a6', padding: 12, font: { size: 11 } },
                  },
                },
              }}
            />
          </div>
        </div>

        {/* Sessions list */}
        <div style={{
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          padding: '1.25rem',
          border: '1px solid var(--border)',
        }}>
          <h3 style={{
            fontSize: '0.8rem',
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '1rem',
          }}>
            Posiciones Activas
          </h3>
          {activeSessions.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>
              Sin posiciones activas
            </p>
          ) : (
            activeSessions.map(s => (
              <div key={s.id} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.6rem 0',
                borderBottom: '1px solid var(--border-light)',
              }}>
                <div>
                  <div style={{ color: 'var(--text-primary)', fontWeight: 500, fontSize: '0.9rem' }}>{s.name}</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{s.pair} / {s.timeframe}</div>
                </div>
                <span style={{
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  color: (s.total_return_pct || 0) >= 0 ? 'var(--profit)' : 'var(--loss)',
                }}>
                  {(s.total_return_pct || 0) >= 0 ? '+' : ''}{(s.total_return_pct || 0).toFixed(2)}%
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default Portfolio;
