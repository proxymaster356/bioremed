import { useCallback, useEffect, useState } from "react";
import Dashboard from "./components/Dashboard.jsx";
import PredictionForm from "./components/PredictionForm.jsx";
import SiteMap from "./components/SiteMap.jsx";
import Reports from "./components/Reports.jsx";
import { checkHealth, predict, getSummary, getTrends, getSites } from "./lib/api.js";

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "prediction", label: "Prediction" },
  { id: "map", label: "Site Map" },
  { id: "reports", label: "Reports" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [apiStatus, setApiStatus] = useState("Connecting");
  const [latestReport, setLatestReport] = useState(null);
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState(null);
  const [sites, setSites] = useState([]);
  const [dashboardError, setDashboardError] = useState("");

  const loadDashboard = useCallback(async () => {
    setDashboardError("");
    try {
      const [summaryData, trendData, siteData] = await Promise.all([getSummary(), getTrends(), getSites()]);
      setSummary(summaryData);
      setTrends(trendData);
      setSites(siteData.sites);
    } catch (loadError) {
      setDashboardError(loadError.message);
    }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        await checkHealth();
        setApiStatus("API online");
        await loadDashboard();
      } catch {
        setApiStatus("API offline");
      }
    })();
  }, [loadDashboard]);

  const runAssessment = useCallback(async (payload) => {
    const result = await predict(payload);
    setLatestReport(result);
    setActiveTab("prediction");
    return result;
  }, []);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" />
          <div>
            <strong>BioRemediate IQ</strong>
            <small>Soil, water, and contaminant intelligence</small>
          </div>
        </div>
        <nav className="nav-tabs" aria-label="Main views">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={activeTab === tab.id ? "active" : ""}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
        <div className={`status-pill ${apiStatus === "API online" ? "online" : "offline"}`}>{apiStatus}</div>
      </aside>

      <main className="shell">
        <header className="topbar">
          <div>
            <p className="eyebrow">Local CSV-backed prototype</p>
            <h1>Bioremediation Intelligence Platform</h1>
          </div>
          <button
            className="primary-action"
            onClick={async () => {
              try {
                await runAssessment({});
              } catch (error) {
                setLatestReport({ error: error.message });
                setActiveTab("reports");
              }
            }}
          >
            Run Sample Assessment
          </button>
        </header>

        {activeTab === "dashboard" && (
          <>
            {dashboardError && (
              <div className="dashboard-error">
                <span>Dashboard data could not be loaded — {dashboardError}</span>
                <button className="secondary-action" onClick={loadDashboard}>Retry</button>
              </div>
            )}
            <Dashboard summary={summary} trends={trends} onRetry={loadDashboard} />
          </>
        )}
        {activeTab === "prediction" && (
          <PredictionForm latestReport={latestReport} onAssess={runAssessment} />
        )}
        {activeTab === "map" && <SiteMap sites={sites} />}
        {activeTab === "reports" && <Reports report={latestReport} />}
      </main>
    </div>
  );
}
