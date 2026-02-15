import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { ErrorBoundary } from 'react-error-boundary';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Strategies from './pages/Strategies';
import Backtests from './pages/Backtests';
import PaperTrading from './pages/PaperTrading';
import Portfolio from './pages/Portfolio';
import TradeJournal from './pages/TradeJournal';
import RiskAnalytics from './pages/RiskAnalytics';
import Settings from './pages/Settings';
import Login from './pages/Login';
import './App.css';

function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div style={{
      padding: '2rem',
      textAlign: 'center',
      color: 'var(--text-primary)',
      background: 'var(--bg-primary)',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <h2 style={{ marginBottom: '1rem', color: 'var(--loss)' }}>Algo salio mal</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>{error.message}</p>
      <button
        onClick={resetErrorBoundary}
        style={{
          padding: '0.75rem 1.5rem',
          background: 'var(--accent)',
          color: 'white',
          border: 'none',
          borderRadius: 'var(--radius-md)',
          cursor: 'pointer',
          fontSize: '1rem',
        }}
      >
        Intentar de nuevo
      </button>
    </div>
  );
}

function NotFound() {
  return (
    <div style={{
      textAlign: 'center',
      padding: '4rem 2rem',
    }}>
      <h1 style={{ fontSize: '4rem', color: 'var(--accent)', marginBottom: '1rem' }}>404</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '1.1rem' }}>
        Pagina no encontrada
      </p>
      <Link
        to="/"
        style={{
          padding: '0.75rem 1.5rem',
          background: 'var(--accent)',
          color: 'white',
          borderRadius: 'var(--radius-md)',
          textDecoration: 'none',
          fontSize: '0.95rem',
        }}
      >
        Ir al Dashboard
      </Link>
    </div>
  );
}

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--bg-primary)',
        color: 'var(--text-secondary)',
      }}>
        Cargando...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <Login />}
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout>
              <Dashboard />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/strategies"
        element={
          <ProtectedRoute>
            <Layout>
              <Strategies />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/backtests"
        element={
          <ProtectedRoute>
            <Layout>
              <Backtests />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/paper-trading"
        element={
          <ProtectedRoute>
            <Layout>
              <PaperTrading />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/portfolio"
        element={
          <ProtectedRoute>
            <Layout>
              <Portfolio />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/trade-journal"
        element={
          <ProtectedRoute>
            <Layout>
              <TradeJournal />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/risk-analytics"
        element={
          <ProtectedRoute>
            <Layout>
              <RiskAnalytics />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Layout>
              <Settings />
            </Layout>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

function App() {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <AuthProvider>
        <Router>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: 'var(--bg-card)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border)',
              },
              success: {
                iconTheme: { primary: 'var(--profit)', secondary: 'var(--bg-card)' },
              },
              error: {
                iconTheme: { primary: 'var(--loss)', secondary: 'var(--bg-card)' },
              },
            }}
          />
          <AppRoutes />
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
