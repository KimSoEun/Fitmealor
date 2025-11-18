import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const { t, i18n } = useTranslation();

  // 로그인/회원가입 페이지 체크
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';

  const toggleLanguage = () => {
    const newLang = i18n.language === 'en' ? 'ko' : 'en';
    i18n.changeLanguage(newLang);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="sticky top-0 z-50 bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center">
              <Link to={isAuthPage ? "/login" : "/home"}>
                <h1 className="text-2xl font-bold text-green-600 cursor-pointer hover:text-green-700">Fitmealor</h1>
              </Link>
            </div>
            <div className="flex items-center gap-4">
              {!isAuthPage && (
                <>
                  <a href="/home" className="text-gray-700 hover:text-green-600 px-3 py-2">{t('nav_home')}</a>
                  <a href="/health-profile" className="text-gray-700 hover:text-green-600 px-3 py-2">{t('nav_health_profile')}</a>
                  <a href="/ocr-scan" className="text-gray-700 hover:text-green-600 px-3 py-2">{t('nav_ocr_scan')}</a>
                  <a href="/history" className="text-gray-700 hover:text-green-600 px-3 py-2">{t('nav_history')}</a>
                  <a href="/favorites" className="text-gray-700 hover:text-green-600 px-3 py-2">{t('nav_favorites')}</a>
                  <button
                    onClick={() => {
                      localStorage.removeItem('isLoggedIn');
                      alert(t('nav_logout') + ' successfully.');
                      window.location.href = '/login';
                    }}
                    className="text-gray-700 hover:text-red-600 px-3 py-2"
                  >
                    {t('nav_logout')}
                  </button>
                </>
              )}
              <button
                onClick={toggleLanguage}
                className="flex items-center gap-1 text-gray-700 font-medium"
              >
                {i18n.language === 'en' ? (
                  <>
                    <span className="text-green-600 font-bold">En</span>
                    <span className="text-gray-400">|</span>
                    <span className="text-gray-400">Kr</span>
                  </>
                ) : (
                  <>
                    <span className="text-gray-400">영</span>
                    <span className="text-gray-400">|</span>
                    <span className="text-green-600 font-bold">한</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main className={isAuthPage ? "" : "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"}>
        {children}
      </main>
    </div>
  );
}
