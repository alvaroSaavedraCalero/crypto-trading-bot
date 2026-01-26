import React, { useState, useEffect } from 'react';
import { healthAPI } from '../services/api';
import './Dashboard.css';

function Dashboard() {
  const [stats, setStats] = useState({
    total_strategies: 0,
    active_backtests: 0,
    paper_trading_sessions: 0,
    total_trades: 0,
    portfolio_value: 10000,
    daily_return: 0,
  });
  const [summary, setSummary] = useState(null);
  const [apiStatus, setApiStatus] = useState('checking');
  const [loading, setLoading] = useState(true);

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

      // Fetch stats
      try {
        const statsRes = await fetch('http://localhost:8000/api/v1/dashboard/stats');
        if (statsRes.ok) {
          const statsData = await statsRes.json();
          setStats(statsData);
        }
      } catch (e) {
        console.log('No stats available yet');
      }

      // Fetch summary
      try {
        const summaryRes = await fetch('http://localhost:8000/api/v1/dashboard/summary');
        if (summaryRes.ok) {
          const summaryData = await summaryRes.json();
          setSummary(summaryData);
        }
      } catch (e) {
        console.log('No summary available yet');
      }
    } catch (e) {
      console.error('Error fetching dashboard data:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <div className={`api-status ${apiStatus}`}>
          <span className="status-dot"></span>
          API: {apiStatus === 'healthy' ? '✅ Conectado' : '❌ Desconectado'}
        </div>
      </div>

      {loading ? (
        <p>Cargando datos...</p>
      ) : (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <h3>Estrategias</h3>
              <p className="stat-value">{stats.total_strategies}</p>
              <p className="stat-label">Estrategias activas</p>
            </div>

            <div className="stat-card">
              <h3>Paper Trading</h3>
              <p className="stat-value">{stats.paper_trading_sessions}</p>
              <p className="stat-label">Sesiones activas</p>
            </div>

            <div className="stat-card">
              <h3>Trades</h3>
              <p className="stat-value">{stats.total_trades}</p>
              <p className="stat-label">Total de operaciones</p>
            </div>

            <div className="stat-card">
              <h3>Portfolio</h3>
              <p className="stat-value">${stats.portfolio_value.toLocaleString()}</p>
              <p className={`stat-label ${stats.daily_return < 0 ? 'negative' : 'positive'}`}>
                {stats.daily_return > 0 ? '+' : ''}{stats.daily_return.toFixed(2)}% hoy
              </p>
            </div>
          </div>

          {summary && (
            <div className="dashboard-summary">
              <div className="summary-section">
                <h2>Últimos Backtests</h2>
                <div className="recent-backtests">
                  {summary.recent_backtests?.length > 0 ? (
                    summary.recent_backtests.map((bt) => (
                      <div key={bt.id} className="summary-item">
                        <p><strong>{bt.strategy}</strong> - {bt.pair}</p>
                        <p className={bt.return < 0 ? 'negative' : 'positive'}>
                          Retorno: {bt.return.toFixed(2)}% | Trades: {bt.trades}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="text-muted">Sin backtests aún</p>
                  )}
                </div>
              </div>

              <div className="summary-section">
                <h2>Mejores Estrategias</h2>
                <div className="best-strategies">
                  {summary.best_strategies?.length > 0 ? (
                    summary.best_strategies.map((st) => (
                      <div key={st.name} className="summary-item">
                        <p><strong>{st.name}</strong></p>
                        <p>Winrate promedio: {st.avg_winrate?.toFixed(1) || 0}% | Backtests: {st.backtests}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-muted">Sin datos de estrategias</p>
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="dashboard-section">
            <h2>Resumen General</h2>
            <div className="info-box">
              <p>
                Bienvenido al dashboard de Crypto Trading Bot integrado con API REST.
              </p>
              <ul>
                <li>📊 Las estrategias, backtests y paper trading ahora están sincronizados con la base de datos</li>
                <li>📈 Todos los resultados se guardan automáticamente en la API</li>
                <li>🎮 Monitorea tus sesiones de paper trading en tiempo real</li>
                <li>🔗 La API está disponible en: http://localhost:8000/docs</li>
              </ul>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default Dashboard;
