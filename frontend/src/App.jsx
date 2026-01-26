import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Strategies from './pages/Strategies';
import Backtests from './pages/Backtests';
import PaperTrading from './pages/PaperTrading';
import './App.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/strategies" element={<Strategies />} />
          <Route path="/backtests" element={<Backtests />} />
          <Route path="/paper-trading" element={<PaperTrading />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
