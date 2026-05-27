import React from 'react';
import { BrowserRouter as Router, Route, Switch, Link } from 'react-router-dom';
import FaceRegistration from './components/FaceRegistration';
import FaceVerification from './components/FaceVerification';
import SecureTransaction from './components/SecureTransaction';
import MultiChainRegistration from './components/MultiChainRegistration';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>Facial Recognition + Blockchain Security</h1>
          <nav>
            <ul>
              <li><Link to="/">Home</Link></li>
              <li><Link to="/register">Register Identity</Link></li>
              <li><Link to="/verify">Verify Identity</Link></li>
              <li><Link to="/transaction">Secure Transaction</Link></li>
              <li><Link to="/multi-chain">Multi-Chain</Link></li>
            </ul>
          </nav>
        </header>
        
        <main className="app-content">
          <Switch>
            <Route exact path="/">
              <div className="home-page">
                <h2>Welcome to Facial Blockchain Security System</h2>
                <p>This application combines facial recognition with blockchain technology to provide secure authentication and transactions.</p>
                <div className="feature-grid">
                  <div className="feature-card">
                    <h3>Face Authentication</h3>
                    <p>Uses AI-based facial recognition with liveness detection to prevent spoofing</p>
                  </div>
                  <div className="feature-card">
                    <h3>Blockchain Identity</h3>
                    <p>Stores facial identity hash on blockchain for secure, decentralized verification</p>
                  </div>
                  <div className="feature-card">
                    <h3>Zero-Knowledge Proofs</h3>
                    <p>Verify identity without revealing your biometric data</p>
                  </div>
                  <div className="feature-card">
                    <h3>Fraud Prevention</h3>
                    <p>AI detects anomalies in transactions using behavioral patterns</p>
                  </div>
                </div>
                <div className="cta-buttons">
                  <Link to="/register" className="cta-button">Register New Identity</Link>
                  <Link to="/transaction" className="cta-button primary">Make Secure Transaction</Link>
                </div>
              </div>
            </Route>
            <Route path="/register">
              <FaceRegistration />
            </Route>
            <Route path="/verify">
              <FaceVerification />
            </Route>
            <Route path="/transaction">
              <SecureTransaction />
            </Route>
            <Route path="/multi-chain">
              <MultiChainRegistration />
            </Route>
          </Switch>
        </main>
        
        <footer className="app-footer">
          <p>&copy; 2023 Facial Blockchain Security System</p>
        </footer>
      </div>
    </Router>
  );
}

export default App; 