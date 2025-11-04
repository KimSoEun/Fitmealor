## 🥗 Fitmealor

**외국인을 위한 건강정보 기반 AI 식단 추천 서비스**

> 영어 설명 + 알레르기 필터링 + TDEE 기반 맞춤 추천

---

### 📌 프로젝트 개요

Fitmealor는 한국에 거주하는 외국인들이

- 언어 장벽
- 알레르기 위험
- 건강 목표 설정

의 문제 없이 자신에게 맞는 식단을 선택할 수 있도록 돕는 **AI 기반 식단 큐레이션 플랫폼**입니다.

---

### 👤 주요 페르소나

| 이름 | 국적 | 특징 |
| --- | --- | --- |
| John | 미국 | 벌크업, 땅콩 알러지 |
| Aiko | 일본 | 다이어트, 유당불내증 |
| Ahmed | 말레이시아 | 근지구력, 할랄 |
| Maria | 스페인 | 채식, 철분 부족 |

---

### 🧭 사용자 시나리오

1. 건강정보 및 알러지 입력
2. AI가 TDEE 계산 + 알러지 필터링 + 영어 설명 생성
3. 식단 카드 확인 (성분, 영양소, 경고, 영어 설명)
4. 찜 / 공유 / 배달 연계 가능

---

### 🧩 핵심 기능 요약

- 🌍 언어 선택 (i18n)
- 🩺 건강정보 입력 (TDEE 계산 포함)
- ⚠️ 알러지 필터링 (다국어 키워드 매핑)
- 🧠 GPT 설명 생성 (Function Calling / JSON 스키마)
- 🍱 식단 카드 UI + 찜/공유/주문 기능

---

### ⚙️ 기술 스택

| 분야 | 사용 기술 |
| --- | --- |
| 프론트엔드 | React, TypeScript, Tailwind CSS, i18next |
| 백엔드 | FastAPI (Python), Node.js (TypeScript) |
| AI/ML | PyTorch, Transformers, OpenAI GPT-4 |
| OCR | CLOVA OCR, Donut (한글 식품 라벨 인식) |
| DB | PostgreSQL, ChromaDB, Redis |
| DevOps | Docker, Kubernetes, AWS |
| 배포 | Vercel, Docker, K8s |

---

### 📊 성능 지표 (MVP 기준)

| 항목 | 지표 | 목표 |
| --- | --- | --- |
| 안전 | 알러지 FN율 | 0% |
| 추천 | 영양소 편차율 | ≤ 15% |
| LLM | JSON 스키마 오류율 | ≤ 1% |
| 사용자 | 찜률 향상 | +15% (A/B 테스트) |
| 정성 품질 | 설명 자연스러움 | ≥ 4.0 (LLM 평가) |

---

### 🧠 추천 알고리즘 설계

- TDEE + 목표에 따른 매크로 비율 설정
- 필터링: 알러지 포함 식단 및 미적합 태그 제거
- 스코어링:
    - 영양소 편차율
    - 칼로리 근접도
    - 사용자 선호도
- 후처리: 다양성 보장 + 설명 생성 트리거링

---

### 🧪 GPT 설명 생성 방식

- **프롬프트 입력**: 음식명, 성분, 영양소, 알러지 여부 포함
- **출력 구조**: JSON 스키마 (Function Calling 기반)
- **검증기**:
    - 스키마 확인
    - 수치 검증
    - 금칙어 필터링
    - 할루시네이션 탐지 및 fail-closed 처리

예시:

```
title_en: "Grilled Chicken Breast with Broccoli"
summary_en: "High-protein, low-carb meal. Safe for peanut allergies."
macros: protein 35g / fat 10g / carbs 12g / 380kcal
allergen_safe: true

```

---

### 🗃️ 데이터베이스 스키마 요약

- `users`, `health_profiles`, `allergies`, `meals`, `descriptions`
- `events` (사용자 행동 로그), `recommendations` (추천 로그)
- GPT 설명은 `ChromaDB` 임베딩 저장 → 유사 질의 응답 활용
- A/B 테스트 데이터도 테이블화하여 정량 분석 가능

---

### 🔒 할루시네이션 방지 대책

- GPT 출력은 **JSON 스키마 강제**
- 서버 측 검증기 적용:
    - 필드 검증
    - 범위 검사
    - 금칙어 필터
- 실패 시 출력 차단 및 대체 문구 제공
- 모든 결과는 **감사로그 저장** (프롬프트, 응답, 검증 결과 포함)

---

### 🔮 확장 계획

- 정기배송 / 쇼핑몰 연계
- 피트니스 앱 연동 (삼성헬스 등)
- 게이미피케이션 기능: 스탬프, 레벨, 미션
- 식사 기록 기반 자동 식단 리빌딩
- 다국어 확장 (영어 → 일본어, 중국어 등)

---

### 🚀 시작하기

#### 사전 요구사항

- **Docker Desktop** (v20.10 이상)
- **Node.js** (v18 이상)
- **Python** (v3.10 이상)
- **PostgreSQL** (v14 이상) - Docker 사용 시 불필요

#### 설치 방법

