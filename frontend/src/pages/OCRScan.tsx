import React, { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';

const OCRScan: React.FC = () => {
  const { t } = useTranslation();
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
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

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFile(files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      handleFile(files[0]);
    }
  };

  const handleFile = (file: File) => {
    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert(t('ocr.업로드실패'));
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert(t('ocr.업로드실패'));
      return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      if (e.target?.result) {
        setSelectedImage(e.target.result as string);
        // Simulate analysis
        setIsAnalyzing(true);
        setTimeout(() => {
          setIsAnalyzing(false);
        }, 2000);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleReset = () => {
    setSelectedImage(null);
    setIsAnalyzing(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {t('ocr.제목')}
        </h1>
        <p className="text-gray-600">
          {t('ocr.부제목')}
        </p>
      </div>

      {/* Upload Area */}
      {!selectedImage ? (
        <div className="bg-white rounded-lg shadow-md p-8">
          <p className="text-lg text-gray-700 mb-6 text-center">
            {t('ocr.안내문구')}
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
              {t('ocr.업로드영역_제목')}
            </p>
            <p className="text-sm text-gray-500">
              {t('ocr.업로드영역_설명')}
            </p>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileInput}
              className="hidden"
            />
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-8">
          {/* Image Preview */}
          <div className="mb-6">
            <img
              src={selectedImage}
              alt="Uploaded food label"
              className="max-w-full max-h-96 mx-auto rounded-lg shadow-md"
            />
          </div>

          {/* Analysis Status */}
          {isAnalyzing ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
              <p className="text-lg text-gray-700">{t('ocr.분석중')}</p>
            </div>
          ) : (
            <div className="text-center">
              <div className="bg-gray-50 rounded-lg p-6 mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  {t('ocr.분석결과')}
                </h2>
                <p className="text-gray-600">
                  {t('ocr.분석실패')}
                </p>
              </div>

              <button
                onClick={handleReset}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                {t('ocr.다시_업로드')}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default OCRScan;
