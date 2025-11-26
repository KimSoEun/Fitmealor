# Fitmealor AWS 배포 가이드

이 문서는 Fitmealor 프로젝트를 AWS Amplify (프론트엔드)와 AWS App Runner (백엔드)를 사용하여 배포하는 방법을 안내합니다.

## 배포 아키텍처

- **Frontend**: AWS Amplify (React + Vite)
- **Backend**: AWS App Runner (FastAPI)
- **Database**: AWS RDS (PostgreSQL)
- **Cache**: AWS ElastiCache (Redis) - 옵션

## 사전 요구사항

- AWS 계정
- GitHub 계정
- AWS CLI 설치 (선택사항)

## 1. AWS RDS PostgreSQL 데이터베이스 생성

### 1.1 RDS 인스턴스 생성

1. AWS Console에서 RDS 서비스로 이동
2. "Create database" 클릭
3. 다음 설정 선택:
   - Engine: PostgreSQL (15.x 이상)
   - Template: Free tier (테스트용) 또는 Production
   - DB instance identifier: `fitmealor-db`
   - Master username: `fitmealor_user`
   - Master password: 강력한 비밀번호 설정
   - Instance configuration: db.t3.micro (Free tier)
   - Storage: 20 GB
   - **Public access: Yes** (App Runner가 접근할 수 있도록)
   - VPC security group: 새로 생성 또는 기존 것 사용

4. "Create database" 클릭

### 1.2 보안 그룹 설정

1. RDS 인스턴스의 보안 그룹으로 이동
2. Inbound rules 편집
3. PostgreSQL (포트 5432) 규칙 추가:
   - Type: PostgreSQL
   - Protocol: TCP
   - Port: 5432
   - Source: 0.0.0.0/0 (프로덕션에서는 App Runner IP만 허용하도록 제한)

### 1.3 데이터베이스 URL 기록

RDS 엔드포인트를 다음 형식으로 기록:
```
postgresql://fitmealor_user:YOUR_PASSWORD@your-db-instance.xxxxx.ap-northeast-2.rds.amazonaws.com:5432/postgres
```

## 2. AWS App Runner로 백엔드 배포

### 2.1 GitHub 저장소 준비

1. 코드가 GitHub에 푸시되어 있는지 확인

### 2.2 App Runner 서비스 생성

1. AWS Console에서 App Runner 서비스로 이동
2. "Create service" 클릭
3. **Source and deployment** 설정:
   - Repository type: Source code repository
   - Provider: GitHub
   - GitHub 계정 연결
   - Repository: `KimSoEun/Fitmealor`
   - Branch: `main`
   - Source directory: `backend/fastapi-service`
   - Deployment trigger: Automatic

4. **Build settings**:
   - Configuration file: Use a configuration file
   - Configuration file: `apprunner.yaml`

5. **Service settings**:
   - Service name: `fitmealor-backend`
   - Port: `8000`

6. **Environment variables** 추가:
   ```
   DATABASE_URL=postgresql://fitmealor_user:YOUR_PASSWORD@your-rds-endpoint:5432/postgres
   REDIS_URL=redis://localhost:6379 (Redis 사용 시)
   OPENAI_API_KEY=your_openai_api_key
   CLOVA_OCR_SECRET=your_clova_ocr_secret
   CLOVA_OCR_URL=your_clova_ocr_url
   ENVIRONMENT=production
   DEBUG=False
   ```

7. **Health check**:
   - Path: `/health`
   - Protocol: HTTP
   - Interval: 10초

8. "Create & deploy" 클릭

### 2.3 백엔드 URL 기록

배포가 완료되면 App Runner 서비스 URL을 기록합니다:
```
https://xxxxx.ap-northeast-2.awsapprunner.com
```

## 3. AWS Amplify로 프론트엔드 배포

### 3.1 Amplify 앱 생성

1. AWS Console에서 Amplify 서비스로 이동
2. "New app" > "Host web app" 클릭
3. GitHub 선택 및 연결
4. Repository: `KimSoEun/Fitmealor` 선택
5. Branch: `main` 선택
6. **Build settings**:
   - App root directory: `frontend`
   - Build command: 자동 감지됨 (amplify.yml 사용)

