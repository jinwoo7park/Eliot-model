import React, { useState } from 'react'
import axios from 'axios'
import Plot from 'react-plotly.js'
import './App.css'

function App() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [previewData, setPreviewData] = useState(null)
  const [selectedPoints, setSelectedPoints] = useState([])
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [fitmode, setFitmode] = useState(2)
  const [logoError, setLogoError] = useState(false)

  // Initial values 기본값
  const defaultInitialValues = {
    Eg: 2.62,
    Eb: 0.050,
    Gamma: 0.100,
    ucvsq: 37,
    mhcnp: 0.060,
    q: 0
  }

  // 상한/하한 기본값
  const defaultBounds = {
    Eg: { lower: null, upper: null }, // 동적으로 계산됨 (initial_Eg ± 0.4 eV)
    Eb: { lower: 0.01, upper: 0.2 },
    Gamma: { lower: 0.0, upper: 0.2 },
    ucvsq: { lower: 0.010, upper: 1000.0 },
    mhcnp: { lower: 0.000, upper: 0.999 },
    q: { lower: 0.0, upper: 1.5 }
  }

  const [initialValues, setInitialValues] = useState({ ...defaultInitialValues })
  const [bounds, setBounds] = useState({ ...defaultBounds })
  const [showBounds, setShowBounds] = useState(false)

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
    setError(null)
    setResults(null)
    setPreviewData(null)
    setSelectedPoints([])
  }

  const handlePreview = async () => {
    if (!file) {
      setError('파일을 선택해주세요.')
      return
    }

    setLoading(true)
    setError(null)
    setPreviewData(null)
    setSelectedPoints([])

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(
        '/api/preview',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )

      setPreviewData(response.data)
    } catch (err) {
      let errorMessage = '파일 업로드 중 오류가 발생했습니다.'

      if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
        errorMessage = '백엔드 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인하세요.\n\n터미널에서 다음 명령어로 백엔드 서버를 실행하세요:\npython3 api.py'
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err.message) {
        errorMessage = err.message
      }

      setError(errorMessage)
      console.error('상세 오류:', err)
    } finally {
      setLoading(false)
    }
  }

  const handlePlotClick = (event) => {
    if (!previewData || loading) return

    if (event.points && event.points.length > 0) {
      const point = event.points[0]
      const energy = point.x

      console.log('Clicked point:', { x: point.x, y: point.y })

      const requiredPoints = fitmode === 0 ? 2 : 3

      if (selectedPoints.length < requiredPoints) {
        setSelectedPoints([...selectedPoints, energy])
      }
    }
  }

  const handleAnalyze = async () => {
    if (!previewData) {
      setError('먼저 파일을 업로드하고 미리보기를 해주세요.')
      return
    }

    const requiredPoints = fitmode === 0 ? 2 : 3
    if (selectedPoints.length !== requiredPoints) {
      setError(`정확히 ${requiredPoints}개의 점을 선택해주세요.`)
      return
    }

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      // bounds에서 유효한 값들만 전송
      const boundsToSend = {}
      Object.keys(bounds).forEach((param) => {
        const paramBounds = bounds[param]
        const lower = paramBounds.lower
        const upper = paramBounds.upper

        // null이 아니고, 빈 문자열이 아니고, 숫자인 경우만 포함
        const hasLower = lower !== null && lower !== '' && !isNaN(parseFloat(lower))
        const hasUpper = upper !== null && upper !== '' && !isNaN(parseFloat(upper))

        if (hasLower || hasUpper) {
          boundsToSend[param] = {}
          if (hasLower) {
            boundsToSend[param].lower = parseFloat(lower)
          }
          if (hasUpper) {
            boundsToSend[param].upper = parseFloat(upper)
          }
        }
      })

      console.log('Sending bounds:', boundsToSend)

      const response = await axios.post('/api/analyze', {
        filename: previewData.filename,
        fitmode: fitmode,
        baseline_points: selectedPoints,
        initial_values: initialValues,
        bounds: Object.keys(boundsToSend).length > 0 ? boundsToSend : null
      })

      setResults(response.data)
      console.log('Analysis results:', response.data)
      console.log('Boundary warnings:', response.data.boundary_warnings)
      console.log('Q warning:', response.data.q_warning)
    } catch (err) {
      let errorMessage = '분석 중 오류가 발생했습니다.'

      if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
        errorMessage = '백엔드 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인하세요.\n\n터미널에서 다음 명령어로 백엔드 서버를 실행하세요:\npython3 api.py'
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err.message) {
        errorMessage = err.message
      }

      setError(errorMessage)
      console.error('상세 오류:', err)
    } finally {
      setLoading(false)
    }
  }

  const resetInitialValues = () => {
    setInitialValues({ ...defaultInitialValues })
  }

  const resetBounds = () => {
    setBounds({ ...defaultBounds })
  }

  const handleBoundChange = (param, boundType, value) => {
    const numValue = parseFloat(value)
    if (!isNaN(numValue) || value === '' || value === '-') {
      setBounds({
        ...bounds,
        [param]: {
          ...bounds[param],
          [boundType]: value === '' || value === '-' ? value : numValue
        }
      })
    }
  }

  const handleInitialValueChange = (param, value) => {
    const numValue = parseFloat(value)
    if (!isNaN(numValue)) {
      setInitialValues({
        ...initialValues,
        [param]: numValue
      })
    } else if (value === '' || value === '-') {
      // 빈 값이나 마이너스 기호만 입력된 경우도 허용 (입력 중)
      setInitialValues({
        ...initialValues,
        [param]: value
      })
    }
  }

  const downloadFile = (filename) => {
    window.open(`/api/download/${filename}`, '_blank')
  }

  const resetSelection = () => {
    setSelectedPoints([])
  }

  // Plotly layout shapes 생성 (선택된 영역 표시)
  const getShapes = () => {
    if (!previewData || selectedPoints.length === 0) return []

    const shapes = []
    const yMin = Math.min(...previewData.ydata)
    const yMax = Math.max(...previewData.ydata)

    // 세로선 (선택된 포인트들)
    selectedPoints.forEach((point, idx) => {
      const color = fitmode === 0 ? 'green' : idx < 2 ? 'orange' : 'green'
      shapes.push({
        type: 'line',
        x0: point,
        y0: yMin,
        x1: point,
        y1: yMax,
        line: {
          color: color,
          width: 2,
          dash: 'dashdot'
        }
      })
    })

    // 영역 표시
    if (fitmode === 0) {
      // No baseline 모드: 점 2개가 선택되면 그 사이를 초록색(피팅 범위)으로 표시
      if (selectedPoints.length >= 2) {
        const x1 = selectedPoints[0]
        const x2 = selectedPoints[1]
        shapes.push({
          type: 'rect',
          x0: Math.min(x1, x2),
          y0: yMin,
          x1: Math.max(x1, x2),
          y1: yMax,
          fillcolor: 'rgba(0, 128, 0, 0.1)',
          line: { width: 0 }
        })
      }
    } else {
      // Baseline 모드
      // 1. Baseline 범위 (점 1-2): 노란색
      if (selectedPoints.length >= 2) {
        const x1 = selectedPoints[0]
        const x2 = selectedPoints[1]
        shapes.push({
          type: 'rect',
          x0: Math.min(x1, x2),
          y0: yMin,
          x1: Math.max(x1, x2),
          y1: yMax,
          fillcolor: 'rgba(255, 165, 0, 0.1)',
          line: { width: 0 }
        })
      }

      // 2. Fitting 범위 (점 1-3): 초록색
      if (selectedPoints.length >= 3) {
        const x1 = selectedPoints[0]
        const x3 = selectedPoints[2]
        shapes.push({
          type: 'rect',
          x0: Math.min(x1, x3),
          y0: yMin,
          x1: Math.max(x1, x3),
          y1: yMax,
          fillcolor: 'rgba(0, 128, 0, 0.1)',
          line: { width: 0 }
        })
      }
    }

    return shapes
  }

  return (
    <div className="app">
      <div className="container">
        <div className="title-section">
          <div className="title-content">
            <h1>Elliott Model: F-sum Rule Fitting</h1>
            <p className="subtitle">Exciton binding energy calculation from UV-abs</p>
          </div>
          <img
            src="/PNEL_logo.png"
            alt="PNEL Logo"
            className="title-logo"
            onError={() => {
              setLogoError(true)
            }}
            style={{ display: logoError ? 'none' : 'block' }}
          />
        </div>

        <div className="form">
          <div className="form-group">
            <label htmlFor="file">데이터 파일 선택</label>
            <input
              type="file"
              id="file"
              accept=".txt,.dat,.csv"
              onChange={handleFileChange}
              disabled={loading}
            />
            {file && <p className="file-name">선택된 파일: {file.name}</p>}
          </div>

          <div className="form-group">
            <label htmlFor="fitmode">Baseline Fit Mode</label>
            <select
              id="fitmode"
              value={fitmode}
              onChange={(e) => {
                setFitmode(parseInt(e.target.value))
                setSelectedPoints([])
              }}
              disabled={loading}
            >
              <option value="0">0 - No baseline</option>
              <option value="1">1 - Linear baseline</option>
              <option value="2">2 - Rayleigh scattering (E^4)</option>
            </select>
          </div>

          <div className="form-group">
            <div className="initial-values-header">
              <label htmlFor="initial-values">Initial Values (피팅 초기값)</label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setShowBounds(!showBounds)}
                  className="btn btn-secondary"
                  style={{ padding: '6px 12px', fontSize: '0.85em' }}
                  disabled={loading}
                >
                  {showBounds ? '상한/하한 숨기기' : '상한/하한 보기'}
                </button>
                <button
                  type="button"
                  onClick={resetInitialValues}
                  className="btn btn-secondary"
                  style={{ padding: '6px 12px', fontSize: '0.85em' }}
                  disabled={loading}
                >
                  기본값으로 되돌리기
                </button>
              </div>
            </div>
            <div className="initial-values-grid">
              <div className="initial-value-item">
                <label htmlFor="Eg">Eg (eV):</label>
                <input
                  type="number"
                  id="Eg"
                  step="0.001"
                  value={initialValues.Eg}
                  onChange={(e) => handleInitialValueChange('Eg', e.target.value)}
                  disabled={loading}
                />
              </div>
              <div className="initial-value-item">
                <label htmlFor="Eb">Eb (eV):</label>
                <input
                  type="number"
                  id="Eb"
                  step="0.001"
                  value={initialValues.Eb}
                  onChange={(e) => handleInitialValueChange('Eb', e.target.value)}
                  disabled={loading}
                />
              </div>
              <div className="initial-value-item">
                <label htmlFor="Gamma">Gamma (eV):</label>
                <input
                  type="number"
                  id="Gamma"
                  step="0.001"
                  value={initialValues.Gamma}
                  onChange={(e) => handleInitialValueChange('Gamma', e.target.value)}
                  disabled={loading}
                />
              </div>
              <div className="initial-value-item">
                <label htmlFor="ucvsq">ucvsq:</label>
                <input
                  type="number"
                  id="ucvsq"
                  step="0.1"
                  value={initialValues.ucvsq}
                  onChange={(e) => handleInitialValueChange('ucvsq', e.target.value)}
                  disabled={loading}
                />
              </div>
              <div className="initial-value-item">
                <label htmlFor="mhcnp">mhcnp:</label>
                <input
                  type="number"
                  id="mhcnp"
                  step="0.001"
                  value={initialValues.mhcnp}
                  onChange={(e) => handleInitialValueChange('mhcnp', e.target.value)}
                  disabled={loading}
                />
              </div>
              <div className="initial-value-item">
                <label htmlFor="q">q:</label>
                <input
                  type="number"
                  id="q"
                  step="0.001"
                  value={initialValues.q}
                  onChange={(e) => handleInitialValueChange('q', e.target.value)}
                  disabled={loading}
                />
              </div>
            </div>

            {showBounds && (
              <div className="bounds-section">
                <div className="bounds-header">
                  <h4>상한/하한 (Bounds)</h4>
                  <button
                    type="button"
                    onClick={resetBounds}
                    className="btn btn-secondary"
                    style={{ padding: '4px 8px', fontSize: '0.8em' }}
                    disabled={loading}
                  >
                    기본값으로 되돌리기
                  </button>
                </div>
                <div className="bounds-grid">
                  {Object.keys(bounds).map((param) => (
                    <div key={param} className="bounds-item">
                      <label className="bounds-param-label">{param}:</label>
                      <div className="bounds-inputs">
                        <div className="bound-input-group">
                          <label>하한:</label>
                          <input
                            type="number"
                            step="0.001"
                            value={bounds[param].lower ?? ''}
                            onChange={(e) => handleBoundChange(param, 'lower', e.target.value)}
                            disabled={loading || param === 'Eg'}
                            placeholder={param === 'Eg' ? '동적 계산' : ''}
                            title={param === 'Eg' ? 'Eg는 동적으로 계산됩니다 (initial_Eg ± 0.4 eV)' : ''}
                          />
                        </div>
                        <div className="bound-input-group">
                          <label>상한:</label>
                          <input
                            type="number"
                            step="0.001"
                            value={bounds[param].upper ?? ''}
                            onChange={(e) => handleBoundChange(param, 'upper', e.target.value)}
                            disabled={loading || param === 'Eg'}
                            placeholder={param === 'Eg' ? '동적 계산' : ''}
                            title={param === 'Eg' ? 'Eg는 동적으로 계산됩니다 (initial_Eg ± 0.4 eV)' : ''}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                {bounds.Eg.lower === null && (
                  <p className="bounds-note">
                    참고: Eg의 상한/하한은 동적으로 계산됩니다 (initial_Eg ± 0.4 eV).
                    다른 파라미터의 상한/하한은 수정 가능합니다.
                  </p>
                )}
              </div>
            )}
          </div>

          {error && <div className="error">{error}</div>}

          <div className="button-group">
            <button
              onClick={handlePreview}
              disabled={loading || !file}
              className="btn btn-primary"
            >
              {loading ? '처리 중...' : '파일 업로드 및 미리보기'}
            </button>
          </div>
        </div>

        {previewData && (
          <div className="preview-section">
            <h2>그래프에서 범위 선택</h2>
            <p className="instruction">
              {fitmode === 0
                ? '피팅 범위 시작점과 끝점을 클릭하세요 (2개 점)'
                : 'Baseline 시작점, Baseline 끝점, 피팅 범위 끝점을 순서대로 클릭하세요 (3개 점)'}
            </p>

            {selectedPoints.length > 0 && (
              <div className="selected-points">
                <p>선택된 점:</p>
                <ul>
                  {selectedPoints.map((point, idx) => (
                    <li key={idx}>
                      {fitmode === 0
                        ? idx === 0 ? '피팅 시작' : '피팅 끝'
                        : idx === 0 ? 'Baseline 시작' : idx === 1 ? 'Baseline 끝' : '피팅 끝'}
                      : {point.toFixed(3)} eV
                    </li>
                  ))}
                </ul>
                <button onClick={resetSelection} className="btn btn-secondary">
                  선택 초기화
                </button>
              </div>
            )}

            <div className="plot-container">
              <Plot
                data={[
                  {
                    x: previewData.xdata,
                    y: previewData.ydata,
                    type: 'scatter',
                    mode: 'lines',
                    marker: { color: 'black' },
                    name: 'Data'
                  }
                ]}
                layout={{
                  width: 800,
                  height: 500,
                  title: 'Baseline 및 피팅 범위 선택',
                  xaxis: {
                    title: 'Energy (eV)',
                    showline: true,
                    showgrid: true,
                    zeroline: false,
                    linecolor: '#000',
                    linewidth: 2,
                    mirror: true
                  },
                  yaxis: {
                    title: 'Absorption',
                    showline: true,
                    showgrid: true,
                    zeroline: false,
                    linecolor: '#000',
                    linewidth: 2,
                    mirror: true
                  },
                  shapes: getShapes(),
                  hovermode: 'closest'
                }}
                config={{
                  displayModeBar: true,
                  scrollZoom: false,
                  displaylogo: false
                }}
                onClick={handlePlotClick}
              />
            </div>

            <button
              onClick={handleAnalyze}
              disabled={loading || selectedPoints.length !== (fitmode === 0 ? 2 : 3)}
              className="btn btn-primary"
            >
              {loading ? '분석 중...' : '분석 시작'}
            </button>
          </div>
        )}

        {results && (
          <div className="results">
            <h2>분석 결과</h2>

            <div className="parameters">
              <h3>Fitting 파라미터</h3>
              <div className="param-grid">
                <div className="param-item">
                  <span className="param-label">Eg (Band gap):</span>
                  <span className="param-value">{results.parameters?.Eg?.toFixed(4) ?? 'N/A'} eV</span>
                </div>
                <div className="param-item">
                  <span className="param-label">Eb (Exciton binding):</span>
                  <span className="param-value">{results.parameters?.Eb?.toFixed(4) ?? 'N/A'} eV</span>
                </div>
                <div className="param-item">
                  <span className="param-label">Gamma (Linewidth):</span>
                  <span className="param-value">{results.parameters?.Gamma?.toFixed(4) ?? 'N/A'} eV</span>
                </div>
                <div className="param-item">
                  <span className="param-label">ucvsq:</span>
                  <span className="param-value">{results.parameters?.ucvsq?.toFixed(6) ?? 'N/A'}</span>
                </div>
                <div className="param-item">
                  <span className="param-label">mhcnp:</span>
                  <span className="param-value">{results.parameters?.mhcnp?.toFixed(6) ?? 'N/A'}</span>
                </div>
                <div className="param-item">
                  <span className="param-label">q:</span>
                  <span className="param-value">{results.parameters?.q?.toFixed(4) ?? 'N/A'}</span>
                </div>
                {results.quality !== undefined && (
                  <div className="param-item">
                    <span className="param-label">R² (Quality):</span>
                    <span className="param-value">{results.quality.toFixed(6)}</span>
                  </div>
                )}
              </div>
            </div>

            {/* 경고 메시지 표시 - 다운로드 섹션 위에 */}
            {results.boundary_warnings && results.boundary_warnings.length > 0 && (
              <div className="warning boundary-warning">
                <strong>⚠️ 경고:</strong> 다음 파라미터들이 경계값에 도달했습니다: {results.boundary_warnings.join(', ')}.
                피팅 결과가 신뢰할 수 없을 수 있습니다. 초기값을 조정하거나 피팅 범위를 변경해보세요.
              </div>
            )}

            {results.q_warning && (
              <div className="warning q-warning">
                <strong>⚠️ 경고:</strong> {results.q_warning}
              </div>
            )}

            <div className="downloads">
              <h3>다운로드</h3>
              <div className="download-buttons">
                <button
                  onClick={() => downloadFile(results.results_file.split('/').pop())}
                  className="btn btn-download"
                >
                  결과 CSV 다운로드
                </button>
                <button
                  onClick={() => downloadFile(results.plot_file.split('/').pop())}
                  className="btn btn-download"
                >
                  그래프 PDF 다운로드
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
