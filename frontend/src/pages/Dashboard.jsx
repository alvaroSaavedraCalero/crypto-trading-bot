import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { healthAPI, dashboardAPI, strategiesAPI, backtestsAPI, paperTradingAPI } from '../services/api';
import StatsGrid from '../components/stats/StatsGrid';
import './Dashboard.css';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [summary, setSummary] = useState(null);
  const [apiStatus, setApiStatus] = useState('checking');
  const [loading, setLoading] = useState(true);
  const [recentStrategies, setRecentStrategies] = useState([]);
  const [recentSessions, setRecentSessions] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);

      // Check API health
      try {
        await healthAPI.check();
        setApiStatus('healthy');
      } catch {
        setApiStatus('down');
      }

      // Fetch all data in parallel
      const results = await Promise.allSettled([
        dashboardAPI.getStats(),
        dashboardAPI.getSummary(),
        strategiesAPI.list(0, 5),
        paperTradingAPI.listSessions(0, 5),
      ]);

      if (results[0].status === 'fulfilled') setStats(results[0].value.data);
      if (results[1].status === 'fulfilled') setSummary(results[1].value.data);
      if (results[2].status === 'fulfilled') setRecentStrategies(results[2].value.data);
      if (results[3].status === 'fulfilled') setRecentSessions(results[3].value.data);
    } catch (e) {
      console.error('Error fetching dashboard data:', e);
    } finally {
      setLoading(false);
    }
  };

  const statsCards = [
    {
      label: 'Estrategias',
      value: stats?.total_strategies ?? 0,
      subtitle: 'Estrategias activas',
      color: 'var(--accent)',
    },
    {
      label: 'Paper Trading',
      value: stats?.paper_trading_sessions ?? 0,
      subtitle: 'Sesiones activas',
      color: 'var(--warning)',
    },
    {
      label: 'Trades',
      value: stats?.total_trades ?? 0,
      subtitle: 'Total de operaciones',
      color: 'var(--profit)',
    },
    {
      label: 'Portafolio',
      value: `$${(stats?.portfolio_value ?? 10000).toLocaleString()}`,
      trend: stats?.daily_return ?? null,
      subtitle: 'Valor actual',
      color: (stats?.daily_return ?? 0) >= 0 ? 'var(--profit)' : 'var(--loss)',
      valueColor: 'var(--text-primary)',
    },
  ];

  if (loading) {
    return (
      <div className="dashboard">
        <div className="dashboard-header">
          <h1>Dashboard</h1>
          <div className={`api-status checking`}>
            <span className="status-dot"></span>
            Verificando...
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="skeleton skeleton-card" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <div className={`api-status ${apiStatus}`}>
          <span className="status-dot"></span>
          API: {apiStatus === 'healthy' ? 'Conectado' : apiStatus === 'down' ? 'Desconectado' : 'Verificando...'}
        </div>
      </div>

      <StatsGrid stats={statsCards} />

      <div className="dashboard-widgets">
        {/* Recent Backtests */}
        <div className="widget">
          <h3 className="widget-title">Ultimos Backtests</h3>
          {summary?.recent_backtests?.length > 0 ? (
            summary.recent_backtests.map((bt) => (
              <div key={bt.id} className="widget-item">
                <div>
                  <div className="widget-item-name">{bt.strategy} - {bt.pair}</div>
                  <div className="widget-item-meta">Trades: {bt.trades}</div>
                </div>
                <span className={`widget-item-value ${(bt.return || 0) >= 0 ? 'positive' : 'negative'}`}>
                  {(bt.return || 0) > 0 ? '+' : ''}{(bt.return || 0).toFixed(2)}%
                </span>
              </div>
            ))
          ) : (
            <div className="widget-empty">Sin backtests aun</div>
          )}
        </div>

        {/* Best Strategies */}
        <div className="widget">
          <h3 className="widget-title">Mejores Estrategias</h3>
          {summary?.best_strategies?.length > 0 ? (
            summary.best_strategies.map((st) => (
              <div key={st.name} className="widget-item">
                <div>
                  <div className="widget-item-name">{st.name}</div>
                  <div className="widget-item-meta">Backtests: {st.backtests}</div>
                </div>
                <span className="widget-item-value" style={{ color: 'var(--accent)' }}>
                  WR: {(st.avg_winrate || 0).toFixed(1)}%
                </span>
              </div>
            ))
          ) : (
            <div className="widget-empty">Sin datos de estrategias</div>
          )}
        </div>

        {/* Strategies List */}
        <div className="widget">
          <h3 className="widget-title">Estrategias Recientes</h3>
          {recentStrategies.length > 0 ? (
            recentStrategies.map((s) => (
              <div key={s.id} className="widget-item">
                <div>
                  <div className="widget-item-name">{s.name}</div>
                  <div className="widget-item-meta">{s.strategy_type}</div>
                </div>
                <span className={`widget-item-value`} style={{
                  color: s.is_active ? 'var(--profit)' : 'var(--text-muted)',
                  fontSize: '0.8rem',
                }}>
                  {s.is_active ? 'Activa' : 'Inactiva'}
                </span>
              </div>
            ))
          ) : (
            <div className="widget-empty">Sin estrategias creadas</div>
          )}
        </div>

        {/* Active Sessions */}
        <div className="widget">
          <h3 className="widget-title">Sesiones Activas</h3>
          {recentSessions.length > 0 ? (
            recentSessions.map((sess) => (
              <div key={sess.id} className="widget-item">
                <div>
                  <div className="widget-item-name">{sess.name}</div>
                  <div className="widget-item-meta">{sess.pair} / {sess.timeframe}</div>
                </div>
                <span className={`widget-item-value ${(sess.total_return_pct || 0) >= 0 ? 'positive' : 'negative'}`}>
                  {(sess.total_return_pct || 0) > 0 ? '+' : ''}{(sess.total_return_pct || 0).toFixed(2)}%
                </span>
              </div>
            ))
          ) : (
            <div className="widget-empty">Sin sesiones activas</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
