# 무료 배포 가이드

이 문서는 **완전 무료**로 ExcitonBindingEnergy_ElliottModel을 배포하는 방법을 설명합니다.

## 무료 배포 옵션 비교

| 서비스 | 무료 티어 | 제한사항 | 추천도 |
|--------|----------|---------|--------|
| **Railway** | 월 $5 크레딧 | 사용량 초과 시 결제 필요 | ⭐⭐⭐⭐⭐ |
| **Render** | 무료 | 15분 비활성 시 sleep (느려짐) | ⭐⭐⭐⭐ |
| **Fly.io** | 무료 | 제한적 리소스 | ⭐⭐⭐ |
| **PythonAnywhere** | 무료 | 제한적 리소스, 외부 API 제한 | ⭐⭐ |

## 방법 1: Railway (가장 추천) ⭐⭐⭐⭐⭐

### 장점
- 월 $5 무료 크레딧 제공
- 빠른 배포 속도
- 자동 HTTPS
- GitHub 연동 자동 배포

### 단점
- 사용량 초과 시 결제 필요 (하지만 소규모 프로젝트는 무료로 충분)

### 배포 방법

1. **Railway 계정 생성**
   - https://railway.app 접속
   - GitHub 계정으로 로그인

2. **프로젝트 생성**
   - "New Project" 클릭
   - "Deploy from GitHub repo" 선택
   - `ExcitonBindingEnergy_ElliottModel` 저장소 선택
   - "Deploy Now" 클릭

3. **서비스 설정**
   - Railway가 자동으로 Python 감지
   - Start Command: `python3 api.py` (자동 설정됨)

4. **환경 변수 설정**
   - Variables 탭 클릭
   - 다음 환경 변수 추가:
     ```
     ALLOWED_ORIGINS=https://elliott-model.vercel.app,http://localhost:3000
     ```

5. **도메인 확인**
   - Settings > Networking 탭
   - "Generate Domain" 클릭
   - 생성된 URL 복사 (예: `https://your-app.up.railway.app`)

6. **Vercel 환경 변수 설정**
   - Vercel 대시보드 > Settings > Environment Variables
   - `VITE_API_BASE_URL` = Railway에서 받은 URL
   - 재배포

## 방법 2: Render (완전 무료) ⭐⭐⭐⭐

### 장점
- 완전 무료 (제한 없음)
- 자동 HTTPS
- GitHub 연동

### 단점
- 15분 비활성 시 sleep (첫 요청이 느림)
- 무료 티어는 느릴 수 있음

### 배포 방법

1. **Render 계정 생성**
   - https://render.com 접속
   - GitHub 계정으로 로그인

2. **Web Service 생성**
   - "New +" > "Web Service" 클릭
   - GitHub 저장소 연결: `ExcitonBindingEnergy_ElliottModel`

3. **설정 입력**
   ```
   Name: exciton-binding-energy-api
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python3 api.py
   ```

4. **환경 변수 추가**
   - Environment Variables 섹션:
     ```
     ALLOWED_ORIGINS=https://elliott-model.vercel.app,http://localhost:3000
     ```

5. **배포**
   - "Create Web Service" 클릭
   - 배포 완료 후 URL 확인 (예: `https://your-app.onrender.com`)

6. **Vercel 환경 변수 설정**
   - Vercel 대시보드 > Settings > Environment Variables
   - `VITE_API_BASE_URL` = Render에서 받은 URL
   - 재배포

## 방법 3: Fly.io (무료 티어) ⭐⭐⭐

### 배포 방법

1. **Fly.io CLI 설치**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **로그인**
   ```bash
   fly auth login
   ```

3. **앱 생성**
   ```bash
   fly launch
   ```

4. **환경 변수 설정**
   ```bash
   fly secrets set ALLOWED_ORIGINS="https://elliott-model.vercel.app,http://localhost:3000"
   ```

## 비용 절감 팁

### Railway 사용량 모니터링
- Railway 대시보드에서 사용량 확인
- 소규모 프로젝트는 월 $5 크레딧으로 충분
- 사용량이 많으면 Render로 전환 고려

### Render Sleep 방지 (선택사항)
- UptimeRobot 같은 무료 서비스로 주기적 ping
- 또는 Railway 사용 (sleep 없음)

## 추천 구성

**가장 추천**: Railway (월 $5 무료 크레딧, 빠르고 안정적)
**완전 무료**: Render (sleep 있지만 무료)

## 배포 후 확인

1. **백엔드 확인**
   ```
   https://your-backend-url/api/health
   ```
   응답: `{"status":"ok"}`

2. **프론트엔드 확인**
   ```
   https://elliott-model.vercel.app/
   ```
   파일 업로드 테스트

## 문제 해결

### Render가 느린 경우
- 첫 요청은 sleep에서 깨어나느라 느릴 수 있음 (정상)
- UptimeRobot으로 주기적 ping 설정

### Railway 크레딧 부족
- Render로 전환
- 또는 사용량 확인 후 필요시 업그레이드

### CORS 오류
- 백엔드의 `ALLOWED_ORIGINS`에 프론트엔드 URL 포함 확인
- Vercel URL: `https://elliott-model.vercel.app`

