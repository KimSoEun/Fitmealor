# Fitmealor Vercel + Render 배포 가이드

이 문서는 Fitmealor 프로젝트를 Vercel (프론트엔드)과 Render (백엔드)를 사용하여 배포하는 방법을 안내합니다.

## 배포 아키텍처

- **Frontend**: Vercel (React + Vite)
- **Backend**: Render (FastAPI)
- **Database**: Render PostgreSQL (Free tier - 90일 제한) 또는 AWS RDS
- **Cache**: Redis (옵션, Render 유료 서비스)

## 장점

✅ **완전 무료** - 신용카드 불필요
✅ **자동 CI/CD** - GitHub push 시 자동 배포
✅ **HTTPS 자동** - SSL 인증서 자동 설정
✅ **간편한 설정** - 클릭 몇 번으로 배포 완료

## 사전 요구사항

- GitHub 계정
- Vercel 계정 (GitHub으로 가입 가능)
- Render 계정 (GitHub으로 가입 가능)

---

## 1. Render로 백엔드 배포

### 1.1 Render 회원가입

1. https://render.com 방문
2. "Get Started" 클릭
3. GitHub 계정으로 로그인

### 1.2 PostgreSQL 데이터베이스 생성

1. Render 대시보드에서 "New +" 클릭
2. "PostgreSQL" 선택
3. 다음 정보 입력:
   - **Name**: `fitmealor-db`
   - **Database**: `fitmealor`
   - **User**: `fitmealor_user`
   - **Region**: Singapore (가장 가까운 지역)
   - **Plan**: Free (90일 제한)

4. "Create Database" 클릭

5. 생성 후 "Internal Database URL" 복사 (나중에 사용)
   ```
   postgresql://fitmealor_user:xxxxx@dpg-xxxxx-a.singapore-postgres.render.com/fitmealor
   ```

**중요**: Free tier 데이터베이스는 90일 후 삭제됩니다. 장기 운영시 AWS RDS 사용을 권장합니다.

### 1.3 백엔드 Web Service 생성

1. Render 대시보드에서 "New +" 클릭
2. "Web Service" 선택
3. GitHub 저장소 연결
   - "Connect GitHub" 클릭
   - 저장소 검색: `KimSoEun/Fitmealor` 또는 본인 저장소
   - "Connect" 클릭

4. 다음 설정 입력:
   - **Name**: `fitmealor-backend`
   - **Region**: Singapore
   - **Branch**: `main`
   - **Root Directory**: `backend/fastapi-service`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - **Plan**: Free

5. **Environment Variables** 추가 (아래 "Advanced" 섹션):
   ```
   DATABASE_URL=postgresql://fitmealor_user:xxxxx@dpg-xxxxx-a.singapore-postgres.render.com/fitmealor
   OPENAI_API_KEY=your_openai_api_key
   CLOVA_OCR_SECRET=your_clova_ocr_secret
   CLOVA_OCR_URL=your_clova_ocr_url
   ENVIRONMENT=production
   DEBUG=False
   PYTHON_VERSION=3.11.0
   ```

   **주의**: `DATABASE_URL`은 1.2에서 복사한 Internal Database URL을 사용

6. "Create Web Service" 클릭

7. 배포 완료까지 5-10분 대기

8. 배포 완료 후 백엔드 URL 확인:
   ```
   https://fitmealor-backend.onrender.com
   ```

### 1.4 데이터베이스 마이그레이션

배포 후 데이터베이스 스키마를 초기화해야 합니다:

**옵션 1: 로컬에서 실행**
```bash
# Render 데이터베이스 URL을 환경 변수로 설정
export DATABASE_URL="postgresql://fitmealor_user:xxxxx@dpg-xxxxx-a.singapore-postgres.render.com/fitmealor"

# 마이그레이션 실행
cd backend/fastapi-service
alembic upgrade head
```

**옵션 2: Render Shell에서 실행**
1. Render 대시보드 > fitmealor-backend 서비스 선택
2. "Shell" 탭 클릭
3. 다음 명령어 실행:
   ```bash
   cd /opt/render/project/src
   alembic upgrade head
   ```

---

