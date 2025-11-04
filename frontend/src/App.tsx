import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Layout from './components/Layout';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import HealthProfile from './pages/HealthProfile';
import OCRScan from './pages/OCRScan';
import Recommendations from './pages/Recommendations';
import Favorites from './pages/Favorites';

function App() {
  const { t } = useTranslation();

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/health-profile" element={<HealthProfile />} />
          <Route path="/ocr-scan" element={<OCRScan />} />
          <Route path="/recommendations" element={<Recommendations />} />
          <Route path="/favorites" element={<Favorites />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
