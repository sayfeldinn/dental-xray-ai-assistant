/**
 * Main App component with routing
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import SignUp from './pages/SignUp';
import Dashboard from './pages/Dashboard';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<SignUp />} />
          
          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          
          {/* Placeholder routes - to be implemented */}
          <Route
            path="/patients"
            element={
              <ProtectedRoute>
                <div style={{ padding: '40px', textAlign: 'center' }}>
                  <h1>Patients Management</h1>
                  <p>Coming soon...</p>
                  <a href="/dashboard">Back to Dashboard</a>
                </div>
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/scans"
            element={
              <ProtectedRoute>
                <div style={{ padding: '40px', textAlign: 'center' }}>
                  <h1>X-Ray Scans</h1>
                  <p>Coming soon...</p>
                  <a href="/dashboard">Back to Dashboard</a>
                </div>
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/review"
            element={
              <ProtectedRoute>
                <div style={{ padding: '40px', textAlign: 'center' }}>
                  <h1>Review Findings</h1>
                  <p>Coming soon...</p>
                  <a href="/dashboard">Back to Dashboard</a>
                </div>
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/treatments"
            element={
              <ProtectedRoute>
                <div style={{ padding: '40px', textAlign: 'center' }}>
                  <h1>Treatments</h1>
                  <p>Coming soon...</p>
                  <a href="/dashboard">Back to Dashboard</a>
                </div>
              </ProtectedRoute>
            }
          />
          
          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
