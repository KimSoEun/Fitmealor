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

  useEffect(() => {
    fetchHistory();
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
              recommendations.map((item) => (
                <div key={item.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="text-xl font-bold text-gray-800">
                        {i18n.language === 'en' && item.meal_name_en
                          ? item.meal_name_en
                          : item.meal_name_ko}
                      </h3>
                      {i18n.language === 'en' && item.meal_name_en && (
                        <p className="text-sm text-gray-500">{item.meal_name_ko}</p>
                      )}
                    </div>
                    <span className="text-sm text-gray-500">
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
              ))
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