## 2. Vercel로 프론트엔드 배포

### 2.1 Vercel 회원가입

1. https://vercel.com 방문
2. "Sign Up" 클릭
3. GitHub 계정으로 로그인

### 2.2 프론트엔드 배포

1. Vercel 대시보드에서 "Add New..." > "Project" 클릭
2. GitHub 저장소 가져오기:
   - "Import Git Repository" 클릭
   - `KimSoEun/Fitmealor` 또는 본인 저장소 선택
   - "Import" 클릭

3. 다음 설정 입력:
   - **Project Name**: `fitmealor`
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (자동 감지됨)
   - **Output Directory**: `dist` (자동 감지됨)
   - **Install Command**: `npm install` (자동 감지됨)

4. **Environment Variables** 추가:
   ```
   VITE_API_URL=https://fitmealor-backend.onrender.com
   ```
   (Render에서 받은 백엔드 URL 사용)

5. "Deploy" 클릭

6. 배포 완료까지 2-5분 대기

7. 배포 완료 후 프론트엔드 URL 확인:
   ```
   https://fitmealor.vercel.app
   ```

---

## 3. CORS 설정

백엔드 코드에서 프론트엔드 Vercel URL을 CORS allowed origins에 추가해야 합니다.

### 3.1 main.py 수정

`backend/fastapi-service/app/main.py` 파일을 수정:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",           # 로컬 개발
        "https://fitmealor.vercel.app",    # Vercel 배포 URL
        "https://*.vercel.app",             # Vercel preview 배포
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3.2 변경사항 push

```bash
git add backend/fastapi-service/app/main.py
git commit -m "Add Vercel URL to CORS origins"
git push origin main
```

Render가 자동으로 재배포합니다 (2-5분 소요).

---

## 4. 배포 확인

### 4.1 백엔드 Health Check

브라우저에서 접속:
```
https://fitmealor-backend.onrender.com/health
```

응답 예시:
```json
{"status": "healthy"}
```

### 4.2 프론트엔드 테스트

1. `https://fitmealor.vercel.app` 방문
2. 회원가입 및 로그인 테스트
3. 식단 추천 기능 테스트
4. OCR 스캔 기능 테스트
5. 히스토리 페이지 확인

---

## 5. 모니터링 및 로그

### Render 백엔드 로그

1. Render 대시보드 > fitmealor-backend 선택
2. "Logs" 탭에서 실시간 로그 확인
3. 에러 발생 시 여기서 확인 가능

### Vercel 프론트엔드 로그

1. Vercel 대시보드 > fitmealor 프로젝트 선택
2. "Deployments" 탭에서 최근 배포 클릭
3. "Build Logs" 및 "Functions" 탭에서 로그 확인

---

## 6. 자동 CI/CD

### GitHub에 push하면 자동 배포됩니다:

- **프론트엔드**: `frontend/` 디렉토리 변경 → Vercel 자동 재배포 (2-5분)
- **백엔드**: `backend/fastapi-service/` 변경 → Render 자동 재배포 (5-10분)

### 배포 확인:

1. **Vercel**: https://vercel.com/dashboard 에서 배포 상태 확인
2. **Render**: https://dashboard.render.com 에서 배포 상태 확인

---

## 7. 비용

### Vercel Free Tier

- **무료 제공**:
  - 100GB 대역폭/월
  - 6000분 빌드 시간/월
  - 100GB 이미지 최적화/월
  - HTTPS 무료
  - Custom domain 무료

### Render Free Tier

- **무료 제공**:
  - PostgreSQL 데이터베이스 (90일 제한)
  - Web Service (15분 비활성 시 sleep 모드)
  - 750시간/월 가동 시간
  - HTTPS 무료

- **제한사항**:
  - Free tier Web Service는 15분 동안 요청이 없으면 sleep 상태로 전환
  - 첫 요청 시 ~30초 cold start 시간 소요
  - PostgreSQL 무료 데이터베이스는 90일 후 삭제됨

---

## 8. 문제 해결

### 백엔드가 sleep 상태에서 깨어나지 않음

**문제**: Free tier는 15분 비활성 시 sleep 모드 진입

