"""
Main fitting script
Python implementation of main.m
"""
import numpy as np
from scipy.optimize import minimize
from scipy.optimize import Bounds
from scipy.optimize import NonlinearConstraint
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import os
from io import StringIO

from fsum2d import fsum2d


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
        # Note: Eg bounds will be set to Eg ± 0.2 eV dynamically
        self.start_point = np.array([2.62, 0.050, 0.043, 37, 0.060, 0])  # Eb=50meV, q=0 (bulk)
        self.lb = np.array([2.54, 0.01, 0.00, 0.010, 0.000, 0.0])      # Eb lower bound: 10meV, q lower bound: 0 (bulk)
        self.rb = np.array([2.68, 0.2, 0.20, 1000.0, 0.999, 1.5])       # q upper bound: 1.5 (strong QD)
        # Note: Eg bounds will be dynamically updated in process_file
        
    def fit_baseline(self, xdata, ydata, Eg=None, Eb=None):
        """
        Fit baseline using data below exciton absorption (Eg - Eb)
        
        Parameters:
        -----------
        xdata : array
            Energy data
        ydata : array
            Absorption data
        Eg : float, optional
            Bandgap energy
        Eb : float, optional
            Exciton binding energy. If provided, uses data below (Eg - Eb) for baseline.
            If None but Eg is provided, uses data below Eg (legacy mode)
            
        Returns:
        --------
        baseline : array
            Baseline values
        baseline_mask : array (bool)
            Mask indicating which data points were used for baseline fitting
        """
        if self.fitmode == 0:
            return np.zeros(len(xdata)), np.zeros(len(xdata), dtype=bool)
        
        # Determine which data points to use for baseline fitting
        if Eg is not None:
            if Eb is not None and Eb > 0:
                # Use data well below exciton peak for baseline fitting
                # Use Eg - 1.5*Eb to get approximately 50 points for baseline fitting
                # Adjusted from Eg - 2*Eb to include more points while still avoiding excitonic absorption
                safe_threshold = Eg - 1.5 * Eb
                
                # Check data sorting direction to correctly select low energy region
                if xdata[0] < xdata[-1]:
                    # Ascending: low energy first, xdata < threshold selects low energy region correctly
                    baseline_mask = xdata < safe_threshold
                else:
                    # Descending: high energy first, xdata < threshold selects low energy region (array end)
                    baseline_mask = xdata < safe_threshold
                
                # Use all eligible points below threshold (removed 50% percentile restriction)
                # This ensures we use more points for better baseline fitting
                if np.sum(baseline_mask) < 5:
                    # Fallback: if too few points, use lowest energy points only
                    # Check data sorting direction
                    baseline_mask = np.zeros(len(xdata), dtype=bool)
                    if xdata[0] < xdata[-1]:
                        # Ascending: use first points (lowest energy) - use more points (30% of data)
                        n_points = max(10, min(50, int(len(xdata) * 0.3)))
                        baseline_mask[:n_points] = True
                    else:
                        # Descending: use last points (lowest energy) - use more points (30% of data)
                        n_points = max(10, min(50, int(len(xdata) * 0.3)))
                        baseline_mask[-n_points:] = True
            else:
                # Legacy mode: use data below Bandgap (if Eb not provided)
                baseline_mask = xdata < Eg
                if np.sum(baseline_mask) < 5:
                    # Fallback: if too few points below Eg, use lowest energy points
                    baseline_mask = np.zeros(len(xdata), dtype=bool)
                    baseline_mask[:min(20, len(xdata))] = True
        else:
            # Legacy mode: use only the lowest energy points (most transparent region)
            # Use more points (30%) for better baseline fitting
            # Check if data is sorted ascending (low energy first) or descending (high energy first)
            if xdata[0] < xdata[-1]:
                # Ascending: low energy first, use first 30% of points
                n_points = max(10, min(50, int(len(xdata) * 0.3)))
                baseline_mask = np.zeros(len(xdata), dtype=bool)
                baseline_mask[:n_points] = True
            else:
                # Descending: high energy first, use last 30% of points (lowest energy)
                n_points = max(10, min(50, int(len(xdata) * 0.3)))
                baseline_mask = np.zeros(len(xdata), dtype=bool)
                baseline_mask[-n_points:] = True
        
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
            # Rayleigh scattering: y = a * E^4
            # Fit coefficient a using least squares: a = sum(y * E^4) / sum(E^8)
            E4_fit = x_fit ** 4
            E8_fit = x_fit ** 8
            
            # Avoid division by zero
            if np.sum(E8_fit) < 1e-10:
                return np.zeros(len(xdata)), baseline_mask
            
            # Calculate coefficient a
            a = np.sum(y_fit * E4_fit) / np.sum(E8_fit)
            
            # Generate baseline for full range: baseline = a * E^4
            baseline = a * (xdata ** 4)
            return baseline, baseline_mask
        else:
            raise ValueError(f"Fitmode {self.fitmode} not implemented")
    
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
    
    def process_file(self, filename, T=None, min_energy=None, max_energy=None, auto_range=None):
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
        xdata_original = raw[:, 0].copy()  # 원본 데이터 저장 (nm 또는 eV)
        
        # nm 단위인지 eV 단위인지 자동 감지
        # 일반적으로 nm는 100 이상, eV는 10 이하
        # 첫 번째 열의 평균값이 50보다 크면 nm로 간주
        is_nm = np.mean(xdata_original) > 50
        
        if is_nm:
            # nm를 eV로 변환: E(eV) = 1239.84193 / λ(nm)
            xdata = 1239.84193 / xdata_original
            print(f'입력 데이터가 nm 단위로 감지되었습니다. eV로 변환합니다.')
        else:
            # 이미 eV 단위
            xdata = xdata_original.copy()
            print(f'입력 데이터가 eV 단위로 감지되었습니다.')
        
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
            
            # Step 0: Estimate initial baseline using transparent region (lowest energy/highest wavelength)
            # Use the lowest energy points where absorption is minimal
            # This gives us a rough baseline estimate without needing Eg/Eb
            if self.fitmode == 0:
                print(f'   📊 Baseline mode: No baseline (fitmode=0)')
                initial_baseline = np.zeros(len(xdata))
                initial_baseline_mask = np.zeros(len(xdata), dtype=bool)
            else:
                baseline_mode_name = {1: 'Linear', 2: 'Rayleigh scattering (E^4)'}.get(self.fitmode, f'Mode {self.fitmode}')
                print(f'   🔍 Estimating initial baseline from transparent region ({baseline_mode_name})...')
                # Check data sorting direction
                if xdata[0] < xdata[-1]:
                    # Ascending: low energy first, use first 30% (lowest energies)
                    transparent_mask = np.zeros(len(xdata), dtype=bool)
                    transparent_mask[:int(len(xdata) * 0.3)] = True
                else:
                    # Descending: high energy first, use last 30% (lowest energies)
                    transparent_mask = np.zeros(len(xdata), dtype=bool)
                    transparent_mask[-int(len(xdata) * 0.3):] = True
                initial_baseline, initial_baseline_mask = self.fit_baseline(xdata, raw[:, i], Eg=None, Eb=None)
            
            # Step 1: Find bandgap from cleaned data (first point where (raw - baseline) > 0.01)
            # This sets the initial Eg and dynamic bounds (Eg ± 0.2 eV)
            if self.fitmode == 0:
                print(f'   🔍 Finding bandgap from raw data (first point where absorption > 0.01)...')
                cleaned_data = raw[:, i]  # No baseline subtraction
            else:
                print(f'   🔍 Finding bandgap from cleaned data (first point where (raw - baseline) > 0.01)...')
                cleaned_data = raw[:, i] - initial_baseline
            
            # Find first point where cleaned data exceeds 0.01
            # Check data sorting direction
            if xdata[0] < xdata[-1]:
                # Ascending: low energy first, search from low to high
                for idx in range(len(cleaned_data)):
                    if cleaned_data[idx] > 0.01:
                        initial_Eg = xdata[idx]
                        break
                else:
                    # If no point exceeds 0.01, use median energy
                    initial_Eg = np.median(xdata)
            else:
                # Descending: high energy first, search from high to low (reverse)
                for idx in range(len(cleaned_data) - 1, -1, -1):
                    if cleaned_data[idx] > 0.01:
                        initial_Eg = xdata[idx]
                        break
                else:
                    # If no point exceeds 0.01, use median energy
                    initial_Eg = np.median(xdata)
            
            if self.fitmode == 0:
                print(f'   📍 Initial Bandgap (from raw data): {initial_Eg:.3f} eV')
            else:
                print(f'   📍 Initial Bandgap (from cleaned data): {initial_Eg:.3f} eV')
            
            # Update start_point with initial_Eg and set dynamic bounds (Eg ± 0.2 eV)
            dynamic_start_point = self.start_point.copy()
            dynamic_start_point[0] = initial_Eg  # Eg
            dynamic_start_point[1] = 0.050  # Eb = 50 meV
            dynamic_start_point[5] = 0.0    # q = 0 (bulk)
            
            # Set dynamic bounds: Eg ± 0.2 eV (always use this range, ignoring absolute bounds)
            dynamic_lb = self.lb.copy()
            dynamic_lb[0] = initial_Eg - 0.2  # Eg lower bound: Eg - 0.2 eV
            dynamic_rb = self.rb.copy()
            dynamic_rb[0] = initial_Eg + 0.2  # Eg upper bound: Eg + 0.2 eV
            
            # Ensure bounds are valid (lower < upper)
            if dynamic_lb[0] >= dynamic_rb[0]:
                # If bounds are invalid, use a wider range
                dynamic_lb[0] = initial_Eg - 0.3
                dynamic_rb[0] = initial_Eg + 0.3
            
            print(f'   📊 Dynamic Eg bounds: {dynamic_lb[0]:.3f} - {dynamic_rb[0]:.3f} eV (±0.2 eV from initial)')
            
            # Step 2: Remove initial baseline and do preliminary fit
            initial_cleandata = raw[:, i] - initial_baseline
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
            
            # Step 3: Refine baseline using only truly transparent region
            if self.fitmode == 0:
                # No baseline mode: baseline is zero
                baseline = np.zeros(len(xdata))
                baseline_mask = np.zeros(len(xdata), dtype=bool)
                print(f'   📊 Baseline mode: No baseline (fitmode=0) - using raw data directly')
            else:
                # Use Eg - 1.5*Eb to get approximately 50 points for baseline fitting
                # Adjusted from Eg - 2*Eb to include more points while still avoiding excitonic absorption
                baseline, baseline_mask = self.fit_baseline(xdata, raw[:, i], Eg=approx_Eg, Eb=approx_Eb)
                baseline_points = np.sum(baseline_mask)
                baseline_range_min = np.min(xdata[baseline_mask]) if np.any(baseline_mask) else 0
                baseline_range_max = np.max(xdata[baseline_mask]) if np.any(baseline_mask) else 0
                safe_threshold = approx_Eg - 1.5 * approx_Eb
                baseline_mode_name = {1: 'Linear', 2: 'Rayleigh scattering (E^4)'}.get(self.fitmode, f'Mode {self.fitmode}')
                print(f'   📊 Baseline ({baseline_mode_name}) fitted using {baseline_points} points in transparent region (below {safe_threshold:.3f} eV, Eg - 1.5*Eb)')
                print(f'   📊 Baseline range: {baseline_range_min:.3f} - {baseline_range_max:.3f} eV')
            
            # Store baseline for saving
            fittedbaseline[:, i] = baseline
            
            # Step 4: Remove refined baseline
            cleandata[:, i] = raw[:, i] - baseline
            ydata = cleandata[:, i]
            
            # Step 5: Create mask for final fitting range
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

            # Step 6: Final fit using cleaned data (baseline removed) and specified range
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
            'xdata_original': xdata_original,  # 원본 데이터 (nm 또는 eV)
            'is_nm': is_nm,  # nm 단위였는지 여부
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
        is_nm = results.get('is_nm', False)
        xdata_original = results.get('xdata_original', xdata)
        
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
                # nm 단위였으면 첫 번째 열을 Wavelength (nm)로 표시
                energy_header = 'Wavelength (nm)' if is_nm else 'Photon Energy (eV)'
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
                fitted_total = results['fittedcurves'][:, dataset_idx]
                
                # 첫 번째 열: nm 단위였으면 원본 nm 값, 아니면 eV 값
                xdata_output = xdata_original if is_nm else xdata
                
                for i in range(len(xdata)):
                    writer.writerow([
                        f'{xdata_output[i]:.6f}',
                        f'{raw_data[i]:.6f}',
                        f'{baseline[i]:.6f}',  # Baseline 추가
                        f'{exciton[i]:.6f}',
                        f'{band[i]:.6f}',
                        f'{fitted_total[i]:.6f}'
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
            ax.plot(xdata, results['fittedbaseline'][:, i], '-', color='gray', linewidth=2, linestyle='--', label='Baseline')
            
            # Plot fitted exciton
            ax.plot(xdata, results['fittedexciton'][:, i], '-', color='blue', linewidth=2, label='Fitted Exciton')
            
            # Plot fitted continuum (band)
            ax.plot(xdata, results['fittedband'][:, i], '-', color='red', linewidth=2, label='Fitted Continuum')
            
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
