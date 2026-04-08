import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * ProtectedRoute: Guards routes based on user role stored in localStorage.
 * - If no role is found, redirects to /login.
 * - If role doesn't match the required role, redirects to the correct dashboard.
 */
export default function ProtectedRoute({ children, requiredRole }) {
  const role = localStorage.getItem('epichat_role');

  // No session → back to login
  if (!role) {
    return <Navigate to="/login" replace />;
  }

  // Wrong role → redirect to correct dashboard
  if (requiredRole && role !== requiredRole) {
    if (role === 'clinician') return <Navigate to="/clinician/dashboard" replace />;
    if (role === 'patient') return <Navigate to="/patient/home" replace />;
  }

  return children;
}
