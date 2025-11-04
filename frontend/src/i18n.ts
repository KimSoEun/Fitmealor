import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      "welcome": "Welcome to Fitmealor",
      "tagline": "AI-Powered Meal Recommendations for Foreigners in Korea",
      "login": "Login",
      "register": "Register",
      "logout": "Logout",
      "scan_food_label": "Scan Food Label",
      "get_recommendations": "Get Recommendations",
      "my_profile": "My Profile",
      "favorites": "Favorites",
      "meal_log": "Meal Log",
      "allergen_warning": "Allergen Warning",
      "safe_to_eat": "Safe to Eat",
      "not_safe": "NOT SAFE - Contains Allergens",
      "health_goal": "Health Goal",
      "allergies": "Allergies",
      "dietary_restrictions": "Dietary Restrictions"
    }
  },
  ko: {
    translation: {
      "welcome": "Fitmealor에 오신 것을 환영합니다",
      "tagline": "외국인을 위한 AI 기반 식단 추천 서비스",
      "login": "로그인",
      "register": "회원가입",
      "logout": "로그아웃",
      "scan_food_label": "식품 라벨 스캔",
      "get_recommendations": "추천 받기",
      "my_profile": "내 프로필",
      "favorites": "즐겨찾기",
      "meal_log": "식사 기록",
      "allergen_warning": "알레르기 경고",
      "safe_to_eat": "안전합니다",
      "not_safe": "위험 - 알레르기 성분 포함",
      "health_goal": "건강 목표",
      "allergies": "알레르기",
      "dietary_restrictions": "식이 제한"
    }
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
