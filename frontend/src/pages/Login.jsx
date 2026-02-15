import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { authAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import './Login.css';

function Login() {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      toast.error('Por favor completa todos los campos');
      return;
    }
    if (isRegister && !email.trim()) {
      toast.error('Por favor ingresa tu email');
      return;
    }
    setLoading(true);

    try {
      let response;
      if (isRegister) {
        response = await authAPI.register({ username: username.trim(), email: email.trim(), password });
      } else {
        response = await authAPI.login(username.trim(), password);
      }

      const token = response.data?.access_token;
      if (!token) {
        toast.error('Respuesta invalida del servidor');
        return;
      }

      login(token);
      toast.success(isRegister ? 'Cuenta creada exitosamente' : 'Bienvenido!');
      // Small delay to ensure state propagates before navigation
      setTimeout(() => navigate('/'), 50);
    } catch (err) {
      console.error('Auth error:', err);
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        toast.error(detail);
      } else if (Array.isArray(detail)) {
        toast.error(detail.map(d => d.msg || d).join(', '));
      } else {
        toast.error(err.message || 'Error de conexion con el servidor');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <div className="login-logo">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
              <rect width="40" height="40" rx="8" fill="var(--accent)" />
              <path d="M12 28L12 16L16 12L20 18L24 10L28 16L28 28" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <h1>TradingBot</h1>
          <p className="login-subtitle">Plataforma de Trading Automatizado</p>
        </div>

        <div className="login-tabs">
          <button
            className={`login-tab ${!isRegister ? 'active' : ''}`}
            onClick={() => setIsRegister(false)}
          >
            Iniciar Sesion
          </button>
          <button
            className={`login-tab ${isRegister ? 'active' : ''}`}
            onClick={() => setIsRegister(true)}
          >
            Registrarse
          </button>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Usuario</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Tu nombre de usuario"
              required
              autoComplete="username"
            />
          </div>

          {isRegister && (
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="tu@email.com"
                required
                autoComplete="email"
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="password">Contrasena</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Tu contrasena"
              required
              minLength={4}
              autoComplete={isRegister ? 'new-password' : 'current-password'}
            />
          </div>

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? (
              <span className="login-spinner"></span>
            ) : isRegister ? (
              'Crear Cuenta'
            ) : (
              'Entrar'
            )}
          </button>
        </form>

        <p className="login-footer">
          {isRegister ? 'Ya tienes cuenta?' : 'No tienes cuenta?'}{' '}
          <button
            className="login-switch"
            onClick={() => setIsRegister(!isRegister)}
          >
            {isRegister ? 'Inicia sesion' : 'Registrate'}
          </button>
        </p>
      </div>
    </div>
  );
}

export default Login;
