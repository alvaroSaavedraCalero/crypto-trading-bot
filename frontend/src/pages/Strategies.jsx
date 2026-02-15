import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { strategiesAPI } from '../services/api';
import './Strategies.css';

const STRATEGY_TYPES = [
  'MA_RSI', 'MACD_ADX', 'KELTNER', 'BB_TREND', 'SQUEEZE',
  'SUPERTREND', 'BOLLINGER_MR', 'SMART_MONEY', 'ICT', 'AI_RF',
];

const DEFAULT_CONFIGS = {
  MA_RSI: { fast_window: 10, slow_window: 20, rsi_window: 14, rsi_overbought: 70, rsi_oversold: 30 },
  MACD_ADX: { fast_ema: 8, slow_ema: 24, signal_ema: 9, adx_window: 14, adx_threshold: 20 },
  KELTNER: { kc_window: 30, kc_mult: 2.5, atr_window: 20, allow_short: true },
  BB_TREND: { bb_window: 20, bb_std: 2.0, trend_ema_window: 200, allow_short: true },
  SQUEEZE: { bb_window: 20, bb_mult: 2.0, kc_window: 20, kc_mult: 1.5, mom_window: 20 },
  SUPERTREND: { atr_period: 10, atr_multiplier: 3.0 },
  BOLLINGER_MR: { bb_window: 20, bb_std: 2.0, rsi_window: 14 },
  SMART_MONEY: { swing_length: 5, use_fvg: true, fvg_min_size_pct: 0.1, use_ob: true, allow_short: true },
  ICT: { kill_zone_start_hour: 7, kill_zone_end_hour: 10, swing_length: 5, liquidity_lookback: 20 },
  AI_RF: { lookback_window: 14, training_size_pct: 0.6, prediction_threshold: 0.55, max_depth: 10 },
};

