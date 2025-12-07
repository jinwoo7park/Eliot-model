"""
Flask 웹 애플리케이션: Elliot Fitting 웹 인터페이스
"""
import os
import io
import base64
import tempfile
from flask import Flask, render_template, request, send_file, jsonify
from elliot_fitting import ElliotFitter
import numpy as np
import matplotlib
matplotlib.use('Agg')  # GUI 백엔드 없이 사용
import matplotlib.pyplot as plt

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 최대 파일 크기
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/fit', methods=['POST'])
def fit_data():
    """데이터 피팅 API"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일이 업로드되지 않았습니다.'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        # 파라미터 가져오기
        fitmode = int(request.form.get('fitmode', 2))
        NS = int(request.form.get('NS', 20))
        
        # 파일 저장
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        file.save(temp_file.name)
        temp_file.close()
        
        # 피팅 실행
        fitter = ElliotFitter(fitmode=fitmode, NS=NS)
        results = fitter.fit(temp_file.name)
        
        # 결과 준비
        response_data = {
            'success': True,
            'results': {}
        }
        
        # 각 데이터셋 결과 처리
        for dataset_num, result in results.items():
            # 그래프 생성
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # 실험 데이터
            ax.plot(fitter.xdata, result['cleandata'], 'o', 
                   markersize=4, label='Experiment', alpha=0.6)
            
            # 피팅 곡선
            ax.plot(fitter.xdata, result['FittedCurve'], '-', 
                   linewidth=2, label='Fit', color='black')
            
            # Baseline 구분선
            baseline_idx = len(fitter.xdata) - NS
            ax.axvline(fitter.xdata[baseline_idx], '--', 
                      color='gray', alpha=0.5, label='Baseline region')
            
            # Band와 Exciton 성분
            ax.fill_between(fitter.xdata, 0, result['band'], 
                           alpha=0.5, color='red', label='Band')
            ax.fill_between(fitter.xdata, 0, result['exciton'], 
                           alpha=0.5, color='blue', label='Exciton')
            
            ax.set_xlabel('Energy (eV)', fontsize=12)
            ax.set_ylabel('Absorption', fontsize=12)
            ax.set_title(f'Dataset {dataset_num}: Eb={result["estimates"][1]:.3f} eV', fontsize=14)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.set_ylim([-0.1, np.max(result['FittedCurve']) * 1.1])
            
            plt.tight_layout()
            
            # 그래프를 base64로 인코딩
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
            
            # 결과 데이터
            response_data['results'][str(dataset_num)] = {
                'Eg': float(result['estimates'][0]),
                'Eb': float(result['estimates'][1]),
                'Gamma': float(result['estimates'][2]),
                'ucvsq': float(result['estimates'][3]),
                'mhcnp': float(result['estimates'][4]),
                'q': float(result['estimates'][5]),
                'r_squared': float(result['r_squared']),
                'urbach_energy': float(result['urbach_energy']) if not np.isnan(result['urbach_energy']) else None,
                'plot': img_base64
            }
        
        # 임시 파일 삭제
        os.unlink(temp_file.name)
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': f'오류 발생: {str(e)}'}), 500

@app.route('/api/download', methods=['POST'])
def download_results():
    """결과 파일 다운로드"""
    try:
        data = request.json
        if 'file' not in data or 'results' not in data:
            return jsonify({'error': '필수 데이터가 없습니다.'}), 400
        
        # 파일 업로드 및 피팅 (다시 실행)
        # 실제 구현에서는 세션에 결과를 저장하거나 다른 방법 사용
        return jsonify({'error': '다운로드 기능은 구현 중입니다.'}), 501
        
    except Exception as e:
        return jsonify({'error': f'오류 발생: {str(e)}'}), 500

# Vercel serverless function을 위한 핸들러
# Vercel은 WSGI 앱을 자동으로 감지하므로 app 객체를 export
# 로컬 개발용
if __name__ == '__main__':
    app.run(debug=True, port=5000)
