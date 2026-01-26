import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FiMenu, FiX } from 'react-icons/fi';
import Sidebar from './Sidebar';
import './Layout.css';

function Layout({ children }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const location = useLocation();

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
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
        </header>
        <main className="page-content">
          {children}
        </main>
      </div>
    </div>
  );
}

export default Layout;
