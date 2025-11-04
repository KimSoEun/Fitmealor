import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

const Home: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="text-center">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">{t('welcome')}</h1>
      <p className="text-xl text-gray-600 mb-8">{t('tagline')}</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link to="/ocr-scan" className="bg-primary text-white p-6 rounded-lg hover:bg-primary-dark">
          <h3 className="text-xl font-semibold mb-2">{t('scan_food_label')}</h3>
          <p>Scan Korean food labels to detect allergens</p>
        </Link>
        <Link to="/recommendations" className="bg-secondary text-white p-6 rounded-lg hover:bg-secondary-dark">
          <h3 className="text-xl font-semibold mb-2">{t('get_recommendations')}</h3>
          <p>Get AI-powered meal recommendations</p>
        </Link>
        <Link to="/health-profile" className="bg-green-600 text-white p-6 rounded-lg hover:bg-green-700">
          <h3 className="text-xl font-semibold mb-2">{t('my_profile')}</h3>
          <p>Manage your health profile and goals</p>
        </Link>
      </div>
    </div>
  );
};

export default Home;
