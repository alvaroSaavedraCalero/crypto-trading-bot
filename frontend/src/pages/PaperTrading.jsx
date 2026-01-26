import React, { useState, useEffect } from 'react';
import './PaperTrading.css';

function PaperTrading() {
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    // Mock data
    setSessions([
      {
        id: 1,
        name: 'USDJPY Session 1',
        pair: 'USDJPY',
        timeframe: '15m',
        capital: 9578,
        trades: 4,
        return: -4.22,
        status: 'active',
        startDate: '2026-01-26',
      },
    ]);
  }, []);

  return (
    <div className="paper-trading-page">
      <div className="page-header">
        <h1>Paper Trading</h1>
        <button className="btn-primary">+ Nueva Sesión</button>
      </div>

      <div className="sessions-list">
        {sessions.length === 0 ? (
          <div className="empty-state">
            <p>No hay sesiones de paper trading activas</p>
          </div>
        ) : (
          sessions.map((session) => (
            <div key={session.id} className="session-card">
              <div className="session-header">
                <div>
                  <h3>{session.name}</h3>
                  <p className="session-meta">{session.pair} • {session.timeframe}</p>
                </div>
                <span className={`status-badge ${session.status}`}>
                  ● {session.status === 'active' ? 'Activa' : 'Cerrada'}
                </span>
              </div>

              <div className="session-stats">
                <div className="stat">
                  <p className="stat-label">Capital</p>
                  <p className="stat-value">${session.capital.toLocaleString()}</p>
                </div>
                <div className="stat">
                  <p className="stat-label">Trades</p>
                  <p className="stat-value">{session.trades}</p>
                </div>
                <div className="stat">
                  <p className="stat-label">Retorno</p>
                  <p className={`stat-value ${session.return < 0 ? 'negative' : 'positive'}`}>
                    {session.return > 0 ? '+' : ''}{session.return.toFixed(2)}%
                  </p>
                </div>
                <div className="stat">
                  <p className="stat-label">Inicio</p>
                  <p className="stat-value">{session.startDate}</p>
                </div>
              </div>

              <div className="session-actions">
                <button className="btn-secondary">Ver Trades</button>
                <button className="btn-secondary">Ver Gráficos</button>
                <button className="btn-secondary">Cerrar Sesión</button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default PaperTrading;
