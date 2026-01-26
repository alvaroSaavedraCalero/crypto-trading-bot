import React, { useState, useEffect } from 'react';
import './Backtests.css';

function Backtests() {
  const [backtests, setBacktests] = useState([]);

  useEffect(() => {
    // Mock data
    setBacktests([
      {
        id: 1,
        strategy: 'MA_RSI',
        pair: 'USDJPY',
        timeframe: '15m',
        return: -0.02,
        winrate: 0,
        trades: 0,
        date: '2026-01-26',
      },
      {
        id: 2,
        strategy: 'KELTNER',
        pair: 'USDJPY',
        timeframe: '15m',
        return: -2.09,
        winrate: 0,
        trades: 2,
        date: '2026-01-26',
      },
    ]);
  }, []);

  return (
    <div className="backtests-page">
      <h1>Backtests</h1>
      
      <div className="backtests-table-container">
        <table className="backtests-table">
          <thead>
            <tr>
              <th>Estrategia</th>
              <th>Par</th>
              <th>Timeframe</th>
              <th>Retorno %</th>
              <th>Winrate %</th>
              <th>Trades</th>
              <th>Fecha</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {backtests.map((bt) => (
              <tr key={bt.id}>
                <td><strong>{bt.strategy}</strong></td>
                <td>{bt.pair}</td>
                <td>{bt.timeframe}</td>
                <td className={bt.return < 0 ? 'negative' : 'positive'}>
                  {bt.return > 0 ? '+' : ''}{bt.return.toFixed(2)}%
                </td>
                <td>{bt.winrate.toFixed(1)}%</td>
                <td>{bt.trades}</td>
                <td>{bt.date}</td>
                <td>
                  <button className="btn-small">Ver</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Backtests;
