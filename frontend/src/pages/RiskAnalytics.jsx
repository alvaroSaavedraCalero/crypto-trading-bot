import React, { useState, useEffect } from 'react';
import { backtestsAPI } from '../services/api';
import DrawdownChart from '../components/charts/DrawdownChart';
import RadarChart from '../components/charts/RadarChart';
import StatsGrid from '../components/stats/StatsGrid';

function RiskAnalytics() {
  const [backtests, setBacktests] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await backtestsAPI.list();
      setBacktests(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const avgDrawdown = backtests.length > 0
    ? backtests.reduce((s, b) => s + (b.max_drawdown_pct || 0), 0) / backtests.length
    : 0;
  const maxDrawdown = backtests.reduce((m, b) => Math.min(m, b.max_drawdown_pct || 0), 0);
  const avgWinrate = backtests.length > 0
    ? backtests.reduce((s, b) => s + (b.winrate_pct || 0), 0) / backtests.length
    : 0;
  const avgPF = backtests.length > 0
    ? backtests.reduce((s, b) => s + (b.profit_factor || 0), 0) / backtests.length
    : 0;

  const riskStats = [
    { label: 'Max Drawdown', value: `${maxDrawdown.toFixed(2)}%`, color: 'var(--loss)', valueColor: 'var(--loss)' },
    { label: 'Drawdown Promedio', value: `${avgDrawdown.toFixed(2)}%`, color: 'var(--warning)', valueColor: 'var(--loss)' },
    { label: 'Win Rate Promedio', value: `${avgWinrate.toFixed(1)}%`, color: 'var(--profit)' },
    { label: 'Profit Factor Promedio', value: avgPF.toFixed(2), color: 'var(--accent)' },
  ];

  // Build drawdown series from backtests (simulated from available data)
  const drawdownLabels = backtests.map((_, i) => `BT #${i + 1}`);
  const drawdownValues = backtests.map(b => b.max_drawdown_pct || 0);

  // Build radar data from backtests grouped by strategy
  const strategyMap = {};
  backtests.forEach(bt => {
    const key = bt.strategy_type || `ID:${bt.strategy_id}`;
    if (!strategyMap[key]) {
      strategyMap[key] = { name: key, returns: [], winrates: [], pfs: [], sharpes: [], drawdowns: [] };
    }
    strategyMap[key].returns.push(bt.total_return_pct || 0);
    strategyMap[key].winrates.push(bt.winrate_pct || 0);
    strategyMap[key].pfs.push(bt.profit_factor || 0);
    strategyMap[key].sharpes.push(bt.sharpe_ratio || 0);
    strategyMap[key].drawdowns.push(Math.abs(bt.max_drawdown_pct || 0));
  });

  const radarStrategies = Object.values(strategyMap).map(s => ({
    name: s.name,
    returnPct: s.returns.reduce((a, b) => a + b, 0) / s.returns.length,
    winRate: s.winrates.reduce((a, b) => a + b, 0) / s.winrates.length,
    profitFactor: s.pfs.reduce((a, b) => a + b, 0) / s.pfs.length,
    sharpe: s.sharpes.reduce((a, b) => a + b, 0) / s.sharpes.length,
    recovery: s.drawdowns.length > 0 ? s.returns.reduce((a, b) => a + b, 0) / s.returns.length / Math.max(s.drawdowns.reduce((a, b) => a + b, 0) / s.drawdowns.length, 0.01) : 0,
  }));

  if (loading) {
    return (
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <h1 style={{ color: 'var(--text-primary)', fontSize: '1.6rem', marginBottom: '1.5rem' }}>Analisis de Riesgo</h1>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
          {[1, 2, 3, 4].map(i => <div key={i} className="skeleton skeleton-card" />)}
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <h1 style={{ color: 'var(--text-primary)', fontSize: '1.6rem', marginBottom: '1.5rem' }}>Analisis de Riesgo</h1>

      <StatsGrid stats={riskStats} />

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '1.25rem',
        marginTop: '1.5rem',
      }}>
        <div>
          <h3 style={{
            fontSize: '0.85rem',
            color: 'var(--text-secondary)',
            marginBottom: '0.75rem',
          }}>
            Drawdown por Backtest
          </h3>
          <DrawdownChart labels={drawdownLabels} values={drawdownValues} height={280} />
        </div>

        <div>
          <h3 style={{
            fontSize: '0.85rem',
            color: 'var(--text-secondary)',
            marginBottom: '0.75rem',
          }}>
            Comparacion de Estrategias
          </h3>
          <RadarChart strategies={radarStrategies} height={280} />
        </div>
      </div>
    </div>
  );
}

export default RiskAnalytics;
