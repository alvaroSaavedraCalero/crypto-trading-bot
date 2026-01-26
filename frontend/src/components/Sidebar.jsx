import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FiHome, FiBarChart2, FiTrendingUp, FiActivity } from 'react-icons/fi';
import './Sidebar.css';

function Sidebar({ isOpen }) {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      <div className="sidebar-brand">
        <h2>🤖 TradingBot</h2>
      </div>

      <nav className="sidebar-nav">
        <Link 
          to="/" 
          className={`nav-link ${isActive('/') ? 'active' : ''}`}
        >
          <FiHome /> <span>Dashboard</span>
        </Link>
        <Link 
          to="/strategies" 
          className={`nav-link ${isActive('/strategies') ? 'active' : ''}`}
        >
          <FiBarChart2 /> <span>Estrategias</span>
        </Link>
        <Link 
          to="/backtests" 
          className={`nav-link ${isActive('/backtests') ? 'active' : ''}`}
        >
          <FiTrendingUp /> <span>Backtests</span>
        </Link>
        <Link 
          to="/paper-trading" 
          className={`nav-link ${isActive('/paper-trading') ? 'active' : ''}`}
        >
          <FiActivity /> <span>Paper Trading</span>
        </Link>
      </nav>
    </aside>
  );
}

export default Sidebar;
