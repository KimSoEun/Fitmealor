import React, { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

interface NutritionInfo {
  calories?: number | null;
  carbohydrates?: number | null;
  protein?: number | null;
  fat?: number | null;
  sodium?: number | null;
  sugar?: number | null;
}

interface ExtractedData {
  product_name?: string | null;
  allergens?: string[];
  nutrition_info?: NutritionInfo;
}

interface UploadedImage {
  id: string;
  dataUrl: string;
  file: File;
  isAnalyzing: boolean;
  extractedData?: ExtractedData;
  error?: string;
  isEditing?: boolean;
}

export default function OCRScan() {
// const OCRScan: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [images, setImages] = useState<UploadedImage[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [aggregatedData, setAggregatedData] = useState<ExtractedData | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    files.forEach(file => handleFile(file));
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    files.forEach(file => handleFile(file));

    // Reset input so the same file can be uploaded again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleFile = async (file: File) => {
    // Validate file type (image or HEIC)
    const isValidType = file.type.startsWith('image/') ||
                        file.name.toLowerCase().endsWith('.heic') ||
                        file.name.toLowerCase().endsWith('.heif');

    if (!isValidType) {
      alert(i18n.language === 'en' ? 'Please upload an image or HEIC file.' : '이미지 또는 HEIC 파일을 업로드해주세요.')
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert(i18n.language === 'en' ? 'File size must be less than 10MB.' : '파일 크기는 10MB 이하여야 합니다.')
      return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onload = async (e) => {
      if (e.target?.result) {
        const newImage: UploadedImage = {
          id: Date.now().toString() + Math.random().toString(36),
          dataUrl: e.target.result as string,
          file: file,
          isAnalyzing: true
        };

        setImages(prev => [...prev, newImage]);

        // Call backend API to analyze image
        try {
          const formData = new FormData();
          formData.append('file', file);

          const response = await axios.post(
            'http://localhost:8000/api/v1/ocr/analyze-with-ai',
            formData,
            {
              headers: {
                'Content-Type': 'multipart/form-data'
              }
            }
          );

          if (response.data.success) {
            setImages(prev => prev.map(img =>
              img.id === newImage.id
                ? {
                    ...img,
                    isAnalyzing: false,
                    extractedData: {
                      product_name: response.data.product_name,
                      allergens: response.data.allergens || [],
                      nutrition_info: response.data.nutrition_info || {}
                    }
                  }
                : img
            ));
          } else {
            throw new Error('Analysis failed');
          }
        } catch (error) {
          console.error('OCR analysis error:', error);
          setImages(prev => prev.map(img =>
            img.id === newImage.id
              ? {
                  ...img,
                  isAnalyzing: false,
                  // error: t('ocr.분석실패')
                  error: i18n.language === 'en' ? 'Failed to analyze image.' : '이미지 분석에 실패했습니다.'
                }
              : img
          ));
        }
      }
    };
    reader.readAsDataURL(file);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleDelete = (id: string) => {
    setImages(prev => prev.filter(img => img.id !== id));
  };

  const handleEdit = (id: string) => {
    setImages(prev => prev.map(img =>
      img.id === id ? { ...img, isEditing: !img.isEditing } : img
    ));
  };

  const handleUpdateData = (id: string, field: keyof ExtractedData, value: any) => {
    setImages(prev => prev.map(img => {
      if (img.id === id && img.extractedData) {
        return {
          ...img,
          extractedData: {
            ...img.extractedData,
            [field]: value
          }
        };
      }
      return img;
    }));
  };

  const handleUpdateNutrition = (id: string, field: keyof NutritionInfo, value: number | null) => {
    setImages(prev => prev.map(img => {
      if (img.id === id && img.extractedData) {
        return {
          ...img,
          extractedData: {
            ...img.extractedData,
            nutrition_info: {
              ...img.extractedData.nutrition_info,
              [field]: value
            }
          }
        };
      }
      return img;
    }));
  };

  // Aggregate data from multiple images
  const aggregateData = (): ExtractedData => {
    const imagesWithData = images.filter(img => img.extractedData && !img.error);

    if (imagesWithData.length === 0) {
      return {
        product_name: null,
        allergens: [],
        nutrition_info: {}
      };
    }

    // Get product names (prioritize non-empty ones)
    const productNames = imagesWithData
      .map(img => img.extractedData?.product_name)
      .filter(name => name && name.trim().length > 0);

    // Use the first non-empty product name, or the most common one
    const productName = productNames.length > 0 ? productNames[0] : null;

    // Merge allergens (union of all allergens)
    const allergensSet = new Set<string>();
    imagesWithData.forEach(img => {
      img.extractedData?.allergens?.forEach(allergen => {
        if (allergen && allergen.trim().length > 0) {
          allergensSet.add(allergen.trim());
        }
      });
    });
    const allergens = Array.from(allergensSet);

    // Aggregate nutrition info (average non-null values)
    const nutritionFields: (keyof NutritionInfo)[] = ['calories', 'carbohydrates', 'protein', 'fat', 'sodium', 'sugar'];
    const nutrition_info: NutritionInfo = {};

    nutritionFields.forEach(field => {
      const values = imagesWithData
        .map(img => img.extractedData?.nutrition_info?.[field])
        .filter(val => val != null && !isNaN(val as number)) as number[];

      if (values.length > 0) {
        // Use average value, rounded to 1 decimal place
        const average = values.reduce((sum, val) => sum + val, 0) / values.length;
        nutrition_info[field] = Math.round(average * 10) / 10;
      }
    });

    return {
      product_name: productName,
      allergens,
      nutrition_info
    };
  };

  // Open registration modal with aggregated data
  const handleOpenRegisterModal = () => {
    const aggregated = aggregateData();
    setAggregatedData(aggregated);
    setShowRegisterModal(true);
  };

  // Update aggregated data in modal
  const handleUpdateAggregatedData = (field: keyof ExtractedData, value: any) => {
    if (aggregatedData) {
      setAggregatedData({
        ...aggregatedData,
        [field]: value
      });
    }
  };

  const handleUpdateAggregatedNutrition = (field: keyof NutritionInfo, value: number | null) => {
    if (aggregatedData) {
      setAggregatedData({
        ...aggregatedData,
        nutrition_info: {
          ...aggregatedData.nutrition_info,
          [field]: value
        }
      });
    }
  };

  // Save product to database
  const handleSaveProduct = async () => {
    if (!aggregatedData) return;

    setIsSaving(true);
    try {
      // Get token from localStorage
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      // Call backend API to save product
      const response = await axios.post(
        'http://localhost:8000/api/v1/foods/register',
        {
          name: aggregatedData.product_name,
          allergens: aggregatedData.allergens,
          nutrition_info: aggregatedData.nutrition_info
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.data.success) {
        alert(i18n.language === 'en' ? 'Product registered successfully!' : '제품이 성공적으로 등록되었습니다!');
        setShowRegisterModal(false);
        // Optionally clear images after successful registration
        // setImages([]);
      } else {
        throw new Error('Registration failed');
      }
    } catch (error) {
      console.error('Product registration error:', error);
      alert(i18n.language === 'en' ? 'Failed to register product.' : '제품 등록에 실패했습니다.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {/* {t('ocr.제목')} */}
          {i18n.language === 'en' ? 'Food Label Scanner' : '식품 라벨 스캔'}
        </h1>
        <p className="text-gray-600">
          {/* {t('ocr.부제목')} */}
          {i18n.language === 'en' ? "Snap a photo and we'll analyze the nutrition facts automatically" : '식품 라벨을 촬영하면 영양 정보를 자동으로 분석해드립니다'}
        </p>
      </div>

      {/* Upload Area */}
      <div className="bg-white rounded-lg shadow-md p-8 mb-6">
        <p className="text-lg text-gray-700 mb-6 text-center">
          {/* {t('ocr.안내문구')} */}
          {i18n.language === 'en' ? 'Take a photo or upload an image of the nutrition facts label' : '식품 포장지의 영양 성분표를 촬영하거나 업로드해주세요'}
        </p>

        <div
          onClick={handleClick}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
            isDragging
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
          }`}
        >
          <svg
            className="mx-auto h-16 w-16 text-gray-400 mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>

          <p className="text-xl font-semibold text-gray-700 mb-2">
            {/* {t('ocr.업로드영역_제목')} */}
            {i18n.language === 'en' ? 'Click or drag to upload photo' : '클릭하거나 드래그하여 사진 업로드'}
          </p>
          <p className="text-sm text-gray-500">
            {/* {t('ocr.업로드영역_설명')} */}
            JPG, PNG, HEIC {i18n.language === 'en' ? 'supported · Max' : '지원 · 최대'} 10MB
          </p>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,.heic,.heif"
            multiple
            onChange={handleFileInput}
            className="hidden"
          />
        </div>
      </div>

      {/* Uploaded Images */}
      {images.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            {/* {t('ocr.업로드된_사진')} ({images.length}{t('ocr.개')}) */}
            {i18n.language === 'en' ? 'Uploaded Photos' : '업로드된 사진'} ({images.length}{i18n.language === 'en' ? '' : '개'})
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {images.map((image) => (
              <div key={image.id} className="relative group">
                <div className="bg-gray-50 rounded-lg overflow-hidden shadow-md">
                  {/* Image */}
                  <div className="relative">
                    <img
                      src={image.dataUrl}
                      alt="Uploaded food label"
                      className="w-full h-64 object-cover"
                    />

                    {/* Action Buttons */}
                    <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      {/* Edit Button */}
                      {!image.isAnalyzing && image.extractedData && (
                        <button
                          onClick={() => handleEdit(image.id)}
                          className={`p-2 rounded-full transition-colors ${
                            image.isEditing
                              ? 'bg-green-500 hover:bg-green-600'
                              : 'bg-blue-500 hover:bg-blue-600'
                          } text-white`}
                        >
                          {image.isEditing ? (
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          ) : (
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          )}
                        </button>
                      )}

                      {/* Delete Button */}
                      <button
                        onClick={() => handleDelete(image.id)}
                        className="bg-red-500 text-white p-2 rounded-full hover:bg-red-600 transition-colors"
                      >
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      </button>
                    </div>
                  </div>

                  {/* Analysis Status */}
                  <div className="p-4">
                    {image.isAnalyzing ? (
                      <div className="flex items-center justify-center">
                        <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-2"></div>
                        <p className="text-sm text-gray-700">
                          {/* {t('ocr.분석중')} */}
                          {i18n.language === 'en' ? 'Analyzing image...' : '이미지 분석 중...'}
                        </p>
                      </div>
                    ) : image.error ? (
                      <div className="text-center">
                        <p className="text-sm font-semibold text-red-600 mb-1">
                          {/* {t('ocr.분석결과')} */}
                          {i18n.language === 'en' ? 'Analysis Result' : '분석 결과'}
                        </p>
                        <p className="text-xs text-red-500">
                          {image.error}
                        </p>
                      </div>
                    ) : image.extractedData ? (
                      <div className="text-left text-sm space-y-3">
                        <p className="font-semibold text-gray-900 mb-2">
                          {i18n.language === 'en' ? 'Analysis Result' : '분석 결과'}
                          {image.isEditing && (
                            <span className="ml-2 text-xs text-blue-600">
                              ({i18n.language === 'en' ? 'Editing' : '편집 중'})
                            </span>
                          )}
                        </p>

                        {/* Product Name */}
                        <div>
                          <label className="block font-medium text-gray-700 mb-1">
                            {i18n.language === 'en' ? 'Product Name' : '제품명'}
                          </label>
                          {image.isEditing ? (
                            <input
                              type="text"
                              value={image.extractedData.product_name || ''}
                              onChange={(e) => handleUpdateData(image.id, 'product_name', e.target.value)}
                              className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                              placeholder={i18n.language === 'en' ? 'Enter product name' : '제품명을 입력하세요'}
                            />
                          ) : (
                            <span className="text-gray-600">
                              {image.extractedData.product_name || '-'}
                            </span>
                          )}
                        </div>

                        {/* Allergens */}
                        <div>
                          <label className="block font-medium text-gray-700 mb-1">
                            {i18n.language === 'en' ? 'Allergen Ingredients' : '알러지 유발 성분'}
                          </label>
                          {image.isEditing ? (
                            <input
                              type="text"
                              value={image.extractedData.allergens?.join(', ') || ''}
                              onChange={(e) => handleUpdateData(image.id, 'allergens', e.target.value.split(',').map(s => s.trim()).filter(s => s))}
                              className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                              placeholder={i18n.language === 'en' ? 'Enter allergens (comma-separated)' : '알러지 성분 입력 (쉼표로 구분)'}
                            />
                          ) : (
                            <span className="text-gray-600">
                              {image.extractedData.allergens && image.extractedData.allergens.length > 0
                                ? image.extractedData.allergens.join(', ')
                                : '-'}
                            </span>
                          )}
                        </div>

                        {/* Nutrition Info */}
                        <div>
                          <span className="block font-medium text-gray-700 mb-1">
                            {i18n.language === 'en' ? 'Nutrition Information' : '영양 정보'}
                          </span>
                          <div className="space-y-1.5 text-xs">
                            {/* Calories */}
                            <div className="flex items-center gap-2">
                              <span className="w-20 text-gray-600">
                                {i18n.language === 'en' ? 'Calories' : '칼로리'}:
                              </span>
                              {image.isEditing ? (
                                <input
                                  type="number"
                                  value={image.extractedData.nutrition_info?.calories ?? ''}
                                  onChange={(e) => handleUpdateNutrition(image.id, 'calories', e.target.value ? Number(e.target.value) : null)}
                                  className="flex-1 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  placeholder="0"
                                />
                              ) : (
                                <span className="text-gray-700">
                                  {image.extractedData.nutrition_info?.calories ?? '-'} kcal
                                </span>
                              )}
                            </div>

                            {/* Carbohydrates */}
                            <div className="flex items-center gap-2">
                              <span className="w-20 text-gray-600">
                                {i18n.language === 'en' ? 'Carbs' : '탄수화물'}:
                              </span>
                              {image.isEditing ? (
                                <input
                                  type="number"
                                  value={image.extractedData.nutrition_info?.carbohydrates ?? ''}
                                  onChange={(e) => handleUpdateNutrition(image.id, 'carbohydrates', e.target.value ? Number(e.target.value) : null)}
                                  className="flex-1 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  placeholder="0"
                                />
                              ) : (
                                <span className="text-gray-700">
                                  {image.extractedData.nutrition_info?.carbohydrates ?? '-'} g
                                </span>
                              )}
                            </div>

                            {/* Protein */}
                            <div className="flex items-center gap-2">
                              <span className="w-20 text-gray-600">
                                {i18n.language === 'en' ? 'Protein' : '단백질'}:
                              </span>
                              {image.isEditing ? (
                                <input
                                  type="number"
                                  value={image.extractedData.nutrition_info?.protein ?? ''}
                                  onChange={(e) => handleUpdateNutrition(image.id, 'protein', e.target.value ? Number(e.target.value) : null)}
                                  className="flex-1 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  placeholder="0"
                                />
                              ) : (
                                <span className="text-gray-700">
                                  {image.extractedData.nutrition_info?.protein ?? '-'} g
                                </span>
                              )}
                            </div>

                            {/* Fat */}
                            <div className="flex items-center gap-2">
                              <span className="w-20 text-gray-600">
                                {i18n.language === 'en' ? 'Fat' : '지방'}:
                              </span>
                              {image.isEditing ? (
                                <input
                                  type="number"
                                  value={image.extractedData.nutrition_info?.fat ?? ''}
                                  onChange={(e) => handleUpdateNutrition(image.id, 'fat', e.target.value ? Number(e.target.value) : null)}
                                  className="flex-1 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  placeholder="0"
                                />
                              ) : (
                                <span className="text-gray-700">
                                  {image.extractedData.nutrition_info?.fat ?? '-'} g
                                </span>
                              )}
                            </div>

                            {/* Sodium */}
                            <div className="flex items-center gap-2">
                              <span className="w-20 text-gray-600">
                                {i18n.language === 'en' ? 'Sodium' : '나트륨'}:
                              </span>
                              {image.isEditing ? (
                                <input
                                  type="number"
                                  value={image.extractedData.nutrition_info?.sodium ?? ''}
                                  onChange={(e) => handleUpdateNutrition(image.id, 'sodium', e.target.value ? Number(e.target.value) : null)}
                                  className="flex-1 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  placeholder="0"
                                />
                              ) : (
                                <span className="text-gray-700">
                                  {image.extractedData.nutrition_info?.sodium ?? '-'} mg
                                </span>
                              )}
                            </div>

                            {/* Sugar */}
                            <div className="flex items-center gap-2">
                              <span className="w-20 text-gray-600">
                                {i18n.language === 'en' ? 'Sugar' : '당류'}:
                              </span>
                              {image.isEditing ? (
                                <input
                                  type="number"
                                  value={image.extractedData.nutrition_info?.sugar ?? ''}
                                  onChange={(e) => handleUpdateNutrition(image.id, 'sugar', e.target.value ? Number(e.target.value) : null)}
                                  className="flex-1 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                  placeholder="0"
                                />
                              ) : (
                                <span className="text-gray-700">
                                  {image.extractedData.nutrition_info?.sugar ?? '-'} g
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Register Product Button */}
      {images.some(img => img.extractedData && !img.error) && (
        <div className="mt-6 flex justify-center">
          <button
            onClick={handleOpenRegisterModal}
            className="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-8 rounded-lg shadow-lg transition-colors"
          >
            {i18n.language === 'en' ? 'Register Product' : '제품 등록하기'}
          </button>
        </div>
      )}

      {/* Registration Confirmation Modal */}
      {showRegisterModal && aggregatedData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 p-6">
              <h2 className="text-2xl font-bold text-gray-900">
                {i18n.language === 'en' ? 'Confirm Product Registration' : '제품 등록 확인'}
              </h2>
              <p className="text-sm text-gray-600 mt-2">
                {i18n.language === 'en'
                  ? 'Review and edit the aggregated data from all images before saving to the database.'
                  : '모든 이미지에서 취합한 데이터를 확인하고 수정한 후 데이터베이스에 저장하세요.'}
              </p>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6">
              {/* Product Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {i18n.language === 'en' ? 'Product Name' : '제품명'}
                </label>
                <input
                  type="text"
                  value={aggregatedData.product_name || ''}
                  onChange={(e) => handleUpdateAggregatedData('product_name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder={i18n.language === 'en' ? 'Enter product name' : '제품명을 입력하세요'}
                />
              </div>

              {/* Allergens */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {i18n.language === 'en' ? 'Allergen Ingredients' : '알러지 유발 성분'}
                </label>
                <input
                  type="text"
                  value={aggregatedData.allergens?.join(', ') || ''}
                  onChange={(e) => handleUpdateAggregatedData('allergens', e.target.value.split(',').map(s => s.trim()).filter(s => s))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder={i18n.language === 'en' ? 'Enter allergens (comma-separated)' : '알러지 성분 입력 (쉼표로 구분)'}
                />
                {aggregatedData.allergens && aggregatedData.allergens.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {aggregatedData.allergens.map((allergen, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-red-100 text-red-800"
                      >
                        {allergen}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Nutrition Info */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  {i18n.language === 'en' ? 'Nutrition Information' : '영양 정보'}
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Calories */}
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">
                      {i18n.language === 'en' ? 'Calories (kcal)' : '칼로리 (kcal)'}
                    </label>
                    <input
                      type="number"
                      value={aggregatedData.nutrition_info?.calories ?? ''}
                      onChange={(e) => handleUpdateAggregatedNutrition('calories', e.target.value ? Number(e.target.value) : null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="0"
                    />
                  </div>

                  {/* Carbohydrates */}
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">
                      {i18n.language === 'en' ? 'Carbohydrates (g)' : '탄수화물 (g)'}
                    </label>
                    <input
                      type="number"
                      value={aggregatedData.nutrition_info?.carbohydrates ?? ''}
                      onChange={(e) => handleUpdateAggregatedNutrition('carbohydrates', e.target.value ? Number(e.target.value) : null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="0"
                    />
                  </div>

                  {/* Protein */}
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">
                      {i18n.language === 'en' ? 'Protein (g)' : '단백질 (g)'}
                    </label>
                    <input
                      type="number"
                      value={aggregatedData.nutrition_info?.protein ?? ''}
                      onChange={(e) => handleUpdateAggregatedNutrition('protein', e.target.value ? Number(e.target.value) : null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="0"
                    />
                  </div>

                  {/* Fat */}
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">
                      {i18n.language === 'en' ? 'Fat (g)' : '지방 (g)'}
                    </label>
                    <input
                      type="number"
                      value={aggregatedData.nutrition_info?.fat ?? ''}
                      onChange={(e) => handleUpdateAggregatedNutrition('fat', e.target.value ? Number(e.target.value) : null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="0"
                    />
                  </div>

                  {/* Sodium */}
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">
                      {i18n.language === 'en' ? 'Sodium (mg)' : '나트륨 (mg)'}
                    </label>
                    <input
                      type="number"
                      value={aggregatedData.nutrition_info?.sodium ?? ''}
                      onChange={(e) => handleUpdateAggregatedNutrition('sodium', e.target.value ? Number(e.target.value) : null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="0"
                    />
                  </div>

                  {/* Sugar */}
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">
                      {i18n.language === 'en' ? 'Sugar (g)' : '당류 (g)'}
                    </label>
                    <input
                      type="number"
                      value={aggregatedData.nutrition_info?.sugar ?? ''}
                      onChange={(e) => handleUpdateAggregatedNutrition('sugar', e.target.value ? Number(e.target.value) : null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                      placeholder="0"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 p-6 flex justify-end gap-3">
              <button
                onClick={() => setShowRegisterModal(false)}
                disabled={isSaving}
                className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors disabled:opacity-50"
              >
                {i18n.language === 'en' ? 'Cancel' : '취소'}
              </button>
              <button
                onClick={handleSaveProduct}
                disabled={isSaving}
                className="px-6 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {isSaving && (
                  <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                )}
                {isSaving
                  ? (i18n.language === 'en' ? 'Saving...' : '저장 중...')
                  : (i18n.language === 'en' ? 'Save to Database' : '데이터베이스에 저장')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// export default OCRScan;
