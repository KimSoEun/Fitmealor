import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      "welcome": "Welcome to Fitmealor",
      "tagline": "Healthy Meal Recommendation Service",
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
      "dietary_restrictions": "Dietary Restrictions",
      "email": "Email",
      "password": "Password",
      "confirm_password": "Confirm Password",
      "remember_me": "Remember me",
      "forgot_password": "Forgot password?",
      "no_account": "Don't have an account?",
      "already_have_account": "Already have an account?",
      "or": "or",
      "name": "Name",
      "age": "Age",
      "gender": "Gender",
      "male": "Male",
      "female": "Female",
      "prefer_not_to_say": "Prefer not to say",
      "height": "Height (cm)",
      "weight": "Weight (kg)",
      "target_weight": "Target Weight (kg)",
      "activity_level": "Activity Level",
      "activity_sedentary": "Sedentary (Rarely exercises)",
      "activity_lightly_active": "Lightly Active (1-3 times/week)",
      "activity_active": "Active (3-5 times/week)",
      "activity_very_active": "Very Active (6-7 times/week)",
      "goal_weight_loss": "Weight Loss",
      "goal_maintain": "Maintain Weight",
      "goal_muscle_gain": "Muscle Gain",
      "health_info": "Health Information",
      "agree_terms": "I agree to the",
      "terms_of_service": "Terms of Service",
      "and": "and",
      "privacy_policy": "Privacy Policy",
      "home": "Home",
      "health_profile": "Health Profile",
      "ocr_scan": "OCR Scan",
      "recommendations": "Recommendations"
    }
  },
  ko: {
    translation: {
      "welcome": "Fitmealor에 오신 것을 환영합니다",
      "tagline": "건강한 식단 추천 서비스",
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
      "dietary_restrictions": "식이 제한",
      "email": "이메일",
      "password": "비밀번호",
      "confirm_password": "비밀번호 확인",
      "remember_me": "로그인 상태 유지",
      "forgot_password": "비밀번호 찾기",
      "no_account": "계정이 없으신가요?",
      "already_have_account": "이미 계정이 있으신가요?",
      "or": "또는",
      "name": "이름",
      "age": "나이",
      "gender": "성별",
      "male": "남성",
      "female": "여성",
      "prefer_not_to_say": "선택 안 함",
      "height": "키 (cm)",
      "weight": "체중 (kg)",
      "target_weight": "목표 체중 (kg)",
      "activity_level": "활동 수준",
      "activity_sedentary": "비활동적 (거의 운동 안 함)",
      "activity_lightly_active": "가볍게 활동적 (주 1-3회 운동)",
      "activity_active": "활동적 (주 3-5회 운동)",
      "activity_very_active": "매우 활동적 (주 6-7회 운동)",
      "goal_weight_loss": "체중감량",
      "goal_maintain": "체중유지",
      "goal_muscle_gain": "근육증가",
      "health_info": "건강 정보",
      "agree_terms": "에 동의합니다",
      "terms_of_service": "이용약관",
      "and": "및",
      "privacy_policy": "개인정보처리방침",
      "home": "홈",
      "health_profile": "건강 프로필",
      "ocr_scan": "OCR 스캔",
      "recommendations": "추천"
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
