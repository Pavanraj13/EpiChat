import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Login from './components/Login'
import Dashboard from './components/Dashboard'
import ProtectedRoute from './components/ProtectedRoute'
import ClinicianDashboard from './components/clinician/ClinicianDashboard'
import PatientHome from './components/patient/PatientHome'

function App() {
  return (
    <Router>
      <div className="app-container">
        <Routes>
          {/* Root → Login */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />

          {/* Legacy dashboard (kept for compatibility) */}
          <Route path="/dashboard" element={<Dashboard />} />

          {/* Clinician Route */}
          <Route
            path="/clinician/dashboard"
            element={
              <ProtectedRoute requiredRole="clinician">
                <ClinicianDashboard />
              </ProtectedRoute>
            }
          />

          {/* Patient Route */}
          <Route
            path="/patient/home"
            element={
              <ProtectedRoute requiredRole="patient">
                <PatientHome />
              </ProtectedRoute>
            }
          />

          {/* Catch-All */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
