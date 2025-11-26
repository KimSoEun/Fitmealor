import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

interface NutritionInfo {
  calories?: number | null;
  carbohydrates?: number | null;
  protein?: number | null;
  fat?: number | null;
  sodium?: number | null;
  sugar?: number | null;
}

interface Product {
  id: number;
  name: string;
  allergens?: string[];
  nutrition_info: NutritionInfo;
  created_at?: string;
}

interface EditProduct extends Product {
  isEditing: boolean;
}

export default function MyProducts() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [products, setProducts] = useState<EditProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingProduct, setEditingProduct] = useState<EditProduct | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const response = await axios.get('http://localhost:8000/api/v1/foods/products', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.data.success) {
        setProducts(response.data.products.map((p: Product) => ({ ...p, isEditing: false })));
      }
    } catch (error) {
      console.error('Error fetching products:', error);
      alert(i18n.language === 'en' ? 'Failed to load products.' : '제품 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (product: EditProduct) => {
    setEditingProduct({ ...product });
    setShowEditModal(true);
  };

  const handleSaveEdit = async () => {
    if (!editingProduct) return;

    try {
      const token = localStorage.getItem('token');
      const response = await axios.put(
        `http://localhost:8000/api/v1/foods/products/${editingProduct.id}`,
        {
          name: editingProduct.name,
          allergens: editingProduct.allergens,
          nutrition_info: editingProduct.nutrition_info
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.data.success) {
        alert(i18n.language === 'en' ? 'Product updated successfully!' : '제품이 성공적으로 수정되었습니다!');
        setShowEditModal(false);
        fetchProducts();
      }
    } catch (error) {
      console.error('Error updating product:', error);
      alert(i18n.language === 'en' ? 'Failed to update product.' : '제품 수정에 실패했습니다.');
    }
  };

  const handleDelete = async (productId: number) => {
    const confirmMessage = i18n.language === 'en'
      ? 'Are you sure you want to delete this product?'
      : '이 제품을 삭제하시겠습니까?';

    if (!confirm(confirmMessage)) return;

    try {
      const token = localStorage.getItem('token');
      const response = await axios.delete(
        `http://localhost:8000/api/v1/foods/products/${productId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.data.success) {
        alert(i18n.language === 'en' ? 'Product deleted successfully!' : '제품이 성공적으로 삭제되었습니다!');
        fetchProducts();
      }
    } catch (error) {
      console.error('Error deleting product:', error);
      alert(i18n.language === 'en' ? 'Failed to delete product.' : '제품 삭제에 실패했습니다.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">{i18n.language === 'en' ? 'Loading...' : '로딩 중...'}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {i18n.language === 'en' ? 'My Registered Products' : '등록된 제품 관리'}
          </h1>
          <p className="text-gray-600">
            {i18n.language === 'en'
              ? 'View and manage products registered through OCR scanning'
              : 'OCR 스캔으로 등록한 제품을 확인하고 관리하세요'}
          </p>
        </div>

        {/* Products List */}
        {products.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-500 text-lg">
              {i18n.language === 'en'
                ? 'No registered products yet.'
                : '등록된 제품이 없습니다.'}
            </p>
            <button
              onClick={() => navigate('/ocr')}
              className="mt-4 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
            >
              {i18n.language === 'en' ? 'Scan Product' : '제품 스캔하기'}
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map((product) => (
              <div key={product.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition">
                <h3 className="text-xl font-bold text-gray-900 mb-4">{product.name}</h3>

                {/* Nutrition Info */}
                <div className="mb-4 space-y-2">
                  <h4 className="font-semibold text-gray-700">
                    {i18n.language === 'en' ? 'Nutrition Facts' : '영양 정보'}
                  </h4>
                  <div className="text-sm text-gray-600 space-y-1">
                    {product.nutrition_info.calories !== null && (
                      <div>{i18n.language === 'en' ? 'Calories' : '칼로리'}: {product.nutrition_info.calories} kcal</div>
                    )}
                    {product.nutrition_info.carbohydrates !== null && (
                      <div>{i18n.language === 'en' ? 'Carbs' : '탄수화물'}: {product.nutrition_info.carbohydrates}g</div>
                    )}
                    {product.nutrition_info.protein !== null && (
                      <div>{i18n.language === 'en' ? 'Protein' : '단백질'}: {product.nutrition_info.protein}g</div>
                    )}
                    {product.nutrition_info.fat !== null && (
                      <div>{i18n.language === 'en' ? 'Fat' : '지방'}: {product.nutrition_info.fat}g</div>
                    )}
                    {product.nutrition_info.sodium !== null && (
                      <div>{i18n.language === 'en' ? 'Sodium' : '나트륨'}: {product.nutrition_info.sodium}mg</div>
                    )}
                    {product.nutrition_info.sugar !== null && (
                      <div>{i18n.language === 'en' ? 'Sugar' : '당류'}: {product.nutrition_info.sugar}g</div>
                    )}
                  </div>
                </div>

                {/* Allergens */}
                {product.allergens && product.allergens.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-semibold text-gray-700 mb-2">
                      {i18n.language === 'en' ? 'Allergens' : '알러지 정보'}
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {product.allergens.map((allergen, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded"
                        >
                          {allergen}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Created At */}
                {product.created_at && (
                  <div className="text-xs text-gray-400 mb-4">
                    {i18n.language === 'en' ? 'Registered' : '등록일'}: {new Date(product.created_at).toLocaleDateString()}
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(product)}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition"
                  >
                    {i18n.language === 'en' ? 'Edit' : '수정'}
                  </button>
                  <button
                    onClick={() => handleDelete(product.id)}
                    className="flex-1 px-4 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition"
                  >
                    {i18n.language === 'en' ? 'Delete' : '삭제'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {showEditModal && editingProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              {i18n.language === 'en' ? 'Edit Product' : '제품 수정'}
            </h2>

            {/* Product Name */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {i18n.language === 'en' ? 'Product Name' : '제품명'}
              </label>
              <input
                type="text"
                value={editingProduct.name}
                onChange={(e) => setEditingProduct({ ...editingProduct, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
              />
            </div>

            {/* Nutrition Info */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">
                {i18n.language === 'en' ? 'Nutrition Facts' : '영양 정보'}
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    {i18n.language === 'en' ? 'Calories (kcal)' : '칼로리 (kcal)'}
                  </label>
                  <input
                    type="number"
                    value={editingProduct.nutrition_info.calories || ''}
                    onChange={(e) => setEditingProduct({
                      ...editingProduct,
                      nutrition_info: { ...editingProduct.nutrition_info, calories: parseFloat(e.target.value) || 0 }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    {i18n.language === 'en' ? 'Carbs (g)' : '탄수화물 (g)'}
                  </label>
                  <input
                    type="number"
                    value={editingProduct.nutrition_info.carbohydrates || ''}
                    onChange={(e) => setEditingProduct({
                      ...editingProduct,
                      nutrition_info: { ...editingProduct.nutrition_info, carbohydrates: parseFloat(e.target.value) || 0 }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    {i18n.language === 'en' ? 'Protein (g)' : '단백질 (g)'}
                  </label>
                  <input
                    type="number"
                    value={editingProduct.nutrition_info.protein || ''}
                    onChange={(e) => setEditingProduct({
                      ...editingProduct,
                      nutrition_info: { ...editingProduct.nutrition_info, protein: parseFloat(e.target.value) || 0 }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    {i18n.language === 'en' ? 'Fat (g)' : '지방 (g)'}
                  </label>
                  <input
                    type="number"
                    value={editingProduct.nutrition_info.fat || ''}
                    onChange={(e) => setEditingProduct({
                      ...editingProduct,
                      nutrition_info: { ...editingProduct.nutrition_info, fat: parseFloat(e.target.value) || 0 }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    {i18n.language === 'en' ? 'Sodium (mg)' : '나트륨 (mg)'}
                  </label>
                  <input
                    type="number"
                    value={editingProduct.nutrition_info.sodium || ''}
                    onChange={(e) => setEditingProduct({
                      ...editingProduct,
                      nutrition_info: { ...editingProduct.nutrition_info, sodium: parseFloat(e.target.value) || 0 }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    {i18n.language === 'en' ? 'Sugar (g)' : '당류 (g)'}
                  </label>
                  <input
                    type="number"
                    value={editingProduct.nutrition_info.sugar || ''}
                    onChange={(e) => setEditingProduct({
                      ...editingProduct,
                      nutrition_info: { ...editingProduct.nutrition_info, sugar: parseFloat(e.target.value) || 0 }
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-green-500"
                  />
                </div>
              </div>
            </div>

            {/* Allergens */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {i18n.language === 'en' ? 'Allergens (comma separated)' : '알러지 정보 (쉼표로 구분)'}
              </label>
              <input
                type="text"
                value={editingProduct.allergens?.join(', ') || ''}
                onChange={(e) => setEditingProduct({
                  ...editingProduct,
                  allergens: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
                placeholder={i18n.language === 'en' ? 'e.g., Milk, Eggs, Peanuts' : '예: 우유, 계란, 땅콩'}
              />
            </div>

            {/* Buttons */}
            <div className="flex gap-4">
              <button
                onClick={handleSaveEdit}
                className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition"
              >
                {i18n.language === 'en' ? 'Save Changes' : '저장'}
              </button>
              <button
                onClick={() => setShowEditModal(false)}
                className="flex-1 px-6 py-3 bg-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-400 transition"
              >
                {i18n.language === 'en' ? 'Cancel' : '취소'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
