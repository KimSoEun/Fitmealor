import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import API_BASE_URL from '../config';

interface NutritionInfo {
  calories?: number;
  carbohydrates?: number;
  protein?: number;
  fat?: number;
  sodium?: number;
  sugar?: number;
}

interface RecommendationHistoryItem {
  id: number;
  meal_code: string;
  meal_name_ko: string;
  meal_name_en?: string;
  nutrition_info: NutritionInfo;
  recommendation_context?: any;
  selected_at: string;
}

interface ProductHistoryItem {
  id: number;
  name: string;
  allergens: string[];
  nutrition_info: NutritionInfo;
  created_at: string;
}

const History = () => {
  const { t, i18n } = useTranslation();
  const [activeTab, setActiveTab] = useState<'recommendations' | 'products'>('recommendations');
  const [recommendations, setRecommendations] = useState<RecommendationHistoryItem[]>([]);
  const [products, setProducts] = useState<ProductHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [favoritedMeals, setFavoritedMeals] = useState<Set<string>>(new Set());

  useEffect(() => {
    fetchHistory();
    fetchFavorites();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      if (!token) {
        setError(i18n.language === 'en' ? 'Please login first' : '로그인이 필요합니다');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/history/all`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(i18n.language === 'en' ? 'Failed to load history' : '히스토리를 불러오지 못했습니다');
      }

      const data = await response.json();

      if (data.success) {
        setRecommendations(data.recommendations.items || []);
        setProducts(data.products.items || []);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString(i18n.language === 'en' ? 'en-US' : 'ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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
  const handleToggleFavorite = async (item: RecommendationHistoryItem, e: React.MouseEvent) => {
    e.stopPropagation();

    const token = localStorage.getItem('token');
    if (!token) {
      alert(i18n.language === 'en' ? 'Please login first' : '로그인이 필요합니다');
      return;
    }

    const mealCode = item.meal_code;
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
            meal_name_ko: item.meal_name_ko,
            meal_name_en: item.meal_name_en,
            calories: item.nutrition_info.calories || null,
            carbohydrates: item.nutrition_info.carbohydrates || null,
            protein: item.nutrition_info.protein || null,
            fat: item.nutrition_info.fat || null,
            sodium: item.nutrition_info.sodium || null
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
      alert(i18n.language === 'en' ? 'Failed to update favorite' : '즐겨찾기 업데이트에 실패했습니다');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">
          {i18n.language === 'en' ? 'Loading...' : '로딩 중...'}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800">
            {i18n.language === 'en' ? 'My History' : '나의 기록'}
          </h1>
          <p className="text-gray-600 mt-2">
            {i18n.language === 'en'
              ? 'View your meal recommendations and registered products'
              : '음식 추천 기록과 등록한 제품을 확인하세요'}
          </p>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Tabs */}
        <div className="flex mb-6 space-x-2 bg-white rounded-lg p-1 shadow-sm">
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-colors ${
              activeTab === 'recommendations'
                ? 'bg-blue-500 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {i18n.language === 'en' ? 'Recommended Meals' : '추천 받은 음식'}
            <span className="ml-2 text-sm">({recommendations.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('products')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-colors ${
              activeTab === 'products'
                ? 'bg-blue-500 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {i18n.language === 'en' ? 'Registered Products' : '등록한 제품'}
            <span className="ml-2 text-sm">({products.length})</span>
          </button>
        </div>

        {/* Content */}
        <div className="space-y-4">
          {activeTab === 'recommendations' ? (
            recommendations.length > 0 ? (
              recommendations.map((item) => {
                const isFavorited = favoritedMeals.has(item.meal_code);
                return (
                  <div key={item.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-start gap-3">
                          <div className="flex-1">
                            <h3 className="text-xl font-bold text-gray-800">
                              {i18n.language === 'en' && item.meal_name_en
                                ? item.meal_name_en
                                : item.meal_name_ko}
                            </h3>
                            {i18n.language === 'en' && item.meal_name_en && (
                              <p className="text-sm text-gray-500">{item.meal_name_ko}</p>
                            )}
                          </div>
                          <button
                            onClick={(e) => handleToggleFavorite(item, e)}
                            className="flex-shrink-0 text-red-500 hover:scale-110 transition-transform"
                            title={isFavorited
                              ? (i18n.language === 'en' ? 'Remove from favorites' : '즐겨찾기에서 제거')
                              : (i18n.language === 'en' ? 'Add to favorites' : '즐겨찾기에 추가')
                            }
                          >
                            <svg className="w-6 h-6" viewBox="0 0 24 24" fill={isFavorited ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
                              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                            </svg>
                          </button>
                        </div>
                      </div>
                      <span className="text-sm text-gray-500 ml-4">
                        {formatDate(item.selected_at)}
                      </span>
                    </div>

                  {/* Nutrition Info */}
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mt-4">
                    {item.nutrition_info.calories && (
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <div className="text-xs text-gray-500">
                          {i18n.language === 'en' ? 'Calories' : '칼로리'}
                        </div>
                        <div className="text-sm font-semibold">{item.nutrition_info.calories} kcal</div>
                      </div>
                    )}
                    {item.nutrition_info.carbohydrates && (
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <div className="text-xs text-gray-500">
                          {i18n.language === 'en' ? 'Carbs' : '탄수화물'}
                        </div>
                        <div className="text-sm font-semibold">{item.nutrition_info.carbohydrates}g</div>
                      </div>
                    )}
                    {item.nutrition_info.protein && (
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <div className="text-xs text-gray-500">
                          {i18n.language === 'en' ? 'Protein' : '단백질'}
                        </div>
                        <div className="text-sm font-semibold">{item.nutrition_info.protein}g</div>
                      </div>
                    )}
                    {item.nutrition_info.fat && (
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <div className="text-xs text-gray-500">
                          {i18n.language === 'en' ? 'Fat' : '지방'}
                        </div>
                        <div className="text-sm font-semibold">{item.nutrition_info.fat}g</div>
                      </div>
                    )}
                    {item.nutrition_info.sodium && (
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <div className="text-xs text-gray-500">
                          {i18n.language === 'en' ? 'Sodium' : '나트륨'}
                        </div>
                        <div className="text-sm font-semibold">{item.nutrition_info.sodium}mg</div>
                      </div>
                    )}
                  </div>
                </div>
                );
              })
            ) : (
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <p className="text-gray-500">
                  {i18n.language === 'en'
                    ? 'No meal recommendations yet'
                    : '아직 추천 받은 음식이 없습니다'}
                </p>
              </div>
            )
          ) : (
            products.length > 0 ? (
              products.map((item) => (
                <div key={item.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-xl font-bold text-gray-800">{item.name}</h3>
                      {item.allergens && item.allergens.length > 0 && (
                        <div className="mt-2">
                          <span className="text-xs text-gray-500 mr-2">
                            {i18n.language === 'en' ? 'Allergens:' : '알레르기 유발 성분:'}
                          </span>
                          {item.allergens.map((allergen, idx) => (
                            <span key={idx} className="inline-block bg-red-100 text-red-700 text-xs px-2 py-1 rounded mr-1">
                              {allergen}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <span className="text-sm text-gray-500">
                      {formatDate(item.created_at)}
                    </span>
                  </div>

                  {/* Nutrition Info */}
                  <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mt-4">
                    {item.nutrition_info.calories && (
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <div className="text-xs text-gray-500">
                          {i18n.language === 'en' ? 'Calories' : '칼로리'}
                        </div>
                        <div className="text-sm font-semibold">{item.nutrition_info.calories} kcal</div>
                      </div>
                    )}
                    {item.nutrition_info.carbohydrates && (
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <div className="text-xs text-gray-500">
                          {i18n.language === 'en' ? 'Carbs' : '탄수화물'}
                        </div>
                        <div className="text-sm font-semibold">{item.nutrition_info.carbohydrates}g</div>
                      </div>
                    )}
                    {item.nutrition_info.protein && (
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <div className="text-xs text-gray-500">
                          {i18n.language === 'en' ? 'Protein' : '단백질'}
                        </div>
                        <div className="text-sm font-semibold">{item.nutrition_info.protein}g</div>
                      </div>
                    )}
                    {item.nutrition_info.fat && (
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <div className="text-xs text-gray-500">
                          {i18n.language === 'en' ? 'Fat' : '지방'}
                        </div>
                        <div className="text-sm font-semibold">{item.nutrition_info.fat}g</div>
                      </div>
                    )}
                    {item.nutrition_info.sodium && (
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <div className="text-xs text-gray-500">
                          {i18n.language === 'en' ? 'Sodium' : '나트륨'}
                        </div>
                        <div className="text-sm font-semibold">{item.nutrition_info.sodium}mg</div>
                      </div>
                    )}
                    {item.nutrition_info.sugar && (
                      <div className="bg-gray-50 p-3 rounded-lg">
                        <div className="text-xs text-gray-500">
                          {i18n.language === 'en' ? 'Sugar' : '당류'}
                        </div>
                        <div className="text-sm font-semibold">{item.nutrition_info.sugar}g</div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <p className="text-gray-500">
                  {i18n.language === 'en'
                    ? 'No registered products yet'
                    : '아직 등록한 제품이 없습니다'}
                </p>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
};

export default History;
