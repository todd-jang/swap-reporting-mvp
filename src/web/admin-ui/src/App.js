// src/admin-ui/src/App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import { Provider } from 'react-redux';
import store from './redux/store';
import ErrorList from './components/ErrorList';
import ErrorDetail from './components/ErrorDetail';
import Dashboard from './components/Dashboard'; // Placeholder
import ProcessedDataList from './components/ProcessedDataList'; // Placeholder
import ReportsList from './components/ReportsList'; // Placeholder
import SubmissionsList from './components/SubmissionsList'; // Placeholder
import HealthStatus from './components/HealthStatus'; // Placeholder
import './App.css'; // Main styling file

function App() {
  return (
    <Provider store={store}>
      <Router>
        <div className="app-container">
          {/* Navigation Bar */}
          <nav className="navbar">
            <div className="navbar-brand">Swap Reporting Admin</div>
            <ul className="navbar-nav">
              <li className="nav-item"><Link to="/" className="nav-link">Dashboard</Link></li>
              <li className="nav-item"><Link to="/errors" className="nav-link">Errors</Link></li>
              <li className="nav-item"><Link to="/processed-data" className="nav-link">Processed Data</Link></li>
              <li className="nav-item"><Link to="/reports" className="nav-link">Reports</Link></li>
              <li className="nav-item"><Link to="/submissions" className="nav-link">Submissions</Link></li>
              <li className="nav-item"><Link to="/health" className="nav-link">Health</Link></li>
            </ul>
          </nav>

          {/* Main Content Area with Routing */}
          <div className="main-content">
            <Routes>
              {/* Placeholder Routes */}
              <Route path="/" element={<Dashboard />} />
              <Route path="/processed-data" element={<ProcessedDataList />} />
              <Route path="/reports" element={<ReportsList />} />
              <Route path="/submissions" element={<SubmissionsList />} />
              <Route path="/health" element={<HealthStatus />} />

              {/* Error Management Routes */}
              <Route path="/errors" element={<ErrorList />} />
              <Route path="/errors/:errorId" element={<ErrorDetail />} />
            </Routes>
          </div>
        </div>
      </Router>
    </Provider>
  );
}

export default App;
