import React, { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';

interface UploadedImage {
  id: string;
  dataUrl: string;
  isAnalyzing: boolean;
}

const OCRScan: React.FC = () => {
  const { t } = useTranslation();
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
        const newImage: UploadedImage = {
          id: Date.now().toString() + Math.random().toString(36),
          dataUrl: e.target.result as string,
          isAnalyzing: true
        };

        setImages(prev => [...prev, newImage]);

        // Simulate analysis
        setTimeout(() => {
          setImages(prev => prev.map(img =>
            img.id === newImage.id ? { ...img, isAnalyzing: false } : img
          ));
        }, 2000);
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
          {t('ocr.제목')}
        </h1>
        <p className="text-gray-600">
          {t('ocr.부제목')}
        </p>
      </div>

      {/* Upload Area */}
      <div className="bg-white rounded-lg shadow-md p-8 mb-6">
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
            {t('ocr.업로드된_사진')} ({images.length}{t('ocr.개')})
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
                        <p className="text-sm text-gray-700">{t('ocr.분석중')}</p>
                      </div>
                    ) : (
                      <div className="text-center">
                        <p className="text-sm font-semibold text-gray-900 mb-1">
                          {t('ocr.분석결과')}
                        </p>
                        <p className="text-xs text-gray-600">
                          {t('ocr.분석실패')}
                        </p>
                      </div>
                    )}
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

export default OCRScan;
