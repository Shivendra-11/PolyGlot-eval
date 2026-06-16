import { useState, useEffect, useRef } from 'react'
import { traceData } from './data.js'

const IO_BADGES = {
  db_write: { icon: '🗄️', label: 'DB Write', color: '#f59e0b' },
  db_read: { icon: '📖', label: 'DB Read', color: '#60a5fa' },
  http_call: { icon: '🌐', label: 'HTTP Call', color: '#3b82f6' },
  queue_publish: { icon: '📤', label: 'Queue Publish', color: '#10b981' },
  queue_consume: { icon: '📥', label: 'Queue Consume', color: '#34d399' },
  file_write: { icon: '📁', label: 'File Write', color: '#fb923c' },
  cache_set: { icon: '⚡', label: 'Cache Set', color: '#e879f9' },
}

const TABS = ['Sequence Diagram', 'Trace Timeline', 'Side Effects & Deps']

export default function App() {
  const [activeTab, setActiveTab] = useState('Sequence Diagram')
  const [selectedStep, setSelectedStep] = useState(null)
  const [mermaidReady, setMermaidReady] = useState(false)
  const [copied, setCopied] = useState(false)
  const [showRaw, setShowRaw] = useState(false)
  const diagramRef = useRef(null)

  useEffect(() => {
    const script = document.createElement('script')
    script.type = 'module'
    script.textContent = `
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
      window.__mermaid = mermaid;
      mermaid.initialize({ startOnLoad: false, theme: 'dark', themeVariables: {
        primaryColor: '#6c63ff', primaryTextColor: '#e0e0e0', primaryBorderColor: '#6c63ff',
        lineColor: '#555', secondaryColor: '#1a1a2e', tertiaryColor: '#0a0a1a',
        actorBkg: '#1e1e3a', actorBorder: '#6c63ff', actorTextColor: '#e0e0e0',
        signalColor: '#e0e0e0', signalTextColor: '#e0e0e0'
      }});
      window.dispatchEvent(new Event('mermaid-ready'));
    `
    document.head.appendChild(script)
    const handler = () => setMermaidReady(true)
    window.addEventListener('mermaid-ready', handler)
    return () => window.removeEventListener('mermaid-ready', handler)
  }, [])

  useEffect(() => {
    if (!mermaidReady || activeTab !== 'Sequence Diagram' || !diagramRef.current) return
    const render = async () => {
      try {
        diagramRef.current.innerHTML = ''
        const { svg } = await window.__mermaid.render('seq-diagram', traceData.mermaidDiagram)
        diagramRef.current.innerHTML = svg
      } catch (e) {
        diagramRef.current.innerHTML = `<pre style="color:#f87171">Mermaid error: ${e.message}</pre>`
      }
    }
    render()
  }, [mermaidReady, activeTab])

  const copyDiagram = () => {
    navigator.clipboard.writeText(traceData.mermaidDiagram)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <h1>Flow Trace — {traceData.tracedFlow}</h1>
          <p className="subtitle">
            Repo: {traceData.repoName} • polyglot-eval I2 • {new Date(traceData.generatedAt).toLocaleString()}
          </p>
        </div>
        <div className="badges">
          <span className="badge badge-purple">{traceData.steps.length} Steps</span>
          <span className="badge badge-blue">{traceData.externalDeps.length} External Deps</span>
          <span className="badge badge-amber">{traceData.sideEffects.length} Side Effects</span>
        </div>
      </header>

      {/* Tabs */}
      <div className="tab-bar">
        {TABS.map(t => (
          <button key={t} className={`tab ${activeTab === t ? 'active' : ''}`} onClick={() => setActiveTab(t)}>
            {t}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="content">
        {activeTab === 'Sequence Diagram' && (
          <div className="diagram-tab">
            <div className="diagram-container" ref={diagramRef}>
              {!mermaidReady && <p className="loading">Loading Mermaid...</p>}
            </div>
            <div className="raw-toggle">
              <button className="btn-secondary" onClick={() => setShowRaw(!showRaw)}>
                {showRaw ? '▲ Hide' : '▼ Show'} Raw Source
              </button>
              <button className="btn-copy" onClick={copyDiagram}>{copied ? '✓ Copied!' : '📋 Copy'}</button>
            </div>
            {showRaw && <pre className="raw-source">{traceData.mermaidDiagram}</pre>}
          </div>
        )}

        {activeTab === 'Trace Timeline' && (
          <div className="timeline-layout">
            <div className="timeline">
              {/* Entry point card */}
              <div className="timeline-entry entry-point">
                <div className="step-circle entry-circle">⬇</div>
                <div className="step-card entry-card">
                  <div className="entry-label">ENTRY POINT</div>
                  <div className="step-file">{traceData.entryPoint.file}:{traceData.entryPoint.line}</div>
                  <div className="step-fn">{traceData.entryPoint.function}()</div>
                  <div className="step-desc">{traceData.entryPoint.description}</div>
                  <div className="step-registered">Registered as: <code>{traceData.entryPoint.registeredAs}</code></div>
                </div>
              </div>

              {/* Steps */}
              {traceData.steps.map(step => (
                <div
                  key={step.index}
                  className={`timeline-entry ${selectedStep === step.index ? 'selected' : ''}`}
                  onClick={() => setSelectedStep(selectedStep === step.index ? null : step.index)}
                >
                  <div className="step-circle">{step.index}</div>
                  <div className="step-card">
                    <div className="step-card-top">
                      <span className="step-file">{step.file}:{step.line}</span>
                      {step.ioType && IO_BADGES[step.ioType] && (
                        <span className="io-badge" style={{
                          background: `${IO_BADGES[step.ioType].color}15`,
                          color: IO_BADGES[step.ioType].color,
                          borderColor: `${IO_BADGES[step.ioType].color}40`
                        }}>
                          {IO_BADGES[step.ioType].icon} {IO_BADGES[step.ioType].label}
                        </span>
                      )}
                    </div>
                    <div className="step-fn">{step.function}()</div>
                    <div className="step-desc">{step.description}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Detail panel */}
            {selectedStep && (
              <div className="detail-panel">
                <h3>Step {selectedStep} Details</h3>
                {(() => {
                  const s = traceData.steps.find(s => s.index === selectedStep)
                  if (!s) return null
                  return (
                    <>
                      <div className="detail-row"><span className="detail-label">File</span><span className="detail-value">{s.file}</span></div>
                      <div className="detail-row"><span className="detail-label">Function</span><span className="detail-value">{s.function}()</span></div>
                      <div className="detail-row"><span className="detail-label">Line</span><span className="detail-value">{s.line}</span></div>
                      <div className="detail-row"><span className="detail-label">I/O Type</span><span className="detail-value">{s.ioType || 'None'}</span></div>
                      <div className="detail-row"><span className="detail-label">Description</span><span className="detail-value">{s.description}</span></div>
                    </>
                  )
                })()}
              </div>
            )}
          </div>
        )}

        {activeTab === 'Side Effects & Deps' && (
          <div className="effects-tab">
            <div className="two-columns">
              <div className="column">
                <h3 className="column-title">🌐 External Dependencies</h3>
                {traceData.externalDeps.length === 0 ? (
                  <div className="empty-card">No external dependencies detected</div>
                ) : traceData.externalDeps.map((d, i) => (
                  <div className="effect-card" key={i}>
                    <div className="effect-name">{d.name}</div>
                    <div className="effect-source">{d.file}:{d.line}</div>
                    <div className="effect-desc">{d.description}</div>
                  </div>
                ))}
              </div>
              <div className="column">
                <h3 className="column-title">⚡ Side Effects</h3>
                {traceData.sideEffects.length === 0 ? (
                  <div className="empty-card">No side effects detected</div>
                ) : traceData.sideEffects.map((e, i) => (
                  <div className="effect-card" key={i}>
                    <div className="effect-type">
                      {IO_BADGES[e.type] ? `${IO_BADGES[e.type].icon} ${IO_BADGES[e.type].label}` : e.type}
                    </div>
                    <div className="effect-source">{e.file}:{e.line}</div>
                    <div className="effect-desc">{e.description}</div>
                  </div>
                ))}
              </div>
            </div>

            {traceData.uncertainty.length > 0 && (
              <div className="uncertainty-section">
                <h3>⚠️ Known Uncertainty</h3>
                {traceData.uncertainty.map((u, i) => (
                  <div className="uncertainty-item" key={i}>
                    <span className="uncertainty-file">{u.file}:{u.line}</span>
                    <span>{u.description}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
