import React, { useState } from 'react';
import toast from 'react-hot-toast';

function Settings() {
  const [defaults, setDefaults] = useState({
    pair: localStorage.getItem('default_pair') || 'BTC-USD',
    timeframe: localStorage.getItem('default_timeframe') || '15m',
    capital: localStorage.getItem('default_capital') || '10000',
    stopLoss: localStorage.getItem('default_sl') || '2',
    takeProfitRR: localStorage.getItem('default_tp_rr') || '2',
  });

  const handleSave = () => {
    localStorage.setItem('default_pair', defaults.pair);
    localStorage.setItem('default_timeframe', defaults.timeframe);
    localStorage.setItem('default_capital', defaults.capital);
    localStorage.setItem('default_sl', defaults.stopLoss);
    localStorage.setItem('default_tp_rr', defaults.takeProfitRR);
    toast.success('Configuracion guardada');
  };

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <h1 style={{ color: 'var(--text-primary)', fontSize: '1.6rem', marginBottom: '1.5rem' }}>Configuracion</h1>

      <div style={{
        background: 'var(--bg-card)',
        borderRadius: 'var(--radius-md)',
        padding: '1.5rem',
        border: '1px solid var(--border)',
        marginBottom: '1.5rem',
      }}>
        <h3 style={{
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          marginBottom: '1.25rem',
        }}>
          Parametros por Defecto
        </h3>

        <div className="form-group">
          <label>Par por defecto</label>
          <input
            type="text"
            value={defaults.pair}
            onChange={(e) => setDefaults({ ...defaults, pair: e.target.value })}
          />
        </div>

        <div className="form-group">
          <label>Timeframe por defecto</label>
          <select
            value={defaults.timeframe}
            onChange={(e) => setDefaults({ ...defaults, timeframe: e.target.value })}
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
          <label>Capital Inicial ($)</label>
          <input
            type="number"
            value={defaults.capital}
            onChange={(e) => setDefaults({ ...defaults, capital: e.target.value })}
            min={100}
          />
        </div>

        <div className="form-group">
          <label>Stop Loss (%)</label>
          <input
            type="number"
            value={defaults.stopLoss}
            onChange={(e) => setDefaults({ ...defaults, stopLoss: e.target.value })}
            min={0.1}
            step={0.1}
          />
        </div>

        <div className="form-group">
          <label>Take Profit R:R</label>
          <input
            type="number"
            value={defaults.takeProfitRR}
            onChange={(e) => setDefaults({ ...defaults, takeProfitRR: e.target.value })}
            min={0.5}
            step={0.5}
          />
        </div>

        <button className="btn-primary" onClick={handleSave} style={{ marginTop: '0.5rem' }}>
          Guardar Configuracion
        </button>
      </div>

      <div style={{
        background: 'var(--bg-card)',
        borderRadius: 'var(--radius-md)',
        padding: '1.5rem',
        border: '1px solid var(--border)',
      }}>
        <h3 style={{
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          marginBottom: '1rem',
        }}>
          Informacion del Sistema
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {[
            { label: 'API URL', value: '/api/v1' },
            { label: 'Documentacion API', value: 'http://localhost:8000/docs' },
            { label: 'Version', value: '1.0.0' },
          ].map(item => (
            <div key={item.label} style={{
              display: 'flex',
              justifyContent: 'space-between',
              padding: '0.5rem 0',
              borderBottom: '1px solid var(--border)',
            }}>
              <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{item.label}</span>
              <span style={{ color: 'var(--text-primary)', fontSize: '0.9rem', fontFamily: 'monospace' }}>{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Settings;