### 3.2 환경 변수 설정

1. Amplify 앱 설정에서 "Environment variables" 로 이동
2. 다음 변수 추가:
   ```
   VITE_API_URL=https://xxxxx.ap-northeast-2.awsapprunner.com
   ```
   (App Runner에서 받은 백엔드 URL 사용)

### 3.3 배포

1. "Save and deploy" 클릭
2. 빌드 및 배포 프로세스 모니터링
3. 완료되면 Amplify에서 제공하는 URL 확인:
   ```
   https://main.xxxxx.amplifyapp.com
   ```

## 4. 데이터베이스 초기화

### 4.1 Alembic 마이그레이션 실행

백엔드가 배포된 후, 데이터베이스 스키마를 초기화해야 합니다:

1. 로컬에서 App Runner 데이터베이스에 연결:
   ```bash
   export DATABASE_URL="postgresql://fitmealor_user:YOUR_PASSWORD@your-rds-endpoint:5432/postgres"
   cd backend/fastapi-service
   alembic upgrade head
   ```

2. 또는 App Runner 서비스의 로그에서 자동 마이그레이션이 실행되는지 확인

## 5. CORS 설정 확인

백엔드 코드에서 프론트엔드 Amplify URL이 CORS allowed origins에 포함되어 있는지 확인:

`backend/fastapi-service/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://main.xxxxx.amplifyapp.com",  # Amplify URL 추가
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 6. 배포 확인

1. 프론트엔드 URL 방문: `https://main.xxxxx.amplifyapp.com`
2. 회원가입 및 로그인 테스트
3. 식단 추천 기능 테스트
4. OCR 스캔 기능 테스트

## 7. 모니터링 및 로그

### App Runner 로그
1. AWS Console > App Runner > 서비스 선택
2. "Logs" 탭에서 실시간 로그 확인

### Amplify 빌드 로그
1. AWS Console > Amplify > 앱 선택
2. 최근 빌드 클릭하여 로그 확인

### RDS 모니터링
1. AWS Console > RDS > 인스턴스 선택
2. "Monitoring" 탭에서 CPU, 메모리, 연결 수 등 확인

## 8. 비용 최적화

### Free Tier 활용
- **RDS**: db.t3.micro 인스턴스, 20GB 스토리지 (12개월 무료)
- **App Runner**: 매월 일정 시간 무료
- **Amplify**: 매월 일정 빌드 시간 및 호스팅 무료

### 비용 절감 팁
1. 개발 환경은 사용하지 않을 때 중지
2. RDS는 밤에 스케일 다운
3. CloudWatch 알람 설정으로 비용 모니터링

## 9. CI/CD

### 자동 배포 설정
- **GitHub에 push하면 자동으로 배포됩니다**:
  - `frontend/` 디렉토리 변경 → Amplify 자동 재배포
  - `backend/fastapi-service/` 변경 → App Runner 자동 재배포

## 10. 문제 해결

### 백엔드 연결 실패
1. App Runner 환경 변수가 올바르게 설정되었는지 확인
2. RDS 보안 그룹이 App Runner의 접근을 허용하는지 확인
3. App Runner 로그에서 에러 메시지 확인

### 프론트엔드 빌드 실패
1. `VITE_API_URL` 환경 변수가 설정되었는지 확인
2. Amplify 빌드 로그에서 에러 확인
3. `frontend/amplify.yml` 설정이 올바른지 확인

### 데이터베이스 연결 문제
1. RDS 엔드포인트가 올바른지 확인
2. 보안 그룹 inbound 규칙 확인
3. 데이터베이스 자격 증명 확인

## 11. 보안 강화

1. **환경 변수 보안**:
   - AWS Secrets Manager를 사용하여 민감한 정보 저장
   - App Runner에서 Secrets Manager 참조

2. **HTTPS 강제**:
   - Amplify와 App Runner는 기본적으로 HTTPS 제공

3. **API Rate Limiting**:
   - FastAPI에 rate limiting 미들웨어 추가

4. **WAF 설정** (선택사항):
   - AWS WAF를 사용하여 DDoS 공격 방어

## 지원

문제가 발생하면 GitHub Issues에 문의하세요:
https://github.com/KimSoEun/Fitmealor/issues