1. **레포지토리 클론**
```bash
git clone https://github.com/KimSoEun/Fitmealor.git
cd Fitmealor
```

2. **환경 변수 설정**
```bash
# 루트 디렉토리에 .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 API 키 입력
# OPENAI_API_KEY=your_key_here
# CLOVA_OCR_SECRET=your_secret_here
```

3. **Docker Compose로 실행** (권장)
```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

4. **개별 서비스 실행** (로컬 개발용)

**데이터베이스**
```bash
docker-compose up -d postgres redis
```

**FastAPI 백엔드**
```bash
cd backend/fastapi-service
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Node.js API Gateway**
```bash
cd backend/nodejs-service
npm install
npm run dev
```

**React 프론트엔드**
```bash
cd frontend
npm install
npm run dev
```

#### 접속 URL

- 🌐 **프론트엔드**: http://localhost:3000
- 🔌 **Node.js API**: http://localhost:3001
- 🤖 **FastAPI**: http://localhost:8000
- 🗄️ **PostgreSQL**: localhost:5432

#### API 문서

- FastAPI Swagger UI: http://localhost:8000/docs
- FastAPI ReDoc: http://localhost:8000/redoc

---

### 📁 프로젝트 구조

```
fitmealor/
├── backend/
│   ├── fastapi-service/        # AI/OCR 서비스
│   │   ├── app/
│   │   │   ├── api/           # 라우터 (recommendations, ocr)
│   │   │   ├── models/        # AI 추천 모델
│   │   │   ├── services/      # OCR, 알레르기 탐지
│   │   │   └── core/          # 설정
│   │   └── requirements.txt
│   └── nodejs-service/         # API Gateway
│       ├── src/
│       │   ├── entities/      # TypeORM 엔티티
│       │   ├── routes/        # Express 라우터
│       │   ├── middleware/    # 인증, 에러 핸들링
│       │   └── config/        # DB 설정
│       └── package.json
├── frontend/                   # React 프론트엔드
│   ├── src/
│   │   ├── pages/            # Home, OCRScan, Recommendations
│   │   ├── components/       # Layout, MealCard
│   │   └── i18n.ts          # 다국어 설정
│   └── package.json
├── database/
│   └── init.sql              # PostgreSQL 초기 스키마
├── docker/
│   ├── Dockerfile.fastapi
│   ├── Dockerfile.nodejs
│   └── Dockerfile.frontend
├── k8s/                       # Kubernetes 배포
│   ├── deployment.yaml
│   └── service.yaml
└── docker-compose.yml
```

---

### 🧪 주요 API 엔드포인트

#### FastAPI (AI/OCR 서비스)

**식단 추천**
```bash
POST http://localhost:8000/api/v1/recommendations/recommend
Content-Type: application/json

{
  "user_id": "uuid",
  "age": 25,
  "gender": "male",
  "height_cm": 175,
  "weight_kg": 70,
  "target_weight_kg": 65,
  "activity_level": "moderate",
  "health_goal": "lose_weight",
  "allergies": ["peanuts", "milk"],
  "symptoms": ["피로", "어지러움"]
}
```

**OCR 스캔**
```bash
POST http://localhost:8000/api/v1/ocr/scan
Content-Type: multipart/form-data

file: [이미지 파일]
language: ko
```

**알레르기 탐지**
```bash
POST http://localhost:8000/api/v1/ocr/detect-allergens
Content-Type: application/json

{
  "text": "원재료: 밀가루, 우유, 계란, 설탕...",
  "user_allergens": ["milk", "eggs"],
  "language": "ko"
}
```

#### Node.js API Gateway

**회원가입**
```bash
POST http://localhost:3001/api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "password"
}
```

**로그인**
```bash
POST http://localhost:3001/api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}
```

---

### 🔧 개발 가이드

#### 코드 스타일

- **Python**: PEP 8, Black formatter
- **TypeScript**: ESLint, Prettier
- **Commit**: Conventional Commits

#### 브랜치 전략

- `main`: 프로덕션 브랜치
- `develop`: 개발 브랜치
- `feature/*`: 기능 개발
- `bugfix/*`: 버그 수정

#### 테스트

**FastAPI**
```bash
cd backend/fastapi-service
pytest
```

**Node.js**
```bash
cd backend/nodejs-service
npm test
```

---

### ✅ 프로젝트 일정 (2025 Q4)

| 주차 | 목표 내용 |
| --- | --- |
| W1 | 데이터 수집 및 추천 알고리즘 v0 구현 ✅ |
| W2 | GPT 설명 생성 + 검증기 구축 ✅ |
| W3 | UI 구성, A/B 테스트 기능 연동 🔄 |
| W4 | 통합 테스트 + 발표 자료 준비 |

---

### 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'feat: Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

### 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능합니다.

---

### 🙋 Contact

- **기획·개발**: 김소은
- **GitHub**: [KimSoEun/Fitmealor](https://github.com/KimSoEun/Fitmealor)
- **Email**: thdms7947@naver.com

---

### 🎉 Special Thanks

Built with ❤️ using [Claude Code](https://claude.com/claude-code)

> 건강한 식사, 지금 이 순간부터.
