"""
간단한 파일 분석 스크립트
파일 경로만 지정하면 바로 분석합니다.
파일 경로를 지정하지 않으면 Finder에서 파일을 선택할 수 있습니다.
"""
import sys
import os
from fitter import FSumFitter

# macOS Tk deprecation warning 억제
os.environ['TK_SILENCE_DEPRECATION'] = '1'

try:
    from tkinter import Tk, filedialog
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

def analyze_file(filepath, datasets=None, NS=20, fitmode=2, min_energy=None, max_energy=None, auto_range=None):
    """
    파일을 분석하는 간단한 함수
    
    Parameters:
    -----------
    filepath : str
        분석할 데이터 파일 경로
    datasets : list, optional
        분석할 데이터셋 번호 리스트 (1부터 시작, None이면 모두 분석)
    NS : int
        Baseline interpolation points (default: 20)
    fitmode : int
        Baseline fit mode: 0=no fit, 1=linear, 2=Rayleigh scattering (E^4) (default: 2)
    min_energy : float, optional
        Minimum energy for fitting range (eV)
    max_energy : float, optional
        Maximum energy for fitting range (eV)
    auto_range : bool, optional
        If False, disables automatic bandgap-focused fitting (Eg ± 0.5 eV).
        If True or None, automatically refits within Eg ± 0.5 eV (default: None, auto-enabled)
    """
    if not os.path.exists(filepath):
        print(f"❌ 파일을 찾을 수 없습니다: {filepath}")
        return
    
    print(f"📂 파일 분석 시작: {filepath}")
    fitmode_names = {0: 'No baseline', 1: 'Linear baseline', 2: 'Rayleigh scattering (E^4)'}
    fitmode_name = fitmode_names.get(fitmode, f'Mode {fitmode}')
    print(f"   NS={NS}, fitmode={fitmode} ({fitmode_name})")
    if min_energy is not None or max_energy is not None:
        print(f"   Fitting Range: {min_energy if min_energy else 'Min'} ~ {max_energy if max_energy else 'Max'} eV")
    if auto_range is not False:
        print(f"   🎯 Bandgap-focused fitting: ON (Eg ± 0.5 eV)")
    
    if datasets:
        print(f"   분석할 데이터셋: {datasets}")
    else:
        print(f"   모든 데이터셋 분석")
    print()
    
    # Fitter 초기화
    fitter = FSumFitter(deltaE=0.2, NS=NS, fitmode=fitmode)
    
    # 파일 분석
    results = fitter.process_file(filepath, T=datasets, min_energy=min_energy, max_energy=max_energy, auto_range=auto_range)
    
    # 결과 저장
    output_dir = os.path.dirname(filepath) or '.'
    fitter.save_results(results, output_dir=output_dir)
    
    # 그래프 저장
    name_with_prefix = f"0_{results['name']}"
    plot_path = os.path.join(output_dir, f"{name_with_prefix}.pdf")
    fitter.plot_results(results, save_path=plot_path)
    
    print()
    print("✅ 분석 완료!")
    print(f"   결과 파일:")
    print(f"   - {name_with_prefix}_Results.csv")
    print(f"   - {name_with_prefix}.pdf")
    
    return results


if __name__ == '__main__':
    filepath = None
    datasets = None
    NS = 20
    fitmode = 2
    min_energy = None
    max_energy = None
    auto_range = None  # Default: auto-enabled (Eg ± 0.5 eV)
    
    # 파일 경로가 제공되었는지 확인
    if len(sys.argv) >= 2 and not sys.argv[1].startswith('--'):
        filepath = sys.argv[1]
        arg_start = 2
    else:
        arg_start = 1
    
    # 파일 경로가 없으면 Finder에서 선택
    if filepath is None:
        if HAS_TKINTER:
            print("📁 파일 선택 창을 엽니다...")
            root = Tk()
            root.withdraw()  # 메인 윈도우 숨기기
            root.attributes('-topmost', True)  # 창을 맨 앞으로
            
            filepath = filedialog.askopenfilename(
                title="분석할 데이터 파일 선택",
                filetypes=[
                    ("데이터 파일", "*.txt *.dat *.csv"),
                    ("CSV 파일", "*.csv"),
                    ("텍스트 파일", "*.txt *.dat"),
                    ("모든 파일", "*.*")
                ]
            )
            root.destroy()
            
            if not filepath:
                print("❌ 파일이 선택되지 않았습니다.")
                sys.exit(1)
        else:
            print("사용법:")
            print("  python3 analyze.py <파일경로> [옵션]")
            print()
            print("옵션:")
            print("  --datasets 1,2,3  : 분석할 데이터셋 번호 (쉼표로 구분)")
            print("  --NS 20           : Baseline points (기본값: 20)")
            print("  --fitmode 2       : Baseline fit mode (0=no fit, 1=linear, 2=Rayleigh scattering E^4, 기본값: 2)")
            print("  --min 2.0         : 최소 에너지 (eV)")
            print("  --max 3.0         : 최대 에너지 (eV)")
            print("  --no-auto         : Bandgap-focused fitting 비활성화 (기본값: Eg ± 0.5 eV 활성화)")
            print()
            print("예시:")
            print("  python3 analyze.py data.txt")
            print("  python3 analyze.py data.txt --datasets 1,2,3 --NS 20 --min 2.4 --max 2.8")
            print("  python3 analyze.py data.txt --auto")
            print()
            print("또는 파일 경로 없이 실행하면 Finder에서 파일을 선택할 수 있습니다.")
            sys.exit(1)
    
    # 옵션 파싱
    i = arg_start
    while i < len(sys.argv):
        if sys.argv[i] == '--datasets' and i + 1 < len(sys.argv):
            datasets = [int(x.strip()) for x in sys.argv[i + 1].split(',')]
            i += 2
        elif sys.argv[i] == '--NS' and i + 1 < len(sys.argv):
            NS = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--fitmode' and i + 1 < len(sys.argv):
            fitmode = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--min' and i + 1 < len(sys.argv):
            min_energy = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--max' and i + 1 < len(sys.argv):
            max_energy = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--no-auto':
            auto_range = False
            i += 1
        else:
            i += 1
    
    # 분석 실행
    analyze_file(filepath, datasets=datasets, NS=NS, fitmode=fitmode, min_energy=min_energy, max_energy=max_energy, auto_range=auto_range)
