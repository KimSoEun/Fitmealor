# Fitmealor GCP 배포 가이드

이 문서는 Fitmealor 프로젝트를 Google Cloud Platform (GCP)을 사용하여 배포하는 방법을 안내합니다.

## 배포 아키텍처

- **Frontend**: Firebase Hosting (React + Vite)
- **Backend**: Cloud Run (FastAPI, Containerized)
- **Database**: Cloud SQL (PostgreSQL)
- **Container Registry**: Google Container Registry (GCR)

## 장점

✅ **$300 무료 크레딧** (90일간 사용 가능)
✅ **서울 리전** (asia-northeast3) 사용 가능
✅ **Cloud Run**: 사용한 만큼만 과금, idle 시 거의 무료
✅ **Firebase Hosting**: 무료 티어로 충분
✅ **Cloud SQL**: 무료 크레딧 사용 가능
✅ **빠른 Cold Start** (Render보다 빠름)
✅ **Auto Scaling**: 트래픽에 따라 자동 확장

## 사전 요구사항

- Google 계정
- 신용카드 (무료 크레딧 받기 위해 필요, 자동 청구 없음)
- gcloud CLI 설치 (옵션, 터미널 배포 시)

---

## 1. GCP 프로젝트 생성

### 1.1 GCP Console 접속

1. https://console.cloud.google.com 접속
2. Google 계정으로 로그인
3. 무료 평가판 시작 ($300 크레딧)
   - 신용카드 정보 입력 (자동 청구 없음)
   - 국가: 한국 선택

### 1.2 새 프로젝트 생성

1. 상단 "프로젝트 선택" 드롭다운 클릭
2. "새 프로젝트" 클릭
3. 프로젝트 이름: `fitmealor`
4. "만들기" 클릭
5. 프로젝트 ID 기록 (예: `fitmealor-12345`)

### 1.3 결제 계정 연결

1. 좌측 메뉴 > "결제" 클릭
2. 무료 평가판 결제 계정과 연결
3. **중요**: 무료 크레딧($300) 사용 중에는 자동 청구되지 않음

---

## 2. Cloud SQL PostgreSQL 데이터베이스 생성

### 2.1 Cloud SQL API 활성화

1. GCP Console에서 검색창에 "Cloud SQL" 검색
2. "Cloud SQL API 사용 설정" 클릭

### 2.2 인스턴스 생성

1. "인스턴스 만들기" 클릭
2. "PostgreSQL" 선택
3. 다음 설정 입력:
   - **인스턴스 ID**: `fitmealor-db`
   - **비밀번호**: 강력한 비밀번호 설정 (기록 필수)
   - **데이터베이스 버전**: PostgreSQL 15
   - **리전**: `asia-northeast3` (서울)
   - **영역**: 단일 영역

4. **머신 구성**:
   - **프리셋**: "샌드박스" 또는 "개발" 선택
   - **머신 유형**: Shared core (1 vCPU, 0.614GB) - 가장 저렴
   - **스토리지**: 10GB SSD
   - **자동 백업**: 비활성화 (비용 절감)

5. **연결**:
   - **공개 IP**: 체크
   - **승인된 네트워크**: 나중에 설정

6. "인스턴스 만들기" 클릭 (5-10분 소요)

### 2.3 데이터베이스 생성

인스턴스 생성 완료 후:

1. 인스턴스 이름(`fitmealor-db`) 클릭
2. "데이터베이스" 탭 클릭
3. "데이터베이스 만들기" 클릭
   - **데이터베이스 이름**: `fitmealor`
   - "만들기" 클릭

### 2.4 연결 정보 기록

1. "개요" 탭에서 다음 정보 기록:
   - **공개 IP 주소**: `xxx.xxx.xxx.xxx`
   - **연결 이름**: `fitmealor-12345:asia-northeast3:fitmealor-db`

2. DATABASE_URL 형식:
   ```
   postgresql://postgres:YOUR_PASSWORD@xxx.xxx.xxx.xxx:5432/fitmealor
   ```

