import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import enTranslations from './locales/en.json';
import koTranslations from './locales/ko.json';

const resources = {
  en: {
    translation: enTranslations
  },
  ko: {
    translation: koTranslations
  },
  zh: {
    translation: {
      "welcome": "欢迎来到Fitmealor",
      "tagline": "为在韩外国人提供的AI饮食推荐服务",
      "login": "登录",
      "register": "注册",
      "logout": "登出",
      "scan_food_label": "扫描食品标签",
      "get_recommendations": "获取推荐",
      "my_profile": "我的资料",
      "favorites": "收藏夹",
      "meal_log": "饮食记录"
    }
  },
  ja: {
    translation: {
      "welcome": "Fitmealorへようこそ",
      "tagline": "在韓外国人のためのAI食事推薦サービス",
      "login": "ログイン",
      "register": "登録",
      "logout": "ログアウト",
      "scan_food_label": "食品ラベルスキャン",
      "get_recommendations": "おすすめを取得",
      "my_profile": "マイプロフィール",
      "favorites": "お気に入り",
      "meal_log": "食事記録"
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
