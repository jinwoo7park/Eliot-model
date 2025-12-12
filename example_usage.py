"""
사용 예시 스크립트
이 파일을 참고하여 자신의 코드에서 사용할 수 있습니다.
"""
from fitter import FSumFitter
import numpy as np

# 방법 1: 파일 경로로 직접 분석
def example1():
    """파일 경로를 지정하여 분석"""
    filepath = "your_data.txt"  # 여기에 파일 경로 입력
    
    # Fitter 생성
    fitter = FSumFitter(deltaE=0.2, NS=20, fitmode=2)
    
    # 파일 분석 (모든 데이터셋)
    results = fitter.process_file(filepath)
    
    # 결과 저장
    fitter.save_results(results, output_dir='.')
    
    # 그래프 생성
    fitter.plot_results(results, save_path='results.pdf')
    
    # 결과 확인
    print("Fitting 결과:")
    for idx, params in enumerate(results['fitresult']):
        print(f"Dataset {idx+1}:")
        print(f"  Eg={params[0]:.4f} eV")
        print(f"  Eb={params[1]:.4f} eV")
        print(f"  R²={results['quality'][idx]:.4f}")


# 방법 2: 특정 데이터셋만 분석
def example2():
    """특정 데이터셋만 분석"""
    filepath = "your_data.txt"
    
    fitter = FSumFitter()
    
    # 데이터셋 1, 2, 3만 분석
    results = fitter.process_file(filepath, T=[1, 2, 3])
    
    fitter.save_results(results)
    fitter.plot_results(results, save_path='results.pdf')


# 방법 3: 직접 데이터 배열로 분석
def example3():
    """numpy 배열로 직접 분석"""
    # 예시 데이터 (실제로는 파일에서 읽어옴)
    xdata = np.linspace(2.0, 3.0, 100)  # 에너지
    ydata = np.random.rand(100) * 0.1  # 흡수 데이터 (예시)
    
    fitter = FSumFitter()
    
    # Baseline 제거
    baseline = fitter.fit_baseline(xdata, ydata)
    cleandata = ydata - baseline
    
    # Fitting 수행
    estimates, sse, fitted_curve, exciton, band = fitter.fit_data(
        xdata, cleandata
    )
    
    print(f"Fitted parameters: {estimates}")
    print(f"SSE: {sse}")


# 방법 4: 파라미터 커스터마이징
def example4():
    """시작점과 경계값 커스터마이징"""
    filepath = "your_data.txt"
    
    fitter = FSumFitter()
    
    # 시작점 변경
    fitter.start_point = np.array([2.60, 0.055, 0.040, 35, 0.065, 0])
    
    # 경계값 변경
    fitter.lb = np.array([2.50, 0.01, 0.00, 0.010, 0.000, 0])
    fitter.rb = np.array([2.70, 0.25, 0.25, 1000.0, 0.999, 0])
    
    results = fitter.process_file(filepath)
    fitter.save_results(results)
    fitter.plot_results(results)


if __name__ == '__main__':
    print("사용 예시를 보려면 각 함수의 주석을 해제하고 실행하세요.")
    print()
    print("가장 간단한 사용법:")
    print("  from fitter import FSumFitter")
    print("  fitter = FSumFitter()")
    print("  results = fitter.process_file('your_data.txt')")
    print("  fitter.save_results(results)")
    print("  fitter.plot_results(results)")