function Strategies() {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState(null);

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await strategiesAPI.list();
      setStrategies(response.data);
    } catch (err) {
      setError('Error al cargar estrategias: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Seguro que deseas eliminar esta estrategia?')) return;
    try {
      setError(null);
      await strategiesAPI.delete(id);
      toast.success('Estrategia eliminada');
      await fetchStrategies();
    } catch (err) {
      toast.error('Error al eliminar: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleEdit = (strategy) => {
    setEditingStrategy(strategy);
    setShowForm(true);
  };

  return (
    <div className="strategies-page">
      <div className="page-header">
        <h1>Estrategias</h1>
        <button
          className="btn-primary"
          onClick={() => { setShowForm(!showForm); setEditingStrategy(null); }}
        >
          {showForm ? 'Cancelar' : '+ Nueva Estrategia'}
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {showForm && (
        <div className="form-container">
          <StrategyForm
            editData={editingStrategy}
            onSuccess={() => {
              setShowForm(false);
              setEditingStrategy(null);
              fetchStrategies();
            }}
            onError={(msg) => setError(msg)}
          />
        </div>
      )}

      <div className="strategies-list">
        {loading ? (
          <div style={{ display: 'grid', gap: '1rem' }}>
            {[1, 2, 3].map(i => <div key={i} className="skeleton skeleton-card" />)}
          </div>
        ) : strategies.length === 0 ? (
          <div className="empty-state">
            <p>No hay estrategias creadas aun</p>
            <p className="text-muted">Crea una nueva estrategia para comenzar</p>
          </div>
        ) : (
          strategies.map((strategy) => (
            <div key={strategy.id} className="strategy-card">
              <div className="strategy-header">
                <h3>{strategy.name}</h3>
                <span className={`status-badge ${strategy.is_active ? 'active' : 'inactive'}`}>
                  {strategy.is_active ? 'Activa' : 'Inactiva'}
                </span>
              </div>
              <p className="strategy-type">Tipo: <strong>{strategy.strategy_type}</strong></p>
              <p className="strategy-description">{strategy.description || 'Sin descripcion'}</p>
              <div className="strategy-meta">
                <span>Capital: ${strategy.initial_capital}</span>
                <span>SL: {strategy.stop_loss_pct}%</span>
                <span>TP Ratio: {strategy.take_profit_rr}:1</span>
              </div>
              <div className="strategy-actions">
                <button className="btn-secondary" onClick={() => handleEdit(strategy)}>
                  Editar
                </button>
                <button className="btn-secondary btn-danger" onClick={() => handleDelete(strategy.id)}>
                  Eliminar
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function StrategyForm({ editData, onSuccess, onError }) {
  const isEditing = !!editData;
  const [formData, setFormData] = useState({
    name: editData?.name || '',
    strategy_type: editData?.strategy_type || 'MA_RSI',
    description: editData?.description || '',
    initial_capital: editData?.initial_capital || 10000,
    stop_loss_pct: editData?.stop_loss_pct || 2,
    take_profit_rr: editData?.take_profit_rr || 2,
    config: JSON.stringify(editData?.config || DEFAULT_CONFIGS['MA_RSI'], null, 2),
  });
  const [submitting, setSubmitting] = useState(false);

  const handleTypeChange = (newType) => {
    setFormData({
      ...formData,
      strategy_type: newType,
      config: JSON.stringify(DEFAULT_CONFIGS[newType] || {}, null, 2),
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    let parsedConfig;
    try {
      parsedConfig = JSON.parse(formData.config);
    } catch {
      onError('El campo config no es JSON valido');
      return;
    }
    try {
      setSubmitting(true);
      const payload = {
        name: formData.name,
        strategy_type: formData.strategy_type,
        description: formData.description || null,
        initial_capital: Number(formData.initial_capital),
        stop_loss_pct: Number(formData.stop_loss_pct),
        take_profit_rr: Number(formData.take_profit_rr),
        config: parsedConfig,
      };
      if (isEditing) {
        await strategiesAPI.update(editData.id, payload);
        toast.success('Estrategia actualizada');
      } else {
        await strategiesAPI.create(payload);
        toast.success('Estrategia creada');
      }
      onSuccess();
    } catch (err) {
      const action = isEditing ? 'actualizar' : 'crear';
      toast.error(`Error al ${action}: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="strategy-form" onSubmit={handleSubmit}>
      <h3>{isEditing ? 'Editar Estrategia' : 'Crear Nueva Estrategia'}</h3>

      <div className="form-group">
        <label>Nombre *</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          required
        />
      </div>

      <div className="form-group">
        <label>Tipo de Estrategia *</label>
        <select
          value={formData.strategy_type}
          onChange={(e) => handleTypeChange(e.target.value)}
          disabled={isEditing}
        >
          {STRATEGY_TYPES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label>Descripcion</label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          rows={2}
        ></textarea>
      </div>

      <div className="form-group">
        <label>Capital Inicial ($)</label>
        <input
          type="number"
          value={formData.initial_capital}
          onChange={(e) => setFormData({ ...formData, initial_capital: e.target.value })}
          min={100}
        />
      </div>

      <div className="form-group">
        <label>Stop Loss (%)</label>
        <input
          type="number"
          value={formData.stop_loss_pct}
          onChange={(e) => setFormData({ ...formData, stop_loss_pct: e.target.value })}
          min={0.1}
          step={0.1}
        />
      </div>

      <div className="form-group">
        <label>Take Profit R:R</label>
        <input
          type="number"
          value={formData.take_profit_rr}
          onChange={(e) => setFormData({ ...formData, take_profit_rr: e.target.value })}
          min={0.5}
          step={0.5}
        />
      </div>

      <div className="form-group">
        <label>Configuracion (JSON)</label>
        <textarea
          value={formData.config}
          onChange={(e) => setFormData({ ...formData, config: e.target.value })}
          rows={6}
          style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}
        ></textarea>
      </div>

      <div className="form-actions">
        <button type="submit" className="btn-primary" disabled={submitting}>
          {submitting ? (isEditing ? 'Guardando...' : 'Creando...') : (isEditing ? 'Guardar Cambios' : 'Crear Estrategia')}
        </button>
      </div>
    </form>
  );
}

export default Strategies;
