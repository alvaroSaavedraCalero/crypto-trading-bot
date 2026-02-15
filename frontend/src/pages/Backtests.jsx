import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { backtestsAPI, strategiesAPI } from '../services/api';
import WinLossChart from '../components/charts/WinLossChart';
import MetricsPanel from '../components/stats/MetricsPanel';
import './Backtests.css';

function Backtests() {
  const [backtests, setBacktests] = useState([]);
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [running, setRunning] = useState(false);
  const [selectedBacktest, setSelectedBacktest] = useState(null);

  const [formData, setFormData] = useState({
    strategy_id: '',
    pair: 'BTC-USD',
    timeframe: '15m',
    period: '60d',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [btRes, stRes] = await Promise.all([
        backtestsAPI.list(),
        strategiesAPI.list(),
      ]);
      setBacktests(btRes.data);
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

  const handleRunBacktest = async (e) => {
    e.preventDefault();
    try {
      setRunning(true);
      setError(null);
      setSuccess(null);
      const res = await backtestsAPI.run({
        strategy_id: Number(formData.strategy_id),
        pair: formData.pair,
        timeframe: formData.timeframe,
        period: formData.period,
      });
      const result = res.data;
      setShowForm(false);

      const stratName = strategies.find(s => s.id === Number(formData.strategy_id))?.name || '';
      const msg = `Backtest completado: ${stratName} - Retorno: ${result.total_return_pct?.toFixed(2)}%, Trades: ${result.num_trades}`;
      setSuccess(msg);
      toast.success('Backtest ejecutado correctamente');

      await fetchData();
      if (result.backtest_id) {
        handleViewBacktest(result.backtest_id);
      }
    } catch (err) {
      const msg = 'Error al ejecutar backtest: ' + (err.response?.data?.detail || err.message);
      setError(msg);
      toast.error(msg);
    } finally {
      setRunning(false);
    }
  };

  const handleViewBacktest = async (id) => {
    try {
      setError(null);
      const res = await backtestsAPI.get(id);
      setSelectedBacktest(res.data);
    } catch (err) {
      setError('Error al cargar detalle: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteBacktest = async (id) => {
    if (!window.confirm('Seguro que deseas eliminar este backtest?')) return;
    try {
      setError(null);
      await backtestsAPI.delete(id);
      if (selectedBacktest?.id === id) setSelectedBacktest(null);
      toast.success('Backtest eliminado');
      await fetchData();
    } catch (err) {
      toast.error('Error al eliminar: ' + (err.response?.data?.detail || err.message));
    }
  };

  const getStrategyName = (bt) => {
    const strat = strategies.find((s) => s.id === bt.strategy_id);
    return strat ? strat.name : `Strategy #${bt.strategy_id}`;
  };

  if (loading) {
    return (
      <div className="backtests-page">
        <div className="page-header"><h1>Backtests</h1></div>
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          {[1, 2, 3].map(i => <div key={i} className="skeleton skeleton-card" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="backtests-page">
      <div className="page-header">
        <h1>Backtests</h1>
        <button className="btn-primary" onClick={() => { setShowForm(!showForm); setSuccess(null); }}>
          {showForm ? 'Cancelar' : '+ Nuevo Backtest'}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      {showForm && (
        <div className="form-container">
          <form className="strategy-form" onSubmit={handleRunBacktest}>
            <h3 style={{ color: 'var(--text-primary)', marginBottom: '1rem' }}>Ejecutar Backtest</h3>

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

            <div className="form-group">
              <label>Periodo</label>
              <select
                value={formData.period}
                onChange={(e) => setFormData({ ...formData, period: e.target.value })}
              >
                <option value="7d">7 dias</option>
                <option value="30d">30 dias</option>
                <option value="60d">60 dias</option>
                <option value="90d">90 dias</option>
                <option value="180d">180 dias</option>
                <option value="1y">1 ano</option>
              </select>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={running || strategies.length === 0}>
                {running ? 'Ejecutando...' : 'Ejecutar Backtest'}
              </button>
            </div>
          </form>
        </div>
      )}

      {selectedBacktest && (
        <div className="form-container">
          <div className="backtest-detail">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3>
                Detalle Backtest #{selectedBacktest.id}
                {' -- '}
                {getStrategyName(selectedBacktest)} / {selectedBacktest.pair}
              </h3>
              <button className="btn-secondary" onClick={() => setSelectedBacktest(null)}>Cerrar</button>
            </div>

            <MetricsPanel metrics={selectedBacktest} />

            {selectedBacktest.trades?.length > 0 && (
              <>
                <div style={{ marginTop: '1.5rem' }}>
                  <h4 style={{ color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
                    Distribucion de PnL ({selectedBacktest.trades.length} trades)
                  </h4>
                  <WinLossChart trades={selectedBacktest.trades} height={220} />
                </div>

                <h4 style={{ marginTop: '1.5rem', color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
                  Trades ({selectedBacktest.trades.length})
                </h4>
                <div className="table-wrapper">
                  <table className="backtests-table">
                    <thead>
                      <tr>
                        <th>Lado</th>
                        <th>Entrada</th>
                        <th>Salida</th>
                        <th>Tamano</th>
                        <th>PnL</th>
                        <th>PnL %</th>
                        <th>Resultado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedBacktest.trades.map((t, idx) => (
                        <tr key={idx}>
                          <td><strong>{t.side === 'long' ? 'LONG' : 'SHORT'}</strong></td>
                          <td>${Number(t.entry_price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                          <td>${Number(t.exit_price).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                          <td>{Number(t.position_size).toFixed(6)}</td>
                          <td className={t.pnl < 0 ? 'negative' : 'positive'}>
                            ${Number(t.pnl).toFixed(2)}
                          </td>
                          <td className={t.pnl_pct < 0 ? 'negative' : 'positive'}>
                            {t.pnl_pct > 0 ? '+' : ''}{Number(t.pnl_pct).toFixed(2)}%
                          </td>
                          <td style={{ color: t.is_winning ? 'var(--profit)' : 'var(--loss)', fontWeight: 600 }}>
                            {t.is_winning ? 'WIN' : 'LOSS'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}

            {(!selectedBacktest.trades || selectedBacktest.trades.length === 0) && (
              <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>
                Este backtest no genero trades. La estrategia no produjo senales en el periodo seleccionado.
              </p>
            )}
          </div>
        </div>
      )}

      {backtests.length === 0 ? (
        <div className="empty-state">
          <p>No hay backtests aun</p>
          <p className="text-muted">Crea una estrategia y ejecuta un backtest para comenzar</p>
        </div>
      ) : (
        <div className="backtest-cards">
          {backtests.map((bt) => (
            <div key={bt.id} className={`backtest-card ${selectedBacktest?.id === bt.id ? 'selected' : ''}`}>
              <div className="backtest-card-header">
                <div>
                  <h3>{getStrategyName(bt)}</h3>
                  <p className="backtest-card-meta">
                    {bt.pair} / {bt.timeframe} -- {bt.created_at ? new Date(bt.created_at).toLocaleDateString() : ''}
                  </p>
                </div>
                <span className={`return-badge ${(bt.total_return_pct || 0) < 0 ? 'negative' : 'positive'}`}>
                  {(bt.total_return_pct || 0) > 0 ? '+' : ''}{bt.total_return_pct?.toFixed(2)}%
                </span>
              </div>

              <div className="backtest-card-stats">
                <div className="mini-stat">
                  <span className="mini-stat-label">Winrate</span>
                  <span className="mini-stat-value">{bt.winrate_pct?.toFixed(1)}%</span>
                </div>
                <div className="mini-stat">
                  <span className="mini-stat-label">Profit Factor</span>
                  <span className="mini-stat-value">{bt.profit_factor?.toFixed(2)}</span>
                </div>
                <div className="mini-stat">
                  <span className="mini-stat-label">Max DD</span>
                  <span className="mini-stat-value negative">{bt.max_drawdown_pct?.toFixed(2)}%</span>
                </div>
                <div className="mini-stat">
                  <span className="mini-stat-label">Trades</span>
                  <span className="mini-stat-value">{bt.num_trades} <small>({bt.winning_trades}W/{bt.losing_trades}L)</small></span>
                </div>
              </div>

              <div className="backtest-card-actions">
                <button className="btn-small" onClick={() => handleViewBacktest(bt.id)}>
                  Ver Detalle
                </button>
                <button className="btn-small btn-danger" onClick={() => handleDeleteBacktest(bt.id)}>
                  Eliminar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Backtests;
