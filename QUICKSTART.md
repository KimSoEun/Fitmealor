# 🚀 Fitmealor Quick Start Guide

## ⚡ 5분 안에 시작하기

### 1️⃣ 사전 준비

필요한 것:
- ✅ OpenAI API Key (설정 완료)
- ✅ CLOVA OCR API Key (설정 완료)
- 📦 Docker Desktop ([다운로드](https://www.docker.com/products/docker-desktop))

### 2️⃣ 프로젝트 클론

```bash
git clone https://github.com/KimSoEun/Fitmealor.git
cd Fitmealor
```

### 3️⃣ 환경 설정 (이미 완료됨 ✅)

```bash
# .env 파일이 이미 생성되어 있습니다
# API 키들이 설정되어 있습니다:
# - OPENAI_API_KEY ✅
# - CLOVA_OCR_SECRET ✅
# - CLOVA_OCR_URL ✅
```

### 4️⃣ Docker로 실행

```bash
# 모든 서비스 시작 (PostgreSQL, Redis, FastAPI, Node.js, React)
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 5️⃣ 접속

서비스들이 시작되면:

- 🌐 **프론트엔드**: http://localhost:3000
- 🔌 **API Gateway**: http://localhost:3001
- 🤖 **FastAPI**: http://localhost:8000
- 📚 **API 문서**: http://localhost:8000/docs

---

## 🧪 API 테스트

### OpenAI API 테스트

```bash
cd backend/fastapi-service
pip install openai python-dotenv
python -c "
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
response = client.chat.completions.create(
    model='gpt-4',
    messages=[{'role': 'user', 'content': 'Hello!'}],
    max_tokens=10
)
print('✅ OpenAI API:', response.choices[0].message.content)
"
```

### 식단 추천 API 테스트

```bash
curl -X POST http://localhost:8000/api/v1/recommendations/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "age": 25,
    "gender": "male",
    "height_cm": 175,
    "weight_kg": 70,
    "target_weight_kg": 65,
    "activity_level": "moderate",
    "health_goal": "lose_weight",
    "allergies": ["peanuts"],
    "dietary_restrictions": [],
    "symptoms": ["피로"],
    "num_recommendations": 3
  }'
```

### OCR 테스트 (이미지 파일 필요)

```bash
# 식품 라벨 이미지를 준비하고
curl -X POST http://localhost:8000/api/v1/ocr/scan \
  -F "file=@your_food_label.jpg" \
  -F "language=ko"
```

---

## 📱 프론트엔드 기능

### 메인 페이지
- 🏠 홈: 서비스 소개 및 주요 기능
- 🔍 OCR 스캔: 식품 라벨 촬영 및 알레르기 탐지
- 🤖 AI 추천: 개인화된 식단 추천
- ❤️ 즐겨찾기: 저장된 식단 관리

### 다국어 지원
- 🇺🇸 English
- 🇰🇷 한국어
- 🇨🇳 中文
- 🇯🇵 日本語

---

## 🛠️ 로컬 개발 (Docker 없이)

### 데이터베이스 시작
```bash
# PostgreSQL 및 Redis만 Docker로 실행
docker-compose up -d postgres redis
```

### FastAPI 백엔드
```bash
cd backend/fastapi-service
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Node.js API Gateway
```bash
cd backend/nodejs-service
npm install
npm run dev
```

### React 프론트엔드
```bash
cd frontend
npm install
npm run dev
```

---

## 🎯 주요 기능 시연

### 1. 건강 프로필 설정
```json
{
  "age": 28,
  "gender": "male",
  "height_cm": 175,
  "weight_kg": 70,
  "target_weight_kg": 65,
  "activity_level": "moderate",
  "health_goal": "lose_weight",
  "allergies": ["peanuts", "milk"],
  "dietary_restrictions": ["vegetarian"]
}
```

→ **결과**: TDEE 자동 계산, 맞춤 식단 추천

### 2. 식품 라벨 OCR
이미지 업로드 → 한글 텍스트 인식 → 알레르기 성분 탐지

→ **결과**: 
- ✅ Safe (안전)
- ⚠️ Caution (주의)
- 🚫 Danger (위험)

### 3. AI 식단 추천
증상 입력 (예: "피로", "어지러움") → GPT-4 영양소 분석

→ **결과**: 
- 부족 영양소 진단
- 추천 음식 리스트
- 영양 정보 상세
- 다국어 설명

---

## 📊 시스템 아키텍처

```
┌─────────────┐
│   React     │ Frontend (Port 3000)
│   + i18n    │
└──────┬──────┘
       │
┌──────▼──────┐
│  Node.js    │ API Gateway (Port 3001)
│  Express    │ - JWT Auth
└──────┬──────┘ - User Management
       │
   ┌───┴────┐
   │        │
┌──▼──┐  ┌─▼────┐
│Fast │  │Post- │
│ API │  │greSQL│
└──┬──┘  └──────┘
   │
┌──▼──────────┐
│  PyTorch    │ AI Models
│  GPT-4      │ - TDEE Calculation
│  CLOVA OCR  │ - Nutrition Analysis
└─────────────┘ - Allergen Detection
```

---

## 🔧 문제 해결

### Docker가 실행되지 않음
```bash
# Docker Desktop이 실행 중인지 확인
docker --version

# Docker 서비스 재시작
# macOS: Docker Desktop 앱 재실행
# Linux: sudo systemctl restart docker
```

### 포트가 이미 사용 중
```bash
# 사용 중인 포트 확인 (macOS/Linux)
lsof -i :3000
lsof -i :3001
lsof -i :8000

# 프로세스 종료
kill -9 <PID>
```

### API 키 오류
```bash
# 환경 변수 확인
cat .env | grep API_KEY

# .env 파일이 올바른 위치에 있는지 확인
ls -la .env
```

---

## 📚 추가 문서

- 📖 [README.md](./README.md) - 전체 프로젝트 개요
- 📋 [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - 상세 구현 문서
- 🔌 [API 문서](http://localhost:8000/docs) - Swagger UI (서비스 실행 후)

---

## 🆘 도움이 필요하신가요?

- 📧 Email: thdms7947@naver.com
- 💻 GitHub Issues: https://github.com/KimSoEun/Fitmealor/issues
- 📝 GitHub: https://github.com/KimSoEun/Fitmealor

---

## ✨ 다음 단계

1. ✅ API 키 설정 완료
2. 🚀 Docker로 서비스 실행
3. 🧪 API 테스트
4. 🎨 프론트엔드 개발 계속
5. 📊 데이터베이스에 샘플 식단 추가
6. 🧪 통합 테스트
7. 🚢 프로덕션 배포

---

**Built with ❤️ using Claude Code**

> 건강한 식사, 지금 이 순간부터.
