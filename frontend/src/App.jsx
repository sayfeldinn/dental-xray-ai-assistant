/**
 * Main App component with routing
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import SignUp from './pages/SignUp';
import Dashboard from './pages/Dashboard';
import Patients from './pages/Patients';
import Scans from './pages/Scans';
import Review from './pages/Review';
import Treatments from './pages/Treatments';
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
          
          {/* Week 2 - Full functional pages */}
          <Route
            path="/patients"
            element={
              <ProtectedRoute>
                <Patients />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/scans"
            element={
              <ProtectedRoute>
                <Scans />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/review/:scanId"
            element={
              <ProtectedRoute>
                <Review />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/treatments/:scanId"
            element={
              <ProtectedRoute>
                <Treatments />
              </ProtectedRoute>
            }
          />
          
          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          {/*
            Dashboard has cards for these two paths, but neither list screen was
            ever built (ReviewFindings.jsx / TreatmentConfirmation.jsx are empty).
            Point them at the scan list, which is where both flows actually start,
            so the cards are not dead ends.
          */}
          <Route path="/review" element={<Navigate to="/scans" replace />} />
          <Route path="/treatments" element={<Navigate to="/scans" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
