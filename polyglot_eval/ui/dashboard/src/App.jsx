import { useState, useEffect, useRef } from 'react'
import { dashboardData } from './data.js'

const I1_VIEWER_URL = import.meta.env.VITE_I1_VIEWER_URL || 'http://localhost:5173'
const I2_VIEWER_URL = import.meta.env.VITE_I2_VIEWER_URL || 'http://localhost:5174'

const NAV = [
  { id: 'overview', label: 'Overview', icon: '📊' },
  ...dashboardData.tasks.map(t => ({ id: t.id, label: `${t.id} · ${t.title}`, icon: t.icon, task: t })),
]

const STATUS_CLASS = { pass: 'status-pass', fail: 'status-fail', skipped: 'status-skipped' }

function TabBar({ tabs, active, onChange }) {
  return (
    <div className="panel-tabs">
      {tabs.map(t => (
        <button key={t} type="button" className={`tab-btn ${active === t ? 'active' : ''}`} onClick={() => onChange(t)}>
          {t}
        </button>
      ))}
    </div>
  )
}

function DataTable({ columns, rows }) {
  if (!rows?.length) return <p className="empty-inline">No data</p>
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>{columns.map(c => <th key={c.key}>{c.label}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.id ?? i}>
              {columns.map(c => (
                <td key={c.key}>{c.render ? c.render(row) : row[c.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function MermaidBlock({ diagram, id }) {
  const ref = useRef(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (window.__mermaid) { setReady(true); return }
    const script = document.createElement('script')
    script.type = 'module'
    script.textContent = `
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
      window.__mermaid = mermaid;
      mermaid.initialize({ startOnLoad: false, theme: 'dark', themeVariables: {
        primaryColor: '#7c6aff', primaryTextColor: '#e0e0e0', lineColor: '#555'
      }});
      window.dispatchEvent(new Event('mermaid-ready'));
    `
    document.head.appendChild(script)
    const h = () => setReady(true)
    window.addEventListener('mermaid-ready', h)
    return () => window.removeEventListener('mermaid-ready', h)
  }, [])

  useEffect(() => {
    if (!ready || !diagram || !ref.current) return
    const run = async () => {
      try {
        ref.current.innerHTML = ''
        const { svg } = await window.__mermaid.render(id, diagram)
        ref.current.innerHTML = svg
      } catch (e) {
        ref.current.innerHTML = `<pre class="error">${e.message}</pre>`
      }
    }
    run()
  }, [ready, diagram, id])

  if (!diagram) return <div className="empty">No diagram data</div>
  return <div className="diagram-box" ref={ref}>{!ready && <p className="loading">Loading diagram…</p>}</div>
}

function Overview() {
  const { stats, tasks, repoName, generatedAt } = dashboardData
  return (
    <div className="overview">
      <div className="stats-row">
        <div className="stat-card"><span className="stat-num">{stats.total}</span><span className="stat-label">Tasks</span></div>
        <div className="stat-card pass"><span className="stat-num">{stats.passed}</span><span className="stat-label">Passed</span></div>
        <div className="stat-card fail"><span className="stat-num">{stats.failed}</span><span className="stat-label">Failed</span></div>
        <div className="stat-card skip"><span className="stat-num">{stats.skipped}</span><span className="stat-label">Skipped</span></div>
      </div>
      <p className="meta">Repo: <strong>{repoName}</strong> · {new Date(generatedAt).toLocaleString()}</p>
      <div className="task-grid">
        {tasks.map(t => (
          <div key={t.id} className={`task-card ${STATUS_CLASS[t.status] || ''}`}>
            <div className="task-card-head">
              <span className="task-icon">{t.icon}</span>
              <div>
                <h3>{t.id} — {t.title}</h3>
                <span className={`pill ${STATUS_CLASS[t.status]}`}>{t.status}</span>
              </div>
            </div>
            <p className="task-summary">{t.summary}</p>
            <div className="task-meta">
              <span className="mode-tag">{t.mode}</span>
              {t.hasData && <span className="data-tag">UI data ✓</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function PanelI1({ data }) {
  if (!data) return <div className="empty">I1 not run — no ER diagram data.</div>
  return (
    <div className="panel">
      <div className="panel-badges">
        <span className="badge">{data.entities?.length || 0} entities</span>
        <span className="badge">{data.relationships?.length || 0} relationships</span>
      </div>
      <MermaidBlock diagram={data.mermaidDiagram} id="dash-er" />
      <div className="entity-chips">
        {(data.entities || []).map(e => (
          <span key={e.name} className="chip">{e.name} <small>{e.sourceFile}:{e.sourceLine}</small></span>
        ))}
      </div>
    </div>
  )
}

function PanelI2({ data }) {
  if (!data) return <div className="empty">I2 not run — no flow trace data.</div>
  return (
    <div className="panel">
      <p className="flow-title">{data.tracedFlow}</p>
      <MermaidBlock diagram={data.mermaidDiagram} id="dash-seq" />
      <div className="step-list">
        {(data.steps || []).slice(0, 12).map(s => (
          <div key={s.index} className="step-row">
            <span className="step-n">{s.index}</span>
            <div>
              <code>{s.file}:{s.line}</code> · <strong>{s.function}()</strong>
              <p>{s.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function PanelI3({ data }) {
  const [tab, setTab] = useState('Summary')
  if (!data) return <div className="empty">I3 not run.</div>
  const stats = data.diffStats || {}
  return (
    <div className="panel">
      <div className="panel-badges">
        <span className="badge">{data.branch}</span>
        <span className={`pill ${data.testResult === 'PASS' ? 'status-pass' : 'status-fail'}`}>{data.testResult}</span>
        {stats.filesTouched != null && <span className="badge">{stats.filesTouched} files · +{stats.linesAdded || 0}/-{stats.linesRemoved || 0}</span>}
      </div>
      <TabBar tabs={['Summary', 'Plan', 'Diff', 'Tests']} active={tab} onChange={setTab} />
      {tab === 'Summary' && (
        <>
          <h3 className="panel-title">{data.changeTitle || 'Safe change'}</h3>
          <p>{data.changeDescription || data.diffSummary}</p>
          {data.changeMotivation && <div className="info-block"><h4>Motivation</h4><p>{data.changeMotivation}</p></div>}
          <p><strong>Risk:</strong> {data.riskAssessment}</p>
          {(data.filesChanged || []).map(f => (
            <div key={f.path} className="file-row">
              <code>{f.path}</code> <span className="chip">{f.changeType || 'edit'}</span>
              <p>{f.reason}</p>
              {f.snippet && <pre className="code-block snippet">{f.snippet}</pre>}
            </div>
          ))}
          {data.rollbackSteps?.length > 0 && (
            <div className="info-block"><h4>Rollback</h4>
              <ul className="bullet-list">{data.rollbackSteps.map(s => <li key={s}><code>{s}</code></li>)}</ul>
            </div>
          )}
        </>
      )}
      {tab === 'Plan' && (
        <ol className="plan-list">
          {(data.changePlan || []).map(p => (
            <li key={p.step}><strong>Step {p.step}</strong> — {p.action}</li>
          ))}
        </ol>
      )}
      {tab === 'Diff' && (
        <>
          <p>{data.diffSummary}</p>
          {data.diffPreview && <pre className="code-block diff">{data.diffPreview}</pre>}
        </>
      )}
      {tab === 'Tests' && (
        <>
          <p><code>{data.testCommand}</code> · Lint: {data.lintResult || '—'}</p>
          <DataTable
            columns={[
              { key: 'name', label: 'Test' },
              { key: 'status', label: 'Status', render: r => <span className={`pill ${r.status === 'PASS' ? 'status-pass' : 'status-fail'}`}>{r.status}</span> },
              { key: 'durationMs', label: 'ms' },
            ]}
            rows={data.tests || [{ name: data.testCommand, status: data.testResult, durationMs: '—' }]}
          />
          <pre className="code-block">{data.testOutput || '—'}</pre>
        </>
      )}
    </div>
  )
}

function PanelI4({ data }) {
  const [tab, setTab] = useState('Overview')
  if (!data) return <div className="empty">I4 not run.</div>
  return (
    <div className="panel">
      <div className="panel-badges">
        {(data.stack && Object.entries(data.stack).map(([k, v]) => (
          <span key={k} className="chip">{k}: {v}</span>
        )))}
      </div>
      <TabBar tabs={['Overview', 'Endpoints', 'Architecture', 'Artifacts']} active={tab} onChange={setTab} />
      {tab === 'Overview' && (
        <>
          <div className="info-block"><h4>FastAPI Service</h4><p>{data.serviceSummary}</p></div>
          <div className="info-block"><h4>Node CLI</h4><p>{data.clientSummary}</p></div>
          <div className="info-block"><h4>React UI</h4><p>{data.uiSummary}</p></div>
          {data.currencies?.length > 0 && (
            <div className="entity-chips">{data.currencies.map(c => <span key={c} className="chip">{c}</span>)}</div>
          )}
          {(data.runInstructions || []).map((line, i) => <p key={i} className="run-line"><span className="step-n">{i + 1}</span> {line}</p>)}
          {data.testOutput && <pre className="code-block">{data.testOutput}</pre>}
        </>
      )}
      {tab === 'Endpoints' && (
        <DataTable
          columns={[
            { key: 'method', label: 'Method' },
            { key: 'path', label: 'Path' },
            { key: 'request', label: 'Request', render: r => <code>{JSON.stringify(r.request)}</code> },
            { key: 'response', label: 'Response', render: r => <code>{JSON.stringify(r.response)}</code> },
          ]}
          rows={data.endpoints || []}
        />
      )}
      {tab === 'Architecture' && (
        <>
          <MermaidBlock diagram={data.architectureDiagram} id="dash-i4-arch" />
          {data.tests && (
            <div className="task-grid">
              {Object.entries(data.tests).map(([k, v]) => (
                <div key={k} className="info-block">
                  <h4>{k}</h4>
                  <p>{v.command}</p>
                  <span className={`pill ${v.failed === 0 ? 'status-pass' : 'status-fail'}`}>{v.passed} passed · {v.failed} failed</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
      {tab === 'Artifacts' && (
        <ul className="artifact-list">{(data.artifacts || []).map(a => <li key={a}><code>{a}</code></li>)}</ul>
      )}
    </div>
  )
}

function PanelI5({ data }) {
  const [tab, setTab] = useState('Summary')
  if (!data) return <div className="empty">I5 not run.</div>
  const hc = data.healthCheck || {}
  return (
    <div className="panel">
      <div className="panel-badges">
        <span className={`pill ${data.status === 'pass' ? 'status-pass' : 'status-skipped'}`}>{data.status}</span>
        {data.strategy && <span className="badge">{data.strategy}</span>}
      </div>
      <TabBar tabs={['Summary', 'Health', 'Build']} active={tab} onChange={setTab} />
      {tab === 'Summary' && (
        <>
          <p>{data.strategy}</p>
          <div className="port-row">
            {data.ports && Object.entries(data.ports).map(([k, v]) => (
              <span key={k} className="chip">{k}: {v}</span>
            ))}
          </div>
          {(data.runInstructions || []).map((line, i) => <p key={i} className="run-line"><span className="step-n">{i + 1}</span> <code>{line}</code></p>)}
          {data.resourceLimits && (
            <p className="meta">Limits: {data.resourceLimits.memory} RAM · {data.resourceLimits.cpu} CPU</p>
          )}
        </>
      )}
      {tab === 'Health' && (
        <>
          <p><strong>Primary:</strong> {hc.url} → <span className={`pill ${hc.status === 'ok' ? 'status-pass' : ''}`}>{hc.status}</span></p>
          <DataTable
            columns={[
              { key: 'name', label: 'Check' },
              { key: 'url', label: 'URL' },
              { key: 'status', label: 'Status' },
              { key: 'latencyMs', label: 'ms' },
            ]}
            rows={data.healthChecks || [hc]}
          />
        </>
      )}
      {tab === 'Build' && (
        <>
          {(data.dockerFiles || []).map(f => (
            <div key={f.path} className="file-row"><code>{f.path}</code> — {f.role} ({f.baseImage})</div>
          ))}
          {(data.buildSteps || []).map(s => <p key={s}><code>{s}</code></p>)}
          <pre className="code-block">{data.buildOutput || data.runOutput || '—'}</pre>
        </>
      )}
    </div>
  )
}

function PanelI6({ data }) {
  const [tab, setTab] = useState('Bug')
  if (!data) return <div className="empty">I6 not run.</div>
  const rc = data.rootCause || {}
  return (
    <div className="panel">
      <div className="panel-badges">
        {data.severity && <span className={`pill status-${data.severity === 'high' ? 'fail' : 'pass'}`}>{data.severity}</span>}
        <span className={`pill ${data.verification?.result === 'PASS' ? 'status-pass' : 'status-fail'}`}>{data.verification?.result}</span>
      </div>
      <TabBar tabs={['Bug', 'Timeline', 'Fix', 'Verify']} active={tab} onChange={setTab} />
      {tab === 'Bug' && (
        <>
          <p><strong>Impact:</strong> {data.impact}</p>
          <p>{data.bugDescription}</p>
          <div className="info-block"><h4>Repro steps</h4>
            <ol className="plan-list">
              {(data.reproSteps || []).map(r => (
                <li key={r.step}><strong>{r.step}.</strong> {r.action}
                  {r.expected && <> — expected: {r.expected}</>}
                  {r.actual && <> — actual: {r.actual}</>}
                </li>
              ))}
            </ol>
          </div>
          <div className="info-block"><h4>Root cause</h4>
            <p>{rc.explanation}</p>
            {rc.file && <code>{rc.file}:{rc.line}</code>}
            {rc.function && <p>Function: <strong>{rc.function}()</strong></p>}
            {rc.callChain?.length > 0 && (
              <ul className="bullet-list">{rc.callChain.map(c => <li key={c}>{c}</li>)}</ul>
            )}
          </div>
        </>
      )}
      {tab === 'Timeline' && (
        <div className="timeline">
          {(data.timeline || []).map((t, i) => (
            <div key={t.phase} className="timeline-row">
              <span className="step-n">{i + 1}</span>
              <div>
                <strong>{t.phase}</strong> · {t.durationMin} min
                <p>{t.outcome}</p>
              </div>
            </div>
          ))}
        </div>
      )}
      {tab === 'Fix' && (
        <>
          <p>{data.fixSummary}</p>
          <div className="info-block"><h4>Before</h4><p>{data.beforeBehavior}</p></div>
          <div className="info-block"><h4>After</h4><p>{data.afterBehavior}</p></div>
          {(data.filesChanged || []).map(f => (
            <div key={f.path} className="file-row"><code>{f.path}</code> (+{f.linesChanged || '?'} lines) — {f.reason}</div>
          ))}
          {data.fixPreview && <pre className="code-block diff">{data.fixPreview}</pre>}
        </>
      )}
      {tab === 'Verify' && (
        <>
          <p><code>{data.verification?.command}</code></p>
          <DataTable
            columns={[
              { key: 'name', label: 'Test' },
              { key: 'status', label: 'Status', render: r => <span className={`pill ${r.status === 'PASS' ? 'status-pass' : 'status-fail'}`}>{r.status}</span> },
            ]}
            rows={data.regressionTests || []}
          />
          <pre className="code-block">{data.verification?.output || '—'}</pre>
          {data.verificationNote && <p className="meta">{data.verificationNote}</p>}
        </>
      )}
    </div>
  )
}

const PANELS = {
  I1: () => <PanelI1 data={dashboardData.i1} />,
  I2: () => <PanelI2 data={dashboardData.i2} />,
  I3: () => <PanelI3 data={dashboardData.i3} />,
  I4: () => <PanelI4 data={dashboardData.i4} />,
  I5: () => <PanelI5 data={dashboardData.i5} />,
  I6: () => <PanelI6 data={dashboardData.i6} />,
}

export default function App() {
  const [active, setActive] = useState('overview')
  const Panel = active === 'overview' ? Overview : (PANELS[active] || (() => <div className="empty">Unknown panel</div>))

  return (
    <div className="dash-app">
      <aside className="dash-nav">
        <div className="dash-brand">
          <span>⚡</span>
          <div>
            <h1>polyglot-eval</h1>
            <p>Dashboard</p>
          </div>
        </div>
        <nav>
          {NAV.map(item => (
            <button
              key={item.id}
              type="button"
              className={`nav-btn ${active === item.id ? 'active' : ''} ${item.task ? STATUS_CLASS[item.task.status] : ''}`}
              onClick={() => setActive(item.id)}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <footer className="dash-foot">
          <a href={I1_VIEWER_URL} target="_blank" rel="noreferrer">I1 viewer</a>
          <a href={I2_VIEWER_URL} target="_blank" rel="noreferrer">I2 viewer</a>
        </footer>
      </aside>
      <main className="dash-main">
        <header className="dash-header">
          <h2>{active === 'overview' ? `Overview — ${dashboardData.repoName}` : `${active} — ${dashboardData.tasks.find(t => t.id === active)?.title || ''}`}</h2>
        </header>
        <div className="dash-content">
          <Panel />
        </div>
      </main>
    </div>
  )
}
