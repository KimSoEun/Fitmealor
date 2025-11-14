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
}

export default function OCRScan() {
// const OCRScan: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [images, setImages] = useState<UploadedImage[]>([]);
  const [isDragging, setIsDragging] = useState(false);
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

                    {/* Delete Button */}
                    <button
                      onClick={() => handleDelete(image.id)}
                      className="absolute top-2 right-2 bg-red-500 text-white p-2 rounded-full hover:bg-red-600 transition-colors opacity-0 group-hover:opacity-100"
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
                      <div className="text-left text-sm space-y-2">
                        <p className="font-semibold text-gray-900 mb-2">
                          {/* {t('ocr.분석결과')} */}
                          {i18n.language === 'en' ? 'Analysis Result' : '분석 결과'}
                        </p>

                        {/* Product Name */}
                        {image.extractedData.product_name && (
                          <div>
                            <span className="font-medium text-gray-700">
                              {/* {t('ocr.제품명')}:  */}
                              {i18n.language === 'en' ? 'Product Name' : '제품명'}: 
                            </span>
                            <span className="text-gray-600">{image.extractedData.product_name}</span>
                          </div>
                        )}

                        {/* Allergens */}
                        {image.extractedData.allergens && image.extractedData.allergens.length > 0 && (
                          <div>
                            <span className="font-medium text-gray-700">
                              {/* {t('ocr.알러지_성분')}:  */}
                              {i18n.language === 'en' ? 'Allergen Ingredients' : '알러지 유발 성분'}: 
                            </span>
                            <span className="text-gray-600">
                              {image.extractedData.allergens.join(', ')}
                            </span>
                          </div>
                        )}

                        {/* Nutrition Info */}
                        {/* {console.log(
                          image.extractedData.nutrition_info
                        )} */}
                        {image.extractedData.nutrition_info && Object.keys(image.extractedData.nutrition_info).length > 0 && (
                          <div>
                            <span className="font-medium text-gray-700">
                              {/* {t('ocr.영양_정보')} */}
                              {i18n.language === 'en' ? 'Nutrition Information' : '영양 정보'}
                            </span>
                            <div className="ml-2 mt-1 space-y-1 text-xs">
                              {(image.extractedData.nutrition_info.calories || image.extractedData.nutrition_info.calories==0) && (
                                <div>
                                  {/* {t('ocr.칼로리')} */}
                                  {i18n.language === 'en' ? 'Calories' : '칼로리'}
                                  : {image.extractedData.nutrition_info.calories} kcal</div>
                              )}
                              {(image.extractedData.nutrition_info.carbohydrates || image.extractedData.nutrition_info.carbohydrates==0) && (
                                <div>
                                  {/* {t('ocr.탄수화물')} */}
                                  {i18n.language === 'en' ? 'Carbohydrates' : '탄수화물'}
                                  : {image.extractedData.nutrition_info.carbohydrates} g</div>
                              )}
                              {(image.extractedData.nutrition_info.protein || image.extractedData.nutrition_info.protein==0) && (
                                <div>
                                  {/* {t('ocr.단백질')} */}
                                  {i18n.language === 'en' ? 'Protein' : '단백질'}
                                  : {image.extractedData.nutrition_info.protein} g</div>
                              )}
                              {(image.extractedData.nutrition_info.fat || image.extractedData.nutrition_info.fat==0) && (
                                <div>
                                  {/* {t('ocr.지방')} */}
                                  {i18n.language === 'en' ? 'Fat' : '지방'}
                                  : {image.extractedData.nutrition_info.fat} g</div>
                              )}
                              {(image.extractedData.nutrition_info.sodium || image.extractedData.nutrition_info.sodium) && (
                                <div>
                                  {/* {t('ocr.나트륨')} */}
                                  {i18n.language === 'en' ? 'Sodium' : '나트륨'}
                                  : {image.extractedData.nutrition_info.sodium} mg</div>
                              )}
                              {(image.extractedData.nutrition_info.sugar || image.extractedData.nutrition_info.sugar==0) && (
                                <div>
                                  {/* {t('ocr.당류')} */}
                                  {i18n.language === 'en' ? 'Sugar' : '당'}
                                  : {image.extractedData.nutrition_info.sugar} g</div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// export default OCRScan;
