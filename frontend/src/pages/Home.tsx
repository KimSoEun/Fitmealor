import React, { useState, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import API_BASE_URL from '../config';

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

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface MealFilters {
  maxCalories?: number;
  minProtein?: number;
  maxCarbs?: number;
  maxFat?: number;
  excludeIngredients?: string[];
  includeIngredients?: string[];
  preferHighProtein?: boolean;
  preferLowCarb?: boolean;
}

const Home: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [recommendations, setRecommendations] = useState<Meal[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMeals, setSelectedMeals] = useState<Meal[]>([]);
  const [currentNutrition, setCurrentNutrition] = useState({
    calories: 0,
    protein: 0,
    carbs: 0,
    fat: 0
  });
  const [selectedAllergies, setSelectedAllergies] = useState<string[]>([]); // Store allergy keys (e.g., 'eggs', 'milk')
  const [isAllergyDropdownOpen, setIsAllergyDropdownOpen] = useState(false);
  const [profileLoaded, setProfileLoaded] = useState(false);
  const [currentLang, setCurrentLang] = useState(i18n.language);
  const [favoritedMeals, setFavoritedMeals] = useState<Set<string>>(new Set());

  // Chatbot states
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [userInput, setUserInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [appliedFilters, setAppliedFilters] = useState<MealFilters | null>(null);
  const [isChatExpanded, setIsChatExpanded] = useState(false);

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
    'oysters': { ko: '굴', en: 'Oysters' },
    'abalone': { ko: '전복', en: 'Abalone' },
    'mussels': { ko: '홍합', en: 'Mussels' }
  };

  const allergyKeys = Object.keys(allergyTranslations);

  // Get display name for an allergy key
  const getAllergyDisplayName = (key: string): string => {
    return currentLang === 'en' ? allergyTranslations[key].en : allergyTranslations[key].ko;
  };

  // Reverse map: Convert allergen display value (from DB) to key
  const mapAllergenValueToKey = (allergenValue: string): string | null => {
    for (const [key, translations] of Object.entries(allergyTranslations)) {
      if (translations.ko === allergenValue || translations.en === allergenValue) {
        return key;
      }
    }
    return null;
  };

  // Health goal translations
  const healthGoalTranslations: Record<string, { ko: string; en: string }> = {
    '체중감량': { ko: '체중감량', en: 'Weight Loss' },
    '체중유지': { ko: '체중유지', en: 'Maintain Weight' },
    '근육증가': { ko: '근육증가', en: 'Muscle Gain' }
  };

  // Gender translations
  const genderTranslations: Record<string, { ko: string; en: string }> = {
    '남성': { ko: '남성', en: 'Male' },
    '여성': { ko: '여성', en: 'Female' }
  };

  // Activity level translations
  const activityLevelTranslations: Record<string, { ko: string; en: string }> = {
    '비활동적': { ko: '비활동적', en: 'Sedentary' },
    '가볍게 활동적': { ko: '가볍게 활동적', en: 'Lightly Active' },
    '활동적': { ko: '활동적', en: 'Active' },
    '매우 활동적': { ko: '매우 활동적', en: 'Very Active' }
  };

  // Get translated health goal
  const getHealthGoalDisplay = (goal: string): string => {
    const translation = healthGoalTranslations[goal];
    if (!translation) return goal;
    return currentLang === 'en' ? translation.en : translation.ko;
  };

  // Get translated gender
  const getGenderDisplay = (gender: string): string => {
    const translation = genderTranslations[gender];
    if (!translation) return gender;
    return currentLang === 'en' ? translation.en : translation.ko;
  };

  // Get translated activity level
  const getActivityLevelDisplay = (level: string): string => {
    const translation = activityLevelTranslations[level];
    if (!translation) return level;
    return currentLang === 'en' ? translation.en : translation.ko;
  };

  // 사용자 프로필 데이터
  const [userProfile, setUserProfile] = useState({
    name: 'Dylan',
    age: 25,
    gender: '남성',
    height: 180.0,
    weight: 70.0,
    targetWeight: 75.0,
    activityLevel: '활동적',
    healthGoal: '근육증가'
  });

  const calculateBMI = (weight: number, height: number): number => {
    const heightInMeters = height / 100;
    return weight / (heightInMeters * heightInMeters);
  };

  const bmi = calculateBMI(userProfile.weight, userProfile.height);

  // TDEE 계산 (useMemo로 즉시 계산)
  const tdeeInfo = useMemo((): TDEEInfo => {
    // 1. BMR 계산 (Mifflin-St Jeor 공식)
    const isMale = userProfile.gender === '남성' || userProfile.gender === 'Male';
    const bmr = isMale
      ? (10 * userProfile.weight) + (6.25 * userProfile.height) - (5 * userProfile.age) + 5
      : (10 * userProfile.weight) + (6.25 * userProfile.height) - (5 * userProfile.age) - 161;

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
    const tdee = bmr * (activityMultipliers[userProfile.activityLevel] || 1.55);

    // 3. Adjusted TDEE (목표에 따른 조정)
    const goalMultipliers: Record<string, number> = {
      '체중감량': 0.8,
      'Weight Loss': 0.8,
      '체중유지': 1.0,
      'Maintain Weight': 1.0,
      '근육증가': 1.1,
      'Muscle Gain': 1.1
    };
    const adjusted_tdee = tdee * (goalMultipliers[userProfile.healthGoal] || 1.0);

    // 4. 영양소 목표 계산
    const macroRatios: Record<string, { protein: number; carbs: number; fat: number }> = {
      '체중감량': { protein: 0.40, carbs: 0.35, fat: 0.25 },
      'Weight Loss': { protein: 0.40, carbs: 0.35, fat: 0.25 },
      '체중유지': { protein: 0.25, carbs: 0.50, fat: 0.25 },
      'Maintain Weight': { protein: 0.25, carbs: 0.50, fat: 0.25 },
      '근육증가': { protein: 0.30, carbs: 0.50, fat: 0.20 },
      'Muscle Gain': { protein: 0.30, carbs: 0.50, fat: 0.20 }
    };
    const ratio = macroRatios[userProfile.healthGoal] || { protein: 0.25, carbs: 0.50, fat: 0.25 };

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
  }, [userProfile]);

  const getDisplayName = (meal: Meal): string => {
    if (currentLang === 'en') {
      // English: Use translated English name with underscores removed
      const englishName = meal.name_en || meal.name;
      return englishName.replace(/_/g, ' ');
    } else {
      // Korean: Use Korean translation if available, otherwise use original name
      const koreanName = meal.name_kr || meal.name;
      return koreanName.replace(/_/g, ' ');
    }
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

  // 알러지 선택/해제 핸들러 (key-based)
  const handleAllergyToggle = (allergyKey: string) => {
    setSelectedAllergies(prev =>
      prev.includes(allergyKey)
        ? prev.filter(a => a !== allergyKey)
        : [...prev, allergyKey]
    );
  };

  // Fetch user's favorites from backend
  const fetchFavorites = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch(`${API_BASE_URL}/api/v1/favorites/list`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.favorites) {
          const favoriteCodes = new Set(data.favorites.map((f: any) => f.meal_code));
          setFavoritedMeals(favoriteCodes);
        }
      }
    } catch (error) {
      console.error('Failed to fetch favorites:', error);
    }
  };

  // Toggle favorite status for a meal
  const handleToggleFavorite = async (meal: Meal, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering meal selection

    const token = localStorage.getItem('token');
    if (!token) {
      alert(currentLang === 'en' ? 'Please login first' : '로그인이 필요합니다');
      return;
    }

    const mealCode = meal.name;
    const isFavorited = favoritedMeals.has(mealCode);

    try {
      if (isFavorited) {
        // Remove from favorites
        const response = await fetch(`${API_BASE_URL}/api/v1/favorites/remove/${mealCode}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          setFavoritedMeals(prev => {
            const newSet = new Set(prev);
            newSet.delete(mealCode);
            return newSet;
          });
        } else {
          throw new Error('Failed to remove favorite');
        }
      } else {
        // Add to favorites
        const response = await fetch(`${API_BASE_URL}/api/v1/favorites/add`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            meal_code: mealCode,
            meal_name_ko: meal.name_kr || meal.name,
            meal_name_en: meal.name_en,
            calories: Math.round(meal.calories),
            carbohydrates: Math.round(meal.carbs_g),
            protein: Math.round(meal.protein_g),
            fat: Math.round(meal.fat_g),
            sodium: null
          })
        });

        if (response.ok) {
          setFavoritedMeals(prev => new Set(prev).add(mealCode));
        } else {
          throw new Error('Failed to add favorite');
        }
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
      alert(currentLang === 'en' ? 'Failed to update favorite' : '즐겨찾기 업데이트에 실패했습니다');
    }
  };

  // Chatbot handler - Process user input and extract filters
  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userInput.trim() || isProcessing) return;

    const userMessage = userInput.trim();
    setUserInput('');
    setIsProcessing(true);

    // Add user message to chat
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    try {
      console.log('=== Chat Request Started ===');
      console.log('User message:', userMessage);
      console.log('Current language:', currentLang);

      // Call backend chatbot API
      const response = await fetch('http://localhost:8000/api/v1/chatbot/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          language: currentLang
        }),
      });

      console.log('Backend API response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('Backend API error response:', errorData);
        throw new Error(errorData.detail || `API request failed: ${response.status}`);
      }

      const data = await response.json();
      console.log('Backend API response data:', data);

      // Add assistant message to chat
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.message }]);

      // Apply filters if present
      if (data.filters) {
        console.log('Applying filters:', data.filters);
        setAppliedFilters(data.filters);
      }

      console.log('=== Chat Request Completed ===');

    } catch (error) {
      console.error('=== Chat Error ===');
      console.error('Error type:', error instanceof Error ? error.constructor.name : typeof error);
      console.error('Error message:', error instanceof Error ? error.message : String(error));
      console.error('Error stack:', error instanceof Error ? error.stack : 'No stack trace');

      const errorMessage = currentLang === 'en'
        ? `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`
        : `죄송합니다. 오류가 발생했습니다: ${error instanceof Error ? error.message : '알 수 없는 오류'}`;
      setChatMessages(prev => [...prev, { role: 'assistant', content: errorMessage }]);
    } finally {
      setIsProcessing(false);
    }
  };

  // Clear chat and filters
  const handleClearChat = () => {
    setChatMessages([]);
    setAppliedFilters(null);
    setUserInput('');
  };

  // Reset chat filters on page load (not on navigation)
  useEffect(() => {
    // Clear filters when component first mounts (page refresh)
    const hasLoadedBefore = sessionStorage.getItem('homePageLoaded');
    if (!hasLoadedBefore) {
      // First time loading this page in this session
      setAppliedFilters(null);
      setChatMessages([]);
      sessionStorage.setItem('homePageLoaded', 'true');
    }

    // Clear the flag when the page is about to unload (refresh or close)
    const handleBeforeUnload = () => {
      sessionStorage.removeItem('homePageLoaded');
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

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

  // Fetch recommendations function (extracted for reuse)
  const fetchRecommendations = async (profile: typeof userProfile) => {
    try {
      setLoading(true);
      console.log('Fetching recommendations with profile:', profile);

      // Validate that all required fields are present and not null/undefined
      if (!profile.age || !profile.gender || !profile.height ||
          !profile.weight || !profile.targetWeight ||
          !profile.activityLevel || !profile.healthGoal) {
        console.error('Profile is missing required fields:', profile);
        setRecommendations([]);
        setLoading(false);
        return;
      }

      // 사용자 프로필 데이터 사용
      const profileData = {
        user_id: 'demo_user',
        age: Number(profile.age),
        gender: profile.gender,
        height_cm: Number(profile.height),
        weight_kg: Number(profile.weight),
        target_weight_kg: Number(profile.targetWeight),
        activity_level: profile.activityLevel,
        health_goal: profile.healthGoal,
        allergies: selectedAllergies,
        dietary_restrictions: []
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
        // 커피, 영양제, 건강기능식품, 음료 등 식사가 아닌 항목 필터링
        const excludedCategories = ['커피', '영양제', '건강기능식품', '음료', '차/음료', '보충제', '비타민'];
        let filteredMeals = data.recommendations.filter((meal: Meal & {category: string}) => {
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

        // Apply chatbot filters if any
        if (appliedFilters) {
          filteredMeals = filteredMeals.filter((meal: Meal) => {
            // Max calories filter
            if (appliedFilters.maxCalories && meal.calories > appliedFilters.maxCalories) {
              return false;
            }

            // Min protein filter
            if (appliedFilters.minProtein && meal.protein_g < appliedFilters.minProtein) {
              return false;
            }

            // Max carbs filter
            if (appliedFilters.maxCarbs && meal.carbs_g > appliedFilters.maxCarbs) {
              return false;
            }

            // Max fat filter
            if (appliedFilters.maxFat && meal.fat_g > appliedFilters.maxFat) {
              return false;
            }

            // Exclude ingredients filter
            if (appliedFilters.excludeIngredients && appliedFilters.excludeIngredients.length > 0) {
              const mealName = meal.name.toLowerCase();
              for (const ingredient of appliedFilters.excludeIngredients) {
                if (mealName.includes(ingredient.toLowerCase())) {
                  return false;
                }
              }
            }

            // Include ingredients filter (at least one must match)
            if (appliedFilters.includeIngredients && appliedFilters.includeIngredients.length > 0) {
              const mealName = meal.name.toLowerCase();
              const hasMatch = appliedFilters.includeIngredients.some(ingredient =>
                mealName.includes(ingredient.toLowerCase())
              );
              if (!hasMatch) {
                return false;
              }
            }

            return true;
          });

          // Sort by preferences
          if (appliedFilters.preferHighProtein) {
            filteredMeals.sort((a, b) => b.protein_g - a.protein_g);
          } else if (appliedFilters.preferLowCarb) {
            filteredMeals.sort((a, b) => a.carbs_g - b.carbs_g);
          }
        }

        setRecommendations(filteredMeals.slice(0, 12)); // 상위 12개만 표시
      }
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  // Load user profile from API on component mount
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const token = localStorage.getItem('token');
        console.log('Token from localStorage:', token ? `${token.substring(0, 20)}...` : 'null');

        let loadedProfile = null;

        // Try authenticated profile first if token exists
        if (token) {
          try {
            console.log('Attempting authenticated profile request');
            const response = await fetch('http://localhost:8000/api/v1/auth/profile', {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
              },
            });

            console.log('Profile response status:', response.status);

            if (response.ok) {
              const data = await response.json();
              console.log('Loaded authenticated profile:', data);
              loadedProfile = {
                name: data.name,
                age: data.age,
                gender: data.gender,
                height: data.height_cm,
                weight: data.weight_kg,
                targetWeight: data.target_weight_kg,
                activityLevel: data.activity_level,
                healthGoal: data.health_goal
              };
              setUserProfile(loadedProfile);
              setProfileLoaded(true);

              // Auto-apply user's allergens to filter
              if (data.allergens && Array.isArray(data.allergens)) {
                const allergenKeys = data.allergens
                  .map(mapAllergenValueToKey)
                  .filter((key): key is string => key !== null);
                console.log('Auto-applying allergens to filter:', allergenKeys);
                setSelectedAllergies(allergenKeys);
              }

              // Fetch recommendations immediately after profile is loaded
              await fetchRecommendations(loadedProfile);
              return; // Successfully loaded authenticated profile
            } else {
              console.error('Profile request failed with status:', response.status);
              const errorData = await response.json().catch(() => ({}));
              console.error('Error details:', errorData);
            }
          } catch (error) {
            console.error('Authenticated profile error:', error);
            console.log('Falling back to demo profile');
          }
        } else {
          console.log('No token found, using demo profile');
        }

        // Fallback to demo profile if no token or authentication failed
        console.log('Loading demo profile');
        const demoResponse = await fetch('http://localhost:8000/api/v1/auth/demo-profile', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (demoResponse.ok) {
          const data = await demoResponse.json();
          loadedProfile = {
            name: data.name,
            age: data.age,
            gender: data.gender,
            height: data.height_cm,
            weight: data.weight_kg,
            targetWeight: data.target_weight_kg,
            activityLevel: data.activity_level,
            healthGoal: data.health_goal
          };
          setUserProfile(loadedProfile);
        }
        setProfileLoaded(true);

        // Fetch recommendations with the loaded profile
        if (loadedProfile) {
          await fetchRecommendations(loadedProfile);
        }
      } catch (error) {
        console.error('Failed to load profile:', error);
        setProfileLoaded(true); // 에러가 나도 기본값으로 진행
        setLoading(false);
      }
    };

    loadProfile();

    // Check for profile update flag and reload if needed
    const checkProfileUpdate = () => {
      const profileUpdated = localStorage.getItem('profileUpdated');
      if (profileUpdated === 'true') {
        console.log('Profile was updated, reloading...');
        localStorage.removeItem('profileUpdated');
        loadProfile();
      }
    };

    // Check on mount
    checkProfileUpdate();

    // Check periodically (every second) for profile updates
    const intervalId = setInterval(checkProfileUpdate, 1000);

    // Reload profile when window gains focus (user returns to this tab/page)
    const handleFocus = () => {
      console.log('Window gained focus, checking for profile updates...');
      checkProfileUpdate();
    };

    window.addEventListener('focus', handleFocus);

    return () => {
      clearInterval(intervalId);
      window.removeEventListener('focus', handleFocus);
    };
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

  // Re-fetch recommendations when allergies or filters change
  useEffect(() => {
    // Only re-fetch if profile is already loaded
    if (!profileLoaded) {
      return;
    }

    console.log('Allergies or filters changed, re-fetching recommendations');
    fetchRecommendations(userProfile);
  }, [selectedAllergies, appliedFilters]); // Re-fetch when allergies change or filters are applied

  // Fetch favorites on component mount
  useEffect(() => {
    fetchFavorites();
  }, []);

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
            <p className="text-base font-semibold text-green-700">{getHealthGoalDisplay(userProfile.healthGoal)}</p>
          </div>
          <div className="flex-1 bg-purple-50 rounded-lg p-3">
            <p className="text-sm text-gray-600 mb-1">{currentLang === 'en' ? 'Target Weight' : '목표 체중'}</p>
            <p className="text-base font-semibold text-purple-700">{userProfile.targetWeight}kg</p>
          </div>
        </div>
      </div>

      {/* AI Chatbot Section */}
      <div className="bg-gradient-to-br from-green-50 to-teal-50 rounded-lg shadow-md p-6 mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-900">
            {currentLang === 'en' ? '🤖 AI Meal Assistant' : '🤖 AI 식단 도우미'}
          </h2>
          {chatMessages.length > 0 && (
            <button
              onClick={handleClearChat}
              className="text-sm text-red-600 hover:text-red-700 font-medium"
            >
              {currentLang === 'en' ? 'Clear Chat' : '대화 초기화'}
            </button>
          )}
        </div>

        <p className="text-gray-600 text-sm mb-4">
          {currentLang === 'en'
            ? 'Tell me about your condition or preferences, and I\'ll filter meal recommendations for you!'
            : '오늘의 컨디션이나 선호하는 음식을 말씀해주세요. 맞춤 식단을 추천해드릴게요!'}
        </p>

        {/* Chat messages display */}
        {chatMessages.length > 0 && (
          <div className="bg-white rounded-lg p-4 mb-4 max-h-64 overflow-y-auto space-y-3">
            {chatMessages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.role === 'user'
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            ))}
            {isProcessing && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-900 rounded-lg px-4 py-2">
                  <p className="text-sm">
                    {currentLang === 'en' ? 'Thinking...' : '생각하는 중...'}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Applied filters display */}
        {appliedFilters && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
            <p className="text-sm font-semibold text-blue-900 mb-2">
              {currentLang === 'en' ? '✓ Active Filters:' : '✓ 적용된 필터:'}
            </p>
            <div className="flex flex-wrap gap-2">
              {appliedFilters.maxCalories && (
                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                  {currentLang === 'en' ? `Max Calories: ${appliedFilters.maxCalories}` : `최대 칼로리: ${appliedFilters.maxCalories}`}
                </span>
              )}
              {appliedFilters.minProtein && (
                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                  {currentLang === 'en' ? `Min Protein: ${appliedFilters.minProtein}g` : `최소 단백질: ${appliedFilters.minProtein}g`}
                </span>
              )}
              {appliedFilters.maxCarbs && (
                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                  {currentLang === 'en' ? `Max Carbs: ${appliedFilters.maxCarbs}g` : `최대 탄수화물: ${appliedFilters.maxCarbs}g`}
                </span>
              )}
              {appliedFilters.maxFat && (
                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                  {currentLang === 'en' ? `Max Fat: ${appliedFilters.maxFat}g` : `최대 지방: ${appliedFilters.maxFat}g`}
                </span>
              )}
              {appliedFilters.preferHighProtein && (
                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                  {currentLang === 'en' ? 'High Protein Priority' : '고단백 우선'}
                </span>
              )}
              {appliedFilters.preferLowCarb && (
                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                  {currentLang === 'en' ? 'Low Carb Priority' : '저탄수화물 우선'}
                </span>
              )}
              {appliedFilters.excludeIngredients && appliedFilters.excludeIngredients.length > 0 && (
                <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded">
                  {currentLang === 'en' ? `Exclude: ${appliedFilters.excludeIngredients.join(', ')}` : `제외: ${appliedFilters.excludeIngredients.join(', ')}`}
                </span>
              )}
              {appliedFilters.includeIngredients && appliedFilters.includeIngredients.length > 0 && (
                <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                  {currentLang === 'en' ? `Include: ${appliedFilters.includeIngredients.join(', ')}` : `포함: ${appliedFilters.includeIngredients.join(', ')}`}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Chat input */}
        <form onSubmit={handleChatSubmit} className="flex gap-2">
          <input
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            placeholder={
              currentLang === 'en'
                ? 'e.g., "I want high protein meals today"'
                : '예: "오늘은 단백질이 많은 음식을 먹고 싶어요"'
            }
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none"
            disabled={isProcessing}
          />
          <button
            type="submit"
            disabled={isProcessing || !userInput.trim()}
            className="px-6 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isProcessing
              ? (currentLang === 'en' ? '...' : '...')
              : (currentLang === 'en' ? 'Send' : '전송')}
          </button>
        </form>
      </div>

      {/* TDEE 정보 Section  */}
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
                  {currentLang === 'en' ? 'kcal/day' : 'kcal/일'} ({getHealthGoalDisplay(userProfile.healthGoal)})
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
                  {allergyKeys.map((allergyKey) => {
                    const isSelected = selectedAllergies.includes(allergyKey);
                    const displayName = getAllergyDisplayName(allergyKey);
                    return (
                      <label
                        key={allergyKey}
                        className={`flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-red-50 border border-red-200'
                            : 'hover:bg-gray-50 border border-transparent'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleAllergyToggle(allergyKey)}
                          className="w-4 h-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                        />
                        <span className={`text-sm ${isSelected ? 'text-red-700 font-medium' : 'text-gray-700'}`}>
                          {displayName}
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
              const isFavorited = favoritedMeals.has(meal.name);
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
                    <div className="flex items-center gap-2">
                      <button
                        onClick={(e) => handleToggleFavorite(meal, e)}
                        className="flex-shrink-0 text-red-500 hover:scale-110 transition-transform"
                        title={isFavorited
                          ? (currentLang === 'en' ? 'Remove from favorites' : '즐겨찾기에서 제거')
                          : (currentLang === 'en' ? 'Add to favorites' : '즐겨찾기에 추가')
                        }
                      >
                        <svg className="w-6 h-6" viewBox="0 0 24 24" fill={isFavorited ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
                          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                        </svg>
                      </button>
                      {isSelected && (
                        <div className="flex-shrink-0 bg-green-500 rounded-full p-1">
                          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                          </svg>
                        </div>
                      )}
                    </div>
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
