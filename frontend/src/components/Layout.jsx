import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiMenu, FiX, FiLogOut } from 'react-icons/fi';
import { useAuth } from '../context/AuthContext';
import Sidebar from './Sidebar';
import './Layout.css';

function Layout({ children }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const { logout } = useAuth();
  const navigate = useNavigate();

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="layout">
      <Sidebar isOpen={isSidebarOpen} />
      <div className="main-content">
        <header className="navbar">
          <button
            className="menu-toggle"
            onClick={toggleSidebar}
          >
            {isSidebarOpen ? <FiX /> : <FiMenu />}
          </button>
          <h1 className="navbar-title">Crypto Trading Bot</h1>
          <div className="navbar-spacer"></div>
          <button className="logout-btn" onClick={handleLogout} title="Cerrar sesion">
            <FiLogOut />
            <span>Salir</span>
          </button>
        </header>
        <main className="page-content">
          {children}
        </main>
      </div>
    </div>
  );
}

export default Layout;
