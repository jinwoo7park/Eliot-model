"""
사용 예제 스크립트
"""

from elliot_fitting import ElliotFitter, fit_absorption_spectrum
import numpy as np

# 예제 1: 간단한 사용법
print("예제 1: 간단한 사용법")
fitter, results = fit_absorption_spectrum('data.txt')
fitter.plot_results()
fitter.save_results('output')

# 예제 2: 커스텀 파라미터로 피팅
print("\n예제 2: 커스텀 파라미터")
fitter = ElliotFitter(
    start_point=[2.62, 0.050, 0.043, 37, 0.060, 0],
    bounds=([2.54, 0.01, 0.00, 0.010, 0.000, 0],
            [2.68, 0.2, 0.20, 1000.0, 0.999, 0]),
    fitmode=2,
    NS=20
)

results = fitter.fit('data.txt', T=[1])  # 첫 번째 데이터셋만 피팅
fitter.plot_results(save_path='custom_fit.pdf')
fitter.save_results('custom_output')

# 예제 3: 결과 접근
print("\n예제 3: 결과 접근")
for dataset_num, result in results.items():
    print(f"\nDataset {dataset_num}:")
    print(f"  Eg = {result['estimates'][0]:.4f} eV")
    print(f"  Eb = {result['estimates'][1]:.4f} eV")
    print(f"  Gamma = {result['estimates'][2]:.4f} eV")
    print(f"  R² = {result['r_squared']:.4f}")
    print(f"  Urbach Energy = {result['urbach_energy']:.4f} eV")


