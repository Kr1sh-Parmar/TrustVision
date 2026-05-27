import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Line, Bar, Pie } from 'react-chartjs-2';
import {
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import './AdminDashboard.css';

// Register Chart.js components
Chart.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const AdminDashboard = () => {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [fraudAlerts, setFraudAlerts] = useState([]);
  const [systemMetrics, setSystemMetrics] = useState(null);
  
  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('adminToken');
      
      const response = await axios.get('/api/admin/dashboard-overview', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.data.success) {
        setOverview(response.data);
        setError(null);
      } else {
        setError(response.data.error || 'Failed to load dashboard data');
      }
    } catch (err) {
      setError('Error connecting to server. Please try again later.');
      console.error('Dashboard data error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchFraudAlerts = async () => {
    try {
      const token = localStorage.getItem('adminToken');
      
      const response = await axios.get('/api/admin/fraud-alerts', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.data.success) {
        setFraudAlerts(response.data.alerts);
      }
    } catch (err) {
      console.error('Error fetching fraud alerts:', err);
    }
  };
  
  const fetchSystemMetrics = async () => {
    try {
      const token = localStorage.getItem('adminToken');
      
      const response = await axios.get('/api/admin/system-metrics', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.data.success) {
        setSystemMetrics(response.data);
      }
    } catch (err) {
      console.error('Error fetching system metrics:', err);
    }
  };
  
  useEffect(() => {
    fetchDashboardData();
    
    // If viewing fraud alerts tab, fetch that data
    if (activeTab === 'fraud') {
      fetchFraudAlerts();
    }
    
    // If viewing system metrics tab, fetch that data
    if (activeTab === 'metrics') {
      fetchSystemMetrics();
    }
    
    // Refresh data periodically
    const intervalId = setInterval(fetchDashboardData, 60000); // Refresh every minute
    
    return () => clearInterval(intervalId);
  }, [activeTab]);
  
  // Render charts if data is available
  const renderActivityChart = () => {
    if (!overview || !overview.daily_activity) return null;
    
    const data = {
      labels: overview.daily_activity.map(day => day.date),
      datasets: [
        {
          label: 'Verifications',
          data: overview.daily_activity.map(day => day.verifications),
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.5)',
        },
        {
          label: 'Registrations',
          data: overview.daily_activity.map(day => day.registrations),
          borderColor: 'rgb(54, 162, 235)',
          backgroundColor: 'rgba(54, 162, 235, 0.5)',
        },
        {
          label: 'Transactions',
          data: overview.daily_activity.map(day => day.transactions),
          borderColor: 'rgb(255, 99, 132)',
          backgroundColor: 'rgba(255, 99, 132, 0.5)',
        }
      ]
    };
    
    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: 'Daily Activity'
        }
      }
    };
    
    return <Line data={data} options={options} />;
  };
  
  const renderBlockchainDistribution = () => {
    if (!overview || !overview.chain_distribution) return null;
    
    const chains = Object.keys(overview.chain_distribution);
    
    const data = {
      labels: chains.map(c => c.charAt(0).toUpperCase() + c.slice(1)),
      datasets: [
        {
          label: 'Registrations by Blockchain',
          data: chains.map(c => overview.chain_distribution[c].registrations),
          backgroundColor: [
            'rgba(255, 99, 132, 0.6)',
            'rgba(54, 162, 235, 0.6)',
            'rgba(255, 206, 86, 0.6)',
            'rgba(75, 192, 192, 0.6)',
            'rgba(153, 102, 255, 0.6)'
          ],
          borderWidth: 1
        }
      ]
    };
    
    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: 'Blockchain Distribution'
        }
      }
    };
    
    return <Pie data={data} options={options} />;
  };
  
  const renderSystemHealthMetrics = () => {
    if (!systemMetrics) return null;
    
    const resourceLabels = Object.keys(systemMetrics.resource_usage);
    
    const data = {
      labels: resourceLabels.map(label => label.toUpperCase()),
      datasets: [
        {
          label: 'Resource Usage (%)',
          data: resourceLabels.map(key => systemMetrics.resource_usage[key]),
          backgroundColor: 'rgba(75, 192, 192, 0.6)',
        }
      ]
    };
    
    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: 'System Resource Usage'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100
        }
      }
    };
    
    return <Bar data={data} options={options} />;
  };
  
  const renderFraudAlertsList = () => {
    if (fraudAlerts.length === 0) {
      return <div className="no-alerts">No fraud alerts found</div>;
    }
    
    return (
      <div className="fraud-alerts-list">
        <h3>Recent Fraud Alerts ({fraudAlerts.length})</h3>
        <table className="alerts-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>User</th>
              <th>Activity</th>
              <th>Reason</th>
              <th>Confidence</th>
              <th>Location</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {fraudAlerts.map((alert, index) => (
              <tr key={index} className={alert.confidence > 0.8 ? 'high-risk' : ''}>
                <td>{new Date(alert.timestamp * 1000).toLocaleString()}</td>
                <td>{alert.user_id}</td>
                <td>{alert.activity_type}</td>
                <td>{alert.reason}</td>
                <td>{Math.round(alert.confidence * 100)}%</td>
                <td>{alert.location || 'Unknown'}</td>
                <td>{alert.status}</td>
                <td>
                  <button className="investigate-btn">Investigate</button>
                  <button className="resolve-btn">Resolve</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };
  
  const renderPerformanceMetrics = () => {
    if (!systemMetrics) return null;
    
    return (
      <div className="performance-metrics">
        <h3>System Performance</h3>
        
        <div className="metrics-grid">
          <div className="metric-card">
            <h4>API Performance</h4>
            <ul>
              <li>Avg Response: {systemMetrics.api_performance.average_response_time}ms</li>
              <li>Requests/min: {systemMetrics.api_performance.requests_per_minute}</li>
              <li>Error Rate: {systemMetrics.api_performance.error_rate * 100}%</li>
              <li>Uptime: {systemMetrics.api_performance.uptime}%</li>
            </ul>
          </div>
          
          <div className="metric-card">
            <h4>Face Recognition Performance</h4>
            <ul>
              <li>Detection Time: {systemMetrics.face_recognition.average_detection_time}ms</li>
              <li>Embedding Time: {systemMetrics.face_recognition.average_embedding_time}ms</li>
              <li>Accuracy: {systemMetrics.face_recognition.accuracy * 100}%</li>
            </ul>
          </div>
          
          <div className="metric-card">
            <h4>Blockchain Performance</h4>
            <ul>
              <li>Transaction Time: {systemMetrics.blockchain.average_transaction_time}ms</li>
              <li>Gas Usage: {systemMetrics.blockchain.gas_usage}</li>
              <li>Confirmation Rate: {systemMetrics.blockchain.confirmation_rate * 100}%</li>
            </ul>
          </div>
        </div>
        
        {renderSystemHealthMetrics()}
        
        <div className="action-buttons">
          <button className="primary-btn" onClick={() => alert('Generating diagnostic report...')}>
            Generate Diagnostic Report
          </button>
          <button className="secondary-btn" onClick={() => alert('Optimizing system performance...')}>
            Optimize Performance
          </button>
        </div>
      </div>
    );
  };
  
  return (
    <div className="admin-dashboard">
      <div className="dashboard-header">
        <h2>Admin Dashboard</h2>
        <div className="refresh-controls">
          <button onClick={fetchDashboardData} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh Data'}
          </button>
          <span className="last-updated">
            {overview && overview.system_health ? 
              `Last updated: ${new Date(overview.system_health.last_updated * 1000).toLocaleString()}` : 
              'Loading...'}
          </span>
        </div>
      </div>
      
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
      
      <div className="dashboard-nav">
        <ul>
          <li className={activeTab === 'overview' ? 'active' : ''} onClick={() => setActiveTab('overview')}>Overview</li>
          <li className={activeTab === 'fraud' ? 'active' : ''} onClick={() => setActiveTab('fraud')}>Fraud Alerts</li>
          <li className={activeTab === 'metrics' ? 'active' : ''} onClick={() => setActiveTab('metrics')}>System Metrics</li>
          <li className={activeTab === 'users' ? 'active' : ''} onClick={() => setActiveTab('users')}>User Management</li>
        </ul>
      </div>
      
      <div className="dashboard-content">
        {loading && !overview ? (
          <div className="loading">Loading dashboard data...</div>
        ) : (
          <>
            {activeTab === 'overview' && overview && (
              <div className="overview-tab">
                <div className="stats-cards">
                  <div className="stat-card">
                    <h3>Total Users</h3>
                    <div className="stat-value">{overview.overview.total_users}</div>
                  </div>
                  <div className="stat-card">
                    <h3>Verifications</h3>
                    <div className="stat-value">{overview.overview.total_verifications}</div>
                  </div>
                  <div className="stat-card">
                    <h3>Transactions</h3>
                    <div className="stat-value">{overview.overview.total_transactions}</div>
                  </div>
                  <div className="stat-card alert">
                    <h3>Fraud Alerts</h3>
                    <div className="stat-value">{overview.overview.fraud_alerts}</div>
                  </div>
                  <div className="stat-card">
                    <h3>Success Rate</h3>
                    <div className="stat-value">{Math.round(overview.overview.success_rate * 100)}%</div>
                  </div>
                </div>
                
                <div className="charts-container">
                  <div className="chart-box">
                    {renderActivityChart()}
                  </div>
                  <div className="chart-box">
                    {renderBlockchainDistribution()}
                  </div>
                </div>
                
                <div className="system-health">
                  <h3>System Health</h3>
                  <div className="health-indicators">
                    <div className={`indicator ${overview.system_health.api_status === 'healthy' ? 'healthy' : 'alert'}`}>
                      <span className="indicator-label">API Status:</span>
                      <span className="indicator-value">{overview.system_health.api_status}</span>
                    </div>
                    <div className="indicator healthy">
                      <span className="indicator-label">Blockchain Connections:</span>
                      <span className="indicator-value">{overview.system_health.blockchain_connections}</span>
                    </div>
                    <div className={`indicator ${overview.system_health.hsm_status ? 'healthy' : 'alert'}`}>
                      <span className="indicator-label">HSM Status:</span>
                      <span className="indicator-value">{overview.system_health.hsm_status ? 'Connected' : 'Disconnected'}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {activeTab === 'fraud' && (
              <div className="fraud-tab">
                {renderFraudAlertsList()}
                
                <div className="action-buttons">
                  <button 
                    className="primary-btn" 
                    onClick={() => alert('Generating fraud report...')}
                  >
                    Generate Fraud Report
                  </button>
                  <button 
                    className="secondary-btn" 
                    onClick={() => alert('Retraining model...')}
                  >
                    Retrain Fraud Model
                  </button>
                </div>
              </div>
            )}
            
            {activeTab === 'metrics' && (
              <div className="metrics-tab">
                {renderPerformanceMetrics()}
              </div>
            )}
            
            {activeTab === 'users' && (
              <div className="users-tab">
                <h3>User Management</h3>
                <div className="user-search">
                  <input type="text" placeholder="Search users by wallet address, email, or name" />
                  <button>Search</button>
                </div>
                
                <div className="user-management-placeholder">
                  <p>User management interface would be implemented here.</p>
                  <p>Features would include:</p>
                  <ul>
                    <li>User search and filtering</li>
                    <li>User profile viewing</li>
                    <li>Account blocking/unblocking</li>
                    <li>Manual identity verification</li>
                    <li>Generating recovery kits</li>
                    <li>Access to user activity logs</li>
                  </ul>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard; 