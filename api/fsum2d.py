"""
F-sum rule 2D fitting function
Python implementation of fsum2D.m
"""
import numpy as np
# Note: trapz was moved from scipy.integrate to numpy in newer scipy versions
# Use np.trapz instead


def _inv_cosh_clipped(z):
    """
    Numerically-stable 1/cosh(z) with clipping to avoid overflow.
    """
    return 1.0 / np.cosh(np.clip(z, -700, 700))


def fsum2d_slow(params, xdata, ydata):
    """
    F-sum rule 2D fitting function
    
    Parameters:
    -----------
    params : array-like
        [Eg, Eb, Gamma, ucvsq, mhcnp, q]
        - Eg: Band gap energy
        - Eb: Exciton binding energy
        - Gamma: Linewidth
        - ucvsq: Transition dipole moment squared
        - mhcnp: Mass parameter
        - q: Fractional dimension parameter (0: bulk, 0.5-0.6: quasi 2D, 1.5: strong QD)
    xdata : array-like
        Energy data points
    ydata : array-like
        Absorption data points
        
    Returns:
    --------
    sse : float
        Sum of squared errors
    FittedCurve : array
        Fitted curve (exciton + band)
    exciton : array
        Exciton contribution
    band : array
        Band contribution
    """
    Eg = params[0]
    Eb = params[1]
    gamma = params[2]
    ucvsq = params[3]
    mhcnp = params[4]
    q = params[5]
    
    xdata = np.array(xdata)
    ydata = np.array(ydata)
    
    # Avoid division by zero for gamma
    gamma_safe = max(abs(gamma), 1e-10)
    
    # Exciton contribution
    a1 = np.zeros(len(xdata))
    for i in range(1, 51):
        # Avoid division by zero
        if abs(i - q) < 1e-10:
            continue
        Enx = Eg - (Eb / (i - q)**2)
        # Avoid overflow in cosh
        cosh_arg = (xdata - Enx) / gamma_safe
        # Clip cosh argument to prevent overflow
        cosh_arg = np.clip(cosh_arg, -700, 700)  # cosh(700) is near float64 max
        anx = 2 * Eb / (i - q)**3 * _inv_cosh_clipped(cosh_arg)
        a1 = a1 + anx
    
    # Band contribution
    E = np.linspace(Eg, 2 * Eg, 10 * len(xdata))
    a2 = np.zeros((len(E), len(xdata)))
    
    for i in range(len(E)):
        energy_diff = E[i] - Eg
        # Avoid division by zero or negative values
        if energy_diff <= 0:
            a2[i, :] = np.zeros(len(xdata))
            continue
            
        b = 10 * mhcnp * energy_diff + 126 * mhcnp**2 * energy_diff**2
        sqrt_arg = Eb / energy_diff
        if sqrt_arg <= 0:
            denominator = 1.0
        else:
            denominator = 1 - np.exp(-2 * np.pi * np.sqrt(sqrt_arg))
            # Avoid division by zero
            if abs(denominator) < 1e-10:
                denominator = 1e-10
        
        # Avoid overflow in cosh
        cosh_arg = (xdata - E[i]) / gamma_safe
        # Clip cosh argument to prevent overflow
        cosh_arg = np.clip(cosh_arg, -700, 700)  # cosh(700) is near float64 max
        a2[i, :] = _inv_cosh_clipped(cosh_arg) * ((1 + b) / denominator)
    
    # Integrate along E axis (axis=0)
    band_contribution = np.trapz(a2, E, axis=0)
    
    FittedCurve = ucvsq * np.sqrt(Eb) * (band_contribution + a1)
    exciton = ucvsq * np.sqrt(Eb) * a1
    band = ucvsq * np.sqrt(Eb) * band_contribution
    
    # Calculate SSE
    ErrorVector = FittedCurve - ydata
    sse = np.sum(ErrorVector**2)
    
    # Penalty for negative mhcnp
    if mhcnp <= 0:
        sse = 10 * sse
    
    return sse, FittedCurve, exciton, band


