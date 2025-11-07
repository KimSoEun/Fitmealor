import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

export default function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    age: '',
    gender: '선택 안 함',
    height: '',
    weight: '',
    targetWeight: '',
    activityLevel: '활동적',
    healthGoal: '체중유지'
  });
  const [error, setError] = useState('');
  const [agreeToTerms, setAgreeToTerms] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // 유효성 검사
    if (!formData.name || !formData.email || !formData.password || !formData.confirmPassword ||
        !formData.age || !formData.height || !formData.weight || !formData.targetWeight) {
      setError('모든 필드를 입력해주세요.');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.');
      return;
    }

    if (formData.password.length < 8) {
      setError('비밀번호는 최소 8자 이상이어야 합니다.');
      return;
    }

    const age = parseInt(formData.age);
    if (age < 10 || age > 100) {
      setError('나이는 10세에서 100세 사이여야 합니다.');
      return;
    }

    const height = parseFloat(formData.height);
    if (height < 100 || height > 250) {
      setError('키는 100cm에서 250cm 사이여야 합니다.');
      return;
    }

    const weight = parseFloat(formData.weight);
    if (weight < 30 || weight > 200) {
      setError('체중은 30kg에서 200kg 사이여야 합니다.');
      return;
    }

    if (!agreeToTerms) {
      setError('이용약관 및 개인정보처리방침에 동의해주세요.');
      return;
    }

    try {
      // API 호출
      const response = await fetch('http://localhost:8000/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          name: formData.name,
          age: parseInt(formData.age),
          gender: formData.gender,
          height_cm: parseFloat(formData.height),
          weight_kg: parseFloat(formData.weight),
          target_weight_kg: parseFloat(formData.targetWeight),
          activity_level: formData.activityLevel,
          health_goal: formData.healthGoal,
          allergies: []
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || '회원가입에 실패했습니다.');
        return;
      }

      // 토큰 저장
      localStorage.setItem('token', data.token);
      localStorage.setItem('isLoggedIn', 'true');
      localStorage.setItem('userEmail', formData.email);

      // 회원가입 성공 시 홈으로 이동
      alert('회원가입이 완료되었습니다!');
      navigate('/home');
    } catch (error) {
      console.error('Register error:', error);
      setError('서버와의 통신에 실패했습니다.');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        {/* 로고 및 타이틀 */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-green-600 mb-2">
            Fitmealor
          </h1>
          <p className="text-gray-600">건강한 식단 추천 서비스</p>
        </div>

        {/* 회원가입 카드 */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">회원가입</h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* 이름 입력 */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                이름
              </label>
              <input
                id="name"
                name="name"
                type="text"
                value={formData.name}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition"
                placeholder="홍길동"
                required
              />
            </div>

            {/* 이메일 입력 */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                이메일
              </label>
              <input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition"
                placeholder="your@email.com"
                required
              />
            </div>

            {/* 비밀번호 입력 */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                비밀번호
              </label>
              <input
                id="password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition"
                placeholder="••••••••"
                required
              />
              <p className="mt-1 text-xs text-gray-500">최소 8자 이상 입력해주세요</p>
            </div>

            {/* 비밀번호 확인 입력 */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                비밀번호 확인
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                value={formData.confirmPassword}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition"
                placeholder="••••••••"
                required
              />
            </div>

            {/* 구분선 */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500 font-medium">건강 정보</span>
              </div>
            </div>

            {/* 나이와 성별 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="age" className="block text-sm font-medium text-gray-700 mb-2">
                  나이
                </label>
                <input
                  id="age"
                  name="age"
                  type="number"
                  value={formData.age}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition"
                  placeholder="25"
                  required
                  min="10"
                  max="100"
                />
              </div>
              <div>
                <label htmlFor="gender" className="block text-sm font-medium text-gray-700 mb-2">
                  성별
                </label>
                <select
                  id="gender"
                  name="gender"
                  value={formData.gender}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition bg-white"
                  required
                >
                  <option value="여성">여성</option>
                  <option value="남성">남성</option>
                  <option value="선택 안 함">선택 안 함</option>
                </select>
              </div>
            </div>

            {/* 키와 체중 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="height" className="block text-sm font-medium text-gray-700 mb-2">
                  키 (cm)
                </label>
                <input
                  id="height"
                  name="height"
                  type="number"
                  step="0.1"
                  value={formData.height}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition"
                  placeholder="175"
                  required
                  min="100"
                  max="250"
                />
              </div>
              <div>
                <label htmlFor="weight" className="block text-sm font-medium text-gray-700 mb-2">
                  체중 (kg)
                </label>
                <input
                  id="weight"
                  name="weight"
                  type="number"
                  step="0.1"
                  value={formData.weight}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition"
                  placeholder="70"
                  required
                  min="30"
                  max="200"
                />
              </div>
            </div>

            {/* 목표 체중 */}
            <div>
              <label htmlFor="targetWeight" className="block text-sm font-medium text-gray-700 mb-2">
                목표 체중 (kg)
              </label>
              <input
                id="targetWeight"
                name="targetWeight"
                type="number"
                step="0.1"
                value={formData.targetWeight}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition"
                placeholder="65"
                required
                min="30"
                max="200"
              />
            </div>

            {/* 활동 수준 */}
            <div>
              <label htmlFor="activityLevel" className="block text-sm font-medium text-gray-700 mb-2">
                활동 수준
              </label>
              <select
                id="activityLevel"
                name="activityLevel"
                value={formData.activityLevel}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition bg-white"
                required
              >
                <option value="비활동적">비활동적 (거의 운동 안 함)</option>
                <option value="가볍게 활동적">가볍게 활동적 (주 1-3회 운동)</option>
                <option value="활동적">활동적 (주 3-5회 운동)</option>
                <option value="매우 활동적">매우 활동적 (주 6-7회 운동)</option>
              </select>
            </div>

            {/* 건강 목표 */}
            <div>
              <label htmlFor="healthGoal" className="block text-sm font-medium text-gray-700 mb-2">
                건강 목표
              </label>
              <select
                id="healthGoal"
                name="healthGoal"
                value={formData.healthGoal}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition bg-white"
                required
              >
                <option value="체중감량">체중감량</option>
                <option value="체중유지">체중유지</option>
                <option value="근육증가">근육증가</option>
              </select>
            </div>

            {/* 약관 동의 */}
            <div className="flex items-start">
              <input
                id="terms"
                type="checkbox"
                checked={agreeToTerms}
                onChange={(e) => setAgreeToTerms(e.target.checked)}
                className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded mt-1"
              />
              <label htmlFor="terms" className="ml-2 block text-sm text-gray-700">
                <a href="#" className="text-green-600 hover:text-green-700">이용약관</a>
                {' '}및{' '}
                <a href="#" className="text-green-600 hover:text-green-700">개인정보처리방침</a>
                에 동의합니다
              </label>
            </div>

            {/* 회원가입 버튼 */}
            <button
              type="submit"
              className="w-full bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition duration-200 shadow-md hover:shadow-lg"
            >
              회원가입
            </button>
          </form>

          {/* 소셜 회원가입 */}
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">또는</span>
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

          {/* 로그인 링크 */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              이미 계정이 있으신가요?{' '}
              <Link to="/login" className="text-green-600 hover:text-green-700 font-semibold">
                로그인
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
