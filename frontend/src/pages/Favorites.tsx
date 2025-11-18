import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import API_BASE_URL from '../config';

interface NutritionInfo {
  calories?: number;
  carbohydrates?: number;
  protein?: number;
  fat?: number;
  sodium?: number;
}

interface FavoriteItem {
  id: number;
  meal_code: string;
  meal_name_ko: string;
  meal_name_en?: string;
  nutrition_info: NutritionInfo;
  created_at: string;
}

const Favorites = () => {
  const { t, i18n } = useTranslation();
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchFavorites();
  }, []);

  const fetchFavorites = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');

      if (!token) {
        setError(i18n.language === 'en' ? 'Please login first' : '로그인이 필요합니다');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/favorites/list`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(i18n.language === 'en' ? 'Failed to load favorites' : '즐겨찾기를 불러오지 못했습니다');
      }

      const data = await response.json();

      if (data.success) {
        setFavorites(data.favorites || []);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveFavorite = async (mealCode: string) => {
    try {
      const token = localStorage.getItem('token');

      if (!token) {
        alert(i18n.language === 'en' ? 'Please login first' : '로그인이 필요합니다');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/favorites/remove/${mealCode}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(i18n.language === 'en' ? 'Failed to remove favorite' : '즐겨찾기 제거에 실패했습니다');
      }

      // Refresh the list
      await fetchFavorites();
    } catch (err: any) {
      alert(err.message);
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
            {i18n.language === 'en' ? 'My Favorites' : '나의 즐겨찾기'}
          </h1>
          <p className="text-gray-600 mt-2">
            {i18n.language === 'en'
              ? 'View and manage your favorite meals'
              : '즐겨찾기한 식단을 확인하고 관리하세요'}
          </p>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Empty State */}
        {favorites.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <svg className="mx-auto h-16 w-16 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {i18n.language === 'en' ? 'No favorites yet' : '아직 즐겨찾기가 없습니다'}
            </h3>
            <p className="text-gray-500">
              {i18n.language === 'en'
                ? 'Add meals to your favorites from Home or History pages'
                : 'Home이나 History 페이지에서 식단을 즐겨찾기에 추가해보세요'}
            </p>
          </div>
        ) : (
          <>
            <div className="mb-4 text-sm text-gray-600">
              {i18n.language === 'en' ? `${favorites.length} favorite meal(s)` : `총 ${favorites.length}개의 즐겨찾기`}
            </div>

            {/* Favorites List */}
            <div className="space-y-4">
              {favorites.map((item) => (
                <div key={item.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-gray-800">
                        {i18n.language === 'en' && item.meal_name_en
                          ? item.meal_name_en
                          : item.meal_name_ko}
                      </h3>
                      {i18n.language === 'en' && item.meal_name_en && (
                        <p className="text-sm text-gray-500">{item.meal_name_ko}</p>
                      )}
                      <span className="text-xs text-gray-400 mt-1 block">
                        {i18n.language === 'en' ? 'Added on' : '추가일'}: {formatDate(item.created_at)}
                      </span>
                    </div>
                    <button
                      onClick={() => handleRemoveFavorite(item.meal_code)}
                      className="ml-4 text-red-500 hover:text-red-700 transition-colors"
                      title={i18n.language === 'en' ? 'Remove from favorites' : '즐겨찾기에서 제거'}
                    >
                      <svg className="w-6 h-6 fill-current" viewBox="0 0 24 24">
                        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                      </svg>
                    </button>
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
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Favorites;