---

## 3. Cloud Run으로 백엔드 배포

### 3.1 Cloud Run API 활성화

1. 검색창에 "Cloud Run" 검색
2. "Cloud Run API 사용 설정" 클릭

### 3.2 gcloud CLI 설치 (옵션)

**터미널 배포 선호 시 설치:**

MacOS:
```bash
brew install google-cloud-sdk
```

Windows:
- https://cloud.google.com/sdk/docs/install 에서 설치 프로그램 다운로드

**인증:**
```bash
gcloud auth login
gcloud config set project fitmealor-12345  # 프로젝트 ID로 변경
```

### 3.3 Cloud Run 배포 (gcloud CLI 사용)

**옵션 A: gcloud CLI로 배포 (권장)**

```bash
# 프로젝트 루트에서 실행
cd backend/fastapi-service

# Cloud Run에 배포
gcloud run deploy fitmealor-backend \
  --source . \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@xxx.xxx.xxx.xxx:5432/fitmealor" \
  --set-env-vars OPENAI_API_KEY="your_openai_api_key" \
  --set-env-vars CLOVA_OCR_SECRET="your_clova_ocr_secret" \
  --set-env-vars CLOVA_OCR_URL="your_clova_ocr_url" \
  --set-env-vars ENVIRONMENT="production" \
  --set-env-vars DEBUG="False"
```

**옵션 B: GCP Console로 배포**

1. Cloud Run 페이지에서 "서비스 만들기" 클릭
2. "소스 코드 저장소에서 지속적으로 배포" 선택
3. Cloud Build API 활성화
4. GitHub 계정 연결
5. 저장소 선택: `KimSoEun/Fitmealor`
6. 브랜치: `main`
7. 빌드 유형: Dockerfile
8. Dockerfile 경로: `backend/fastapi-service/Dockerfile`
9. 다음 설정:
   - **서비스 이름**: `fitmealor-backend`
   - **리전**: `asia-northeast3` (서울)
   - **CPU 할당**: 요청을 처리하는 동안에만 할당 (비용 절감)
   - **최소 인스턴스 수**: 0 (idle 시 비용 없음)
   - **최대 인스턴스 수**: 10
   - **메모리**: 512MB

10. **환경 변수** 설정:
    ```
    DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@xxx.xxx.xxx.xxx:5432/fitmealor
    OPENAI_API_KEY=your_openai_api_key
    CLOVA_OCR_SECRET=your_clova_ocr_secret
    CLOVA_OCR_URL=your_clova_ocr_url
    ENVIRONMENT=production
    DEBUG=False
    ```

11. **인증**: "미인증 호출 허용" 체크
12. "만들기" 클릭

### 3.4 배포 완료 및 URL 확인

배포 완료 후 Cloud Run 서비스 URL 확인:
```
https://fitmealor-backend-xxxxx-an.a.run.app
```

### 3.5 Cloud SQL 연결 설정

Cloud SQL과 연결하려면 추가 설정 필요:

1. Cloud Run 서비스 페이지에서 "수정 및 새 버전 배포" 클릭
2. "연결" 탭 클릭
3. "Cloud SQL 연결" 섹션:
   - "Cloud SQL 인스턴스 추가" 클릭
   - `fitmealor-db` 선택
4. 환경 변수에서 DATABASE_URL 수정:
   ```
   # Unix 소켓 방식 (권장)
   postgresql://postgres:YOUR_PASSWORD@/fitmealor?host=/cloudsql/fitmealor-12345:asia-northeast3:fitmealor-db
   ```
5. "배포" 클릭

---

## 4. 데이터베이스 마이그레이션

### 4.1 로컬에서 마이그레이션 실행

**방법 1: 로컬에서 Cloud SQL에 연결**

```bash
# Cloud SQL 공개 IP에 연결 (로컬 IP 허용 필요)
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@xxx.xxx.xxx.xxx:5432/fitmealor"

cd backend/fastapi-service
alembic upgrade head
```

