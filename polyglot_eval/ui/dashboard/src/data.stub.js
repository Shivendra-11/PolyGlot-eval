/** Placeholder dashboard data — replaced by `serve-ui` / `generate-data` into `data.js`. */
export const dashboardData = {
  repoName: "(no eval data yet)",
  repoPath: "",
  generatedAt: new Date().toISOString(),
  stats: { total: 6, passed: 0, failed: 0, skipped: 6 },
  tasks: [
    { id: "I1", title: "ER Diagram", icon: "🗄️", mode: "read-only", status: "skipped", summary: "Not run", reportPath: "reports/I1_er_diagram.md", hasData: false },
    { id: "I2", title: "Flow Trace", icon: "🔀", mode: "read-only", status: "skipped", summary: "Not run", reportPath: "reports/I2_flow_trace.md", hasData: false },
    { id: "I3", title: "Safe Change", icon: "✏️", mode: "writes-repo", status: "skipped", summary: "Not run", reportPath: "reports/I3_safe_change.md", hasData: false },
    { id: "I4", title: "Polyglot Pair", icon: "🔗", mode: "creates-artifacts", status: "skipped", summary: "Not run", reportPath: "reports/I4_polyglot_pair.md", hasData: false },
    { id: "I5", title: "Dockerize", icon: "🐳", mode: "creates-artifacts", status: "skipped", summary: "Not run", reportPath: "reports/I5_dockerize.md", hasData: false },
    { id: "I6", title: "Bug Diagnosis", icon: "🐛", mode: "writes-repo", status: "skipped", summary: "Not run", reportPath: "reports/I6_bug_diagnosis.md", hasData: false },
  ],
  i1: null,
  i2: null,
  i3: null,
  i4: null,
  i5: null,
  i6: null,
  hasSummary: false,
};
