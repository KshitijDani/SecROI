import { useEffect, useMemo, useState } from "react";
import { Link, Route, Routes, useLocation, useNavigate } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8001";
const SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNSPECIFIED"];
const SEVERITY_SCORE = {
  CRITICAL: 4,
  HIGH: 3,
  MEDIUM: 2,
  LOW: 1,
  UNSPECIFIED: 0,
};

function flattenFindings(records) {
  const rows = [];
  records.forEach((record) => {
    const fileName = record.file || "";
    const repoName = record.repo_name || "";
    const repoUrl = record.repo_url || "";
    const findings = record.findings || [];
    findings.forEach((finding) => {
      rows.push({
        repo_name: repoName,
        repo_url: repoUrl,
        file_name: finding.file_name || fileName,
        bug_type: finding.bug_type || "",
        bug_name: finding.bug_name || "",
        bug_priority: finding.bug_priority || "",
        file_lines: finding.file_lines || "",
      });
    });
  });
  return rows;
}

function formatReportName(name) {
  const match = name.match(/vulnerabilities_(\d{8})_(\d{6})\.json$/);
  if (!match) {
    return name;
  }
  const [, datePart, timePart] = match;
  const year = Number(datePart.slice(0, 4));
  const month = Number(datePart.slice(4, 6)) - 1;
  const day = Number(datePart.slice(6, 8));
  const hour = Number(timePart.slice(0, 2));
  const minute = Number(timePart.slice(2, 4));
  const second = Number(timePart.slice(4, 6));
  const dt = new Date(year, month, day, hour, minute, second);
  if (Number.isNaN(dt.getTime())) {
    return name;
  }
  const dateLabel = new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(dt);
  const timeLabel = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  })
    .format(dt)
    .replace(" AM", "AM")
    .replace(" PM", "PM");
  return `${dateLabel} - ${timeLabel}`;
}

function normalizePriority(value) {
  if (!value) {
    return "UNSPECIFIED";
  }
  const upper = value.toUpperCase();
  if (upper.includes("CRIT")) return "CRITICAL";
  if (upper.includes("HIGH")) return "HIGH";
  if (upper.includes("MED")) return "MEDIUM";
  if (upper.includes("LOW")) return "LOW";
  return "UNSPECIFIED";
}

