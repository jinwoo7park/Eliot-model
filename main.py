"""
메인 실행 스크립트
MATLAB main.m의 Python 버전
"""

import argparse
from elliot_fitting import ElliotFitter


def main():
    parser = argparse.ArgumentParser(
        description='Elliot Fitting: Exciton Binding Energy Analysis'
    )
    parser.add_argument('filename', type=str, 
                       help='Input data file (txt format)')
    parser.add_argument('--fitmode', type=int, default=2,
                       help='Baseline fitting mode (0: no fit, 1: linear, 2: power)')
    parser.add_argument('--NS', type=int, default=20,
                       help='Number of datapoints for baseline interpolation')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file prefix (default: input filename)')
    
    args = parser.parse_args()
    
    # 출력 파일명 설정
    if args.output is None:
        import os
        base_name = os.path.splitext(os.path.basename(args.filename))[0]
        output_prefix = base_name
    else:
        output_prefix = args.output
    
    # Fitter 생성 및 실행
    fitter = ElliotFitter(fitmode=args.fitmode, NS=args.NS)
    results = fitter.fit(args.filename)
    
    # 결과 저장 및 시각화
    fitter.save_results(output_prefix)
    fitter.plot_results(save_path=f'{output_prefix}.pdf')
    
    print("\n피팅 완료!")
    print(f"결과 파일: {output_prefix}_*.dat")
    print(f"그래프: {output_prefix}.pdf")


if __name__ == '__main__':
    main()


