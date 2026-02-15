import React from 'react';
import { Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

function RadarChart({ strategies = [], height = 350 }) {
  if (strategies.length === 0) {
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
        Sin datos de estrategias para comparar
      </div>
    );
  }

  const labels = ['Retorno', 'Win Rate', 'Profit Factor', 'Sharpe', 'Recuperacion'];

  const chartColors = [
    { border: '#2196f3', bg: 'rgba(33, 150, 243, 0.2)' },
    { border: '#00c853', bg: 'rgba(0, 200, 83, 0.2)' },
    { border: '#ff9800', bg: 'rgba(255, 152, 0, 0.2)' },
    { border: '#e040fb', bg: 'rgba(224, 64, 251, 0.2)' },
    { border: '#ff1744', bg: 'rgba(255, 23, 68, 0.2)' },
  ];

  const datasets = strategies.map((s, i) => {
    const c = chartColors[i % chartColors.length];
    return {
      label: s.name,
      data: [
        Math.min(Math.max((s.returnPct || 0) / 50 * 100, 0), 100),
        s.winRate || 0,
        Math.min((s.profitFactor || 0) / 3 * 100, 100),
        Math.min(Math.max((s.sharpe || 0) / 3 * 100, 0), 100),
        Math.min(Math.max((s.recovery || 0) / 5 * 100, 0), 100),
      ],
      borderColor: c.border,
      backgroundColor: c.bg,
      borderWidth: 2,
      pointRadius: 3,
      pointBackgroundColor: c.border,
    };
  });

  const data = { labels, datasets };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: '#8899a6' },
      },
    },
    scales: {
      r: {
        angleLines: { color: '#2d3748' },
        grid: { color: '#2d3748' },
        pointLabels: { color: '#8899a6', font: { size: 11 } },
        ticks: {
          color: '#5c6e7e',
          backdropColor: 'transparent',
          stepSize: 25,
        },
        suggestedMin: 0,
        suggestedMax: 100,
      },
    },
  };

  return (
    <div style={{ height, background: 'var(--bg-card)', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
      <Radar data={data} options={options} />
    </div>
  );
}

export default RadarChart;