export default function App() {
  const [rows, setRows] = useState([]);
  const [status, setStatus] = useState("Idle");
  const [error, setError] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const navigate = useNavigate();
  const location = useLocation();
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [remediationSummary, setRemediationSummary] = useState("");
  const [repoName, setRepoName] = useState("");
  const [repoLink, setRepoLink] = useState("");

  const counts = useMemo(() => {
    const total = rows.length;
    const byPriority = rows.reduce((acc, row) => {
      const key = normalizePriority(row.bug_priority);
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
    return { total, byPriority };
  }, [rows]);

  const severityByFile = useMemo(() => {
    const map = new Map();
    rows.forEach((row) => {
      const file = row.file_name || "unknown";
      const priority = normalizePriority(row.bug_priority);
      const score = SEVERITY_SCORE[priority] ?? 0;
      map.set(file, (map.get(file) || 0) + score);
    });
    const entries = Array.from(map.entries())
      .map(([file, score]) => ({ file, score }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 6);
    return entries;
  }, [rows]);

  const priorityCounts = useMemo(() => {
    return SEVERITY_ORDER.map((key) => ({
      key,
      count: counts.byPriority[key] || 0,
    }));
  }, [counts]);

  const remediationPriorities = useMemo(() => {
    return rows
      .map((row) => ({
        file: row.file_name,
        bug: row.bug_name || row.bug_type || "Unknown",
        priority: normalizePriority(row.bug_priority),
        score: SEVERITY_SCORE[normalizePriority(row.bug_priority)] ?? 0,
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 8);
  }, [rows]);

  const allBugs = useMemo(() => {
    return rows
      .map((row) => ({
        file: row.file_name,
        bug: row.bug_name || row.bug_type || "Unknown",
        priority: normalizePriority(row.bug_priority),
        lines: row.file_lines || "",
      }))
      .filter((item) => item.bug);
  }, [rows]);

  async function fetchLatestReport() {
    setStatus("Loading report...");
    setError("");
    try {
      const response = await fetch(`${API_BASE}/report`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Could not fetch vulnerabilities report.");
      }
      const payload = await response.json();
      const flattened = flattenFindings(payload.data || []);
      setSelectedReport(payload.report_path?.split("/").slice(-1)[0] || null);
      setRows(flattened);
      setStatus("Loaded");
    } catch (err) {
      setStatus("Idle");
      setError(err.message || "Failed to parse report.");
    }
  }

  async function fetchReportList(selectLatest = true) {
    try {
      const response = await fetch(`${API_BASE}/reports`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Could not fetch report list.");
      }
      const payload = await response.json();
      const list = payload.reports || [];
      setReports(list);
      if (selectLatest && list.length > 0) {
        setSelectedReport(list[0].name);
        await fetchReportByName(list[0].name);
      }
    } catch (err) {
      setError(err.message || "Failed to load report list.");
    }
  }

  async function fetchReportByName(name) {
    setStatus("Loading report...");
    setError("");
    try {
      const response = await fetch(`${API_BASE}/report?name=${encodeURIComponent(name)}`, {
        cache: "no-store",
      });
      if (!response.ok) {
        throw new Error("Could not fetch vulnerabilities report.");
      }
      const payload = await response.json();
      const flattened = flattenFindings(payload.data || []);
      const firstRecord = (payload.data || []).find((entry) => entry.repo_name || entry.repo_url) || {};
      const firstRepo = firstRecord.repo_name || "";
      const firstRepoUrl = firstRecord.repo_url || "";
      setSelectedReport(name);
      setRepoName(firstRepo);
      setRepoLink(firstRepoUrl);
      setRows(flattened);
      setStatus("Loaded");
      await fetchRemediationSummary(name);
    } catch (err) {
      setStatus("Idle");
      setError(err.message || "Failed to parse report.");
    }
  }

  async function fetchRemediationSummary(name) {
    try {
      const response = await fetch(`${API_BASE}/remediation?name=${encodeURIComponent(name)}`, {
        cache: "no-store",
      });
      if (!response.ok) {
        setRemediationSummary("");
        return;
      }
      const payload = await response.json();
      setRemediationSummary(payload.summary || "");
    } catch {
      setRemediationSummary("");
    }
  }

  async function runPipeline() {
    if (!repoUrl.trim()) {
      setError("Please enter a public GitHub repository URL.");
      return;
    }
    setStatus("Running ETL pipeline...");
    setError("");
    navigate("/loading");
    try {
      const response = await fetch(`${API_BASE}/run?repo_url=${encodeURIComponent(repoUrl.trim())}`, {
        method: "POST",
      });
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Failed to run ETL pipeline.");
      }
      await fetchReportList(true);
      navigate("/reports");
    } catch (err) {
      setStatus("Idle");
      setError(err.message || "Failed to run ETL pipeline.");
      navigate("/");
    }
  }

  useEffect(() => {
    if (location.pathname === "/reports") {
      fetchReportList(true);
    }
  }, [location.pathname]);

  return (
    <div className="fade-in">
      <header>
        <h1>SecROI</h1>
        <p className="tagline">your security assistant</p>
      </header>
      <main>
        <div className="panel">
          <div className="tab-bar">
            <Link
              to="/"
              className={`tab-button ${location.pathname === "/" ? "active" : ""}`}
            >
              New Scan
            </Link>
            <Link
              to="/reports"
              className={`tab-button ${location.pathname === "/reports" ? "active" : ""}`}
            >
              Reports
            </Link>
          </div>

          <Routes>
            <Route
              path="/"
              element={
                <>
                  <div className="controls">
                    <input
                      type="text"
                      value={repoUrl}
                      onChange={(event) => setRepoUrl(event.target.value)}
                      placeholder="Public GitHub URL (e.g. https://github.com/user/repo)"
                    />
                    <button onClick={runPipeline}>Run Scan</button>
                    <Link className="secondary-link" to="/reports">
                      View Reports
                    </Link>
                  </div>
                  {error ? <div className="state">{error}</div> : null}
                </>
              }
            />
            <Route
              path="/loading"
              element={
                <div className="loading">
                  <div className="spinner" />
                  <div className="state">{status}</div>
                </div>
              }
            />
            <Route
              path="/reports"
              element={
                <div className="reports-layout">
                  <aside className="report-list">
                    <div className="report-list-header">Scans</div>
                    {reports.length === 0 ? (
                      <div className="state">No reports yet.</div>
                    ) : (
                      reports.map((report) => (
                      <button
                        key={report.name}
                        className={`report-item ${selectedReport === report.name ? "active" : ""}`}
                        onClick={() => fetchReportByName(report.name)}
                        title={report.name}
                      >
                        {formatReportName(report.name)}
                      </button>
                    ))
                  )}
                </aside>

                  <section className="report-detail">
                    <div className="meta-block">
                      {repoName ? (
                        <div className="repo-line">
                          {repoLink ? (
                            <a className="repo-link" href={repoLink} target="_blank" rel="noreferrer">
                              {repoName}
                            </a>
                          ) : (
                            repoName
                          )}
                        </div>
                      ) : null}
                      <div className="meta">
                        <span className="chip">Status: {status}</span>
                        <span className="chip">Rows: {counts.total}</span>
                        {Object.keys(counts.byPriority).map((key) => (
                          <span key={key} className="chip">
                            {key}: {counts.byPriority[key]}
                          </span>
                        ))}
                      </div>
                    </div>

                    {error ? <div className="state">{error}</div> : null}

                    <div className="dashboard-grid">
                      <div className="card">
                        <details open>
                          <summary>Severity Chart</summary>
                          <div className="chart">
                            {severityByFile.length === 0 ? (
                              <div className="state">No data yet.</div>
                            ) : (
                              severityByFile.map((item) => (
                                <div key={item.file} className="bar-row">
                                  <span className="bar-label">{item.file}</span>
                                  <div className="bar-track">
                                    <div
                                      className="bar-fill"
                                      style={{ width: `${Math.min(100, item.score * 8)}%` }}
                                    />
                                  </div>
                                </div>
                              ))
                            )}
                          </div>
                        </details>
                      </div>

                      <div className="card">
                        <details open>
                          <summary>Occurrences of Severity</summary>
                          <div className="occurrence-list">
                            {priorityCounts.map((item) => (
                              <div key={item.key} className="occurrence-row">
                                <span className="occurrence-label">{item.key}</span>
                                <div className="occurrence-bar">
                                  <div
                                    className="occurrence-fill"
                                    style={{
                                      width: `${counts.total ? (item.count / counts.total) * 100 : 0}%`,
                                    }}
                                  />
                                </div>
                                <span className="occurrence-count">{item.count}</span>
                              </div>
                            ))}
                          </div>
                        </details>
                      </div>

                      <div className="card">
                        <details open>
                          <summary>Remediation Summary</summary>
                          <p className="summary-text">
                            {remediationSummary
                              ? remediationSummary
                              : "No remediation summary available yet. Run a scan to generate it."}
                          </p>
                        </details>
                      </div>

                      <div className="card">
                        <details open>
                          <summary>Remediation Priorities</summary>
                          <div className="table-wrap compact">
                            <table className="table">
                              <thead>
                                <tr>
                                  <th>File</th>
                                  <th>Vuln Type</th>
                                  <th>Priority</th>
                                </tr>
                              </thead>
                              <tbody>
                                {remediationPriorities.length === 0 ? (
                                  <tr>
                                    <td colSpan="3" className="state">
                                      No findings yet.
                                    </td>
                                  </tr>
                                ) : (
                                  remediationPriorities.map((item, index) => (
                                    <tr key={`${item.file}-${index}`}>
                                      <td>{item.file}</td>
                                      <td>{item.bug}</td>
                                      <td>{item.priority}</td>
                                    </tr>
                                  ))
                                )}
                              </tbody>
                            </table>
                          </div>
                        </details>
                      </div>

                      <div className="card bugs-card">
                        <details>
                          <summary>Bugs</summary>
                          <div className="table-wrap compact">
                            <table className="table">
                              <thead>
                                <tr>
                                  <th>File</th>
                                  <th>Bug</th>
                                  <th>Priority</th>
                                  <th>Lines</th>
                                </tr>
                              </thead>
                              <tbody>
                                {allBugs.length === 0 ? (
                                  <tr>
                                    <td colSpan="4" className="state">
                                      No bugs found.
                                    </td>
                                  </tr>
                                ) : (
                                  allBugs.map((item, index) => (
                                    <tr key={`${item.file}-${item.bug}-${index}`}>
                                      <td>{item.file}</td>
                                      <td>{item.bug}</td>
                                      <td>{item.priority}</td>
                                      <td>{item.lines}</td>
                                    </tr>
                                  ))
                                )}
                              </tbody>
                            </table>
                          </div>
                        </details>
                      </div>
                    </div>
                  </section>
                </div>
              }
            />
          </Routes>
        </div>
      </main>
    </div>
  );
}
