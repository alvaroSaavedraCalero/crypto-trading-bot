import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses gracefully
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token may be expired or invalid - clear it so ProtectedRoute redirects to login
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          if (payload.exp * 1000 < Date.now()) {
            localStorage.removeItem('token');
            window.location.href = '/login';
          }
        } catch {
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
};

// Strategies endpoints
export const strategiesAPI = {
  list: (skip = 0, limit = 100) => api.get('/strategies', { params: { skip, limit } }),
  get: (id) => api.get(`/strategies/${id}`),
  create: (data) => api.post('/strategies', data),
  update: (id, data) => api.put(`/strategies/${id}`, data),
  delete: (id) => api.delete(`/strategies/${id}`),
  types: () => api.get('/strategies/types'),
  clone: (id) => api.post(`/strategies/${id}/clone`),
};

// Backtests endpoints
export const backtestsAPI = {
  list: (skip = 0, limit = 100) => api.get('/backtests', { params: { skip, limit } }),
  get: (id) => api.get(`/backtests/${id}`),
  run: (data) => api.post('/backtests', data),
  delete: (id) => api.delete(`/backtests/${id}`),
};

// Paper Trading endpoints
export const paperTradingAPI = {
  listSessions: (skip = 0, limit = 100) =>
    api.get('/paper-trading', { params: { skip, limit } }),
  getSession: (id) => api.get(`/paper-trading/${id}`),
  createSession: (data) => api.post('/paper-trading', data),
  runSession: (id) => api.post(`/paper-trading/${id}/run`),
  closeSession: (id) => api.post(`/paper-trading/${id}/close`),
  getTrades: (sessionId, skip = 0, limit = 100) =>
    api.get(`/paper-trading/${sessionId}/trades`, { params: { skip, limit } }),
};

// Dashboard endpoints
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getSummary: () => api.get('/dashboard/summary'),
};

// Market data endpoints
export const marketAPI = {
  getPrice: (symbol) => api.get(`/market/prices/${symbol}`),
  getOHLCV: (symbol, period = '60d', interval = '1d') =>
    api.get(`/market/ohlcv/${symbol}`, { params: { period, interval } }),
};

// Health check
export const healthAPI = {
  check: () => api.get('/health'),
};

export default api;
