# 분리 배포 설정 가이드

이 프로젝트는 프론트엔드와 백엔드를 분리하여 배포합니다.

## 배포 구조

- **프론트엔드**: Vercel (React + Vite)
- **백엔드**: Railway (FastAPI)

## Vercel 설정

### 1. 환경 변수 설정

Vercel 대시보드에서 다음 환경 변수를 설정해야 합니다:

```
VITE_API_BASE_URL=https://web-production-af7d7.up.railway.app
```

**설정 방법:**
1. Vercel 대시보드 접속
2. 프로젝트 선택 → Settings → Environment Variables
3. `VITE_API_BASE_URL` 추가 (Value: `https://web-production-af7d7.up.railway.app`)
4. 환경 선택 (Production, Preview, Development 모두 선택 가능)
5. Save

### 2. 빌드 확인

Vercel은 이제 프론트엔드만 빌드하므로:
- Python 패키지 설치하지 않음
- 서버리스 함수 생성하지 않음
- `dist/` 폴더만 배포

## Railway 설정

### 1. 환경 변수 (선택사항)

Railway에서 CORS를 위한 환경 변수를 설정할 수 있습니다:

```
ALLOWED_ORIGINS=https://your-vercel-app.vercel.app,https://your-vercel-app.vercel.app
```

기본적으로 Railway 백엔드는 모든 Vercel 도메인(`*.vercel.app`)을 허용합니다.

### 2. 배포 확인

Railway 백엔드가 정상적으로 실행되는지 확인:
- URL: `https://web-production-af7d7.up.railway.app`
- Health check: `https://web-production-af7d7.up.railway.app/api/health`

## 로컬 개발

### 프론트엔드만 실행

```bash
pnpm install
pnpm dev
```

### 백엔드만 실행

```bash
pip install -r requirements.txt
python3 -m api.index
```

### 프론트엔드 + 백엔드 동시 실행

```bash
# 방법 1: package.json 스크립트 사용
pnpm run dev:all

# 방법 2: 수동으로
# 터미널 1
python3 -m api.index

# 터미널 2
pnpm dev
```

로컬 개발 시 프론트엔드는 `vite.config.js`의 proxy 설정을 통해 자동으로 백엔드(`http://localhost:8000`)로 요청을 보냅니다.

## 문제 해결

### CORS 오류

백엔드(Railway)에서 프론트엔드(Vercel) 요청을 거부하는 경우:

1. Railway 환경 변수에 `ALLOWED_ORIGINS` 설정 확인
2. 또는 `api/index.py`의 `allowed_origins`에 Vercel 도메인 추가

### API 연결 오류

프론트엔드에서 백엔드로 연결되지 않는 경우:

1. Vercel 환경 변수 `VITE_API_BASE_URL` 확인
2. Railway 백엔드가 정상 실행 중인지 확인 (`/api/health` 엔드포인트 확인)
3. 브라우저 콘솔에서 실제 요청 URL 확인

## 장점

- ✅ Vercel: 프론트엔드 빌드만 하므로 빠르고 안정적
- ✅ Railway: Python 패키지 크기 제한 없음 (250MB 제한 우회)
- ✅ 각각 독립적으로 배포 및 스케일링 가능

