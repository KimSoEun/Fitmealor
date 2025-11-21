import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import i18n from '../i18n';

export default function Login() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    console.log('Login form submitted');
    e.preventDefault();

    console.log('Email:', email, 'Password:', password ? '***' : 'empty');

    if (!email || !password) {
      console.log('Validation failed: missing email or password');
      setError(t('login.이메일과_비밀번호를_입력해주세요.'));
      return;
    }

    try {
      console.log('Sending login request to backend...');
      // API 호출
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Response data:', data);

      if (!response.ok) {
        console.log('Login failed:', data.detail);
        setError(data.detail || t('login.로그인에_실패했습니다.'));
        return;
      }

      // 토큰 저장
      console.log('Login successful, saving token...');
      localStorage.setItem('token', data.token);
      localStorage.setItem('isLoggedIn', 'true');
      localStorage.setItem('userEmail', email);

      // 로그인 성공 시 홈으로 이동
      console.log('Navigating to /home...');
      navigate('/home');
    } catch (error) {
      console.error('Login error:', error);
      setError(t('login.서버와의_통신에_실패했습니다.'));
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        {/* 로고 및 타이틀 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-green-600 mb-2">
            Fitmealor
          </h1>
          <p className="text-gray-600">{t('login.건강한_식단_추천_서비스')}</p>
        </div>

        {/* 로그인 카드 */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">{t('login.로그인')}</h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* 이메일 입력 */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                {t('login.이메일')}
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition"
                placeholder="your@email.com"
                required
              />
            </div>

            {/* 비밀번호 입력 */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                {t('login.비밀번호')}
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition"
                placeholder="••••••••"
                required
              />
            </div>

            {/* 비밀번호 찾기 */}
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember"
                  type="checkbox"
                  className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                />
                <label htmlFor="remember" className="ml-2 block text-sm text-gray-700">
                  {t('login.로그인_상태_유지')}
                </label>
              </div>
              <a href="#" className="text-sm text-green-600 hover:text-green-700">
                {t('login.비밀번호_찾기')}
              </a>
            </div>

            {/* 로그인 버튼 */}
            <button
              type="submit"
              className="w-full bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition duration-200 shadow-md hover:shadow-lg"
            >
              {t('login.로그인')}
            </button>
          </form>

          {/* 소셜 로그인 */}
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">{t('login.또는')}</span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-3">
              <button className="flex items-center justify-center px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition">
                <span className="text-sm font-medium text-gray-700">Google</span>
              </button>
              <button className="flex items-center justify-center px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition">
                <span className="text-sm font-medium text-gray-700">Kakao</span>
              </button>
            </div>
          </div>

          {/* 회원가입 링크 */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              {t('login.계정이_없으신가요?')}{' '}
              <Link to="/register" className="text-green-600 hover:text-green-700 font-semibold">
                {t('login.회원가입')}
              </Link>
            </p>
          </div>
        </div>

        {/* 하단 텍스트 */}
        {i18n.language === 'en' ?
          <p className="mt-8 text-center text-sm text-gray-500">
            {t('login.로그인하시면')},{' '}
            {t('login.에_동의하는_것으로_간주됩니다.')}{' '}
            <a href="#" className="text-green-600 hover:text-green-700">
              {t('login.이용약관')}
            </a>
            {' '}and{' '}
            <a href="#" className="text-green-600 hover:text-green-700">
              {t('login.개인정보처리방침')}
            </a>.
          </p>
          :
          <p className="mt-8 text-center text-sm text-gray-500">
            {t('login.로그인하시면')}{' '}
            <a href="#" className="text-green-600 hover:text-green-700">
              {t('login.이용약관')}
            </a>
            과{' '}
            <a href="#" className="text-green-600 hover:text-green-700">
              {t('login.개인정보처리방침')}
            </a>
            {t('login.에_동의하는_것으로_간주됩니다.')}.
          </p>
        } 
      </div>
    </div>
  );
}