def fsum2d(params, xdata, ydata):
    """
    Vectorized / chunked version of fsum2d for speed.

    Notes:
    - Keeps the same signature/outputs as the original MATLAB-like implementation.
    - Uses chunked trapezoidal integration to avoid allocating a full (len(E) x len(xdata)) matrix.
    """
    Eg, Eb, gamma, ucvsq, mhcnp, q = params

    xdata = np.asarray(xdata, dtype=float)
    ydata = np.asarray(ydata, dtype=float)

    # Avoid division by zero for gamma and sqrt(Eb) for Eb<=0
    gamma_safe = max(abs(float(gamma)), 1e-10)
    Eb_safe = max(float(Eb), 0.0)
    sqrt_Eb = np.sqrt(Eb_safe)

    # ----------------------------
    # Exciton contribution (sum n=1..50)
    # ----------------------------
    n = np.arange(1.0, 51.0)
    den = n - float(q)
    valid = np.abs(den) > 1e-10
    if np.any(valid) and Eb_safe > 0:
        den = den[valid]  # (K,)
        Enx = float(Eg) - (Eb_safe / (den**2))  # (K,)
        pref = (2.0 * Eb_safe) / (den**3)       # (K,)
        cosh_arg = (xdata[None, :] - Enx[:, None]) / gamma_safe  # (K, N)
        a1 = np.sum(pref[:, None] * _inv_cosh_clipped(cosh_arg), axis=0)  # (N,)
    else:
        a1 = np.zeros_like(xdata)

    # ----------------------------
    # Band contribution (integral over E)
    # ----------------------------
    nE = max(2, 10 * len(xdata))
    E_grid = np.linspace(float(Eg), 2.0 * float(Eg), nE)  # (nE,)

    # Trapezoidal integration along E, chunked to reduce peak memory
    band_contribution = np.zeros_like(xdata)
    prev_E = None
    prev_f = None

    # Chunk size trades memory vs speed. 512 keeps allocations moderate.
    chunk = 512
    for start in range(0, nE, chunk):
        end = min(nE, start + chunk)
        E = E_grid[start:end]  # (m,)

        # Match original behavior: if (E - Eg) <= 0, integrand is 0
        dE_raw = E - float(Eg)
        pos = dE_raw > 0
        # For numerical stability in denominators, use a small floor ONLY for positive region
        dE = np.where(pos, np.maximum(dE_raw, 1e-12), 1.0)  # (m,)

        b = 10.0 * float(mhcnp) * dE + 126.0 * (float(mhcnp) ** 2) * (dE ** 2)  # (m,)

        # denominator = 1 - exp(-2*pi*sqrt(Eb/dE))
        if Eb_safe > 0:
            sqrt_arg = Eb_safe / dE
            denom = 1.0 - np.exp(-2.0 * np.pi * np.sqrt(sqrt_arg))
        else:
            denom = np.ones_like(dE)

        denom = np.where(np.abs(denom) < 1e-10, 1e-10, denom)  # (m,)
        weight = (1.0 + b) / denom  # (m,)
        # Zero-out non-positive region to match the slow implementation
        weight = np.where(pos, weight, 0.0)

        # f(E, x) = (1/cosh((x - E)/gamma)) * weight(E)
        cosh_arg = (xdata[None, :] - E[:, None]) / gamma_safe  # (m, N)
        f = _inv_cosh_clipped(cosh_arg) * weight[:, None]        # (m, N)

        # Boundary trapezoid between previous chunk and this chunk's first point
        if prev_E is not None:
            d = float(E[0] - prev_E)
            if d != 0.0:
                band_contribution += 0.5 * (prev_f + f[0]) * d

        # Internal trapezoids within the chunk
        if len(E) >= 2:
            d = np.diff(E)[:, None]  # (m-1, 1)
            band_contribution += np.sum(0.5 * (f[:-1] + f[1:]) * d, axis=0)

        prev_E = float(E[-1])
        prev_f = f[-1]

    FittedCurve = float(ucvsq) * sqrt_Eb * (band_contribution + a1)
    exciton = float(ucvsq) * sqrt_Eb * a1
    band = float(ucvsq) * sqrt_Eb * band_contribution

    # SSE
    err = FittedCurve - ydata
    sse = float(np.sum(err * err))

    # Penalty for negative mhcnp (kept for compatibility)
    if float(mhcnp) <= 0:
        sse = 10.0 * sse

    return sse, FittedCurve, exciton, band
