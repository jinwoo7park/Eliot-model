"""
FastAPI 백엔드 서버
F-sum rule fitting을 위한 REST API
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import tempfile
import numpy as np
from fitter import FSumFitter

app = FastAPI(title="F-sum Rule Fitting API")

# CORS 설정 (프론트엔드에서 접근 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 임시 파일 저장 디렉토리
TEMP_DIR = tempfile.mkdtemp(prefix="fsum_fitting_")
os.makedirs(TEMP_DIR, exist_ok=True)

# 업로드된 파일 정보 저장 (세션별)
uploaded_files = {}


class InitialValues(BaseModel):
    Eg: float = 2.62
    Eb: float = 0.050
    Gamma: float = 0.100
    ucvsq: float = 37
    mhcnp: float = 0.060
    q: float = 0


class Bounds(BaseModel):
    Eg: Optional[dict] = None  # {lower: float, upper: float} 또는 None (동적 계산)
    Eb: Optional[dict] = None
    Gamma: Optional[dict] = None
    ucvsq: Optional[dict] = None
    mhcnp: Optional[dict] = None
    q: Optional[dict] = None
    
    class Config:
        extra = "allow"  # 추가 필드 허용


class AnalyzeRequest(BaseModel):
    filename: str
    fitmode: int = 2
    baseline_points: List[float]  # [x1, x2, x3] 또는 [x1, x2] (fitmode==0일 때)
    initial_values: Optional[InitialValues] = None
    bounds: Optional[Bounds] = None


@app.get("/")
async def root():
    return {"message": "F-sum Rule Fitting API", "version": "1.0.0"}


@app.post("/api/preview")
async def preview_file(file: UploadFile = File(...)):
    """
    파일을 업로드하고 그래프를 생성하여 클릭 선택을 위한 이미지를 반환합니다.
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from io import BytesIO
        import base64
        
        # 파일 저장
        file_path = os.path.join(TEMP_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 데이터 읽기
        fitter = FSumFitter(deltaE=0.2, NS=20, fitmode=2)
        
        # process_file과 동일한 방식으로 데이터 읽기
        from io import StringIO
        file_ext = os.path.splitext(file_path)[1].lower()
        delimiter = ',' if file_ext == '.csv' else None
        
        encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr', 'latin-1']
        all_lines = None
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    all_lines = f.readlines()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if all_lines is None:
            raise ValueError("파일을 읽을 수 없습니다.")
        
        # 데이터 시작 줄 찾기
        data_start_idx = 0
        for i, line in enumerate(all_lines):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if delimiter:
                parts = [p.strip() for p in line.split(delimiter)]
            else:
                parts = line.split()
            if len(parts) < 2:
                continue
            try:
                float(parts[0])
                float(parts[1])
                data_start_idx = i
                break
            except ValueError:
                continue
        
        data_lines = [all_lines[i].strip() for i in range(data_start_idx, len(all_lines)) if all_lines[i].strip()]
        data_string = '\n'.join(data_lines)
        
        if file_ext == '.csv':
            raw = np.loadtxt(StringIO(data_string), delimiter=',')
        else:
            raw = np.loadtxt(StringIO(data_string))
        
        # 데이터 형식 확인
        if len(raw.shape) == 1:
            raise ValueError("데이터가 1차원입니다. 최소 2열(파장, 흡수)이 필요합니다.")
        if raw.shape[1] < 2:
            raise ValueError(f"데이터 열이 부족합니다. 현재 {raw.shape[1]}열, 최소 2열 필요.")
        
        xdata_original = raw[:, 0].copy()
        xdata = 1239.84193 / xdata_original  # nm to eV
        
        # 첫 번째 데이터셋만 표시 (두 번째 열)
        if raw.shape[1] >= 2:
            ydata = raw[:, 1]
        else:
            raise ValueError("데이터셋이 없습니다.")
        
        # 파일 정보 저장
        uploaded_files[file.filename] = {
            'path': file_path,
            'xdata': xdata.tolist(),
            'ydata': ydata.tolist()
        }
        
        # 그래프 생성
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 여백 고정 (정확한 좌표 계산을 위해)
        # left, bottom, right, top은 figure 크기에 대한 비율 (0~1)
        margins = {
            'left': 0.12,
            'right': 0.95,
            'bottom': 0.12,
            'top': 0.90
        }
        fig.subplots_adjust(**margins)
        
        ax.plot(xdata, ydata, '-', color='black', linewidth=1.5, alpha=0.7)
        ax.set_xlabel('Energy (eV)', fontsize=12)
        ax.set_ylabel('Absorption', fontsize=12)
        ax.set_title('Baseline 및 피팅 범위 선택', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # x축 범위를 데이터 범위로 고정
        x_min, x_max = np.min(xdata), np.max(xdata)
        ax.set_xlim(x_min, x_max)
        
        # y축 범위도 설정 (선택적)
        y_min, y_max = np.min(ydata), np.max(ydata)
        y_margin = (y_max - y_min) * 0.05
        ax.set_ylim(y_min - y_margin, y_max + y_margin)
        
        # 이미지로 변환 (고정 크기 사용하여 정확한 좌표 계산)
        # pad_inches=0으로 하여 subplots_adjust로 설정한 여백이 그대로 유지되도록 함
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches=None, pad_inches=0)
        plt.close(fig)
        buf.seek(0)
        
        # 이미지 크기 읽기
        try:
            from PIL import Image
            img_pil = Image.open(buf)
            img_width_px = img_pil.width
            img_height_px = img_pil.height
            buf.seek(0)  # 다시 처음으로
        except ImportError:
            # PIL이 없으면 계산된 값 사용 (dpi=100, figsize=(10,6) = 1000x600)
            img_width_px = 1000
            img_height_px = 600
            buf.seek(0)
        
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        
        return {
            "success": True,
            "image": f"data:image/png;base64,{image_base64}",
            "xdata": xdata.tolist(),
            "ydata": ydata.tolist(),
            "filename": file.filename,
            "xmin": float(x_min),
            "xmax": float(x_max),
            "ymin": float(y_min),
            "ymax": float(y_max),
            "ax_x0": float(margins['left']),  # 고정된 여백 값 사용
            "ax_x1": float(margins['right']),
            "ax_y0": float(margins['bottom']),
            "ax_y1": float(margins['top']),
            "img_width": int(img_width_px),  # 이미지 실제 픽셀 너비
            "img_height": int(img_height_px)  # 이미지 실제 픽셀 높이
        }
    except Exception as e:
        import traceback
        error_detail = str(e)
        # 사용자에게 친숙한 오류 메시지 제공
        if "데이터" in error_detail or "열" in error_detail:
            error_message = error_detail
        else:
            error_message = f"파일 처리 중 오류가 발생했습니다: {error_detail}"
        print(f"Preview 오류: {error_message}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_message)


@app.post("/api/analyze")
async def analyze_file(request: AnalyzeRequest):
    """
    클릭 좌표를 받아서 분석을 수행합니다.
    웹에서는 그래프 클릭이 불가능하므로, 클릭 좌표를 받아서 
    임시 파일에 저장하고 process_file을 호출합니다.
    """
    try:
        if request.filename not in uploaded_files:
            raise HTTPException(status_code=404, detail="File not found. Please upload file first.")
        
        file_info = uploaded_files[request.filename]
        file_path = file_info['path']
        
        # 클릭 좌표에서 에너지 값 추출
        baseline_points = request.baseline_points
        fitmode = request.fitmode
        
        # 클릭 좌표를 임시 파일에 저장하여 process_file에서 읽을 수 있도록 함
        # 하지만 process_file은 그래프를 띄우므로, 다른 방법 필요
        
        # 임시 해결책: 클릭 좌표를 환경 변수나 파일에 저장하고
        # fitter.py를 수정하여 이를 읽도록 하거나,
        # 또는 process_file을 직접 수정하여 클릭 좌표를 받을 수 있도록 함
        
        # 일단 기본 동작으로 진행 (baseline_select=True이지만,
        # 실제로는 클릭 좌표를 사용해야 함)
        # 이 부분은 fitter.py를 수정해야 정확히 작동함
        
        # Fitter 초기화
        fitter = FSumFitter(deltaE=0.2, NS=20, fitmode=fitmode)
        
        # 클릭 좌표를 사용하여 min_energy, max_energy 계산
        if fitmode == 0:
            if len(baseline_points) != 2:
                raise HTTPException(status_code=400, detail="fitmode=0일 때는 2개의 점이 필요합니다.")
            fit_min, fit_max = sorted(baseline_points)
        else:
            if len(baseline_points) != 3:
                raise HTTPException(status_code=400, detail="fitmode!=0일 때는 3개의 점이 필요합니다.")
            x1, x2, x3 = baseline_points
            fit_min, fit_max = sorted([x1, x3])
        
        # Initial values 설정
        if request.initial_values:
            initial_vals = request.initial_values
            fitter.start_point = np.array([
                initial_vals.Eg,
                initial_vals.Eb,
                initial_vals.Gamma,
                initial_vals.ucvsq,
                initial_vals.mhcnp,
                initial_vals.q
            ])
        
        # Bounds 설정 (사용자가 제공한 경우)
        print(f"DEBUG: Received bounds: {request.bounds}")
        if request.bounds:
            bounds_data = request.bounds
            param_order = ['Eg', 'Eb', 'Gamma', 'ucvsq', 'mhcnp', 'q']
            
            # 기본 bounds 복사
            new_lb = fitter.lb.copy()
            new_rb = fitter.rb.copy()
            
            print(f"DEBUG: Default bounds - lb: {new_lb}, rb: {new_rb}")
            
            # Pydantic 모델에서 값을 가져오기 (여러 방법 시도)
            bounds_dict = {}
            try:
                # 방법 1: model_dump() (Pydantic v2)
                if hasattr(bounds_data, 'model_dump'):
                    bounds_dict = bounds_data.model_dump()
                    print(f"DEBUG: Using model_dump() - {bounds_dict}")
                # 방법 2: dict() (Pydantic v1)
                elif hasattr(bounds_data, 'dict'):
                    bounds_dict = bounds_data.dict()
                    print(f"DEBUG: Using dict() - {bounds_dict}")
                # 방법 3: 직접 속성 접근
                else:
                    for param in param_order:
                        param_val = getattr(bounds_data, param, None)
                        if param_val is not None:
                            bounds_dict[param] = param_val
                    print(f"DEBUG: Using direct attribute access - {bounds_dict}")
            except Exception as e:
                print(f"DEBUG: Error converting bounds: {e}")
                bounds_dict = {}
            
            # 사용자가 제공한 bounds로 업데이트
            for idx, param in enumerate(param_order):
                if param == 'Eg':
                    # Eg는 동적으로 계산되므로 건너뜀
                    continue
                
                # dict에서 파라미터 bounds 가져오기
                param_bounds = bounds_dict.get(param)
                
                if param_bounds and isinstance(param_bounds, dict):
                    lower_val = param_bounds.get('lower')
                    upper_val = param_bounds.get('upper')
                    
                    # None이 아니고 유효한 숫자인 경우에만 업데이트
                    if lower_val is not None and lower_val != '':
                        try:
                            new_lb[idx] = float(lower_val)
                            print(f"DEBUG: Updated {param} lower bound: {fitter.lb[idx]} -> {new_lb[idx]}")
                        except (ValueError, TypeError) as e:
                            print(f"DEBUG: Invalid lower bound for {param}: {lower_val}, error: {e}")
                    
                    if upper_val is not None and upper_val != '':
                        try:
                            new_rb[idx] = float(upper_val)
                            print(f"DEBUG: Updated {param} upper bound: {fitter.rb[idx]} -> {new_rb[idx]}")
                        except (ValueError, TypeError) as e:
                            print(f"DEBUG: Invalid upper bound for {param}: {upper_val}, error: {e}")
            
            fitter.lb = new_lb
            fitter.rb = new_rb
            print(f"DEBUG: Final bounds after update - lb: {fitter.lb}, rb: {fitter.rb}")
        
        # 파일 분석 (클릭 좌표를 직접 사용)
        # process_file_with_points 메서드가 있으면 사용, 없으면 기본 동작
        if hasattr(fitter, 'process_file_with_points'):
            results = fitter.process_file_with_points(
                file_path,
                baseline_points=baseline_points,
                fitmode=fitmode,
                T=[1],
                auto_range=False  # 사용자가 지정한 범위를 그대로 사용하기 위해 자동 범위 조정 끄기
            )
        else:
            # 기본 동작 (그래프가 나타나지만, 웹에서는 사용 불가)
            results = fitter.process_file(
                file_path,
                T=[1],
                min_energy=fit_min,
                max_energy=fit_max,
                auto_range=None,
                baseline_select=True
            )
        
        # 결과 저장
        output_dir = TEMP_DIR
        fitter.save_results(results, output_dir=output_dir)
        
        # 그래프 생성
        name_with_prefix = f"0_{results['name']}"
        plot_path = os.path.join(output_dir, f"{name_with_prefix}.pdf")
        fitter.plot_results(results, save_path=plot_path)
        
        # 결과 파일 경로 반환
        results_file = os.path.join(output_dir, f"{name_with_prefix}_Results.csv")
        
        # fitresult에서 첫 번째 데이터셋의 파라미터 추출
        # fitresult 구조: [Eg, Eb, Gamma, ucvsq, mhcnp, q]
        if len(results['fitresult']) > 0:
            fit_params = results['fitresult'][0]  # 첫 번째 데이터셋
            quality = results['quality'][0] if len(results['quality']) > 0 else 0.0
        else:
            # 기본값 설정
            fit_params = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            quality = 0.0
        
        # 경계값 확인
        Eg = float(fit_params[0])
        Eb = float(fit_params[1])
        Gamma = float(fit_params[2])
        q = float(fit_params[5])
        
        # Initial values에서 Eg 가져오기 (동적 경계값 계산용)
        # 실제로는 fitter에서 데이터로부터 계산된 initial_Eg를 사용하지만,
        # 사용자가 제공한 initial_Eg와 비슷할 것으로 예상됨
        initial_Eg = request.initial_values.Eg if request.initial_values else 2.62
        Eg_lb = initial_Eg - 0.4
        Eg_ub = initial_Eg + 0.4
        
        # 경계값 도달 여부 확인
        boundary_warnings = []
        tolerance = 0.002  # 경계값에 가까운 경우를 확인하기 위한 허용 오차 (0.002 eV = 2 meV)
        
        # 디버깅을 위한 로그
        print(f"DEBUG: Eg={Eg:.6f}, Eb={Eb:.6f}, Gamma={Gamma:.6f}")
        print(f"DEBUG: Eg bounds: {Eg_lb:.6f} ~ {Eg_ub:.6f}")
        
        # Eg 경계값 확인 (동적 경계값: initial_Eg ± 0.4 eV)
        Eg_diff_lb = abs(Eg - Eg_lb)
        Eg_diff_ub = abs(Eg - Eg_ub)
        print(f"DEBUG: Eg differences - lb: {Eg_diff_lb:.6f}, ub: {Eg_diff_ub:.6f}, tolerance: {tolerance}")
        if Eg_diff_lb <= tolerance or Eg_diff_ub <= tolerance:
            boundary_warnings.append("Eg (Band gap)")
            print(f"DEBUG: ✓ Eg boundary reached!")
        
        # Eb 경계값 확인 (0.01 ~ 0.2 eV)
        # 하한값: 0.01 eV, 상한값: 0.2 eV
        Eb_lb = 0.01
        Eb_ub = 0.2
        Eb_diff_lb = abs(Eb - Eb_lb)
        Eb_diff_ub = abs(Eb - Eb_ub)
        print(f"DEBUG: Eb differences - lb: {Eb_diff_lb:.6f}, ub: {Eb_diff_ub:.6f}, tolerance: {tolerance}")
        print(f"DEBUG: Eb check - abs({Eb:.6f} - {Eb_lb}) = {Eb_diff_lb:.6f} <= {tolerance}? {Eb_diff_lb <= tolerance}")
        print(f"DEBUG: Eb check - abs({Eb:.6f} - {Eb_ub}) = {Eb_diff_ub:.6f} <= {tolerance}? {Eb_diff_ub <= tolerance}")
        if Eb_diff_lb <= tolerance or Eb_diff_ub <= tolerance:
            boundary_warnings.append("Eb (Exciton binding energy)")
            print(f"DEBUG: ✓ Eb boundary reached!")
        
        # Gamma 경계값 확인 (0.0 ~ 0.2 eV)
        Gamma_lb = 0.0
        Gamma_ub = 0.2
        Gamma_diff_lb = abs(Gamma - Gamma_lb)
        Gamma_diff_ub = abs(Gamma - Gamma_ub)
        print(f"DEBUG: Gamma differences - lb: {Gamma_diff_lb:.6f}, ub: {Gamma_diff_ub:.6f}, tolerance: {tolerance}")
        if Gamma_diff_lb <= tolerance or Gamma_diff_ub <= tolerance:
            boundary_warnings.append("Gamma")
            print(f"DEBUG: ✓ Gamma boundary reached!")
        
        print(f"DEBUG: Final boundary_warnings={boundary_warnings}")
        
        # q값 경고 (0.4보다 큰 경우)
        q_warning = None
        if q > 0.4:
            q_warning = "q값이 0.4보다 큽니다. Strongly confined low dimension에서는 다른 모델 적용이 필요할 수 있습니다."
        
        return {
            "success": True,
            "results_file": results_file,
            "plot_file": plot_path,
            "name": results['name'],
            "parameters": {
                "Eg": Eg,
                "Eb": Eb,
                "Gamma": Gamma,
                "ucvsq": float(fit_params[3]),
                "mhcnp": float(fit_params[4]),
                "q": q,
            },
            "quality": float(quality),
            "boundary_warnings": boundary_warnings,
            "q_warning": q_warning
        }
    except Exception as e:
        import traceback
        error_detail = str(e)
        # 사용자에게 친숙한 오류 메시지 제공
        print(f"Analyze 오류: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """
    분석 결과 파일을 다운로드합니다.
    """
    file_path = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@app.get("/api/health")
async def health_check():
    """
    서버 상태 확인
    """
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
