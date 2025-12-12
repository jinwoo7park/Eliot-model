"""
Main fitting script
Python implementation of main.m
"""
import os
import tempfile
import numpy as np
from scipy.optimize import minimize
from scipy.optimize import Bounds
from scipy.optimize import NonlinearConstraint
from scipy.optimize import curve_fit
from io import StringIO

from fsum2d import fsum2d

# Ensure Matplotlib has a writable config/cache directory (prevents slow import & warnings on some macOS setups)
_mpl_config_dir = os.path.join(tempfile.gettempdir(), "matplotlib")
try:
    os.makedirs(_mpl_config_dir, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", _mpl_config_dir)
except Exception:
    # If we can't create it, Matplotlib will fall back; not fatal.
    pass

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정 (macOS)
try:
    # macOS에서 사용 가능한 한글 폰트 찾기
    font_list = [f.name for f in fm.fontManager.ttflist]
    korean_fonts = ['AppleGothic', 'NanumGothic', 'NanumBarunGothic', 'Malgun Gothic', 'Apple SD Gothic Neo']
    korean_font = None
    for font_name in korean_fonts:
        if font_name in font_list:
            korean_font = font_name
            break
    
    if korean_font:
        plt.rcParams['font.family'] = korean_font
        plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
except Exception:
    # 폰트 설정 실패 시 경고만 출력하고 계속 진행
    pass


class FSumFitter:
    """
    F-sum rule fitting class
    """
    
    def __init__(self, deltaE=0.2, NS=20, fitmode=2):
        """
        Parameters:
        -----------
        deltaE : float
            Offset of normalization energy relative to first exciton transition peak
        NS : int
            Number of datapoints for spline interpolation
        fitmode : int
            0 = no baseline (baseline = 0), 1 = linear baseline, 2 = Rayleigh scattering baseline (E^4)
        """
        self.deltaE = deltaE
        self.NS = NS
        self.fitmode = fitmode
        
        # Default starting point and bounds
        # q parameter bounds: 0 (bulk) to 1.5 (strong QD)
        # Deff = 3 - 2*q, so q <= 1.5 ensures Deff >= 0
        # Note: Eg will be dynamically set from data (first point where absorption > 0.01)
        # Note: Eg bounds will be set to Eg ± 0.4 eV dynamically
        self.start_point = np.array([2.62, 0.050, 0.100, 37, 0.060, 0])  # Eb=50meV, gamma=100meV, q=0 (bulk)
        self.lb = np.array([2.54, 0.01, 0.00, 0.010, 0.000, 0.0])      # Eb lower bound: 10meV, q lower bound: 0 (bulk)
        self.rb = np.array([2.68, 0.2, 0.20, 1000.0, 0.999, 1.5])       # q upper bound: 1.5 (strong QD)
        # Note: Eg bounds will be dynamically updated in process_file
        
    def fit_baseline(self, xdata, ydata, baseline_mask):
        """
        Fit baseline using user-selected mask only.
        
        Parameters:
        -----------
        xdata : array
            Energy data
        ydata : array
            Absorption data
        baseline_mask : array (bool)
            Mask indicating which data points were used for baseline fitting
            
        Returns:
        --------
        baseline : array
            Baseline values
        baseline_mask : array (bool)
            The same mask used for baseline fitting
        """
        if self.fitmode == 0:
            return np.zeros(len(xdata)), np.zeros(len(xdata), dtype=bool)

        baseline_mask = np.asarray(baseline_mask, dtype=bool)
        if baseline_mask.shape != (len(xdata),):
            raise ValueError("baseline_mask must have the same length as xdata")
        
        x_fit = xdata[baseline_mask]
        y_fit = ydata[baseline_mask]
        
        if len(x_fit) < 2:
            return np.zeros(len(xdata)), baseline_mask
        
        if self.fitmode == 1:
            # Linear fit
            coeffs = np.polyfit(x_fit, y_fit, 1)
            baseline = np.polyval(coeffs, xdata)
            return baseline, baseline_mask
        elif self.fitmode == 2:
            # Rayleigh scattering: y = a * E^4 + b * E + c
            # Fit coefficients using least squares
            E_fit = x_fit
            E4_fit = x_fit ** 4
            
            # Create design matrix: [E^4, E, 1]
            A = np.column_stack([E4_fit, E_fit, np.ones(len(E_fit))])
            
            # Solve least squares: A * [a, b, c]^T = y_fit
            coeffs, residuals, rank, s = np.linalg.lstsq(A, y_fit, rcond=None)
            
            # Extract coefficients
            a, b, c = coeffs[0], coeffs[1], coeffs[2]
            
            # Generate baseline for full range: baseline = a * E^4 + b * E + c
            baseline = a * (xdata ** 4) + b * xdata + c
            return baseline, baseline_mask
        else:
            raise ValueError(f"Fitmode {self.fitmode} not implemented")

    def select_baseline_mask_interactive(self, xdata, ydata, title=None, fitmode=None):
        """
        Interactive baseline range and fitting range selection using a plot.

        Usage:
        - If fitmode == 0: Click TWO points for fitting range only
        - Otherwise: Click THREE points:
          1. First point: baseline start point
          2. Second point: baseline end point
          3. Third point: fitting range end point
        - Vertical lines appear immediately when clicking.
        - Fitting range is from first point to last point.
        - After selecting all points, fitting proceeds automatically.

        Parameters
        ----------
        fitmode : int, optional
            If 0, only fitting range (2 points) is selected.
            Otherwise, baseline and fitting range (3 points) are selected.

        Returns
        -------
        tuple : (baseline_mask, fit_mask) or None
            baseline_mask: Mask for baseline range (first to second point, None if fitmode==0)
            fit_mask: Mask for fitting range (first to last point)
            Returns None if selection failed/cancelled.
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot data with better styling (solid line)
            ax.plot(xdata, ydata, '-', color='black', linewidth=1.5, alpha=0.7, label='Data')
            ax.set_xlabel('Energy (eV)', fontsize=12)
            ax.set_ylabel('Absorption', fontsize=12)
            if title:
                ax.set_title(title, fontsize=13, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--')
            
            # Improved instruction text
            if fitmode == 0:
                initial_text = "1) 피팅 범위 시작점 클릭\n2) 피팅 범위 끝점 클릭"
            else:
                initial_text = "1) Baseline 시작점 클릭\n2) Baseline 끝점 클릭\n3) 피팅 범위 끝점 클릭"
            
            instruction_text = ax.text(
                0.02, 0.98,
                initial_text,
                transform=ax.transAxes,
                va='top',
                ha='left',
                fontsize=11,
                bbox=dict(boxstyle="round,pad=0.5", fc="lightyellow", ec="orange", alpha=0.9, linewidth=1.5)
            )
            
            # Set better axis limits
            y_margin = (np.max(ydata) - np.min(ydata)) * 0.1
            ax.set_ylim([np.min(ydata) - y_margin, np.max(ydata) + y_margin])
            
            plt.tight_layout()
            
            # Store selected points and line objects
            selected_points = []
            vlines = []  # Store vertical line objects
            baseline_vspan = None  # Store baseline vertical span object
            fit_vspan = None  # Store fitting range vertical span object
            
            def on_click(event):
                """Handle mouse click events"""
                nonlocal baseline_vspan, fit_vspan, cid
                if event.inaxes != ax:
                    return
                if event.button != 1:  # Only left mouse button
                    return
                # Get x coordinate
                x_click = event.xdata
                if x_click is None:
                    return

                selected_points.append(x_click)
                
                # Draw vertical line immediately
                y_min, y_max = ax.get_ylim()
                if fitmode == 0:
                    # For fitmode==0, all points are for fitting range (green)
                    vline = ax.axvline(x=x_click, color='green', linestyle='--', 
                                      linewidth=2, alpha=0.8)
                else:
                    # For other modes, first two are baseline (orange), third is fitting end (green)
                    if len(selected_points) <= 2:
                        vline = ax.axvline(x=x_click, color='orange', linestyle='--', 
                                          linewidth=2, alpha=0.8)
                    else:
                        vline = ax.axvline(x=x_click, color='green', linestyle='--', 
                                          linewidth=2, alpha=0.8)
                vlines.append(vline)
                
                # Update instruction text and draw spans
                if fitmode == 0:
                    # Two-point selection for fitting range only
                    if len(selected_points) == 1:
                        instruction_text.set_text(
                            f"1) 피팅 범위 시작점 선택됨: {x_click:.3f} eV\n2) 피팅 범위 끝점을 클릭하세요"
                        )
                    elif len(selected_points) == 2:
                        x1, x2 = selected_points[0], selected_points[1]
                        fit_min, fit_max = (x1, x2) if x1 <= x2 else (x2, x1)
                        
                        # Draw fitting range span
                        if fit_vspan is not None:
                            fit_vspan.remove()
                        fit_vspan = ax.axvspan(fit_min, fit_max, alpha=0.15, color='green')
                        
                        instruction_text.set_text(
                            f"✅ 선택 완료!\n피팅 범위: {fit_min:.3f} - {fit_max:.3f} eV\n피팅을 시작합니다..."
                        )
                        
                        # Disconnect event handler and close figure
                        fig.canvas.mpl_disconnect(cid)
                        plt.draw()
                        plt.pause(0.5)  # Brief pause to show final state
                        plt.close(fig)
                        return
                else:
                    # Three-point selection: baseline + fitting range
                    if len(selected_points) == 1:
                        instruction_text.set_text(
                            f"1) Baseline 시작점 선택됨: {x_click:.3f} eV\n2) Baseline 끝점을 클릭하세요"
                        )
                    elif len(selected_points) == 2:
                        x1, x2 = selected_points[0], selected_points[1]
                        baseline_min, baseline_max = (x1, x2) if x1 <= x2 else (x2, x1)
                        
                        # Draw baseline span
                        if baseline_vspan is not None:
                            baseline_vspan.remove()
                        baseline_vspan = ax.axvspan(baseline_min, baseline_max, alpha=0.15, color='orange')
                        
                        instruction_text.set_text(
                            f"2) Baseline 끝점 선택됨: {x2:.3f} eV\nBaseline 범위: {baseline_min:.3f} - {baseline_max:.3f} eV\n3) 피팅 범위 끝점을 클릭하세요"
                        )
                    elif len(selected_points) == 3:
                        x1, x2, x3 = selected_points[0], selected_points[1], selected_points[2]
                        baseline_min, baseline_max = (x1, x2) if x1 <= x2 else (x2, x1)
                        fit_min, fit_max = (x1, x3) if x1 <= x3 else (x3, x1)
                        
                        # Draw fitting range span (green, more transparent)
                        if fit_vspan is not None:
                            fit_vspan.remove()
                        fit_vspan = ax.axvspan(fit_min, fit_max, alpha=0.1, color='green')
                        
                        instruction_text.set_text(
                            f"✅ 선택 완료!\nBaseline: {baseline_min:.3f} - {baseline_max:.3f} eV\n피팅 범위: {fit_min:.3f} - {fit_max:.3f} eV\n피팅을 시작합니다..."
                        )
                        
                        # Disconnect event handler and close figure
                        fig.canvas.mpl_disconnect(cid)
                        plt.draw()
                        plt.pause(0.5)  # Brief pause to show final state
                        plt.close(fig)
                        return
                
                plt.draw()

            # Connect click event handler
            cid = fig.canvas.mpl_connect('button_press_event', on_click)
            
            # Show plot and wait for clicks
            required_points = 2 if fitmode == 0 else 3
            plt.show(block=True)
            
            # Check if we got enough points
            if len(selected_points) < required_points:
                plt.close(fig)
                return None

            if fitmode == 0:
                # Two points: fitting range only
                x1, x2 = selected_points[0], selected_points[1]
                fit_min, fit_max = (x1, x2) if x1 <= x2 else (x2, x1)
                fit_mask = (xdata >= fit_min) & (xdata <= fit_max)
                
                if np.sum(fit_mask) < 2:
                    return None
                
                print(f'   ✅ 선택된 피팅 범위: {fit_min:.3f} - {fit_max:.3f} eV ({np.sum(fit_mask)} points)')
                return None, fit_mask  # baseline_mask is None for fitmode==0
            else:
                # Three points: baseline + fitting range
                x1, x2, x3 = selected_points[0], selected_points[1], selected_points[2]
                
                # Baseline range: first to second point
                baseline_min, baseline_max = (x1, x2) if x1 <= x2 else (x2, x1)
                baseline_mask = (xdata >= baseline_min) & (xdata <= baseline_max)
                
                # Fitting range: first to third point
                fit_min, fit_max = (x1, x3) if x1 <= x3 else (x3, x1)
                fit_mask = (xdata >= fit_min) & (xdata <= fit_max)
                
                if np.sum(baseline_mask) < 2:
                    return None
                if np.sum(fit_mask) < 2:
                    return None
                
                print(f'   ✅ 선택된 baseline 구간: {baseline_min:.3f} - {baseline_max:.3f} eV ({np.sum(baseline_mask)} points)')
                print(f'   ✅ 선택된 피팅 범위: {fit_min:.3f} - {fit_max:.3f} eV ({np.sum(fit_mask)} points)')
                return baseline_mask, fit_mask
            
        except Exception as e:
            print(f"⚠️  Baseline 선택 중 오류 발생: {e}")
            if 'fig' in locals():
                plt.close(fig)
            return None
        except Exception:
            # If backend/GUI is not available or user closed window unexpectedly
            try:
                plt.close('all')
            except Exception:
                pass
            return None
    
    def objective_function(self, params, xdata, ydata):
        """
        Objective function for optimization
        """
        sse, _, _, _ = fsum2d(params, xdata, ydata)
        return sse
    
    def fit_data(self, xdata, ydata, start_point=None, bounds=None):
        """
        Fit data using fsum2d model
        
        Parameters:
        -----------
        xdata : array
            Energy data
        ydata : array
            Absorption data (after baseline subtraction)
        start_point : array, optional
            Starting point for optimization
        bounds : Bounds, optional
            Bounds for optimization. If None, uses self.lb and self.rb
            
        Returns:
        --------
        estimates : array
            Fitted parameters [Eg, Eb, Gamma, ucvsq, mhcnp, q]
        sse : float
            Sum of squared errors
        FittedCurve : array
            Fitted curve
        exciton : array
            Exciton contribution
        band : array
            Band contribution
        """
        if start_point is None:
            start_point = self.start_point.copy()
        
        # Define bounds
        if bounds is None:
            bounds = Bounds(self.lb, self.rb)
        
        # Optimize
        result = minimize(
            self.objective_function,
            start_point,
            args=(xdata, ydata),
            method='L-BFGS-B',
            bounds=bounds,
            options={'maxiter': 1000, 'ftol': 1e-13, 'gtol': 1e-12}
        )
        
        estimates = result.x
        
        # Get full results
        sse, FittedCurve, exciton, band = fsum2d(estimates, xdata, ydata)
        
        return estimates, sse, FittedCurve, exciton, band
    
    def calculate_urbach_energy(self, xdata, ydata, Eb, Eg):
        """
        Calculate Urbach energy from exponential tail
        
        Parameters:
        -----------
        xdata : array
            Energy data
        ydata : array
            Absorption data
        Eb : float
            Exciton binding energy
        Eg : float
            Band gap energy
            
        Returns:
        --------
        slope : float
            Urbach slope
        intersect : float
            Intercept
        fitted_urbach : array
            Fitted Urbach tail
        """
        # Find index where energy is less than Eb-Eg
        threshold = abs(Eb - Eg)
        indices = np.where(xdata < threshold)[0]
        
        if len(indices) == 0:
            return 0, 0, np.zeros(len(xdata))
        
        index = indices[0]
        # Use points from index+2 to index+10
        start_idx = min(index + 2, len(xdata) - 1)
        end_idx = min(index + 10, len(xdata))
        
        if end_idx <= start_idx:
            return 0, 0, np.zeros(len(xdata))
        
        x_fit = xdata[start_idx:end_idx]
        y_fit = ydata[start_idx:end_idx]
        
        # Fit log(y) = slope * x + intercept
        log_y = np.log(y_fit)
        coeffs = np.polyfit(x_fit, log_y, 1)
        slope = coeffs[0]
        intersect = coeffs[1]
        
        fitted_urbach = intersect + slope * xdata
        
        return slope, intersect, fitted_urbach
    
    def process_file(self, filename, T=None, min_energy=None, max_energy=None, auto_range=None, baseline_select=True):
        """
        Process a data file and perform fitting
        
        Parameters:
        -----------
        filename : str
            Path to data file (tab, space, or comma delimited)
            Supports .txt, .dat, and .csv files
        T : list, optional
            List of dataset indices to fit (1-indexed, like MATLAB)
            If None, fits all datasets
        min_energy : float, optional
            Minimum energy for fitting range (eV)
        max_energy : float, optional
            Maximum energy for fitting range (eV)
        auto_range : bool, optional
            If False, disables automatic bandgap-focused fitting.
            If True or None, automatically refits within Eg +/- 0.5 eV (default: None, auto-enabled)
        baseline_select : bool, optional
            If True (default), Step 0 baseline range MUST be selected from an interactive plot
            (click two x-positions to define the baseline range).
            
        Returns:
        --------
        results : dict
            Dictionary containing all results
        """
        # Read data - CSV 파일인지 확인하여 구분자 설정
        file_ext = os.path.splitext(filename)[1].lower()
        delimiter = ',' if file_ext == '.csv' else None
        
        # 여러 인코딩을 시도하여 파일 읽기
        encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr', 'latin-1']
        all_lines = None
        for encoding in encodings:
            try:
                with open(filename, 'r', encoding=encoding) as f:
                    all_lines = f.readlines()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if all_lines is None:
            raise ValueError(f"파일을 읽을 수 없습니다. 지원되는 인코딩을 시도했지만 실패했습니다: {encodings}")
        
        # 숫자 데이터가 시작하는 줄 찾기
        # 첫 번째와 두 번째 열이 모두 숫자인 줄을 찾음
        data_start_idx = 0
        for i, line in enumerate(all_lines):
            line = line.strip()
            if not line:  # 빈 줄 건너뛰기
                continue
            if line.startswith('#'):  # 주석 줄 건너뛰기
                continue
            
            # 구분자로 분리
            if delimiter:
                parts = [p.strip() for p in line.split(delimiter)]
            else:
                # 공백/탭으로 분리
                parts = line.split()
            
            if len(parts) < 2:
                continue
            
            # 첫 번째와 두 번째 열이 모두 숫자인지 확인
            try:
                float(parts[0])
                float(parts[1])
                # 둘 다 숫자면 데이터 시작
                data_start_idx = i
                break
            except ValueError:
                # 숫자가 아니면 계속 찾기
                continue
        
        # 데이터 부분만 추출
        data_lines = []
        for i in range(data_start_idx, len(all_lines)):
            line = all_lines[i].strip()
            if line:  # 빈 줄이 아닌 경우만 추가
                data_lines.append(line)
        
        # StringIO를 사용하여 np.loadtxt에 전달
        data_string = '\n'.join(data_lines)
        
        if file_ext == '.csv':
            # CSV 파일인 경우 쉼표 구분자 사용
            raw = np.loadtxt(StringIO(data_string), delimiter=',')
        else:
            # 기본적으로 공백/탭 구분자 사용 (.txt, .dat 등)
            raw = np.loadtxt(StringIO(data_string))
        
        # Extract filename without extension
        name = os.path.splitext(os.path.basename(filename))[0]
        
        data_size = raw.shape
        xdata_original = raw[:, 0].copy()  # 원본 데이터 저장 (nm 단위)
        
        # nm를 eV로 변환: E(eV) = 1239.84193 / λ(nm)
        # 모든 입력 데이터는 nm 단위로 가정
        xdata = 1239.84193 / xdata_original
        
        # Determine which datasets to fit
        if T is None:
            T = list(range(0, data_size[1] - 1))  # Fit all datasets (0-indexed)
        else:
            T = [t - 1 for t in T]  # Convert to 0-indexed
        
        # Initialize result arrays
        fittedcurves = np.zeros(data_size)
        fittedcurves[:, 0] = raw[:, 0]
        fittedurbach = fittedcurves.copy()
        fittedexciton = fittedcurves.copy()
        fittedband = fittedcurves.copy()
        fittedbaseline = fittedcurves.copy()  # Baseline 저장용
        cleandata = fittedcurves.copy()
        
        fitresult = []
        quality = []
        slopes = []
        intersects = []
        processed_T = []  # 실제로 처리된 데이터셋 인덱스 저장
        fit_masks = []  # 각 데이터셋의 피팅 범위 마스크 저장
        baseline_masks = []  # 각 데이터셋의 baseline 계산 범위 마스크 저장
        
        # Process each dataset
        for i in range(1, data_size[1]):
            if (i - 1) not in T:
                continue
                
            print(f'Dataset {i} loaded successfully')
            
            # Step 0: Baseline and fitting range must be selected by the user
            user_fit_mask = None  # Initialize user-selected fit mask
            if self.fitmode == 0:
                # 웹 인터페이스를 위해 클릭 좌표를 직접 받을 수 있도록 수정
                if hasattr(self, '_web_fit_mask'):
                    user_fit_mask = self._web_fit_mask
                    print(f'   📊 Baseline mode: No baseline (fitmode=0) - 웹에서 선택된 범위 사용')
                else:
                    print(f'   📊 Baseline mode: No baseline (fitmode=0)')
                    print(f'   🖱️ 피팅 범위를 그래프에서 선택하세요 (두 점)...')
                    result = self.select_baseline_mask_interactive(
                        xdata,
                        raw[:, i],
                        title=f"Fitting Range Selection - Dataset {i} (No Baseline)",
                        fitmode=0
                    )
                    if result is None:
                        raise ValueError("피팅 범위 선택이 취소되었거나 구간이 너무 짧습니다.")
                    _, user_fit_mask = result  # For fitmode=0, baseline_mask is None
                baseline = np.zeros(len(xdata))
                baseline_mask = np.zeros(len(xdata), dtype=bool)
            else:
                # 웹 인터페이스를 위해 클릭 좌표를 직접 받을 수 있도록 수정
                if hasattr(self, '_web_baseline_mask') and hasattr(self, '_web_fit_mask'):
                    # 웹에서 전달된 마스크 사용
                    user_baseline_mask = self._web_baseline_mask
                    user_fit_mask = self._web_fit_mask
                    baseline, baseline_mask = self.fit_baseline(xdata, raw[:, i], baseline_mask=user_baseline_mask)
                elif not baseline_select:
                    raise ValueError("baseline_select=False 이고 fitmode!=0 입니다. 자동 baseline은 제거되었으므로 baseline_select=True로 실행하세요.")
                else:
                    baseline_mode_name = {1: 'Linear', 2: 'Rayleigh scattering (E^4)'}.get(self.fitmode, f'Mode {self.fitmode}')
                    print(f'   🖱️ Step 0 baseline 구간과 피팅 범위를 그래프에서 선택하세요 ({baseline_mode_name})...')
                    result = self.select_baseline_mask_interactive(
                        xdata,
                        raw[:, i],
                        title=f"Step 0 Baseline & Fitting Range Selection - Dataset {i} ({baseline_mode_name})",
                        fitmode=self.fitmode
                    )
                    if result is None:
                        raise ValueError("Baseline 구간 선택이 취소되었거나 구간이 너무 짧습니다. (자동 baseline은 제거됨)")
                    user_baseline_mask, user_fit_mask = result
                    baseline, baseline_mask = self.fit_baseline(xdata, raw[:, i], baseline_mask=user_baseline_mask)
            
            # Step 1: Find bandgap from cleaned data
            # 사용자가 제공한 initial_Eg를 우선 사용 (데이터 범위 내에 있으면)
            user_provided_Eg = self.start_point[0]  # 사용자가 설정한 initial Eg
            
            if self.fitmode == 0:
                print(f'   🔍 Finding bandgap from raw data...')
                cleaned_data = raw[:, i]  # No baseline subtraction
            else:
                print(f'   🔍 Finding bandgap from cleaned data (absorption significantly above baseline)...')
                cleaned_data = raw[:, i] - baseline
            
            # 사용자가 제공한 Eg가 데이터 범위 내에 있으면 우선 사용
            if user_provided_Eg > 0 and np.min(xdata) <= user_provided_Eg <= np.max(xdata):
                initial_Eg = user_provided_Eg
                print(f'   📍 Using user-provided initial Bandgap: {initial_Eg:.3f} eV')
            else:
                # 데이터에서 계산: absorption이 baseline보다 유의하게 커지는 지점 찾기
                # Threshold: max(0.1, 5% of max cleaned_data) to avoid noise
                if len(cleaned_data) > 0:
                    max_cleaned = np.max(cleaned_data)
                    threshold = max(0.1, 0.05 * max_cleaned)  # At least 0.1 or 5% of max
                else:
                    threshold = 0.1
                
                # 에너지가 낮은 쪽(파장이 긴 쪽)에서 검색하여 bandgap 찾기
                # 데이터가 에너지 내림차순(파장 오름차순)으로 정렬되어 있을 가능성이 높음
                if xdata[0] > xdata[-1]:
                    # Descending: high energy first, search from low energy (end) to high energy (start)
                    # 에너지가 낮은 쪽에서 시작하여 높은 쪽으로 검색
                    found_idx = None
                    for idx in range(len(cleaned_data) - 1, -1, -1):
                        if cleaned_data[idx] > threshold:
                            found_idx = idx
                            break
                    
                    if found_idx is not None:
                        initial_Eg = xdata[found_idx]
                    else:
                        # If no point exceeds threshold, use median energy
                        initial_Eg = np.median(xdata)
                else:
                    # Ascending: low energy first, search from low to high
                    found_idx = None
                    for idx in range(len(cleaned_data)):
                        if cleaned_data[idx] > threshold:
                            found_idx = idx
                            break
                    
                    if found_idx is not None:
                        initial_Eg = xdata[found_idx]
                    else:
                        # If no point exceeds threshold, use median energy
                        initial_Eg = np.median(xdata)
                
                if self.fitmode == 0:
                    print(f'   📍 Initial Bandgap (calculated from raw data): {initial_Eg:.3f} eV')
                else:
                    print(f'   📍 Initial Bandgap (calculated from cleaned data): {initial_Eg:.3f} eV')
            
            # Update start_point with initial_Eg and set dynamic bounds (Eg ± 0.4 eV)
            # 사용자가 설정한 initial values를 사용하되, Eg는 위에서 결정된 값 사용
            dynamic_start_point = self.start_point.copy()
            dynamic_start_point[0] = initial_Eg  # Eg는 결정된 값 사용
            # Eb, Gamma, ucvsq, mhcnp, q는 사용자가 설정한 initial values 사용 (self.start_point에 이미 설정됨)
            
            # Set dynamic bounds: Eg ± 0.4 eV (always use this range, ignoring absolute bounds)
            dynamic_lb = self.lb.copy()
            dynamic_lb[0] = initial_Eg - 0.4  # Eg lower bound: Eg - 0.4 eV
            dynamic_rb = self.rb.copy()
            dynamic_rb[0] = initial_Eg + 0.4  # Eg upper bound: Eg + 0.4 eV
            
            # Ensure bounds are valid (lower < upper)
            if dynamic_lb[0] >= dynamic_rb[0]:
                # If bounds are invalid, use a wider range
                dynamic_lb[0] = initial_Eg - 0.5
                dynamic_rb[0] = initial_Eg + 0.5
            
            print(f'   📊 Dynamic Eg bounds: {dynamic_lb[0]:.3f} - {dynamic_rb[0]:.3f} eV (±0.4 eV from initial)')
            print(f'   📊 Using bounds - lb: {dynamic_lb}, rb: {dynamic_rb}')
            
            # Step 2: Remove initial baseline and do preliminary fit
            initial_cleandata = raw[:, i] - baseline
            # Use only reasonable energy range for preliminary fit (avoid extreme values)
            prelim_mask = (xdata >= np.percentile(xdata, 10)) & (xdata <= np.percentile(xdata, 90))
            print(f'   🔍 Preliminary fit to estimate Bandgap and Exciton binding energy...')
            dynamic_bounds = Bounds(dynamic_lb, dynamic_rb)
            prelim_estimates, _, _, _, _ = self.fit_data(xdata[prelim_mask], initial_cleandata[prelim_mask], 
                                                         start_point=dynamic_start_point, bounds=dynamic_bounds)
            approx_Eg = prelim_estimates[0]
            approx_Eb = prelim_estimates[1]
            exciton_threshold = approx_Eg - approx_Eb
            print(f'   📍 Estimated Bandgap: {approx_Eg:.3f} eV, Exciton binding: {approx_Eb*1000:.1f} meV')
            print(f'   📍 Exciton threshold (Eg - Eb): {exciton_threshold:.3f} eV')
            
            # Store baseline for saving (user-selected baseline)
            fittedbaseline[:, i] = baseline
            
            # Step 3: Remove baseline (user-selected)
            cleandata[:, i] = raw[:, i] - baseline
            ydata = cleandata[:, i]
            
            # Step 4: Create mask for final fitting range
            # Use user-selected fit_mask if available, otherwise use min_energy/max_energy
            if user_fit_mask is not None:
                fit_mask = user_fit_mask.copy()
            else:
                fit_mask = np.ones(len(xdata), dtype=bool)
                if min_energy is not None:
                    fit_mask &= (xdata >= min_energy)
                if max_energy is not None:
                    fit_mask &= (xdata <= max_energy)
            
            # Check if we have enough points
            if np.sum(fit_mask) < 10:
                print(f"⚠️ Warning: Fitting range contains too few points ({np.sum(fit_mask)}). Using full range.")
                fit_mask = np.ones(len(xdata), dtype=bool)
                
            if min_energy is not None or max_energy is not None:
                print(f'   Fitting range: {np.min(xdata[fit_mask]):.3f} - {np.max(xdata[fit_mask]):.3f} eV ({np.sum(fit_mask)} points)')

            # Step 5: Final fit using cleaned data (baseline removed) and specified range
            estimates, sse, _, _, _ = self.fit_data(xdata[fit_mask], ydata[fit_mask], 
                                                     start_point=prelim_estimates, bounds=dynamic_bounds)
            
            # --- Auto Range Refinement: Use Eg ± 0.5 eV for final fitting (unless disabled) ---
            # This ensures focus on bandgap region and reduces high-energy overestimation
            if auto_range is not False:  # Default (None) or True: enable bandgap-focused fitting
                approx_Eg = estimates[0]
                
                # Define range: Eg - 0.5 eV ~ Eg + 0.5 eV
                # This focuses on the critical bandgap region while including exciton features below Eg
                auto_min = approx_Eg - 0.5
                auto_max = approx_Eg + 0.5
                
                # Create new mask
                auto_mask = (xdata >= auto_min) & (xdata <= auto_max)
                
                # If user explicitly provided limits, respect the tighter constraint
                if min_energy is not None:
                    auto_mask &= (xdata >= min_energy)
                if max_energy is not None:
                    auto_mask &= (xdata <= max_energy)
                
                # Check if we have enough points for refinement
                if np.sum(auto_mask) > 10:
                    print(f"   🎯 Focusing on bandgap region: {np.min(xdata[auto_mask]):.3f} - {np.max(xdata[auto_mask]):.3f} eV (Eg ≈ {approx_Eg:.3f} eV, ±0.5 eV)")
                    
                    # Final fit with bandgap-focused range
                    # Use previous estimates as starting point
                    estimates, sse, _, _, _ = self.fit_data(xdata[auto_mask], ydata[auto_mask], 
                                                             start_point=estimates, bounds=dynamic_bounds)
                    
                    # Update fit_mask for R^2 calculation to reflect the actual range used
                    fit_mask = auto_mask
                else:
                    print(f"   ⚠️ Bandgap-focused range resulted in too few points ({np.sum(auto_mask)}). Using original range.")
            # -----------------------------

            self.start_point = estimates.copy()  # Use previous result as new start point
            
            # Generate curves for the FULL range using the estimated parameters
            _, FittedCurve, exciton, band = fsum2d(estimates, xdata, ydata)
            
            fittedcurves[:, i] = FittedCurve
            fittedexciton[:, i] = exciton
            fittedband[:, i] = band
            fitresult.append(estimates)
            processed_T.append(i)  # 실제로 처리된 데이터셋 인덱스 저장 (1-indexed)
            
            # Calculate R^2 based on the FITTING RANGE
            ydata_fit = ydata[fit_mask]
            ss_tot = np.sum((ydata_fit - np.mean(ydata_fit))**2)
            r_squared = 1 - sse / ss_tot if ss_tot > 0 else 0
            quality.append(r_squared)
            
            # Calculate Urbach energy
            slope, intersect, fitted_urbach = self.calculate_urbach_energy(
                xdata, ydata, estimates[1], estimates[0]
            )
            slopes.append(slope)
            intersects.append(intersect)
            fittedurbach[:, i] = fitted_urbach
            
            # Store fit mask and baseline mask for this dataset
            fit_masks.append(fit_mask.copy())
            baseline_masks.append(baseline_mask.copy())
            
            # Print results
            print(f'Iteration number {i}')
            print(f'Results: Eg={estimates[0]:.3f} (eV), Eb={estimates[1]*1000:.3f} (meV), '
                  f'gamma={estimates[2]:.3f} (eV), mu_cp={estimates[3]:.3f}, '
                  f'c_np={estimates[4]:.3f}, q={estimates[5]:.3f}')
            print(f'Effective dimension Deff={3 - 2*estimates[5]:.3f}')
            print(f'R^2={r_squared:.4f}')
        
        # Prepare results dictionary
        results = {
            'name': name,
            'xdata': xdata,  # eV 단위로 변환된 데이터
            'xdata_original': xdata_original,  # 원본 데이터 (nm 단위)
            'raw': raw,  # 원본 raw data 추가
            'fittedcurves': fittedcurves,
            'fittedexciton': fittedexciton,
            'fittedband': fittedband,
            'fittedurbach': fittedurbach,
            'fittedbaseline': fittedbaseline,  # Baseline 추가
            'cleandata': cleandata,
            'fitresult': np.array(fitresult),
            'quality': np.array(quality),
            'slopes': np.array(slopes),
            'intersects': np.array(intersects),
            'T': processed_T,  # 실제로 처리된 데이터셋만 저장
            'fit_masks': fit_masks,  # 각 데이터셋의 피팅 범위 마스크
            'baseline_masks': baseline_masks  # 각 데이터셋의 baseline 계산 범위 마스크
        }
        
        return results
    
    def save_results(self, results, output_dir='.'):
        """
        Save results to CSV file
        
        Parameters:
        -----------
        results : dict
            Results dictionary from process_file
        output_dir : str
            Output directory
        """
        import csv
        
        name = results['name']
        # 파일명 앞에 "0_" 추가
        name = f'0_{name}'
        
        # 빈 배열 체크
        if len(results['fitresult']) == 0:
            print("⚠️  경고: 처리된 데이터셋이 없습니다. 결과 파일을 저장하지 않습니다.")
            return
        
        xdata = results['xdata']
        xdata_original = results.get('xdata_original', xdata)  # nm 단위 원본 데이터
        
        # CSV 파일 경로
        csv_path = os.path.join(output_dir, f'{name}_Results.csv')
        
        # CSV 파일 작성
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # 모든 데이터셋에 대해 반복
            for dataset_num, dataset_idx in enumerate(results['T']):
                # 데이터셋 헤더
                if dataset_num > 0:
                    writer.writerow([])  # 데이터셋 간 구분을 위한 빈 줄
                writer.writerow([f'Dataset {dataset_num + 1}'])
                writer.writerow([])
                
                fit_params = results['fitresult'][dataset_num]
                
                # 첫 번째 행: 데이터 헤더 + Fitting Parameters (H열부터)
                # 첫 번째 열은 항상 Wavelength (nm)
                energy_header = 'Wavelength (nm)'
                header_row = [
                    energy_header, 
                    'Raw Data', 
                    'Baseline',  # Baseline 추가
                    'Fitted Exciton', 
                    'Fitted Band', 
                    'Fitted Result (Band+Exciton)',
                    '',  # G열 (빈 열)
                    'Eg (eV)', 
                    'Eb (meV)', 
                    'Gamma (eV)', 
                    'ucvsq', 
                    'mhcnp', 
                    'q', 
                    'Deff', 
                    'R²',
                    'Urbach Slope',
                    'Urbach Intercept'
                ]
                writer.writerow(header_row)
                
                # 두 번째 행: 파라미터 설명 (H열부터)
                description_row = [
                    '',  # A열
                    '',  # B열
                    '',  # C열
                    '',  # D열
                    '',  # E열
                    '',  # F열
                    '',  # G열
                    'Band gap energy',  # H열: Eg 설명
                    'Exciton binding energy',  # I열: Eb 설명
                    'Linewidth (broadening)',  # J열: Gamma 설명
                    'Transition dipole moment squared',  # K열: ucvsq 설명
                    'Mass parameter',  # L열: mhcnp 설명
                    'Fractional dimension parameter (0=bulk, 0.5-0.6=quasi 2D, 1.5=strong QD)',  # M열: q 설명
                    'Effective dimension (Deff = 3 - 2*q)',  # N열: Deff 설명
                    'Coefficient of determination',  # O열: R² 설명
                ]
                # Urbach 정보 설명 추가
                description_row.append('Urbach tail slope')  # P열: Urbach Slope 설명
                description_row.append('Urbach tail intercept')  # Q열: Urbach Intercept 설명
                writer.writerow(description_row)
                
                # 세 번째 행: Fitting Parameter 값들 (H열부터)
                param_row = [
                    '',  # A열
                    '',  # B열
                    '',  # C열
                    '',  # D열
                    '',  # E열
                    '',  # F열
                    '',  # G열
                    f'{fit_params[0]:.6f}',  # H열: Eg
                    f'{fit_params[1]*1000:.6f}',  # I열: Eb (meV)
                    f'{fit_params[2]:.6f}',  # J열: Gamma
                    f'{fit_params[3]:.6f}',  # K열: ucvsq
                    f'{fit_params[4]:.6f}',  # L열: mhcnp
                    f'{fit_params[5]:.6f}',  # M열: q
                    f'{3 - 2*fit_params[5]:.6f}',  # N열: Deff
                    f'{results["quality"][dataset_num]:.6f}',  # O열: R²
                ]
                # Urbach 정보 추가
                if len(results['slopes']) > dataset_num:
                    param_row.append(f'{results["slopes"][dataset_num]:.6f}')  # P열: Urbach Slope
                    param_row.append(f'{results["intersects"][dataset_num]:.6f}')  # Q열: Urbach Intercept
                else:
                    param_row.append('')  # P열
                    param_row.append('')  # Q열
                writer.writerow(param_row)
                writer.writerow([])  # 파라미터와 데이터 사이 빈 줄
                
                # 데이터 작성
                raw_data = results['raw'][:, dataset_idx]
                baseline = results['fittedbaseline'][:, dataset_idx]
                exciton = results['fittedexciton'][:, dataset_idx]
                band = results['fittedband'][:, dataset_idx]
                fitted_curve = results['fittedcurves'][:, dataset_idx]  # baseline 제거된 상태의 fitting
                # Fitted Result = Exciton + Band + Baseline (baseline을 다시 더함)
                fitted_total = exciton + band + baseline
                
                # 첫 번째 열: 원본 nm 값
                xdata_output = xdata_original
                
                for i in range(len(xdata)):
                    writer.writerow([
                        f'{xdata_output[i]:.6f}',
                        f'{raw_data[i]:.6f}',
                        f'{baseline[i]:.6f}',  # Baseline 추가
                        f'{exciton[i]:.6f}',
                        f'{band[i]:.6f}',
                        f'{fitted_total[i]:.6f}'  # Exciton + Band + Baseline
                    ])
    
    def plot_results(self, results, save_path=None):
        """
        Plot fitting results
        
        Parameters:
        -----------
        results : dict
            Results dictionary from process_file
        save_path : str, optional
            Path to save figure (PDF format)
        """
        num_datasets = len(results['T'])
        if num_datasets == 0:
            print("⚠️  경고: 처리된 데이터셋이 없어 그래프를 생성할 수 없습니다.")
            return None
        
        n_cols = int(np.ceil(np.sqrt(num_datasets)))
        n_rows = int(np.ceil(num_datasets / n_cols))
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 10))
        if num_datasets == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        xdata = results['xdata']
        NS = self.NS
        
        for idx, j in enumerate(results['T']):
            i = j  # T는 이미 1-indexed로 저장됨
            ax = axes[idx]
            
            # Get fit mask and baseline mask for this dataset
            fit_mask = results['fit_masks'][idx] if idx < len(results['fit_masks']) else np.ones(len(xdata), dtype=bool)
            baseline_mask = results['baseline_masks'][idx] if idx < len(results['baseline_masks']) else np.zeros(len(xdata), dtype=bool)
            
            # Plot raw data
            ax.plot(xdata, results['raw'][:, i], 'o', color='black', markersize=3, alpha=0.7, label='Raw Data')
            
            # Plot baseline
            baseline = results['fittedbaseline'][:, i]
            ax.plot(xdata, baseline, '-', color='gray', linewidth=2, linestyle='--', label='Baseline')
            
            # Plot fitted exciton
            exciton = results['fittedexciton'][:, i]
            ax.plot(xdata, exciton, '-', color='blue', linewidth=2, label='Fitted Exciton')
            
            # Plot fitted continuum (band)
            band = results['fittedband'][:, i]
            ax.plot(xdata, band, '-', color='red', linewidth=2, label='Fitted Continuum')
            
            # Plot fitted result (Exciton + Band + Baseline) as solid line
            fitted_total = exciton + band + baseline
            ax.plot(xdata, fitted_total, '-', color='green', linewidth=2.5, label='Fitted Result (Total)')
            
            # Plot vertical lines showing fitting range boundaries (green dashed)
            if np.any(fit_mask):
                fit_range_min = np.min(xdata[fit_mask])
                fit_range_max = np.max(xdata[fit_mask])
                ax.axvline(x=fit_range_min, color='green', linestyle='--', linewidth=1.5, 
                          alpha=0.7, label=f'Fitting range: {fit_range_min:.3f} - {fit_range_max:.3f} eV')
                ax.axvline(x=fit_range_max, color='green', linestyle='--', linewidth=1.5, alpha=0.7)
            
            # Plot vertical lines showing baseline calculation range boundaries (orange dashed)
            if np.any(baseline_mask):
                baseline_range_min = np.min(xdata[baseline_mask])
                baseline_range_max = np.max(xdata[baseline_mask])
                ax.axvline(x=baseline_range_min, color='orange', linestyle='--', linewidth=1.5, 
                          alpha=0.7, label=f'Baseline range: {baseline_range_min:.3f} - {baseline_range_max:.3f} eV')
                ax.axvline(x=baseline_range_max, color='orange', linestyle='--', linewidth=1.5, alpha=0.7)
            
            # Set limits
            y_max = np.max(results['raw'][:, i]) * 1.1
            ax.set_ylim([-0.1, y_max])
            ax.set_xlabel('Energy (eV)')
            ax.set_ylabel('Absorption')
            
            # Title
            Eb = results['fitresult'][idx, 1]
            ax.set_title(f'Dataset: {idx+1}, Eb={Eb*1000:.3f} meV')
            ax.legend(fontsize=8, loc='best')
            ax.grid(True, alpha=0.3)
        
        # Hide unused subplots
        for idx in range(num_datasets, len(axes)):
            axes[idx].set_visible(False)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, format='pdf', dpi=300, bbox_inches='tight')
        else:
            plt.show()
        
        return fig
    
    def process_file_with_points(self, filename, baseline_points, fitmode, T=None, auto_range=None):
        """
        웹 인터페이스를 위한 메서드: 클릭 좌표를 직접 받아서 분석합니다.
        process_file과 동일하지만, 그래프 대신 클릭 좌표를 직접 사용합니다.
        """
        # fitmode 설정
        original_fitmode = self.fitmode
        self.fitmode = fitmode
        
        try:
            # 데이터 읽기하여 xdata 얻기
            from io import StringIO
            file_ext = os.path.splitext(filename)[1].lower()
            delimiter = ',' if file_ext == '.csv' else None
            
            encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr', 'latin-1']
            all_lines = None
            for encoding in encodings:
                try:
                    with open(filename, 'r', encoding=encoding) as f:
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
            
            xdata_original = raw[:, 0].copy()
            xdata = 1239.84193 / xdata_original
            
            # 클릭 좌표를 사용하여 baseline_mask와 fit_mask 생성
            if fitmode == 0:
                if len(baseline_points) != 2:
                    raise ValueError("fitmode=0일 때는 2개의 점이 필요합니다.")
                fit_min, fit_max = sorted(baseline_points)
                self._web_fit_mask = (xdata >= fit_min) & (xdata <= fit_max)
                self._web_baseline_mask = None
            else:
                if len(baseline_points) != 3:
                    raise ValueError("fitmode!=0일 때는 3개의 점이 필요합니다.")
                x1, x2, x3 = baseline_points
                baseline_min, baseline_max = sorted([x1, x2])
                fit_min, fit_max = sorted([x1, x3])
                self._web_baseline_mask = (xdata >= baseline_min) & (xdata <= baseline_max)
                self._web_fit_mask = (xdata >= fit_min) & (xdata <= fit_max)
            
            # process_file 호출 (웹 마스크 사용)
            results = self.process_file(
                filename,
                T=T,
                min_energy=fit_min,
                max_energy=fit_max,
                auto_range=auto_range,
                baseline_select=True  # 웹 마스크가 있으면 사용
            )
            
            # 웹 마스크 제거
            if hasattr(self, '_web_baseline_mask'):
                delattr(self, '_web_baseline_mask')
            if hasattr(self, '_web_fit_mask'):
                delattr(self, '_web_fit_mask')
        finally:
            self.fitmode = original_fitmode
        
        return results