**해결책**:
1. UptimeRobot 같은 무료 모니터링 서비스 사용
2. 5분마다 `/health` 엔드포인트 호출하도록 설정
3. 또는 Render 유료 플랜($7/월) 사용

### CORS 에러 발생

**문제**: 프론트엔드에서 백엔드 API 호출 시 CORS 에러

**해결책**:
1. `backend/fastapi-service/app/main.py`의 CORS 설정 확인
2. Vercel URL이 `allow_origins`에 포함되어 있는지 확인
3. 변경 후 GitHub에 push하여 재배포

### 데이터베이스 연결 실패

**문제**: 백엔드가 데이터베이스에 연결할 수 없음

**해결책**:
1. Render 대시보드에서 `DATABASE_URL` 환경 변수 확인
2. PostgreSQL 데이터베이스가 실행 중인지 확인
3. Internal Database URL을 사용하는지 확인 (External이 아님)

### 프론트엔드 빌드 실패

**문제**: Vercel 배포 시 빌드 에러

**해결책**:
1. `VITE_API_URL` 환경 변수가 설정되어 있는지 확인
2. Vercel 대시보드 > Settings > Environment Variables 확인
3. 로컬에서 `npm run build` 실행하여 빌드 테스트

---

## 9. 업그레이드 옵션

### Render 유료 플랜 ($7/월)

- Sleep 없음 (항상 활성 상태)
- 더 빠른 응답 시간
- 더 많은 리소스 (512MB → 1GB RAM)

### PostgreSQL 장기 운영

**옵션 1**: AWS RDS Free Tier (12개월 무료)
- db.t3.micro 인스턴스
- 20GB 스토리지
- 12개월 후 유료 전환 ($15-20/월)

**옵션 2**: Render PostgreSQL 유료 플랜 ($7/월)
- 1GB 스토리지
- 무제한 기간
- 자동 백업

---

## 10. 보안 강화

### 환경 변수 보호

- ✅ Vercel과 Render는 환경 변수를 암호화하여 저장
- ✅ GitHub에 환경 변수 절대 push하지 않기
- ✅ `.env` 파일을 `.gitignore`에 추가

### HTTPS 강제

- ✅ Vercel과 Render는 기본적으로 HTTPS 제공
- ✅ HTTP 요청은 자동으로 HTTPS로 리다이렉트

### Rate Limiting

FastAPI에 rate limiting 미들웨어 추가:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/recommendations")
@limiter.limit("10/minute")
async def get_recommendations(request: Request):
    # ...
```

---

## 11. 배포 체크리스트

### 백엔드 (Render)

- [ ] PostgreSQL 데이터베이스 생성
- [ ] Web Service 생성
- [ ] 환경 변수 설정
  - [ ] DATABASE_URL
  - [ ] OPENAI_API_KEY
  - [ ] CLOVA_OCR_SECRET
  - [ ] CLOVA_OCR_URL
  - [ ] ENVIRONMENT=production
  - [ ] DEBUG=False
- [ ] 데이터베이스 마이그레이션 실행 (`alembic upgrade head`)
- [ ] `/health` 엔드포인트 테스트

### 프론트엔드 (Vercel)

- [ ] 프로젝트 생성 및 GitHub 연결
- [ ] Root Directory를 `frontend`로 설정
- [ ] 환경 변수 설정
  - [ ] VITE_API_URL
- [ ] 배포 성공 확인
- [ ] 실제 URL 접속 테스트

### CORS 설정

- [ ] `main.py`에 Vercel URL 추가
- [ ] GitHub에 push
- [ ] Render 재배포 확인

### 기능 테스트

- [ ] 회원가입
- [ ] 로그인
- [ ] 식단 추천
- [ ] OCR 스캔
- [ ] 히스토리 저장 및 조회

---

## 지원

문제가 발생하면 GitHub Issues에 문의하세요:
https://github.com/KimSoEun/Fitmealor/issues

---

## 참고 링크

- Render 문서: https://render.com/docs
- Vercel 문서: https://vercel.com/docs
- FastAPI 배포 가이드: https://fastapi.tiangolo.com/deployment/
- Vite 프로덕션 빌드: https://vitejs.dev/guide/build.html
