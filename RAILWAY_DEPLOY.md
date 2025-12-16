# Railway 배포 가이드

## Railway 배포 방법

### 1. Railway 계정 생성 및 프로젝트 연결

1. [Railway](https://railway.app)에 가입/로그인
2. "New Project" 클릭
3. "Deploy from GitHub repo" 선택
4. 이 저장소 연결

### 2. 환경 변수 설정 (필요시)

Railway 대시보드에서:
- Settings → Variables
- 필요한 환경 변수 추가:
  - `PORT`: Railway가 자동으로 설정 (선택사항)
  - `ALLOWED_ORIGINS`: CORS 허용 도메인 (필요시)

### 3. 빌드 및 배포

Railway는 자동으로:
1. `railway.json`의 `buildCommand` 실행
   - 프론트엔드 빌드: `pnpm install && pnpm build`
   - Python 의존성 설치: `pip install -r requirements.txt`
2. `startCommand`로 서버 시작: `python3 -m api.index`

### 4. 도메인 설정

Railway 대시보드에서:
- Settings → Domains
- Custom domain 설정 또는 Railway 제공 도메인 사용

## 빌드 과정

1. **프론트엔드 빌드**: `pnpm build` → `dist/` 폴더 생성
2. **Python 의존성 설치**: `pip install -r requirements.txt`
3. **서버 시작**: FastAPI가 `dist/` 폴더의 정적 파일을 서빙

## 주의사항

- Railway는 자동으로 `PORT` 환경 변수를 설정합니다
- FastAPI는 `PORT` 환경 변수를 읽어 사용합니다 (기본값: 8000)
- 프론트엔드는 빌드되어 `dist/` 폴더에 생성되며, FastAPI가 서빙합니다
- API 엔드포인트는 `/api/*` 경로로 접근 가능합니다

## 트러블슈팅

### 빌드 실패
- Railway 로그 확인: 대시보드 → Deployments → View Logs
- `pnpm`이 설치되지 않은 경우: Nixpacks가 자동으로 감지합니다

### 서버가 시작되지 않음
- `Procfile` 또는 `railway.json`의 `startCommand` 확인
- 포트 설정 확인 (Railway가 자동으로 설정)

### 정적 파일이 로드되지 않음
- `dist/` 폴더가 생성되었는지 확인
- FastAPI의 정적 파일 마운트 경로 확인

## Railway의 장점

1. **용량 제한 없음**: Vercel의 250MB 제한 없이 모든 Python 패키지 포함 가능
2. **단일 서비스**: 프론트엔드와 백엔드를 하나의 서비스로 배포
3. **자동 배포**: GitHub에 푸시 시 자동 배포
4. **간편한 설정**: `railway.json` 하나로 모든 설정 관리

