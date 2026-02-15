import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { paperTradingAPI, strategiesAPI } from '../services/api';
import './PaperTrading.css';

function PaperTrading() {
  const [sessions, setSessions] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [creating, setCreating] = useState(false);
  const [expandedSession, setExpandedSession] = useState(null);
  const [sessionTrades, setSessionTrades] = useState({});
  const [runningSession, setRunningSession] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    strategy_id: '',
    pair: 'BTC-USD',
    timeframe: '15m',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sessRes, stRes] = await Promise.all([
        paperTradingAPI.listSessions(),
        strategiesAPI.list(),
      ]);
      setSessions(sessRes.data);
      setStrategies(stRes.data);
      if (stRes.data.length > 0 && !formData.strategy_id) {
        setFormData((prev) => ({ ...prev, strategy_id: stRes.data[0].id }));
      }
    } catch (err) {
      setError('Error al cargar datos: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async (e) => {
    e.preventDefault();
    try {
      setCreating(true);
      setError(null);
      await paperTradingAPI.createSession({
        name: formData.name,
        strategy_id: Number(formData.strategy_id),
        pair: formData.pair,
        timeframe: formData.timeframe,
      });
      setShowForm(false);
      setFormData({ name: '', strategy_id: strategies[0]?.id || '', pair: 'BTC-USD', timeframe: '15m' });
      toast.success('Sesion creada correctamente');
      await fetchData();
    } catch (err) {
      toast.error('Error al crear sesion: ' + (err.response?.data?.detail || err.message));
    } finally {
      setCreating(false);
    }
  };

  const handleCloseSession = async (sessionId) => {
    try {
      setError(null);
      await paperTradingAPI.closeSession(sessionId);
      toast.success('Sesion cerrada');
      await fetchData();
    } catch (err) {
      toast.error('Error al cerrar sesion: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleRunSession = async (sessionId) => {
    try {
      setRunningSession(sessionId);
      setError(null);
      await paperTradingAPI.runSession(sessionId);
      toast.success('Sesion ejecutada correctamente');
      await fetchData();
    } catch (err) {
      toast.error('Error al ejecutar: ' + (err.response?.data?.detail || err.message));
    } finally {
      setRunningSession(null);
    }
  };

  const handleToggleTrades = async (sessionId) => {
    if (expandedSession === sessionId) {
      setExpandedSession(null);
      return;
    }
    try {
      const res = await paperTradingAPI.getTrades(sessionId);
      setSessionTrades(prev => ({ ...prev, [sessionId]: res.data }));
      setExpandedSession(sessionId);
    } catch (err) {
      toast.error('Error al cargar trades: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) {
    return (
      <div className="paper-trading-page">
        <div className="page-header"><h1>Paper Trading</h1></div>
        <div style={{ display: 'grid', gap: '1rem' }}>
          {[1, 2].map(i => <div key={i} className="skeleton skeleton-card" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="paper-trading-page">
      <div className="page-header">
        <h1>Paper Trading</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancelar' : '+ Nueva Sesion'}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {showForm && (
        <div className="form-container">
          <form className="strategy-form" onSubmit={handleCreateSession}>
            <h3 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>Nueva Sesion de Paper Trading</h3>

            <div className="form-group">
              <label>Nombre *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Mi sesion BTC"
                required
              />
            </div>

            <div className="form-group">
              <label>Estrategia *</label>
              <select
                value={formData.strategy_id}
                onChange={(e) => setFormData({ ...formData, strategy_id: e.target.value })}
                required
              >
                {strategies.length === 0 && <option value="">Sin estrategias</option>}
                {strategies.map((s) => (
                  <option key={s.id} value={s.id}>{s.name} ({s.strategy_type})</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Par *</label>
              <input
                type="text"
                value={formData.pair}
                onChange={(e) => setFormData({ ...formData, pair: e.target.value })}
                placeholder="BTC-USD, ETH-USD..."
                required
              />
            </div>

            <div className="form-group">
              <label>Timeframe</label>
              <select
                value={formData.timeframe}
                onChange={(e) => setFormData({ ...formData, timeframe: e.target.value })}
              >
                <option value="5m">5m</option>
                <option value="15m">15m</option>
                <option value="30m">30m</option>
                <option value="1h">1h</option>
                <option value="4h">4h</option>
                <option value="1d">1d</option>
              </select>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={creating || strategies.length === 0}>
                {creating ? 'Creando...' : 'Crear Sesion'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="sessions-list">
        {sessions.length === 0 ? (
          <div className="empty-state">
            <p>No hay sesiones de paper trading</p>
            <p className="text-muted">Crea una nueva sesion para comenzar</p>
          </div>
        ) : (
          sessions.map((session) => (
            <div key={session.id} className="session-card">
              <div className="session-header">
                <div>
                  <h3>{session.name}</h3>
                  <p className="session-meta">{session.pair} / {session.timeframe}</p>
                </div>
                <span className={`status-badge ${session.is_active ? 'active' : 'inactive'}`}>
                  {session.is_active ? 'Activa' : 'Cerrada'}
                </span>
              </div>

              <div className="session-stats">
                <div className="stat">
                  <p className="stat-label">Capital</p>
                  <p className="stat-value">
                    ${(session.current_capital || session.initial_capital || 0).toLocaleString()}
                  </p>
                </div>
                <div className="stat">
                  <p className="stat-label">Trades</p>
                  <p className="stat-value">{session.total_trades || 0}</p>
                </div>
                <div className="stat">
                  <p className="stat-label">Retorno</p>
                  <p className={`stat-value ${(session.total_return_pct || 0) < 0 ? 'negative' : 'positive'}`}>
                    {(session.total_return_pct || 0) > 0 ? '+' : ''}
                    {(session.total_return_pct || 0).toFixed(2)}%
                  </p>
                </div>
                <div className="stat">
                  <p className="stat-label">Inicio</p>
                  <p className="stat-value" style={{ fontSize: '0.85rem' }}>
                    {session.created_at ? new Date(session.created_at).toLocaleDateString() : '-'}
                  </p>
                </div>
              </div>

              <div className="session-actions">
                {session.is_active && (
                  <>
                    <button
                      className="btn-primary"
                      style={{ fontSize: '0.85rem', padding: '0.4rem 0.75rem' }}
                      onClick={() => handleRunSession(session.id)}
                      disabled={runningSession === session.id}
                    >
                      {runningSession === session.id ? 'Ejecutando...' : 'Ejecutar'}
                    </button>
                    <button className="btn-secondary" onClick={() => handleCloseSession(session.id)}>
                      Cerrar Sesion
                    </button>
                  </>
                )}
                <button className="btn-secondary" onClick={() => handleToggleTrades(session.id)}>
                  {expandedSession === session.id ? 'Ocultar Trades' : 'Ver Trades'}
                </button>
              </div>

              {expandedSession === session.id && (
                <div className="session-trades">
                  <h4>Trades de la sesion</h4>
                  {(sessionTrades[session.id] || []).length === 0 ? (
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Sin trades aun</p>
                  ) : (
                    <div className="table-wrapper">
                      <table className="trades-table">
                        <thead>
                          <tr>
                            <th>Lado</th>
                            <th>Entrada</th>
                            <th>Salida</th>
                            <th>PnL</th>
                            <th>PnL %</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sessionTrades[session.id].map((t, idx) => (
                            <tr key={idx}>
                              <td><strong>{(t.side || 'long').toUpperCase()}</strong></td>
                              <td>${Number(t.entry_price || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                              <td>{t.exit_price ? `$${Number(t.exit_price).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '-'}</td>
                              <td className={(t.pnl || 0) < 0 ? 'negative' : 'positive'}>
                                ${Number(t.pnl || 0).toFixed(2)}
                              </td>
                              <td className={(t.pnl_pct || 0) < 0 ? 'negative' : 'positive'}>
                                {(t.pnl_pct || 0) > 0 ? '+' : ''}{Number(t.pnl_pct || 0).toFixed(2)}%
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default PaperTrading;
