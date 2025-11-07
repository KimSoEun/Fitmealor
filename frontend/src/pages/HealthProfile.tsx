import { useState, useEffect } from 'react';

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

  const bmi = calculateBMI(profile.weight, profile.height);
  const bmiCategory = getBMICategory(bmi);
  const bmiPosition = getBMIPosition(bmi);

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
        <h1 className="text-3xl font-bold text-gray-800 mb-8">건강 프로필</h1>

        {/* Profile Info Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">기본 정보</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-500">이름</p>
              <p className="text-lg font-medium">{profile.name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">나이</p>
              <p className="text-lg font-medium">{profile.age}세</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">성별</p>
              <p className="text-lg font-medium">{profile.gender}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">활동량</p>
              <p className="text-lg font-medium">{profile.activityLevel}</p>
            </div>
          </div>
        </div>

        {/* BMI Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-6">체질량 지수 (BMI)</h2>

          {/* Current BMI Display */}
          <div className="text-center mb-8">
            <div className="inline-flex items-baseline gap-2">
              <span className="text-6xl font-bold" style={{ color: bmiCategory.color }}>
                {bmi.toFixed(1)}
              </span>
              <span className="text-3xl text-gray-600">kg/m²</span>
            </div>
            <p className="mt-4 text-2xl font-semibold" style={{ color: bmiCategory.color }}>
              {bmiCategory.label}
            </p>
            <p className="mt-2 text-base text-gray-500">{bmiCategory.description}</p>
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
                  {category.label}
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
            <h2 className="text-xl font-semibold text-gray-800 mb-6">칼로리 및 영양소 목표</h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <p className="text-sm text-gray-600 mb-1">기초대사량 (BMR)</p>
                <p className="text-3xl font-bold text-gray-900">{tdeeInfo.bmr.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">kcal/일</p>
              </div>
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <p className="text-sm text-gray-600 mb-1">일일 소모 칼로리 (TDEE)</p>
                <p className="text-3xl font-bold text-indigo-600">{tdeeInfo.tdee.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">kcal/일</p>
              </div>
              <div className="bg-white rounded-lg p-4 shadow-sm">
                <p className="text-sm text-gray-600 mb-1">목표 칼로리</p>
                <p className="text-3xl font-bold text-purple-600">{tdeeInfo.adjusted_tdee.toLocaleString()}</p>
                <p className="text-xs text-gray-500 mt-1">kcal/일</p>
              </div>
            </div>

            <div className="bg-white rounded-lg p-5 shadow-sm">
              <h3 className="text-base font-semibold text-gray-800 mb-4">일일 영양소 목표</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">단백질</span>
                    <span className="text-lg font-bold text-red-600">{tdeeInfo.macro_targets.protein_g.toFixed(1)}g</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div className="bg-gradient-to-r from-red-400 to-red-600 h-3 rounded-full" style={{width: '100%'}}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">탄수화물</span>
                    <span className="text-lg font-bold text-green-600">{tdeeInfo.macro_targets.carbs_g.toFixed(1)}g</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div className="bg-gradient-to-r from-green-400 to-green-600 h-3 rounded-full" style={{width: '100%'}}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">지방</span>
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
          <h2 className="text-xl font-semibold text-gray-800 mb-4">체중 정보</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">현재 체중</p>
              <p className="text-3xl font-bold text-blue-600">{profile.weight} kg</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">목표 체중</p>
              <p className="text-3xl font-bold text-green-600">{profile.targetWeight} kg</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">키</p>
              <p className="text-3xl font-bold text-purple-600">{profile.height} cm</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">BMI</p>
              <p className="text-2xl font-bold mb-3" style={{ color: bmiCategory.color }}>
                {bmi.toFixed(1)} <span className="text-sm">({bmiCategory.label})</span>
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
            <p className="text-sm text-gray-600 mb-1">건강 목표</p>
            <p className="text-lg font-semibold text-gray-800">{profile.healthGoal}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
