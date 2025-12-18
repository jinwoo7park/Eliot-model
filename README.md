# ExcitonBindingEnergy_ElliottModel

MATLAB 코드를 Python으로 변환한 **Elliot Theory 기반 F-sum rule fitting 도구**입니다. 반도체 및 나노구조 물질의 광학 흡수 스펙트럼에서 Exciton binding energy를 계산하고 Exciton과 band-to-band 전이를 분리하여 정량적으로 분석합니다.

## 📋 목차

- [과학적 배경](#과학적-배경)
- [주요 기능](#주요-기능)
- [빠른 시작](#빠른-시작)
- [설치](#설치)
- [사용 방법](#사용-방법)
- [파일 형식](#파일-형식)
- [출력 파일](#출력-파일)
- [물리적 파라미터](#물리적-파라미터)
- [문제 해결](#문제-해결)

## 🔬 과학적 배경

### Elliot Theory

이 코드는 **Elliot Theory** (1957, R. J. Elliot)를 기반으로 합니다. Elliot Theory는 반도체에서 발생하는 exciton과 band-to-band 전이를 통합적으로 설명하는 이론입니다.

### 주요 개념

- **Exciton (엑시톤)**: 전자와 정공이 쿨롱 상호작용으로 결합한 준입자. Band gap보다 낮은 에너지에서 흡수가 발생합니다.
- **Band-to-Band 전이**: Band gap 에너지(Eg) 이상에서 전자가 가전자대에서 전도대로 직접 전이하는 현상
- **F-sum Rule**: 전기 쌍극자 전이의 oscillator strength에 대한 합 규칙을 활용하여 exciton과 band 전이의 상대적 기여도를 정량 분석
- **Fractional Dimension (q)**: 나노구조에서 양자 구속 효과로 인한 유효 차원 변화
  - q = 0: Bulk (3차원)
  - q = 0.5-0.6: Quasi-2D (양자우물)
  - q = 1.5: Strong Quantum Dot (강한 구속)

자세한 과학적 배경은 [CODE_EXPLANATION.md](CODE_EXPLANATION.md)를 참고하세요.

## ✨ 주요 기능

- ✅ **F-sum rule 기반 2D fitting**: Elliot Theory를 사용한 정량적 분석
- ✅ **Exciton/Band 분리**: Exciton과 band contribution을 자동으로 분리
- ✅ **Baseline 제거**: Linear 또는 Rayleigh scattering (E⁴) baseline 지원
- ✅ **Urbach energy 추출**: Band gap 아래 지수적 흡수 꼬리 분석
- ✅ **다중 데이터셋 처리**: 한 파일에 여러 데이터셋 포함 가능
- ✅ **웹 인터페이스**: 브라우저에서 쉽게 사용 가능
- ✅ **명령줄 인터페이스**: 스크립트 및 자동화 지원
- ✅ **시뮬레이션 기능**: 파라미터 변화에 따른 스펙트럼 예측

## 🚀 빠른 시작

### 웹 인터페이스 (가장 간단한 방법)

```bash
# 의존성 설치 (처음 한 번만)
pnpm install
pip install -r requirements.txt

# 백엔드와 프론트엔드 자동 실행
pnpm run dev:all
```

브라우저에서 **http://localhost:3000** 접속하면 됩니다!

**참고**: macOS에서는 `python` 대신 `python3`를 사용하세요.

## 📦 설치

### 필수 요구사항

- Python 3.7 이상
- Node.js 16 이상 (웹 인터페이스 사용 시)
- pnpm (웹 인터페이스 사용 시)

### Python 의존성 설치

```bash
pip install -r requirements.txt
```

또는

```bash
python3 -m pip install -r requirements.txt
```

### Node.js 의존성 설치 (웹 인터페이스)

```bash
pnpm install
```

또는

```bash
npm install -g pnpm
pnpm install
```

## 💻 사용 방법

### 1. 웹 인터페이스

**시작하기:**

```bash
pnpm run dev:all
```

**사용 절차:**

1. 브라우저에서 http://localhost:3000 접속
2. 데이터 파일 업로드 (.txt, .dat, .csv)
3. Baseline Fit Mode 선택 (0=없음, 1=선형, 2=Rayleigh scattering)
4. "파일 업로드 및 미리보기" 클릭
5. 그래프에서 클릭하여 baseline과 피팅 범위 선택
   - fitmode=0: 2개 점 (피팅 범위)
   - fitmode=1 또는 2: 3개 점 (baseline 범위 2개 + 피팅 범위 1개)
6. "분석 시작" 클릭
7. 결과 확인 및 파일 다운로드

자세한 내용은 [README_WEB.md](README_WEB.md)를 참고하세요.

### 2. Python 코드에서 직접 사용

```python
from fitter import FSumFitter

# Fitter 생성
fitter = FSumFitter(deltaE=0.2, NS=20, fitmode=2)

# 파일 분석
results = fitter.process_file('data.txt', baseline_select=True)

# 결과 저장
fitter.save_results(results, output_dir='.')

# 그래프 생성
fitter.plot_results(results, save_path='results.pdf')
```


## 📄 파일 형식

입력 파일은 공백 또는 탭으로 구분된 텍스트 파일이어야 합니다:

- **첫 번째 열**: 파장 (nm)
- **두 번째 열 이후**: 흡수 데이터 (여러 데이터셋 가능)

### 예시 파일 형식

```
620.0    0.001    0.002    0.001
590.0    0.005    0.008    0.006
563.6    0.015    0.020    0.018
538.9    0.035    0.045    0.040
...
```

- 첫 번째 열: 파장 값 (nm 단위)
- 두 번째 열: 첫 번째 데이터셋의 흡수 데이터
- 세 번째 열: 두 번째 데이터셋의 흡수 데이터
- ...

**참고:**
- 공백 또는 탭으로 구분
- CSV 파일도 지원 (`.csv` 확장자)
- 주석 라인은 `#`으로 시작 가능
- 빈 줄은 무시됨
- 여러 데이터셋을 한 파일에 포함 가능

## 📊 출력 파일

각 데이터셋에 대해 다음 파일들이 생성됩니다:

- **`*_Results.csv`**: 피팅 파라미터 및 결과 데이터
  - 파라미터: Eg, Eb_Rydberg, Eb_GroundState, Gamma, ucvsq, mhcnp, q, Deff, R²
  - 데이터: Wavelength, Raw Data, Baseline, Fitted Exciton, Fitted Band, Fitted Result
- **`*.pdf`**: 피팅 결과 그래프
  - Raw data (검은색 점)
  - Baseline (회색 점선)
  - Fitted Exciton (파란색 실선)
  - Fitted Band (빨간색 실선)
  - Fitted Result Total (초록색 굵은 실선)

## 🔬 물리적 파라미터

### 피팅 파라미터

1. **Eg (Band Gap Energy)**: 전도대와 가전자대 사이의 에너지 차이 (eV)

2. **Eb (Exciton Binding Energy)**: 
   - **Eb_Rydberg**: 코드에서 직접 피팅되는 파라미터 (Rydberg 상수, eV 또는 meV)
   - **Eb_GroundState**: 실제 n=1 exciton binding energy
     ```
     Eb_GS = Eb_Rydberg / (1-q)²
     ```

3. **Gamma (Linewidth)**: 스펙트럼 선폭 (eV 또는 meV)
   - 작은 Gamma: 날카로운 피크, 높은 결정성
   - 큰 Gamma: 넓은 피크, 불순물/온도 효과

4. **ucvsq**: Transition dipole moment squared (전이 쌍극자 모멘트의 제곱)

5. **mhcnp**: Mass parameter (유효 질량 관련 파라미터)

6. **q (Fractional Dimension)**: 양자 구속 파라미터
   - q = 0: Bulk (3차원)
   - q = 0.5-0.6: Quasi-2D (양자우물)
   - q = 1.5: Strong Quantum Dot

**Effective Dimension**: Deff = 3 - 2q

### 피팅 품질

- **R² > 0.99**: 매우 좋은 피팅
- **R² > 0.95**: 좋은 피팅
- **R² < 0.90**: 피팅 개선 필요 (baseline 선택, 범위 조정 등)

## 🌐 무료 배포 가이드

**완전 무료로 배포하는 방법**: [DEPLOYMENT_FREE.md](DEPLOYMENT_FREE.md) 참고

### 빠른 요약

1. **백엔드 배포** (무료 옵션):
   - **Railway** (추천): 월 $5 무료 크레딧, 빠르고 안정적
   - **Render**: 완전 무료, 15분 비활성 시 sleep

2. **프론트엔드**: 이미 Vercel에 배포됨 (무료)

3. **환경 변수 설정**:
   - Vercel: `VITE_API_BASE_URL` = 백엔드 URL
   - 백엔드: `ALLOWED_ORIGINS` = Vercel 도메인

자세한 내용은 [DEPLOYMENT_FREE.md](DEPLOYMENT_FREE.md)를 참고하세요.

---

## 🌐 Vercel 배포

### 환경 변수 설정

Vercel에 배포할 때는 백엔드 API 서버 URL을 환경 변수로 설정해야 합니다.

1. **Vercel 대시보드에서 환경 변수 설정:**
   - 프로젝트 설정 > Environment Variables
   - `VITE_API_BASE_URL` 추가
   - 값: 백엔드 API 서버 URL (예: `https://your-backend.railway.app` 또는 `https://your-backend.render.com`)
   - Production, Preview, Development 모두에 적용

2. **로컬 개발 환경:**
   - `.env.local` 파일 생성 (선택사항)
   - `VITE_API_BASE_URL=http://localhost:8000` (또는 비워두면 Vite proxy 사용)

3. **백엔드 배포:**
   - FastAPI 백엔드는 별도로 배포해야 합니다 (Railway, Render, Heroku 등)
   - CORS 설정이 올바른지 확인 (`api/index.py`에서 이미 설정됨)

### 배포 후 확인사항

- 백엔드 API 서버가 실행 중인지 확인
- 환경 변수 `VITE_API_BASE_URL`이 올바르게 설정되었는지 확인
- 브라우저 콘솔에서 네트워크 오류 확인

## 🛠️ 문제 해결

### Vercel 배포 시 404 오류

**원인**: 백엔드 API URL이 설정되지 않았거나 잘못 설정됨

**해결 방법**:
1. Vercel 대시보드에서 `VITE_API_BASE_URL` 환경 변수 확인
2. 백엔드 API 서버가 실행 중인지 확인
3. CORS 설정 확인 (백엔드에서 프론트엔드 도메인 허용)

### Python 의존성 설치 오류

**가장 흔한 문제입니다!** 다음 명령어로 Python 의존성을 설치하세요:

```bash
pip install -r requirements.txt
```

또는

```bash
python3 -m pip install -r requirements.txt
pip3 install -r requirements.txt
```

### 포트가 이미 사용 중인 경우

```bash
# 포트 확인
lsof -i :8000  # 백엔드
lsof -i :3000  # 프론트엔드

# 프로세스 종료
kill -9 <PID>
```

### pnpm이 설치되지 않은 경우

```bash
npm install -g pnpm
```

### Baseline 선택 팁

- **중요**: Baseline 선택이 피팅 품질에 큰 영향을 미칩니다
- 투명 구간(흡수가 거의 없는 에너지 범위)을 선택하세요
- fitmode=2 (Rayleigh scattering)는 나노입자 산란을 고려합니다

### 피팅 범위 팁

- Bandgap 주변 (Eg ± 0.5 eV)에 집중하는 것이 좋습니다
- 너무 넓은 범위는 고에너지 영역의 오차를 증가시킬 수 있습니다
- `auto_range=True` (기본값)로 자동 최적화 가능

## 📚 추가 자료

- [CODE_EXPLANATION.md](CODE_EXPLANATION.md): 상세한 코드 설명 및 과학적 배경
- [README_WEB.md](README_WEB.md): 웹 인터페이스 상세 가이드
- [DEPLOYMENT.md](DEPLOYMENT.md): 배포 가이드 (Railway, Render, Vercel)

## 📖 참고 문헌

1. **Elliot, R. J. (1957)**: "Intensity of Optical Absorption by Excitons", Physical Review, 108, 1384-1389
2. **F-sum Rule**: 전기 쌍극자 전이의 oscillator strength 합 규칙
3. **Fractional Dimension Model**: 나노구조에서의 양자 구속 효과

## 🏗️ 프로젝트 구조

```
.
├── api/                    # API 모듈
│   ├── index.py           # FastAPI 백엔드 서버
│   ├── fitter.py          # 피팅 메인 모듈
│   └── fsum2d.py          # F-sum rule 계산 모듈
├── src/                   # React 프론트엔드
├── requirements.txt       # Python 의존성
├── package.json          # Node.js 의존성
└── README.md             # 이 파일
```

## 📝 라이선스

이 코드는 원본 MATLAB 코드를 Python으로 변환한 것입니다.

## 🤝 기여

버그 리포트 및 기능 제안은 이슈로 등록해주세요.
