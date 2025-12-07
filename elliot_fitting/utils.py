"""
유틸리티 함수들
"""

from .fitter import ElliotFitter


def fit_absorption_spectrum(filename, **kwargs):
    """
    간단한 인터페이스로 absorption spectrum 피팅
    
    Parameters
    ----------
    filename : str
        데이터 파일 경로
    **kwargs
        ElliotFitter에 전달할 추가 파라미터
        
    Returns
    -------
    fitter : ElliotFitter
        피팅된 ElliotFitter 객체
    results : dict
        피팅 결과 딕셔너리
    """
    fitter = ElliotFitter(**kwargs)
    results = fitter.fit(filename)
    return fitter, results


