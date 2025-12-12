"""
F-sum rule 2D fitting function
Python implementation of fsum2D.m
"""
import numpy as np
from scipy.integrate import trapz


def fsum2d(params, xdata, ydata):
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
        anx = 2 * Eb / (i - q)**3 * (1 / np.cosh(cosh_arg))
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
        a2[i, :] = (1 / np.cosh(cosh_arg)) * ((1 + b) / denominator)
    
    # Integrate along E axis (axis=0)
    band_contribution = trapz(a2, E, axis=0)
    
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
