# ExcitonBindingEnergy_ElliottModel - Web Interface

웹 인터페이스를 사용하여 Exciton binding energy를 계산하고 F-sum rule fitting을 수행할 수 있습니다.

## 빠른 시작 (가장 간단한 방법)

**한 번의 명령어로 백엔드와 프론트엔드를 모두 실행:**

```bash
# 처음 한 번만: 의존성 설치
pnpm install
pip install -r requirements.txt

# 이후에는 이것만 실행
pnpm run dev:all
```

이 명령어 하나로 백엔드 서버와 프론트엔드가 모두 자동으로 시작됩니다!

브라우저에서 http://localhost:3000 접속하면 됩니다.

**주의:** `pnpm run dev:all`을 실행하면 Python 의존성 설치를 시도하지만, 실패할 경우 명시적으로 `pip install -r requirements.txt`를 실행해야 합니다.

## 개발 환경 설정 (Dev Container)

### 사전 요구사항
- Docker Desktop 설치
- Visual Studio Code 설치
- VS Code의 "Dev Containers" 확장 설치

### 시작하기

1. **Dev Container로 프로젝트 열기**
   - VS Code에서 프로젝트 폴더 열기
   - `F1` 키를 누르고 "Dev Containers: Reopen in Container" 선택
   - 또는 명령 팔레트에서 "Dev Containers: Reopen in Container"

2. **자동으로 실행되는 작업**
   - Python 의존성 설치 (`pip install -r requirements.txt`)
   - Node.js 의존성 설치 (`pnpm install`)

3. **서비스 실행**
   
   Dev Container 내에서 터미널을 열고:
   
   ```bash
   pnpm run dev:all
   ```
   
   또는 기존 스크립트 사용:
   ```bash
   ./start.sh
   ```

4. **브라우저에서 접속**
   - 프론트엔드: http://localhost:3000
   - 백엔드 API: http://localhost:8000
   - API 문서: http://localhost:8000/docs

## 로컬 개발 (Dev Container 없이)

### 방법 1: 한 번에 실행 (권장)

```bash
# 의존성 설치 (처음 한 번만, 필수!)
pnpm install
pip install -r requirements.txt

# 백엔드와 프론트엔드를 함께 실행
pnpm run dev:all
```

### 방법 2: 개별 실행

**백엔드만 실행:**
```bash
python3 -m api.index
```

**프론트엔드만 실행:**
```bash
pnpm dev
```

## 사용 방법

1. **서버 실행**
   - `pnpm run dev:all` 실행 (백엔드와 프론트엔드 자동 시작)

2. **브라우저에서 접속**
   - http://localhost:3000 접속

3. **파일 업로드 및 분석**
   - 데이터 파일 선택 (.txt, .dat, .csv 형식)
   - Baseline Fit Mode 선택
   - "파일 업로드 및 미리보기" 버튼 클릭
   - 그래프에서 클릭하여 baseline과 피팅 범위 선택
   - "분석 시작" 버튼 클릭
   - 결과 확인 및 파일 다운로드

## 문제 해결

### FastAPI 모듈이 없다는 오류

**가장 흔한 문제입니다!** 다음 명령어로 Python 의존성을 설치하세요:

```bash
pip install -r requirements.txt
```

만약 `pip`가 없다면:
```bash
# macOS
python3 -m pip install -r requirements.txt

# 또는 pip3 사용
pip3 install -r requirements.txt
```

### 포트가 이미 사용 중인 경우
- 다른 애플리케이션이 포트 8000 또는 3000을 사용 중일 수 있습니다.
- `lsof -i :8000` 또는 `lsof -i :3000`으로 확인
- 사용 중인 프로세스를 종료하거나 포트를 변경하세요.

### pnpm이 설치되지 않은 경우
```bash
npm install -g pnpm
```

### Python 의존성 설치 오류
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### concurrently가 설치되지 않은 경우
```bash
pnpm install
```

## API 엔드포인트

### POST /api/preview
파일을 업로드하고 그래프 이미지를 반환합니다.

### POST /api/analyze
클릭 좌표를 받아서 분석을 수행합니다.

**파라미터:**
- `filename`: 파일명
- `fitmode`: Baseline fit mode (0, 1, 2)
- `baseline_points`: 클릭 좌표 배열 [x1, x2, x3] 또는 [x1, x2]

### GET /api/download/{filename}
분석 결과 파일을 다운로드합니다.

### GET /api/health
서버 상태 확인

## 기술 스택

- **Backend**: FastAPI (Python)
- **Frontend**: React + Vite
- **Package Manager**: pnpm
- **Container**: Docker + Dev Containers
