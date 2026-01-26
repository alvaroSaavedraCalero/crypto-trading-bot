import React, { useState, useEffect } from 'react';
import { strategiesAPI } from '../services/api';
import './Strategies.css';

function Strategies() {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      setLoading(true);
      const response = await strategiesAPI.list();
      setStrategies(response.data);
    } catch (error) {
      console.error('Error fetching strategies:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="strategies-page">
      <div className="page-header">
        <h1>Estrategias</h1>
        <button 
          className="btn-primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? '✕ Cancelar' : '+ Nueva Estrategia'}
        </button>
      </div>

      {showForm && (
        <div className="form-container">
          <StrategyForm 
            onSuccess={() => {
              setShowForm(false);
              fetchStrategies();
            }}
          />
        </div>
      )}

      <div className="strategies-list">
        {loading ? (
          <p>Cargando estrategias...</p>
        ) : strategies.length === 0 ? (
          <div className="empty-state">
            <p>No hay estrategias creadas aún</p>
            <p className="text-muted">Crea una nueva estrategia para comenzar</p>
          </div>
        ) : (
          strategies.map((strategy) => (
            <div key={strategy.id} className="strategy-card">
              <div className="strategy-header">
                <h3>{strategy.name}</h3>
                <span className={`status-badge ${strategy.is_active ? 'active' : 'inactive'}`}>
                  {strategy.is_active ? '● Activa' : '● Inactiva'}
                </span>
              </div>
              <p className="strategy-type">Tipo: <strong>{strategy.strategy_type}</strong></p>
              <p className="strategy-description">{strategy.description || 'Sin descripción'}</p>
              <div className="strategy-meta">
                <span>Capital: ${strategy.initial_capital}</span>
                <span>SL: {strategy.stop_loss_pct}%</span>
                <span>TP Ratio: {strategy.take_profit_rr}:1</span>
              </div>
              <div className="strategy-actions">
                <button className="btn-secondary">Ver Detalles</button>
                <button className="btn-secondary">Editar</button>
                <button className="btn-secondary">Eliminar</button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function StrategyForm({ onSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    strategy_type: 'MA_RSI',
    description: '',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await strategiesAPI.create(formData);
      onSuccess();
    } catch (error) {
      console.error('Error creating strategy:', error);
    }
  };

  return (
    <form className="strategy-form" onSubmit={handleSubmit}>
      <h3>Crear Nueva Estrategia</h3>
      
      <div className="form-group">
        <label>Nombre *</label>
        <input 
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({...formData, name: e.target.value})}
          required
        />
      </div>

      <div className="form-group">
        <label>Tipo de Estrategia *</label>
        <select 
          value={formData.strategy_type}
          onChange={(e) => setFormData({...formData, strategy_type: e.target.value})}
        >
          <option>MA_RSI</option>
          <option>KELTNER</option>
          <option>BOLLINGER_MR</option>
          <option>SUPERTREND</option>
        </select>
      </div>

      <div className="form-group">
        <label>Descripción</label>
        <textarea 
          value={formData.description}
          onChange={(e) => setFormData({...formData, description: e.target.value})}
          rows={4}
        ></textarea>
      </div>

      <div className="form-actions">
        <button type="submit" className="btn-primary">Crear Estrategia</button>
      </div>
    </form>
  );
}

export default Strategies;
