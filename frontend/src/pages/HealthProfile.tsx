import { useState, useEffect } from 'react';
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
    name: '김건강',
    age: 25,
    gender: '남성',
    height: 175,
    weight: 70,
    targetWeight: 65,
    activityLevel: '활동적',
    healthGoal: '근육증가'
  });

  const [tdeeInfo, setTdeeInfo] = useState<TDEEInfo | null>(null);
  const [editedProfile, setEditedProfile] = useState(profile);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { t, i18n } = useTranslation();
  const [currentLang, setCurrentLang] = useState(i18n.language);

  const bmi = calculateBMI(profile.weight, profile.height);
  const bmiCategory = getBMICategory(bmi);
  const bmiPosition = getBMIPosition(bmi);

  const handleCancel = () => {
    setEditedProfile(profile);
  };

  const handleSave = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        alert('로그인이 필요합니다.');
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
        throw new Error('프로필 저장 실패');
      }

      setProfile(editedProfile);
      alert('프로필이 저장되었습니다!');
    } catch (error) {
      console.error('Failed to save profile:', error);
      alert('프로필 저장에 실패했습니다.');
    }
  };

  const handleInputChange = (field: string, value: string | number) => {
    setEditedProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };

  useEffect(() => {
    const handleLanguageChange = (lng: string) => {
      setCurrentLang(lng);
    };

    i18n.on('languageChanged', handleLanguageChange);

    return () => {
      i18n.off('languageChanged', handleLanguageChange);
    };
  }, [i18n]);

  // Load user profile from API on component mount
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setError('로그인이 필요합니다.');
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
          throw new Error('프로필 로드 실패');
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
        setError('프로필을 불러오는데 실패했습니다.');
        setLoading(false);
      }
    };

    loadProfile();
  }, []);

  useEffect(() => {
    const fetchTDEE = async () => {
      try {
        const profileData = {
          user_id: 'demo_user',
          age: profile.age,
          gender: profile.gender,
          height_cm: profile.height,
          weight_kg: profile.weight,
          target_weight_kg: profile.targetWeight,
          activity_level: profile.activityLevel,
          health_goal: profile.healthGoal
        };

        const response = await fetch('http://localhost:8000/api/v1/recommendations/recommend', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(profileData)
        });

        if (response.ok) {
          const data = await response.json();
          setTdeeInfo(data.tdee_info);
        }
      } catch (error) {
        console.error('Failed to fetch TDEE info:', error);
      }
    };

    fetchTDEE();
  }, [profile]);

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">{currentLang === 'en' ? 'Health Profile' : '건강 프로필'}</h1>
          <div className="flex gap-2">
            <button
              onClick={handleCancel}
              className="bg-gray-500 text-white px-6 py-2 rounded-lg font-semibold hover:bg-gray-600 transition duration-200"
            >
              {currentLang === 'en' ? 'Cancel' : '취소'}
            </button>
            <button
              onClick={handleSave}
              className="bg-green-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-green-700 transition duration-200"
            >
              {currentLang === 'en' ? 'Save' : '저장'}
            </button>
          </div>
        </div>

        {/* Profile Info Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">{currentLang === 'en' ? 'Personal Details' : '기본 정보'}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm text-gray-500 mb-2">{currentLang === 'en' ? 'Name' : '이름'}</label>
              <input
                type="text"
                value={editedProfile.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-2">{currentLang === 'en' ? 'Age' : '나이'}</label>
              <input
                type="number"
                value={editedProfile.age}
                onChange={(e) => handleInputChange('age', parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-2">{currentLang === 'en' ? 'Sex' : '성별'}</label>
              <select
                value={editedProfile.gender}
                onChange={(e) => handleInputChange('gender', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="남성">{currentLang === 'en' ? 'Male' : '남성'}</option>
                <option value="여성">{currentLang === 'en' ? 'Female' : '여성'}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-2">{currentLang === 'en' ? 'Height' : '키'} (cm)</label>
              <input
                type="number"
                value={editedProfile.height}
                onChange={(e) => handleInputChange('height', parseInt(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-2">{currentLang === 'en' ? 'Current Weight' : '현재 체중'} (kg)</label>
              <input
                type="number"
                value={editedProfile.weight}
                onChange={(e) => handleInputChange('weight', parseFloat(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-2">{currentLang === 'en' ? 'Goal Weight' : '목표 체중'} (kg)</label>
              <input
                type="number"
                value={editedProfile.targetWeight}
                onChange={(e) => handleInputChange('targetWeight', parseFloat(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-2">{currentLang === 'en' ? 'Activity Level' : '활동량'}</label>
              <select
                value={editedProfile.activityLevel}
                onChange={(e) => handleInputChange('activityLevel', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value={currentLang === 'en' ? 'sedentary' : '비활동적'}>{currentLang === 'en' ? 'Sedentary' : '비활동적'}</option>
                <option value={currentLang === 'en' ? 'lignt' : '가볍게 활동적'}>{currentLang === 'en' ? 'Light' : '가볍게 활동적'}</option>
                <option value={currentLang === 'en' ? 'active' : '활동적'}>{currentLang === 'en' ? 'Active' : '활동적'}</option>
                <option value={currentLang === 'en' ? 'very_active' : '매우 활동적'}>{currentLang === 'en' ? 'Very Active' : '매우 활동적'}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-500 mb-2">{currentLang === 'en' ? 'Health Goal' : '건강 목표'}</label>
              <select
                value={editedProfile.healthGoal}
                onChange={(e) => handleInputChange('healthGoal', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value={currentLang === 'en' ? 'wight_loss' : '체중감량'}>{currentLang === 'en' ? 'Weight Loss' : '체중감량'}</option>
                <option value={currentLang === 'en' ? 'maintain_weight' : '체중유지'}>{currentLang === 'en' ? 'Maintain Weight' : '체중유지'}</option>
                <option value={currentLang === 'en' ? 'muscle_gain' : '근육증가'}>{currentLang === 'en' ? 'Muscle Gain' : '근육증가'}</option>
              </select>
            </div>
          </div>
        </div>

        {/* BMI Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-6">{currentLang === 'en' ? 'BMI' : '체질량 지수 (BMI)'}</h2>

          {/* Current BMI Display */}
          <div className="text-center mb-8">
            <div className="inline-flex items-baseline gap-2">
              <span className="text-6xl font-bold" style={{ color: bmiCategory.color }}>
                {bmi.toFixed(1)}
              </span>
              <span className="text-3xl text-gray-600">kg/m²</span>
            </div>
            <p className="mt-4 text-2xl font-semibold" style={{ color: bmiCategory.color }}>
              {currentLang === 'en' ? bmiCategory.description : bmiCategory.label}
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
                  {currentLang === 'en' ? category.description : category.label}
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
            <h2 className="text-xl font-semibold text-gray-800 mb-6">{currentLang === 'en' ? 'Calorie & Nutrient Goals' : '칼로리 및 영양소 목표'}</h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <p className="text-sm text-gray-600 mb-1">{currentLang === 'en' ? 'Basal Metabolic Rate (BMR)' : '기초대사량 (BMR)'}</p>
                <p className="text-3xl font-bold text-gray-900">{tdeeInfo.bmr.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">{currentLang === 'en' ? 'kcal/day' : 'kcal/일'}</p>
              </div>
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <p className="text-sm text-gray-600 mb-1">{currentLang === 'en' ? 'Total Daily Energy Expenditure (TDEE)' : '일일 소모 칼로리 (TDEE)'}</p>
                <p className="text-3xl font-bold text-indigo-600">{tdeeInfo.tdee.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">{currentLang === 'en' ? 'kcal/day' : 'kcal/일'}</p>
              </div>
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <p className="text-sm text-gray-600 mb-1">{currentLang === 'en' ? 'Target Calories' : '목표 칼로리'}</p>
                <p className="text-3xl font-bold text-purple-600">{tdeeInfo.adjusted_tdee.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">{currentLang === 'en' ? 'kcal/day' : 'kcal/일'}</p>
              </div>
            </div>

            <div className="bg-white rounded-lg p-5 shadow-sm">
              <h3 className="text-base font-semibold text-gray-800 mb-4">{currentLang === 'en' ? 'Daily Nutrient Goals' : '일일 영양소 목표'}</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">{currentLang === 'en' ? 'Protein' : '단백질'}</span>
                    <span className="text-lg font-bold text-red-600">{tdeeInfo.macro_targets.protein_g.toFixed(1)}g</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div className="bg-gradient-to-r from-red-400 to-red-600 h-3 rounded-full" style={{width: '100%'}}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">{currentLang === 'en' ? 'Carbohydrates' : '탄수화물'}</span>
                    <span className="text-lg font-bold text-green-600">{tdeeInfo.macro_targets.carbs_g.toFixed(1)}g</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div className="bg-gradient-to-r from-green-400 to-green-600 h-3 rounded-full" style={{width: '100%'}}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">{currentLang === 'en' ? 'Fat' : '지방'}</span>
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
          <h2 className="text-xl font-semibold text-gray-800 mb-4">{currentLang === 'en' ? 'Body Metrics' : '체중 정보'}</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">{currentLang === 'en' ? 'Current Weight' : '현재 체중'}</p>
              <p className="text-3xl font-bold text-blue-600">{profile.weight} kg</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">{currentLang === 'en' ? 'Goal Weight' : '목표 체중'}</p>
              <p className="text-3xl font-bold text-green-600">{profile.targetWeight} kg</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">{currentLang === 'en' ? 'Height' : '키'}</p>
              <p className="text-3xl font-bold text-purple-600">{profile.height} cm</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">BMI</p>
              <p className="text-2xl font-bold mb-3" style={{ color: bmiCategory.color }}>
                {bmi.toFixed(1)} <span className="text-sm">({currentLang === 'en' ? bmiCategory.description : bmiCategory.label})</span>
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
            <p className="text-sm text-gray-600 mb-1">{currentLang === 'en' ? 'Health Goal' : '건강 목표'}</p>
            <p className="text-lg font-semibold text-gray-800">{profile.healthGoal}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
