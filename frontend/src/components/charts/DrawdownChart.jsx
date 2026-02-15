import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

function DrawdownChart({ labels = [], values = [], height = 200 }) {
  if (values.length === 0) {
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
        Sin datos de drawdown
      </div>
    );
  }

  const data = {
    labels,
    datasets: [
      {
        label: 'Drawdown %',
        data: values,
        borderColor: '#ff1744',
        backgroundColor: 'rgba(255, 23, 68, 0.2)',
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 1.5,
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
          label: (ctx) => `${ctx.parsed.y?.toFixed(2)}%`,
        },
      },
    },
    scales: {
      x: {
        ticks: { color: '#8899a6', maxTicksLimit: 8 },
        grid: { color: '#2d3748' },
      },
      y: {
        reverse: true,
        ticks: {
          color: '#8899a6',
          callback: (v) => `${v}%`,
        },
        grid: { color: '#2d3748' },
      },
    },
  };

  return (
    <div style={{ height, background: 'var(--bg-card)', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
      <Line data={data} options={options} />
    </div>
  );
}

export default DrawdownChart;
