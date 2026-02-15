import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

function WinLossChart({ trades = [], height = 250 }) {
  if (trades.length === 0) {
    return (
      <div style={{
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-card)',
        borderRadius: 'var(--radius-md)',
        color: 'var(--text-muted)',
      }}>
        Sin trades para mostrar
      </div>
    );
  }

  const pnlValues = trades.map(t => Number(t.pnl || t.pnl_pct || 0));
  const colors = pnlValues.map(v => v >= 0 ? '#00c853' : '#ff1744');

  const data = {
    labels: trades.map((_, i) => `#${i + 1}`),
    datasets: [
      {
        label: 'PnL',
        data: pnlValues,
        backgroundColor: colors,
        borderRadius: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1e2d3d',
        titleColor: '#e0e0e0',
        bodyColor: '#8899a6',
        borderColor: '#2d3748',
        borderWidth: 1,
        callbacks: {
          label: (ctx) => `PnL: $${ctx.parsed.y?.toFixed(2)}`,
        },
      },
    },
    scales: {
      x: {
        ticks: { color: '#8899a6', maxTicksLimit: 20 },
        grid: { display: false },
      },
      y: {
        ticks: {
          color: '#8899a6',
          callback: (v) => `$${v}`,
        },
        grid: { color: '#2d3748' },
      },
    },
  };

  return (
    <div style={{ height, background: 'var(--bg-card)', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
      <Bar data={data} options={options} />
    </div>
  );
}

export default WinLossChart;
