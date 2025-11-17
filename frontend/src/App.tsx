import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Layout from './components/Layout';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import HealthProfile from './pages/HealthProfile';
import OCRScan from './pages/OCRScan';
import Recommendations from './pages/Recommendations';
import Favorites from './pages/Favorites';
import History from './pages/History';

// Protected route component - redirects to login if not authenticated
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  return isLoggedIn ? <>{children}</> : <Navigate to="/login" replace />;
};

// Root redirect component - redirects based on login status
const RootRedirect = () => {
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  return isLoggedIn ? <Navigate to="/home" replace /> : <Navigate to="/login" replace />;
};

function App() {
  const { t } = useTranslation();

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<RootRedirect />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/home" element={<ProtectedRoute><Home /></ProtectedRoute>} />
          <Route path="/health-profile" element={<ProtectedRoute><HealthProfile /></ProtectedRoute>} />
          <Route path="/ocr-scan" element={<ProtectedRoute><OCRScan /></ProtectedRoute>} />
          <Route path="/recommendations" element={<ProtectedRoute><Recommendations /></ProtectedRoute>} />
          <Route path="/favorites" element={<ProtectedRoute><Favorites /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
