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
  const [currentLang, setCurrentLang] = useState(i18n.language);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const profileData = {
          user_id: 'demo_user',
          age: 25,
          gender: '남성',
          height_cm: 175.0,
          weight_kg: 70.0,
          target_weight_kg: 65.0,
          activity_level: '활동적',
          health_goal: '근육증가'
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
  }, []);

  useEffect(() => {
    const handleLanguageChange = (lng: string) => {
      setCurrentLang(lng);
    };

    i18n.on('languageChanged', handleLanguageChange);

    return () => {
      i18n.off('languageChanged', handleLanguageChange);
    };
  }, [i18n]);

  const getDisplayName = (meal: Meal): string => {
    if (currentLang === 'en') {
      return meal.name_en || meal.name;
    } else {
      return meal.name_kr || meal.name;
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {currentLang === 'en' ? 'Personalized Meal Recommendations' : '맞춤 추천 식단'}
        </h1>
        <p className="text-gray-600">
          {currentLang === 'en'
            ? 'Meal recommendations tailored to your health goals.'
            : '회원님의 건강 목표에 맞춘 식단을 추천해드립니다.'}
        </p>
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
          {recommendations.map((meal, index) => (
            <div key={index} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-lg font-semibold text-gray-900">{getDisplayName(meal)}</h3>
                <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-1 rounded">
                  {meal.score.toFixed(0)}{currentLang === 'en' ? ' pts' : '점'}
                </span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">{currentLang === 'en' ? 'Calories' : '칼로리'}</span>
                  <span className="font-medium text-gray-900">{meal.calories} kcal</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">{currentLang === 'en' ? 'Protein' : '단백질'}</span>
                  <span className="font-medium text-gray-900">{meal.protein_g.toFixed(1)} g</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">{currentLang === 'en' ? 'Carbs' : '탄수화물'}</span>
                  <span className="font-medium text-gray-900">{meal.carbs_g.toFixed(1)} g</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">{currentLang === 'en' ? 'Fat' : '지방'}</span>
                  <span className="font-medium text-gray-900">{meal.fat_g.toFixed(1)} g</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-600">
            {currentLang === 'en' ? 'Unable to load meal recommendations.' : '추천 식단을 불러올 수 없습니다.'}
          </p>
        </div>
      )}
    </div>
  );
};

export default Recommendations;
