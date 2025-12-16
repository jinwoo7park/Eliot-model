# Serverless Function 용량 최적화 가이드

## 문제 상황
Vercel Serverless Function이 250MB unzipped 크기 제한을 초과했습니다.

## 주요 원인
1. **Python 패키지 크기**: numpy, scipy, matplotlib 등이 매우 큽니다
   - numpy: ~20-30MB
   - scipy: ~100-150MB (가장 큼)
   - matplotlib: ~40-50MB

2. **node_modules**: 프론트엔드 빌드용이지만, 실수로 포함될 수 있음 (372MB)

## 적용된 최적화

### 1. .vercelignore 개선 ✅
- Python 캐시 파일 제외 (`__pycache__`, `*.pyc` 등)
- matplotlib 폰트 캐시 제외
- 불필요한 빌드 파일 제외
- 테스트 및 개발 파일 제외

## 추가 최적화 방법

### 2. Matplotlib 백엔드 최적화 (이미 적용됨)
코드에서 이미 `matplotlib.use('Agg')`를 사용하고 있어 최적화되어 있습니다.

### 3. Requirements.txt 최적화
현재 requirements.txt는 최소한의 패키지만 포함하고 있습니다. 추가 최적화:

```txt
# 핵심 패키지만 포함 (이미 최적화됨)
numpy>=1.21.0
scipy>=1.7.0
matplotlib>=3.4.0  # Agg 백엔드 사용으로 불필요한 GUI 의존성 제외
pandas>=1.3.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
Pillow>=9.0.0
mangum>=0.17.0
```

### 4. Vercel 설정 최적화
`vercel.json`에서 이미 최적화되어 있습니다. 필요시 다음 설정 추가:

```json
{
  "functions": {
    "api/**/*.py": {
      "maxDuration": 30,
      "memory": 3008,  // 최대 메모리 사용
      "includeFiles": "api/**"  // api 폴더만 포함
    }
  }
}
```

### 5. 패키지 대안 검토 (고급)

#### Option A: Scipy 대신 더 가벼운 최적화 라이브러리 사용
- 현재 scipy의 `minimize`, `curve_fit` 사용 중
- 대안: `scipy.optimize`만 사용하고 나머지 scipy 모듈 제외 (하지만 scipy는 통합 패키지라 어려움)

#### Option B: Lambda Layer 사용 (Vercel에서는 지원 안 함)
- Vercel은 Lambda Layer를 지원하지 않음

#### Option C: 패키지 버전 다운그레이드
- 오래된 버전이 더 작을 수 있지만, 보안 및 호환성 문제 가능

### 6. 코드 레벨 최적화

#### matplotlib 폰트 관리 최적화
서버리스 환경에서는 폰트 캐시가 불필요할 수 있습니다:

```python
# fitter.py에서 폰트 검색 로직 간소화 가능
# 단, 한글 표시가 필요하면 유지해야 함
```

### 7. 배포 전 체크리스트

배포 전에 다음을 확인하세요:

```bash
# 1. .vercelignore가 올바르게 적용되는지 확인
vercel build --dry-run  # 또는 실제 빌드 테스트

# 2. 포함되는 파일 크기 확인
# (로컬에서 확인 어려움, Vercel 빌드 로그 확인 필요)

# 3. 필요한 파일만 포함되는지 확인
# - api/ 폴더만 포함되어야 함
# - node_modules는 제외되어야 함
# - data_testresult는 제외되어야 함
```

### 8. Vercel 빌드 로그 확인

배포 시 Vercel 대시보드에서 다음을 확인:
- "Function size" 메시지
- "Unzipped size" 경고
- 실제 번들에 포함된 파일 목록

### 9. 최종 해결책 (여전히 초과하는 경우)

#### Option 1: Vercel Pro 플랜으로 업그레이드
- Pro 플랜은 더 큰 함수 크기 허용 (확인 필요)

#### Option 2: 다른 플랫폼 고려
- Railway: 더 큰 크기 제한
- Render: 더 큰 크기 제한
- AWS Lambda with API Gateway: 250MB 제한 (동일)

#### Option 3: 아키텍처 변경
- 프론트엔드와 백엔드를 별도로 배포
- 백엔드는 다른 플랫폼에 배포 (Railway, Render 등)
- 프론트엔드는 Vercel에 배포

#### Option 4: 핵심 기능만 Serverless로 분리
- 복잡한 계산은 별도 서버에서 처리
- API Gateway만 Vercel에 배포

## 권장 조치 순서

1. ✅ **완료**: .vercelignore 개선
2. **다음 단계**: Vercel에 재배포하여 크기 확인
3. **여전히 초과하면**: Vercel 빌드 로그에서 실제 크기와 포함된 파일 확인
4. **최종 조치**: 위 Option 1-4 중 선택

## 참고
- Vercel Serverless Function 크기 제한: 250MB (unzipped)
- Python 패키지는 특히 크기가 큼 (특히 scipy)
- node_modules는 반드시 제외해야 함 (프론트엔드 빌드에만 필요)

