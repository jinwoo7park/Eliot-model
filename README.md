# F-sum Rule Fitting Tool

MATLAB 코드를 Python으로 변환한 F-sum rule fitting 도구입니다. Exciton과 band 분리 분석을 수행할 수 있습니다.

## 기능

- F-sum rule을 사용한 2D fitting
- Exciton과 band contribution 분리
- Baseline subtraction (linear/power function)
- Urbach energy 추출
- 명령줄 인터페이스

## 설치

```bash
pip install -r requirements.txt
```

## 사용 방법

### 가장 간단한 방법 (권장)

```bash
python3 analyze.py your_data.txt
```

파일 경로만 지정하면 바로 분석합니다.

옵션:
```bash
python3 analyze.py your_data.txt --datasets 1,2,3 --NS 20 --fitmode 2
```

**참고**: macOS에서는 `python` 대신 `python3`를 사용하세요.

### Python 코드에서 직접 사용

```python
from fitter import FSumFitter

fitter = FSumFitter()
results = fitter.process_file('your_data.txt')
fitter.save_results(results)
fitter.plot_results(results, save_path='results.pdf')
```

### 명령줄 인터페이스

```bash
python3 main.py data.txt
```

옵션:
- `--deltaE`: Normalization energy offset (default: 0.2)
- `--NS`: Baseline interpolation points (default: 20)
- `--fitmode`: Baseline fit mode - 0=no fit, 1=linear, 2=Rayleigh scattering (E^4) (default: 2)
- `--datasets`: Comma-separated dataset indices to fit (default: all)
- `--no-plot`: Do not generate plots
- `--output-dir`: Output directory (default: current directory)

예시:
```bash
python3 main.py data.txt --NS 20 --fitmode 2 --datasets 1,2,3
```

## 파일 형식

입력 파일은 공백 또는 탭으로 구분된 텍스트 파일이어야 합니다:
- 첫 번째 열: 에너지 (eV)
- 두 번째 열 이후: 흡수 데이터 (여러 데이터셋 가능)

### 예시 파일 형식

```
2.0    0.001    0.002    0.001
2.1    0.005    0.008    0.006
2.2    0.015    0.020    0.018
2.3    0.035    0.045    0.040
...
```

- 첫 번째 열: 에너지 값 (2.0, 2.1, 2.2, ...)
- 두 번째 열: 첫 번째 데이터셋의 흡수 데이터
- 세 번째 열: 두 번째 데이터셋의 흡수 데이터
- 네 번째 열: 세 번째 데이터셋의 흡수 데이터
- ...

**참고**: 
- 공백 또는 탭으로 구분
- 주석 라인은 `#`으로 시작 가능
- 빈 줄은 무시됨
- 여러 데이터셋을 한 파일에 포함 가능

## 출력 파일

- `*_FittedBand.dat`: Band contribution
- `*_FittedExciton.dat`: Exciton contribution
- `*_FitResult.dat`: Fitting 파라미터 및 결과
- `*.pdf`: 결과 그래프

## Fitting 파라미터

- **Eg**: Band gap energy (eV)
- **Eb**: Exciton binding energy (eV)
- **Gamma**: Linewidth (eV)
- **ucvsq**: Transition dipole moment squared
- **mhcnp**: Mass parameter
- **q**: Fractional dimension parameter
  - 0: bulk
  - 0.5-0.6: quasi 2D
  - 1.5: strong QD

Effective dimension: Deff = 3 - 2*q

## 원본 MATLAB 코드

이 코드는 다음 MATLAB 파일들을 Python으로 변환한 것입니다:
- `fsum2D.m`: F-sum rule fitting 함수
- `main.m`: 메인 스크립트
