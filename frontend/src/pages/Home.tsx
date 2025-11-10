import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

interface Meal {
  name: string;
  name_en?: string;
  name_kr?: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  category: string;
  score: number;
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

const Home: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [recommendations, setRecommendations] = useState<Meal[]>([]);
  const [tdeeInfo, setTdeeInfo] = useState<TDEEInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedMeals, setSelectedMeals] = useState<Meal[]>([]);
  const [currentNutrition, setCurrentNutrition] = useState({
    calories: 0,
    protein: 0,
    carbs: 0,
    fat: 0
  });
  const [selectedAllergies, setSelectedAllergies] = useState<string[]>([]);
  const [isAllergyDropdownOpen, setIsAllergyDropdownOpen] = useState(false);
  const [profileLoaded, setProfileLoaded] = useState(false);
  const [currentLang, setCurrentLang] = useState(i18n.language);

  // 22종 알러지 목록 (Language-aware)
  const allergyTranslations: Record<string, { ko: string; en: string }> = {
    'eggs': { ko: '난류(계란)', en: 'Eggs' },
    'milk': { ko: '우유', en: 'Milk' },
    'buckwheat': { ko: '메밀', en: 'Buckwheat' },
    'peanuts': { ko: '땅콩', en: 'Peanuts' },
    'soybeans': { ko: '대두', en: 'Soybeans' },
    'wheat': { ko: '밀', en: 'Wheat' },
    'mackerel': { ko: '고등어', en: 'Mackerel' },
    'crab': { ko: '게', en: 'Crab' },
    'shrimp': { ko: '새우', en: 'Shrimp' },
    'pork': { ko: '돼지고기', en: 'Pork' },
    'peach': { ko: '복숭아', en: 'Peach' },
    'tomato': { ko: '토마토', en: 'Tomato' },
    'sulfites': { ko: '아황산류', en: 'Sulfites' },
    'walnuts': { ko: '호두', en: 'Walnuts' },
    'chicken': { ko: '닭고기', en: 'Chicken' },
    'beef': { ko: '쇠고기', en: 'Beef' },
    'squid': { ko: '오징어', en: 'Squid' },
    'shellfish': { ko: '조개류', en: 'Shellfish' },
    'pine_nuts': { ko: '잣', en: 'Pine Nuts' },
    'crustaceans': { ko: '갑각류', en: 'Crustaceans' },
    'tree_nuts': { ko: '견과류', en: 'Tree Nuts' },
    'dairy': { ko: '유제품', en: 'Dairy' }
  };

  const allergyKeys = Object.keys(allergyTranslations);
  const allergyList = allergyKeys.map(key =>
    currentLang === 'en' ? allergyTranslations[key].en : allergyTranslations[key].ko
  );

  // 사용자 프로필 데이터
  const [userProfile, setUserProfile] = useState({
    name: '김건강',
    age: 25,
    gender: '남성',
    height: 175.0,
    weight: 70.0,
    targetWeight: 65.0,
    activityLevel: '활동적',
    healthGoal: '근육증가'
  });

  const calculateBMI = (weight: number, height: number): number => {
    const heightInMeters = height / 100;
    return weight / (heightInMeters * heightInMeters);
  };

  const bmi = calculateBMI(userProfile.weight, userProfile.height);

  const getDisplayName = (meal: Meal): string => {
    const displayName = currentLang === 'en'
      ? (meal.name_en || meal.name)
      : (meal.name_kr || meal.name);

    console.log(`getDisplayName: currentLang=${currentLang}, name=${meal.name}, name_en=${meal.name_en}, name_kr=${meal.name_kr}, returning=${displayName}`);

    return displayName;
  };

  // 식단 선택/해제 핸들러
  const handleMealToggle = (meal: Meal) => {
    const isSelected = selectedMeals.some(m => m.name === meal.name);

    if (isSelected) {
      // 선택 해제
      const newSelected = selectedMeals.filter(m => m.name !== meal.name);
      setSelectedMeals(newSelected);

      // 영양소 빼기
      setCurrentNutrition(prev => ({
        calories: Math.max(0, prev.calories - meal.calories),
        protein: Math.max(0, prev.protein - meal.protein_g),
        carbs: Math.max(0, prev.carbs - meal.carbs_g),
        fat: Math.max(0, prev.fat - meal.fat_g)
      }));
    } else {
      // 선택 추가
      setSelectedMeals([...selectedMeals, meal]);

      // 영양소 더하기
      setCurrentNutrition(prev => ({
        calories: prev.calories + meal.calories,
        protein: prev.protein + meal.protein_g,
        carbs: prev.carbs + meal.carbs_g,
        fat: prev.fat + meal.fat_g
      }));
    }
  };

  // 알러지 선택/해제 핸들러
  const handleAllergyToggle = (allergy: string) => {
    setSelectedAllergies(prev =>
      prev.includes(allergy)
        ? prev.filter(a => a !== allergy)
        : [...prev, allergy]
    );
  };

  // 드롭다운 외부 클릭 시 닫기
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (isAllergyDropdownOpen && !target.closest('.allergy-dropdown-container')) {
        setIsAllergyDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isAllergyDropdownOpen]);

  // Load user profile from API on component mount
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          console.log('No token found, using default profile');
          setProfileLoaded(true);  // 토큰이 없어도 기본값으로 진행
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
          console.error('Failed to load profile');
          setProfileLoaded(true);  // API 실패 시에도 기본값으로 진행
          return;
        }

        const data = await response.json();
        setUserProfile({
          name: data.name,
          age: data.age,
          gender: data.gender,
          height: data.height_cm,
          weight: data.weight_kg,
          targetWeight: data.target_weight_kg,
          activityLevel: data.activity_level,
          healthGoal: data.health_goal
        });
        setProfileLoaded(true);
      } catch (error) {
        console.error('Failed to load profile:', error);
        setProfileLoaded(true); // 에러가 나도 기본값으로 진행
      }
    };

    loadProfile();
  }, []);

  useEffect(() => {
    const handleLanguageChange = (lng: string) => {
      console.log('Language changed to:', lng);
      setCurrentLang(lng);
    };

    console.log('Setting up language change listener, initial language:', i18n.language);
    i18n.on('languageChanged', handleLanguageChange);

    return () => {
      i18n.off('languageChanged', handleLanguageChange);
    };
  }, [i18n]);

  useEffect(() => {
    // 프로필이 로드되지 않았으면 실행하지 않음
    if (!profileLoaded) {
      return;
    }

    // 추천 식단 가져오기
    const fetchRecommendations = async () => {
      try {
        // 사용자 프로필 데이터 사용
        const profileData = {
          user_id: 'demo_user',
          age: userProfile.age,
          gender: userProfile.gender,
          height_cm: userProfile.height,
          weight_kg: userProfile.weight,
          target_weight_kg: userProfile.targetWeight,
          activity_level: userProfile.activityLevel,
          health_goal: userProfile.healthGoal
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
          // TDEE 정보 저장
          setTdeeInfo(data.tdee_info);
          // 커피, 영양제, 건강기능식품, 음료 등 식사가 아닌 항목 필터링
          const excludedCategories = ['커피', '영양제', '건강기능식품', '음료', '차/음료', '보충제', '비타민'];
          const filteredMeals = data.recommendations.filter((meal: Meal & {category: string}) => {
            const category = meal.category.toLowerCase();
            const name = meal.name.toLowerCase();

            // 제외할 카테고리 체크
            for (const excluded of excludedCategories) {
              if (category.includes(excluded.toLowerCase())) {
                return false;
              }
            }

            // 이름에 커피, 비타민, 영양제가 포함되어 있으면 제외
            if (name.includes('커피') || name.includes('coffee') ||
                name.includes('비타민') || name.includes('vitamin') ||
                name.includes('영양제') || name.includes('supplement')) {
              return false;
            }

            return true;
          });

          setRecommendations(filteredMeals.slice(0, 6)); // 상위 6개만 표시
        }
      } catch (error) {
        console.error('Failed to fetch recommendations:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [profileLoaded]); // userProfile 대신 profileLoaded를 의존성으로 사용

  return (
    <div>
      {/* Hero Section */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">{t('welcome')}</h1>
        <p className="text-xl text-gray-600 mb-8">{t('tagline')}</p>
      </div>

      {/* 사용자 프로필 Section */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-900">
            {currentLang === 'en' ? 'My Profile' : '내 프로필'}
          </h2>
          <Link to="/health-profile" className="text-blue-600 hover:text-blue-700 font-medium text-sm">
            {currentLang === 'en' ? 'View Details →' : '자세히 보기 →'}
          </Link>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">{currentLang === 'en' ? 'Name' : '이름'}</p>
            <p className="text-lg font-semibold text-gray-900">{userProfile.name}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">{currentLang === 'en' ? 'Age' : '나이'}</p>
            <p className="text-lg font-semibold text-gray-900">
              {userProfile.age}{currentLang === 'en' ? ' years old' : '세'}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">{currentLang === 'en' ? 'Height / Weight' : '키 / 체중'}</p>
            <p className="text-lg font-semibold text-gray-900">{userProfile.height}cm / {userProfile.weight}kg</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">BMI</p>
            <p className="text-lg font-semibold text-blue-600">{bmi.toFixed(1)}</p>
          </div>
        </div>
        <div className="mt-4 flex gap-4">
          <div className="flex-1 bg-green-50 rounded-lg p-3">
            <p className="text-sm text-gray-600 mb-1">{currentLang === 'en' ? 'Health Goal' : '건강 목표'}</p>
            <p className="text-base font-semibold text-green-700">{userProfile.healthGoal}</p>
          </div>
          <div className="flex-1 bg-purple-50 rounded-lg p-3">
            <p className="text-sm text-gray-600 mb-1">{currentLang === 'en' ? 'Target Weight' : '목표 체중'}</p>
            <p className="text-base font-semibold text-purple-700">{userProfile.targetWeight}kg</p>
          </div>
        </div>
      </div>

      {/* TDEE 정보 Section */}
      {tdeeInfo && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            {currentLang === 'en' ? 'My Calorie and Nutrition Goals' : '나의 칼로리 및 영양소 목표'}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <p className="text-sm text-gray-600 mb-1">
                {currentLang === 'en' ? 'Basal Metabolic Rate (BMR)' : '기초대사량 (BMR)'}
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {tdeeInfo.bmr.toLocaleString()} <span className="text-xs text-gray-500">
                  {currentLang === 'en' ? 'kcal/day' : 'kcal/일'}
                </span>
              </p>
            </div>
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <p className="text-sm text-gray-600 mb-1">
                {currentLang === 'en' ? 'Total Daily Energy Expenditure (TDEE)' : '일일 소모 칼로리 (TDEE)'}
              </p>
              <p className="text-2xl font-bold text-blue-600">
                {tdeeInfo.tdee.toLocaleString()} <span className="text-xs text-gray-500">
                  {currentLang === 'en' ? 'kcal/day' : 'kcal/일'}
                </span>
              </p>
            </div>
            <div className="bg-white rounded-lg p-4 shadow-sm">
              <p className="text-sm text-gray-600 mb-1">
                {currentLang === 'en' ? 'Target Calories' : '목표 칼로리'}
              </p>
              <p className="text-2xl font-bold text-indigo-600">
                {tdeeInfo.adjusted_tdee.toLocaleString()} <span className="text-xs text-gray-500">
                  {currentLang === 'en' ? 'kcal/day' : 'kcal/일'} ({userProfile.healthGoal})
                </span>
              </p>
            </div>
          </div>

          {/* 애니메이션 게이지 바 섹션 */}
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <p className="text-lg font-semibold text-gray-800 mb-6">
              {currentLang === 'en' ? 'Daily Nutrition Goals' : '일일 영양소 목표'}
            </p>
            <div className="space-y-6">
              {/* 칼로리 게이지 */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    {currentLang === 'en' ? 'Calories' : '칼로리'}
                  </span>
                  <div className="text-right">
                    <span className="text-lg font-bold text-purple-600">{currentNutrition.calories.toFixed(0)}</span>
                    <span className="text-sm text-gray-500"> / {tdeeInfo.macro_targets.calories.toFixed(0)} kcal</span>
                  </div>
                </div>
                <div className="relative w-full h-6 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="absolute top-0 left-0 h-full bg-gradient-to-r from-purple-400 to-purple-600 rounded-full transition-all duration-700 ease-out"
                    style={{width: `${Math.min(100, (currentNutrition.calories / tdeeInfo.macro_targets.calories) * 100)}%`}}
                  >
                    <div className="absolute inset-0 bg-gradient-to-t from-white/20 to-transparent"></div>
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xs font-semibold text-white drop-shadow-md">
                      {((currentNutrition.calories / tdeeInfo.macro_targets.calories) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* 단백질 게이지 */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    {currentLang === 'en' ? 'Protein' : '단백질'}
                  </span>
                  <div className="text-right">
                    <span className="text-lg font-bold text-red-600">{currentNutrition.protein.toFixed(1)}</span>
                    <span className="text-sm text-gray-500"> / {tdeeInfo.macro_targets.protein_g.toFixed(1)} g</span>
                  </div>
                </div>
                <div className="relative w-full h-6 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="absolute top-0 left-0 h-full bg-gradient-to-r from-red-400 to-red-600 rounded-full transition-all duration-700 ease-out"
                    style={{width: `${Math.min(100, (currentNutrition.protein / tdeeInfo.macro_targets.protein_g) * 100)}%`}}
                  >
                    <div className="absolute inset-0 bg-gradient-to-t from-white/20 to-transparent"></div>
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xs font-semibold text-white drop-shadow-md">
                      {((currentNutrition.protein / tdeeInfo.macro_targets.protein_g) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* 탄수화물 게이지 */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    {currentLang === 'en' ? 'Carbs' : '탄수화물'}
                  </span>
                  <div className="text-right">
                    <span className="text-lg font-bold text-green-600">{currentNutrition.carbs.toFixed(1)}</span>
                    <span className="text-sm text-gray-500"> / {tdeeInfo.macro_targets.carbs_g.toFixed(1)} g</span>
                  </div>
                </div>
                <div className="relative w-full h-6 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="absolute top-0 left-0 h-full bg-gradient-to-r from-green-400 to-green-600 rounded-full transition-all duration-700 ease-out"
                    style={{width: `${Math.min(100, (currentNutrition.carbs / tdeeInfo.macro_targets.carbs_g) * 100)}%`}}
                  >
                    <div className="absolute inset-0 bg-gradient-to-t from-white/20 to-transparent"></div>
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xs font-semibold text-white drop-shadow-md">
                      {((currentNutrition.carbs / tdeeInfo.macro_targets.carbs_g) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* 지방 게이지 */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    {currentLang === 'en' ? 'Fat' : '지방'}
                  </span>
                  <div className="text-right">
                    <span className="text-lg font-bold text-yellow-600">{currentNutrition.fat.toFixed(1)}</span>
                    <span className="text-sm text-gray-500"> / {tdeeInfo.macro_targets.fat_g.toFixed(1)} g</span>
                  </div>
                </div>
                <div className="relative w-full h-6 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="absolute top-0 left-0 h-full bg-gradient-to-r from-yellow-400 to-yellow-600 rounded-full transition-all duration-700 ease-out"
                    style={{width: `${Math.min(100, (currentNutrition.fat / tdeeInfo.macro_targets.fat_g) * 100)}%`}}
                  >
                    <div className="absolute inset-0 bg-gradient-to-t from-white/20 to-transparent"></div>
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xs font-semibold text-white drop-shadow-md">
                      {((currentNutrition.fat / tdeeInfo.macro_targets.fat_g) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 추천 식단 Section */}
      <div>
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">
            {currentLang === 'en' ? 'Personalized Meal Recommendations' : '맞춤 추천 식단'}
          </h2>
          <Link to="/recommendations" className="text-blue-600 hover:text-blue-700 font-medium">
            {currentLang === 'en' ? 'View More →' : '더보기 →'}
          </Link>
        </div>

        {/* 알러지 필터 드롭다운 */}
        <div className="mb-6 relative allergy-dropdown-container">
          <button
            onClick={() => setIsAllergyDropdownOpen(!isAllergyDropdownOpen)}
            className="flex items-center gap-2 px-4 py-3 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm"
          >
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            <span className="font-medium text-gray-700">
              {currentLang === 'en' ? 'Allergy Filter' : '알러지 필터'}
              {selectedAllergies.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">
                  {selectedAllergies.length}
                </span>
              )}
            </span>
            <svg
              className={`w-4 h-4 text-gray-600 transition-transform ${isAllergyDropdownOpen ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* 드롭다운 메뉴 */}
          {isAllergyDropdownOpen && (
            <div className="absolute top-full left-0 mt-2 w-full md:w-96 bg-white border border-gray-200 rounded-lg shadow-xl z-10 max-h-96 overflow-y-auto">
              <div className="p-4">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-sm font-semibold text-gray-900">
                    {currentLang === 'en' ? 'Select Allergy Items' : '알러지 항목 선택'}
                  </h3>
                  {selectedAllergies.length > 0 && (
                    <button
                      onClick={() => setSelectedAllergies([])}
                      className="text-xs text-red-600 hover:text-red-700 font-medium"
                    >
                      {currentLang === 'en' ? 'Clear All' : '전체 해제'}
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {allergyList.map((allergy) => {
                    const isSelected = selectedAllergies.includes(allergy);
                    return (
                      <label
                        key={allergy}
                        className={`flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-red-50 border border-red-200'
                            : 'hover:bg-gray-50 border border-transparent'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleAllergyToggle(allergy)}
                          className="w-4 h-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                        />
                        <span className={`text-sm ${isSelected ? 'text-red-700 font-medium' : 'text-gray-700'}`}>
                          {allergy}
                        </span>
                      </label>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">
              {currentLang === 'en' ? 'Loading recommendations...' : '추천 식단을 불러오는 중...'}
            </p>
          </div>
        ) : recommendations.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recommendations.map((meal, index) => {
              const isSelected = selectedMeals.some(m => m.name === meal.name);
              return (
                <div
                  key={index}
                  className={`bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:scale-105 ${
                    isSelected ? 'ring-4 ring-green-500 bg-green-50' : 'hover:ring-2 hover:ring-gray-300'
                  }`}
                  onClick={() => handleMealToggle(meal)}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-semibold text-gray-900 flex-1">{getDisplayName(meal)}</h3>
                    {isSelected && (
                      <div className="flex-shrink-0 bg-green-500 rounded-full p-1">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                        </svg>
                      </div>
                    )}
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">{currentLang === 'en' ? 'Calories' : '칼로리'}</span>
                      <span className="font-medium text-gray-900">{meal.calories} kcal</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">{currentLang === 'en' ? 'Protein' : '단백질'}</span>
                      <span className="font-medium text-gray-900">{meal.protein_g.toFixed(1)} g</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">{currentLang === 'en' ? 'Carbs' : '탄수화물'}</span>
                      <span className="font-medium text-gray-900">{meal.carbs_g.toFixed(1)} g</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">{currentLang === 'en' ? 'Fat' : '지방'}</span>
                      <span className="font-medium text-gray-900">{meal.fat_g.toFixed(1)} g</span>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">{currentLang === 'en' ? 'Recommendation Score' : '추천 점수'}</span>
                      <span className="text-lg font-bold text-blue-600">{meal.score.toFixed(0)}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <p className="text-gray-600">추천 식단을 불러올 수 없습니다.</p>
            <Link to="/health-profile" className="text-blue-600 hover:text-blue-700 font-medium mt-2 inline-block">
              건강 프로필을 설정해주세요 →
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;
