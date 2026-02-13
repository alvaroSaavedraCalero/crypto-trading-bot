import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Strategies endpoints
export const strategiesAPI = {
  list: (skip = 0, limit = 100) => api.get('/strategies', { params: { skip, limit } }),
  get: (id) => api.get(`/strategies/${id}`),
  create: (data) => api.post('/strategies', data),
  update: (id, data) => api.put(`/strategies/${id}`, data),
  delete: (id) => api.delete(`/strategies/${id}`),
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
  closeSession: (id) => api.post(`/paper-trading/${id}/close`),
  getTrades: (sessionId, skip = 0, limit = 100) =>
    api.get(`/paper-trading/${sessionId}/trades`, { params: { skip, limit } }),
};

// Health check - health router is mounted at /api/v1/health
export const healthAPI = {
  check: () => api.get('/health'),
};

export default api;
