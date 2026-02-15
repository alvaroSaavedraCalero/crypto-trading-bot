import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FiHome, FiBarChart2, FiTrendingUp, FiActivity, FiPieChart, FiBookOpen, FiShield, FiSettings } from 'react-icons/fi';
import './Sidebar.css';

function Sidebar({ isOpen }) {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      <div className="sidebar-brand">
        <h2>TradingBot</h2>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Principal</div>
        <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>
          <FiHome /> <span>Dashboard</span>
        </Link>
        <Link to="/strategies" className={`nav-link ${isActive('/strategies') ? 'active' : ''}`}>
          <FiBarChart2 /> <span>Estrategias</span>
        </Link>
        <Link to="/backtests" className={`nav-link ${isActive('/backtests') ? 'active' : ''}`}>
          <FiTrendingUp /> <span>Backtests</span>
        </Link>
        <Link to="/paper-trading" className={`nav-link ${isActive('/paper-trading') ? 'active' : ''}`}>
          <FiActivity /> <span>Paper Trading</span>
        </Link>

        <div className="sidebar-section-label">Analisis</div>
        <Link to="/portfolio" className={`nav-link ${isActive('/portfolio') ? 'active' : ''}`}>
          <FiPieChart /> <span>Portafolio</span>
        </Link>
        <Link to="/trade-journal" className={`nav-link ${isActive('/trade-journal') ? 'active' : ''}`}>
          <FiBookOpen /> <span>Diario de Trades</span>
        </Link>
        <Link to="/risk-analytics" className={`nav-link ${isActive('/risk-analytics') ? 'active' : ''}`}>
          <FiShield /> <span>Riesgo</span>
        </Link>

        <div className="sidebar-section-label">Sistema</div>
        <Link to="/settings" className={`nav-link ${isActive('/settings') ? 'active' : ''}`}>
          <FiSettings /> <span>Configuracion</span>
        </Link>
      </nav>
    </aside>
  );
}

export default Sidebar;
