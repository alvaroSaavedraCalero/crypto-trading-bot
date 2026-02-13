import React, { useState, useEffect } from 'react';
import { paperTradingAPI, strategiesAPI } from '../services/api';
import './PaperTrading.css';

function PaperTrading() {
  const [sessions, setSessions] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [creating, setCreating] = useState(false);

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
      await fetchData();
    } catch (err) {
      setError('Error al crear sesion: ' + (err.response?.data?.detail || err.message));
    } finally {
      setCreating(false);
    }
  };

  const handleCloseSession = async (sessionId) => {
    try {
      setError(null);
      await paperTradingAPI.closeSession(sessionId);
      await fetchData();
    } catch (err) {
      setError('Error al cerrar sesion: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) return <div className="paper-trading-page"><p>Cargando sesiones...</p></div>;

  return (
    <div className="paper-trading-page">
      <div className="page-header">
        <h1>Paper Trading</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? '✕ Cancelar' : '+ Nueva Sesion'}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {showForm && (
        <div className="form-container">
          <form className="strategy-form" onSubmit={handleCreateSession}>
            <h3>Nueva Sesion de Paper Trading</h3>

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
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.strategy_type})
                  </option>
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
                  <p className="session-meta">{session.pair} • {session.timeframe}</p>
                </div>
                <span className={`status-badge ${session.is_active ? 'active' : 'inactive'}`}>
                  ● {session.is_active ? 'Activa' : 'Cerrada'}
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
                  <p className="stat-value">
                    {session.created_at ? new Date(session.created_at).toLocaleDateString() : '-'}
                  </p>
                </div>
              </div>

              <div className="session-actions">
                {session.is_active && (
                  <button
                    className="btn-secondary"
                    onClick={() => handleCloseSession(session.id)}
                  >
                    Cerrar Sesion
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default PaperTrading;
