import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

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

const Recommendations: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [recommendations, setRecommendations] = useState<Meal[]>([]);
  const [loading, setLoading] = useState(true);
  const [userProfile, setUserProfile] = useState({
    age: 25,
    gender: '남성',
    height: 175.0,
    weight: 70.0,
    targetWeight: 65.0,
    activityLevel: '활동적',
    healthGoal: '근육증가'
  });

  // Load user profile from API
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const token = localStorage.getItem('token');

        if (token) {
          try {
            const response = await fetch('http://localhost:8000/api/v1/auth/profile', {
              method: 'GET',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
              },
            });

            if (response.ok) {
              const data = await response.json();
              setUserProfile({
                age: data.age,
                gender: data.gender,
                height: data.height_cm,
                weight: data.weight_kg,
                targetWeight: data.target_weight_kg,
                activityLevel: data.activity_level,
                healthGoal: data.health_goal
              });
              return;
            }
          } catch (error) {
            console.log('Failed to load authenticated profile, using demo');
          }
        }

        // Fallback to demo profile
        const demoResponse = await fetch('http://localhost:8000/api/v1/auth/demo-profile');
        if (demoResponse.ok) {
          const data = await demoResponse.json();
          setUserProfile({
            age: data.age,
            gender: data.gender,
            height: data.height_cm,
            weight: data.weight_kg,
            targetWeight: data.target_weight_kg,
            activityLevel: data.activity_level,
            healthGoal: data.health_goal
          });
        }
      } catch (error) {
        console.error('Failed to load profile:', error);
      }
    };

    loadProfile();
  }, []);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const profileData = {
          user_id: 'demo_user',
          age: userProfile.age,
          gender: userProfile.gender,
          height_cm: userProfile.height,
          weight_kg: userProfile.weight,
          target_weight_kg: userProfile.targetWeight,
          activity_level: userProfile.activityLevel,
          health_goal: userProfile.healthGoal,
          allergies: [],
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
          console.log('API Response data:', data);
          console.log('First recommendation:', data.recommendations?.[0]);
          const excludedCategories = ['커피', '영양제', '건강기능식품', '음료', '차/음료', '보충제', '비타민'];
          const filteredMeals = data.recommendations.filter((meal: Meal & {category: string}) => {
            const category = meal.category.toLowerCase();
            const name = meal.name.toLowerCase();

            for (const excluded of excludedCategories) {
              if (category.includes(excluded.toLowerCase())) {
                return false;
              }
            }

            if (name.includes('커피') || name.includes('coffee') ||
                name.includes('비타민') || name.includes('vitamin') ||
                name.includes('영양제') || name.includes('supplement')) {
              return false;
            }

            return true;
          });

          setRecommendations(filteredMeals.slice(0, 15)); // 15개 표시
        }
      } catch (error) {
        console.error('Failed to fetch recommendations:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [userProfile]); // Re-fetch when profile changes

  const getDisplayName = (meal: Meal): string => {
    if (i18n.language === 'en') {
      // English: Use translated English name with underscores removed
      const englishName = meal.name_en || meal.name;
      return englishName.replace(/_/g, ' ');
    } else {
      // Korean: Use Korean translation if available, otherwise use original name
      const koreanName = meal.name_kr || meal.name;
      return koreanName.replace(/_/g, ' ');
    }
  };

  const handleMealClick = async (meal: Meal) => {
    try {
      const token = localStorage.getItem('token');

      if (!token) {
        alert(t('recommendations.로그인이_필요합니다'));
        return;
      }

      const response = await fetch('http://localhost:8000/api/v1/history/recommendations/add', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          meal_code: meal.name,  // Use meal name as code
          meal_name_ko: meal.name_kr || meal.name,
          meal_name_en: meal.name_en || meal.name,
          calories: Math.round(meal.calories),
          carbohydrates: Math.round(meal.carbs_g),
          protein: Math.round(meal.protein_g),
          fat: Math.round(meal.fat_g),
          sodium: 0,
          recommendation_context: {
            score: meal.score,
            category: meal.category
          }
        })
      });

      if (response.ok) {
        alert(t('recommendations.히스토리에_저장되었습니다'));
      } else {
        const errorData = await response.json();
        console.error('Failed to save to history:', errorData);
        alert(t('recommendations.히스토리_저장_실패'));
      }
    } catch (error) {
      console.error('Error saving to history:', error);
      alert(t('recommendations.히스토리_저장_실패'));
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {t('recommendations.맞춤_추천_식단')}
        </h1>
        <p className="text-gray-600">
          {t('recommendations.회원님의_건강_목표에_맞춘_식단을_추천해드립니다.')}
        </p>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">
            {t('recommendations.추천_식단을_불러오는_중...')}
          </p>
        </div>
      ) : recommendations.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recommendations.map((meal, index) => (
            <div
              key={index}
              onClick={() => handleMealClick(meal)}
              className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-all cursor-pointer hover:scale-105 transform"
              title={t('recommendations.클릭하여_히스토리에_저장')}
            >
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-lg font-semibold text-gray-900">{getDisplayName(meal)}</h3>
                <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-1 rounded">
                  {meal.score.toFixed(0)}{t('recommendations.점')}
                </span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">{t('recommendations.칼로리')}</span>
                  <span className="font-medium text-gray-900">{meal.calories} kcal</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">{t('recommendations.단백질')}</span>
                  <span className="font-medium text-gray-900">{meal.protein_g.toFixed(1)} g</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">{t('recommendations.탄수화물')}</span>
                  <span className="font-medium text-gray-900">{meal.carbs_g.toFixed(1)} g</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">{t('recommendations.지방')}</span>
                  <span className="font-medium text-gray-900">{meal.fat_g.toFixed(1)} g</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-600">
            {t('recommendations.추천_식단을_불러올_수_없습니다.')}
          </p>
        </div>
      )}
    </div>
  );
};

export default Recommendations;