**주의**: Cloud SQL 인스턴스에 로컬 IP를 승인된 네트워크에 추가해야 합니다:
1. Cloud SQL 인스턴스 > "연결" 탭
2. "네트워킹" > "승인된 네트워크" > "네트워크 추가"
3. 내 IP 주소 입력 (https://www.whatismyip.com 에서 확인)

**방법 2: Cloud Run 서비스에서 실행**

Cloud Run 인스턴스에 직접 접속하여 마이그레이션 실행:

```bash
# Cloud Run 인스턴스 목록 확인
gcloud run services list

# Cloud Run 컨테이너에 접속 (일회성 작업 실행)
gcloud run jobs create fitmealor-migrate \
  --image gcr.io/PROJECT_ID/fitmealor-backend:latest \
  --region asia-northeast3 \
  --set-env-vars DATABASE_URL="..." \
  --command alembic \
  --args "upgrade,head"

gcloud run jobs execute fitmealor-migrate --region asia-northeast3
```

---

## 5. Firebase로 프론트엔드 배포

### 5.1 Firebase 프로젝트 생성

1. https://console.firebase.google.com 접속
2. "프로젝트 추가" 클릭
3. **프로젝트 선택**: "기존 Google Cloud 프로젝트 선택"
   - `fitmealor` 선택
4. Firebase 약관 동의
5. Google Analytics 비활성화 (옵션)
6. "Firebase 추가" 클릭

### 5.2 Firebase CLI 설치

```bash
npm install -g firebase-tools
```

### 5.3 Firebase 로그인

```bash
firebase login
```

### 5.4 프론트엔드 빌드

```bash
cd frontend

# 환경 변수 설정
export VITE_API_URL="https://fitmealor-backend-xxxxx-an.a.run.app"

# 빌드
npm run build
```

### 5.5 Firebase 프로젝트 초기화

```bash
# frontend 디렉토리에서 실행
firebase init hosting

# 다음 옵션 선택:
# - Project: fitmealor (기존 프로젝트 선택)
# - Public directory: dist
# - Single-page app: Yes
# - GitHub Actions: No (나중에 설정)
```

### 5.6 Firebase 배포

```bash
# frontend 디렉토리에서 실행
firebase deploy --only hosting
```

배포 완료 후 URL 확인:
```
https://fitmealor.web.app
또는
https://fitmealor.firebaseapp.com
```

---

## 6. CORS 설정

백엔드 코드에서 Firebase Hosting URL을 CORS allowed origins에 추가:

`backend/fastapi-service/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://fitmealor.web.app",
        "https://fitmealor.firebaseapp.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

변경 후 다시 배포:
```bash
cd backend/fastapi-service
gcloud run deploy fitmealor-backend --source .
```

---

## 7. 환경 변수 관리 (Secret Manager 사용)

보안을 위해 Secret Manager 사용 권장:

### 7.1 Secret Manager API 활성화

```bash
gcloud services enable secretmanager.googleapis.com
```

### 7.2 시크릿 생성

```bash
# DATABASE_URL 저장
echo -n "postgresql://..." | gcloud secrets create database-url --data-file=-

# OPENAI_API_KEY 저장
echo -n "your_openai_api_key" | gcloud secrets create openai-api-key --data-file=-

# CLOVA_OCR_SECRET 저장
echo -n "your_clova_secret" | gcloud secrets create clova-ocr-secret --data-file=-

# CLOVA_OCR_URL 저장
echo -n "your_clova_url" | gcloud secrets create clova-ocr-url --data-file=-
```

### 7.3 Cloud Run에서 시크릿 사용

```bash
gcloud run deploy fitmealor-backend \
  --source . \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --update-secrets DATABASE_URL=database-url:latest \
  --update-secrets OPENAI_API_KEY=openai-api-key:latest \
  --update-secrets CLOVA_OCR_SECRET=clova-ocr-secret:latest \
  --update-secrets CLOVA_OCR_URL=clova-ocr-url:latest \
  --set-env-vars ENVIRONMENT=production,DEBUG=False
```

---

## 8. 자동 배포 (GitHub Actions) - 선택사항

`.github/workflows/deploy-gcp.yml` 파일이 이미 포함되어 있습니다.

### 8.1 서비스 계정 생성

```bash
# 서비스 계정 생성
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"

# 권한 부여
gcloud projects add-iam-policy-binding fitmealor-12345 \
  --member="serviceAccount:github-actions@fitmealor-12345.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding fitmealor-12345 \
  --member="serviceAccount:github-actions@fitmealor-12345.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# 키 생성
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions@fitmealor-12345.iam.gserviceaccount.com
```

### 8.2 GitHub Secrets 설정

GitHub 저장소 > Settings > Secrets and variables > Actions:

1. `GCP_PROJECT_ID`: `fitmealor-12345`
2. `GCP_SA_KEY`: `key.json` 파일 내용 전체 복사
3. `DATABASE_URL`: Cloud SQL 연결 문자열
4. `OPENAI_API_KEY`: OpenAI API 키
5. `CLOVA_OCR_SECRET`: Clova OCR Secret
6. `CLOVA_OCR_URL`: Clova OCR URL
7. `VITE_API_URL`: Cloud Run 백엔드 URL
8. `FIREBASE_SERVICE_ACCOUNT`: Firebase 서비스 계정 JSON
9. `FIREBASE_PROJECT_ID`: `fitmealor`

### 8.3 자동 배포 확인

이제 `main` 브랜치에 push하면 자동으로 배포됩니다!

---

## 9. 비용 최적화

### 9.1 무료 크레딧 모니터링

1. GCP Console > "결제" 클릭
2. "보고서" 탭에서 사용량 확인
3. 알림 설정: 예산 $50 도달 시 이메일 알림

### 9.2 Cloud Run 비용 절감

- **최소 인스턴스**: 0 설정 (idle 시 비용 없음)
- **CPU 할당**: "요청 처리 중에만" 선택
- **메모리**: 512MB (필요 시 증가)
- **동시 요청**: 80 (기본값)

### 9.3 Cloud SQL 비용 절감

- **머신 유형**: Shared core 사용
- **스토리지**: 필요한 최소 용량만
- **자동 백업**: 비활성화 (개발 단계)
- **고가용성**: 비활성화 (단일 영역)

### 9.4 예상 비용 (무료 크레딧 이후)

**Cloud Run** (월 트래픽 가정: 10,000 요청):
- 요청: 무료 (200만 요청까지 무료)
- CPU: $1-2
- 메모리: $0.5-1
- **합계**: ~$2-3/월

**Cloud SQL** (db-f1-micro, 10GB):
- 인스턴스: $7-10/월
- 스토리지: $0.17/GB/월 = $1.7/월
- **합계**: ~$9-12/월

**Firebase Hosting**:
- 완전 무료 (10GB 저장, 360MB/일 전송)

**총 예상 비용**: ~$11-15/월 (무료 크레딧 이후)

---

## 10. 모니터링 및 로그

### 10.1 Cloud Run 로그

```bash
# 실시간 로그 확인
gcloud run services logs read fitmealor-backend --region asia-northeast3 --follow

# 또는 GCP Console에서:
# Cloud Run > fitmealor-backend > 로그 탭
```

### 10.2 Cloud SQL 모니터링

1. Cloud SQL > `fitmealor-db` 클릭
2. "모니터링" 탭에서 CPU, 메모리, 연결 수 확인

### 10.3 Firebase Hosting 모니터링

1. Firebase Console > Hosting
2. "사용량" 탭에서 트래픽 확인

---

## 11. 문제 해결

### Cloud Run 배포 실패

**문제**: Dockerfile 빌드 실패

**해결책**:
```bash
# 로컬에서 Docker 빌드 테스트
cd backend/fastapi-service
docker build -t test-image .
docker run -p 8000:8000 test-image
```

### Cloud SQL 연결 실패

**문제**: Cloud Run에서 데이터베이스 연결 불가

**해결책**:
1. Cloud Run 서비스에 Cloud SQL 인스턴스 연결 확인
2. DATABASE_URL이 Unix 소켓 경로 사용하는지 확인:
   ```
   postgresql://postgres:PASSWORD@/fitmealor?host=/cloudsql/PROJECT:REGION:INSTANCE
   ```

### Firebase 배포 실패

**문제**: `firebase deploy` 시 권한 오류

**해결책**:
```bash
# 로그아웃 후 재로그인
firebase logout
firebase login

# 프로젝트 재설정
firebase use fitmealor
```

### CORS 에러

**문제**: 프론트엔드에서 백엔드 API 호출 시 CORS 에러

**해결책**:
1. `main.py`에서 Firebase URL이 `allow_origins`에 포함되었는지 확인
2. Cloud Run 재배포:
   ```bash
   cd backend/fastapi-service
   gcloud run deploy fitmealor-backend --source .
   ```

---

## 12. 배포 체크리스트

### GCP 설정

- [ ] GCP 프로젝트 생성
- [ ] 무료 크레딧 활성화
- [ ] 결제 계정 연결

### Cloud SQL

- [ ] Cloud SQL 인스턴스 생성
- [ ] 데이터베이스 생성
- [ ] 연결 정보 기록
- [ ] Alembic 마이그레이션 실행

### Cloud Run (백엔드)

- [ ] Cloud Run API 활성화
- [ ] Docker 이미지 빌드 및 배포
- [ ] 환경 변수 설정
  - [ ] DATABASE_URL
  - [ ] OPENAI_API_KEY
  - [ ] CLOVA_OCR_SECRET
  - [ ] CLOVA_OCR_URL
  - [ ] ENVIRONMENT=production
  - [ ] DEBUG=False
- [ ] Cloud SQL 연결 설정
- [ ] `/health` 엔드포인트 테스트

### Firebase Hosting (프론트엔드)

- [ ] Firebase 프로젝트 생성
- [ ] Firebase CLI 설치
- [ ] `VITE_API_URL` 환경 변수 설정
- [ ] 프론트엔드 빌드 (`npm run build`)
- [ ] Firebase 배포
- [ ] 배포된 URL 확인

### CORS 및 테스트

- [ ] `main.py`에 Firebase URL 추가
- [ ] Cloud Run 재배포
- [ ] 회원가입 테스트
- [ ] 로그인 테스트
- [ ] 식단 추천 테스트
- [ ] OCR 스캔 테스트
- [ ] 히스토리 기능 테스트

### 선택사항

- [ ] Secret Manager 설정
- [ ] GitHub Actions CI/CD 설정
- [ ] Custom Domain 설정
- [ ] Cloud Monitoring 알림 설정

---

## 13. Custom Domain 설정 (선택사항)

### 13.1 Firebase Hosting Custom Domain

1. Firebase Console > Hosting > "도메인 추가" 클릭
2. 도메인 입력 (예: `fitmealor.com`)
3. DNS 레코드 추가 (도메인 등록업체에서 설정)
4. SSL 인증서 자동 발급 대기 (최대 24시간)

### 13.2 Cloud Run Custom Domain

```bash
gcloud beta run domain-mappings create \
  --service fitmealor-backend \
  --domain api.fitmealor.com \
  --region asia-northeast3
```

---

## 지원

문제가 발생하면 GitHub Issues에 문의하세요:
https://github.com/KimSoEun/Fitmealor/issues

## 참고 링크

- GCP 문서: https://cloud.google.com/docs
- Cloud Run 문서: https://cloud.google.com/run/docs
- Firebase Hosting 문서: https://firebase.google.com/docs/hosting
- Cloud SQL 문서: https://cloud.google.com/sql/docs
