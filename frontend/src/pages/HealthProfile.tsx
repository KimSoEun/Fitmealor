import { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';

interface BMICategory {
  label: string;
  range: [number, number];
  color: string;
  description: string;
}

interface TDEEInfo {
  bmr: number;
  tdee: number;
  adjusted_tdee: number;
  macro_targets: {
    protein_g: number;
    carbs_g: number;
    fat_g: number;
    calories: number;
  };
}

const bmiCategories: BMICategory[] = [
  { label: '저체중', range: [0, 18.5], color: '#60A5FA', description: 'Underweight' },
  { label: '정상', range: [18.5, 23], color: '#34D399', description: 'Normal' },
  { label: '과체중', range: [23, 25], color: '#FBBF24', description: 'Overweight' },
  { label: '경도비만', range: [25, 30], color: '#FB923C', description: 'Mild Obesity' },
  { label: '비만', range: [30, 35], color: '#F87171', description: 'Obesity' },
  { label: '고도비만', range: [35, 50], color: '#DC2626', description: 'Severe Obesity' }
];

const calculateBMI = (weight: number, height: number): number => {
  const heightInMeters = height / 100;
  return weight / (heightInMeters * heightInMeters);
};

const getBMICategory = (bmi: number): BMICategory => {
  return bmiCategories.find(cat => bmi >= cat.range[0] && bmi < cat.range[1]) || bmiCategories[bmiCategories.length - 1];
};

const getBMIPosition = (bmi: number): number => {
  const minBMI = 15;
  const maxBMI = 40;
  const clampedBMI = Math.max(minBMI, Math.min(maxBMI, bmi));
  return ((clampedBMI - minBMI) / (maxBMI - minBMI)) * 100;
};

export default function HealthProfile() {
  const [profile, setProfile] = useState({
    name: 'Dylan',
    age: 25,
    gender: '남성',
    height: 180,
    weight: 70,
    targetWeight: 65,
    activityLevel: '활동적',
    healthGoal: '근육증가'
  });

  const [editedProfile, setEditedProfile] = useState(profile);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { t, i18n } = useTranslation();

  const bmi = calculateBMI(profile.weight, profile.height);
  const bmiCategory = getBMICategory(bmi);
  const bmiPosition = getBMIPosition(bmi);

  // TDEE 계산 (useMemo로 즉시 계산)
  const tdeeInfo = useMemo((): TDEEInfo => {
    // 1. BMR 계산 (Mifflin-St Jeor 공식)
    const isMale = profile.gender === '남성' || profile.gender === 'Male';
    const bmr = isMale
      ? (10 * profile.weight) + (6.25 * profile.height) - (5 * profile.age) + 5
      : (10 * profile.weight) + (6.25 * profile.height) - (5 * profile.age) - 161;

    // 2. TDEE 계산 (활동 수준 계수 적용)
    const activityMultipliers: Record<string, number> = {
      '비활동적': 1.2,
      'Sedentary': 1.2,
      '가볍게 활동적': 1.375,
      'Lightly Active': 1.375,
      '활동적': 1.55,
      'Active': 1.55,
      '매우 활동적': 1.725,
      'Very Active': 1.725
    };
    const tdee = bmr * (activityMultipliers[profile.activityLevel] || 1.55);

    // 3. Adjusted TDEE (목표에 따른 조정)
    const goalMultipliers: Record<string, number> = {
      '체중감량': 0.8,
      'Weight Loss': 0.8,
      '체중유지': 1.0,
      'Maintain Weight': 1.0,
      '근육증가': 1.1,
      'Muscle Gain': 1.1
    };
    const adjusted_tdee = tdee * (goalMultipliers[profile.healthGoal] || 1.0);

    // 4. 영양소 목표 계산
    const macroRatios: Record<string, { protein: number; carbs: number; fat: number }> = {
      '체중감량': { protein: 0.40, carbs: 0.35, fat: 0.25 },
      'Weight Loss': { protein: 0.40, carbs: 0.35, fat: 0.25 },
      '체중유지': { protein: 0.25, carbs: 0.50, fat: 0.25 },
      'Maintain Weight': { protein: 0.25, carbs: 0.50, fat: 0.25 },
      '근육증가': { protein: 0.30, carbs: 0.50, fat: 0.20 },
      'Muscle Gain': { protein: 0.30, carbs: 0.50, fat: 0.20 }
    };
    const ratio = macroRatios[profile.healthGoal] || { protein: 0.25, carbs: 0.50, fat: 0.25 };

    const protein_g = (adjusted_tdee * ratio.protein) / 4; // 단백질 1g = 4kcal
    const carbs_g = (adjusted_tdee * ratio.carbs) / 4;     // 탄수화물 1g = 4kcal
    const fat_g = (adjusted_tdee * ratio.fat) / 9;         // 지방 1g = 9kcal

    return {
      bmr: Math.round(bmr),
      tdee: Math.round(tdee),
      adjusted_tdee: Math.round(adjusted_tdee),
      macro_targets: {
        protein_g: Math.round(protein_g),
        carbs_g: Math.round(carbs_g),
        fat_g: Math.round(fat_g),
        calories: Math.round(adjusted_tdee)
      }
    };
  }, [profile]);

  const handleCancel = () => {
    setEditedProfile(profile);
  };

  const handleSave = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        alert(t('healthprofile.로그인이_필요합니다.'));
        return;
      }

      const response = await fetch('http://localhost:8000/api/v1/auth/profile', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: editedProfile.name,
          age: editedProfile.age,
          gender: editedProfile.gender,
          height_cm: editedProfile.height,
          weight_kg: editedProfile.weight,
          target_weight_kg: editedProfile.targetWeight,
          activity_level: editedProfile.activityLevel,
          health_goal: editedProfile.healthGoal
        }),
      });

      if (!response.ok) {
        throw new Error(t('healthprofile.프로필_저장_실패'));
      }

      setProfile(editedProfile);
      // Set flag to trigger profile reload in Home page
      localStorage.setItem('profileUpdated', 'true');
      alert(t('healthprofile.프로필이_저장되었습니다!'));
    } catch (error) {
      console.error('Failed to save profile:', error);
      alert(t('healthprofile.프로필_저장에_실패했습니다.'));
    }
  };

  const handleInputChange = (field: string, value: string | number) => {
    setEditedProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // Load user profile from API on component mount
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setError(t('healthprofile.로그인이_필요합니다.'));
          setLoading(false);
          return;
        }

        const response = await fetch('http://localhost:8000/api/v1/auth/profile', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(t('healthprofile.프로필_로드_실패'));
        }

        const data = await response.json();
        const loadedProfile = {
          name: data.name,
          age: data.age,
          gender: data.gender,
          height: data.height_cm,
          weight: data.weight_kg,
          targetWeight: data.target_weight_kg,
          activityLevel: data.activity_level,
          healthGoal: data.health_goal
        };

        setProfile(loadedProfile);
        setEditedProfile(loadedProfile);
        setLoading(false);
      } catch (error) {
        console.error('Failed to load profile:', error);
        setError(t('healthprofile.프로필을_불러오는데_실패했습니다.'));
        setLoading(false);
      }
    };

    loadProfile();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">{t('healthprofile.건강_프로필')}</h1>
          <div className="flex gap-2">
            <button
              onClick={handleCancel}
              className="bg-gray-500 text-white px-6 py-2 rounded-lg font-semibold hover:bg-gray-600 transition duration-200"
            >
              {t('healthprofile.취소')}
            </button>
            <button
              onClick={handleSave}
              className="bg-green-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-green-700 transition duration-200"
            >
              {t('healthprofile.저장')}
            </button>
          </div>
        </div>

        {/* Profile Info Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">{t('healthprofile.기본_정보')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm text-gray-500 mb-2">{t('healthprofile.이름')}</label>
              <input
                type="text"
                value={editedProfile.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-2">{t('healthprofile.나이')}</label>
              <input
                type="number"
                value={editedProfile.age}
                onChange={(e) => handleInputChange('age', parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-2">{t('healthprofile.성별')}</label>
              <select
                value={editedProfile.gender}
                onChange={(e) => handleInputChange('gender', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="남성">{t('healthprofile.남성')}</option>
                <option value="여성">{t('healthprofile.여성')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-2">{t('healthprofile.키')} (cm)</label>
              <input
                type="number"
                value={editedProfile.height}
                onChange={(e) => handleInputChange('height', parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-2">{t('healthprofile.현재_체중')} (kg)</label>
              <input
                type="number"
                value={editedProfile.weight}
                onChange={(e) => handleInputChange('weight', parseFloat(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-2">{t('healthprofile.목표_체중')} (kg)</label>
              <input
                type="number"
                value={editedProfile.targetWeight}
                onChange={(e) => handleInputChange('targetWeight', parseFloat(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-2">{t('healthprofile.활동량')}</label>
              <select
                value={editedProfile.activityLevel}
                onChange={(e) => handleInputChange('activityLevel', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="비활동적">{t('healthprofile.비활동적')}</option>
                <option value="가볍게 활동적">{t('healthprofile.가볍게_활동적')}</option>
                <option value="활동적">{t('healthprofile.활동적')}</option>
                <option value="매우 활동적">{t('healthprofile.매우_활동적')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-2">{t('healthprofile.건강_목표')}</label>
              <select
                value={editedProfile.healthGoal}
                onChange={(e) => handleInputChange('healthGoal', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="체중감량">{t('healthprofile.체중감량')}</option>
                <option value="체중유지">{t('healthprofile.체중유지')}</option>
                <option value="근육증가">{t('healthprofile.근육증가')}</option>
              </select>
            </div>
          </div>
        </div>

        {/* BMI Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-6">{t('healthprofile.체질량_지수_(BMI)')}</h2>

          {/* Current BMI Display */}
          <div className="text-center mb-8">
            <div className="inline-flex items-baseline gap-2">
              <span className="text-6xl font-bold" style={{ color: bmiCategory.color }}>
                {bmi.toFixed(1)}
              </span>
              <span className="text-3xl text-gray-600">kg/m²</span>
            </div>
            <p className="mt-4 text-2xl font-semibold" style={{ color: bmiCategory.color }}>
              {i18n.language === 'en' ? bmiCategory.description : bmiCategory.label}
            </p>
          </div>

          {/* BMI Bar Chart */}
          <div className="mt-8">
            {/* BMI Range Labels */}
            <div className="flex justify-between text-xs text-gray-500 mb-2 px-1">
              <span>15</span>
              <span>18.5</span>
              <span>23</span>
              <span>25</span>
              <span>30</span>
              <span>35</span>
              <span>40</span>
            </div>

            {/* Color Bar */}
            <div className="relative h-12 flex rounded-lg overflow-hidden">
              {bmiCategories.map((category, index) => (
                <div
                  key={index}
                  className="flex-1 flex items-center justify-center text-xs font-medium text-white"
                  style={{ backgroundColor: category.color }}
                >
                  {i18n.language === 'en' ? category.description : category.label}
                </div>
              ))}
            </div>

            {/* Current BMI Indicator */}
            <div className="relative h-8">
              <div
                className="absolute top-0 transform -translate-x-1/2"
                style={{ left: `${bmiPosition}%` }}
              >
                <div className="flex flex-col items-center">
                  <div className="w-0 h-0 border-l-8 border-r-8 border-b-8 border-transparent border-b-gray-800"></div>
                  <div className="bg-gray-800 text-white text-xs font-bold px-2 py-1 rounded whitespace-nowrap">
                    {bmi.toFixed(1)}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* TDEE Information Card */}
        {tdeeInfo && (
          <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-6">{t('healthprofile.칼로리_및_영양소_목표')}</h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <p className="text-sm text-gray-600 mb-1">{t('healthprofile.기초대사량_(BMR)')}</p>
                <p className="text-3xl font-bold text-gray-900">{tdeeInfo.bmr.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">{t('healthprofile.kcal/일')}</p>
              </div>
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <p className="text-sm text-gray-600 mb-1">{t('healthprofile.일일_소모_칼로리_(TDEE)')}</p>
                <p className="text-3xl font-bold text-indigo-600">{tdeeInfo.tdee.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">{t('healthprofile.kcal/일')}</p>
              </div>
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <p className="text-sm text-gray-600 mb-1">{t('healthprofile.목표_칼로리')}</p>
                <p className="text-3xl font-bold text-purple-600">{tdeeInfo.adjusted_tdee.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">{t('healthprofile.kcal/일')}</p>
              </div>
            </div>

            <div className="bg-white rounded-lg p-5 shadow-sm">
              <h3 className="text-base font-semibold text-gray-800 mb-4">{t('healthprofile.일일_영양소_목표')}</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">{t('healthprofile.단백질')}</span>
                    <span className="text-lg font-bold text-red-600">{tdeeInfo.macro_targets.protein_g.toFixed(1)}g</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div className="bg-gradient-to-r from-red-400 to-red-600 h-3 rounded-full" style={{width: '100%'}}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">{t('healthprofile.탄수화물')}</span>
                    <span className="text-lg font-bold text-green-600">{tdeeInfo.macro_targets.carbs_g.toFixed(1)}g</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div className="bg-gradient-to-r from-green-400 to-green-600 h-3 rounded-full" style={{width: '100%'}}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">{t('healthprofile.지방')}</span>
                    <span className="text-lg font-bold text-yellow-600">{tdeeInfo.macro_targets.fat_g.toFixed(1)}g</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div className="bg-gradient-to-r from-yellow-400 to-yellow-600 h-3 rounded-full" style={{width: '100%'}}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Body Metrics Card */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">{t('healthprofile.체중_정보')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">{t('healthprofile.현재_체중')}</p>
              <p className="text-3xl font-bold text-blue-600">{profile.weight} kg</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">{t('healthprofile.목표_체중')}</p>
              <p className="text-3xl font-bold text-green-600">{profile.targetWeight} kg</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">{t('healthprofile.키')}</p>
              <p className="text-3xl font-bold text-purple-600">{profile.height} cm</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">BMI</p>
              <p className="text-2xl font-bold mb-3" style={{ color: bmiCategory.color }}>
                {bmi.toFixed(1)} <span className="text-sm">({i18n.language === 'en' ? bmiCategory.description : bmiCategory.label})</span>
              </p>
              {/* BMI Bar */}
              <div className="relative h-5 rounded overflow-hidden shadow-sm">
                <div className="flex h-full">
                  {bmiCategories.map((cat, idx) => (
                    <div key={idx} className="flex-1" style={{ backgroundColor: cat.color }}></div>
                  ))}
                </div>
                {/* Current BMI Indicator */}
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-black shadow"
                  style={{ left: `${bmiPosition}%`, transform: 'translateX(-50%)' }}
                ></div>
              </div>
            </div>
          </div>

          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">{t('healthprofile.건강_목표')}</p>
            <p className="text-lg font-semibold text-gray-800">{profile.healthGoal}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
