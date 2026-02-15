import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { backtestsAPI, paperTradingAPI } from '../services/api';

function TradeJournal() {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ side: '', result: '', search: '' });

  useEffect(() => {
    fetchTrades();
  }, []);

  const fetchTrades = async () => {
    try {
      setLoading(true);
      const allTrades = [];

      // Collect trades from backtests
      const btRes = await backtestsAPI.list();
      for (const bt of btRes.data.slice(0, 20)) {
        try {
          const detail = await backtestsAPI.get(bt.id);
          if (detail.data.trades) {
            detail.data.trades.forEach(t => {
              allTrades.push({
                ...t,
                source: 'backtest',
                strategyName: bt.strategy_type || bt.pair || `Backtest #${bt.id}`,
                pair: bt.pair,
                date: t.entry_date || bt.created_at,
              });
            });
          }
        } catch {
          // skip
        }
      }

      // Collect trades from paper trading
      const sessRes = await paperTradingAPI.listSessions();
      for (const sess of sessRes.data.slice(0, 20)) {
        try {
          const trRes = await paperTradingAPI.getTrades(sess.id);
          trRes.data.forEach(t => {
            allTrades.push({
              ...t,
              source: 'paper',
              strategyName: sess.name,
              pair: sess.pair,
              date: t.created_at || sess.created_at,
            });
          });
        } catch {
          // skip
        }
      }

      setTrades(allTrades);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const filteredTrades = trades.filter(t => {
    if (filter.side && (t.side || 'long') !== filter.side) return false;
    if (filter.result === 'win' && !t.is_winning) return false;
    if (filter.result === 'loss' && t.is_winning) return false;
    if (filter.search) {
      const search = filter.search.toLowerCase();
      if (!(t.pair || '').toLowerCase().includes(search) && !(t.strategyName || '').toLowerCase().includes(search)) return false;
    }
    return true;
  });

  const handleExportCSV = () => {
    if (filteredTrades.length === 0) {
      toast.error('Sin trades para exportar');
      return;
    }
    const headers = ['Fuente', 'Estrategia', 'Par', 'Lado', 'Entrada', 'Salida', 'PnL', 'PnL %', 'Resultado'];
    const rows = filteredTrades.map(t => [
      t.source,
      t.strategyName || '',
      t.pair || '',
      (t.side || 'long').toUpperCase(),
      t.entry_price || '',
      t.exit_price || '',
      Number(t.pnl || 0).toFixed(2),
      Number(t.pnl_pct || 0).toFixed(2),
      t.is_winning ? 'WIN' : 'LOSS',
    ]);
    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trade_journal_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('CSV exportado');
  };

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ color: 'var(--text-primary)', fontSize: '1.6rem' }}>Diario de Trades</h1>
        <button className="btn-primary" onClick={handleExportCSV}>
          Exportar CSV
        </button>
      </div>

      {/* Filters */}
      <div style={{
        display: 'flex',
        gap: '0.75rem',
        marginBottom: '1.25rem',
        flexWrap: 'wrap',
      }}>
        <input
          type="text"
          placeholder="Buscar por par o estrategia..."
          value={filter.search}
          onChange={(e) => setFilter({ ...filter, search: e.target.value })}
          style={{
            padding: '0.5rem 0.75rem',
            background: 'var(--bg-input)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-primary)',
            fontSize: '0.9rem',
            minWidth: 200,
          }}
        />
        <select
          value={filter.side}
          onChange={(e) => setFilter({ ...filter, side: e.target.value })}
          style={{
            padding: '0.5rem 0.75rem',
            background: 'var(--bg-input)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-primary)',
            fontSize: '0.9rem',
          }}
        >
          <option value="">Todos los lados</option>
          <option value="long">Long</option>
          <option value="short">Short</option>
        </select>
        <select
          value={filter.result}
          onChange={(e) => setFilter({ ...filter, result: e.target.value })}
          style={{
            padding: '0.5rem 0.75rem',
            background: 'var(--bg-input)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--text-primary)',
            fontSize: '0.9rem',
          }}
        >
          <option value="">Todos los resultados</option>
          <option value="win">Ganadores</option>
          <option value="loss">Perdedores</option>
        </select>
      </div>

      <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '0.75rem' }}>
        {filteredTrades.length} trades encontrados
      </div>

      {loading ? (
        <div style={{ display: 'grid', gap: '0.5rem' }}>
          {[1, 2, 3, 4, 5].map(i => <div key={i} className="skeleton" style={{ height: 40 }} />)}
        </div>
      ) : filteredTrades.length === 0 ? (
        <div className="empty-state">
          <p>Sin trades encontrados</p>
          <p className="text-muted">Ejecuta backtests o sesiones de paper trading para ver trades aqui</p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="backtests-table">
            <thead>
              <tr>
                <th>Fuente</th>
                <th>Estrategia</th>
                <th>Par</th>
                <th>Lado</th>
                <th>Entrada</th>
                <th>Salida</th>
                <th>PnL</th>
                <th>PnL %</th>
                <th>Resultado</th>
              </tr>
            </thead>
            <tbody>
              {filteredTrades.slice(0, 200).map((t, idx) => (
                <tr key={idx}>
                  <td style={{ textTransform: 'capitalize' }}>{t.source}</td>
                  <td>{t.strategyName}</td>
                  <td>{t.pair}</td>
                  <td><strong>{(t.side || 'long').toUpperCase()}</strong></td>
                  <td>${Number(t.entry_price || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                  <td>{t.exit_price ? `$${Number(t.exit_price).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '-'}</td>
                  <td className={(t.pnl || 0) < 0 ? 'negative' : 'positive'}>
                    ${Number(t.pnl || 0).toFixed(2)}
                  </td>
                  <td className={(t.pnl_pct || 0) < 0 ? 'negative' : 'positive'}>
                    {(t.pnl_pct || 0) > 0 ? '+' : ''}{Number(t.pnl_pct || 0).toFixed(2)}%
                  </td>
                  <td style={{ color: t.is_winning ? 'var(--profit)' : 'var(--loss)', fontWeight: 600 }}>
                    {t.is_winning ? 'WIN' : 'LOSS'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default TradeJournal;
