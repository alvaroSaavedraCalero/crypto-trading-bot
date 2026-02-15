import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler, Legend);

function EquityCurveChart({ labels = [], values = [], startingCapital = 10000, height = 300 }) {
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
        Sin datos de equity disponibles
      </div>
    );
  }

  const aboveStarting = values.map(v => v >= startingCapital ? v : startingCapital);
  const belowStarting = values.map(v => v < startingCapital ? v : startingCapital);

  const data = {
    labels,
    datasets: [
      {
        label: 'Equity (ganancia)',
        data: aboveStarting,
        borderColor: '#00c853',
        backgroundColor: 'rgba(0, 200, 83, 0.1)',
        fill: { target: { value: startingCapital }, above: 'rgba(0, 200, 83, 0.1)' },
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
      },
      {
        label: 'Equity (perdida)',
        data: belowStarting,
        borderColor: '#ff1744',
        backgroundColor: 'rgba(255, 23, 68, 0.1)',
        fill: { target: { value: startingCapital }, below: 'rgba(255, 23, 68, 0.1)' },
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
      },
      {
        label: 'Valor del portafolio',
        data: values,
        borderColor: '#2196f3',
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      intersect: false,
      mode: 'index',
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: '#1e2d3d',
        titleColor: '#e0e0e0',
        bodyColor: '#8899a6',
        borderColor: '#2d3748',
        borderWidth: 1,
        callbacks: {
          label: (ctx) => `$${ctx.parsed.y?.toLocaleString(undefined, { minimumFractionDigits: 2 })}`,
        },
      },
    },
    scales: {
      x: {
        ticks: { color: '#8899a6', maxTicksLimit: 10 },
        grid: { color: '#2d3748' },
      },
      y: {
        ticks: {
          color: '#8899a6',
          callback: (v) => `$${v.toLocaleString()}`,
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

export default EquityCurveChart;
