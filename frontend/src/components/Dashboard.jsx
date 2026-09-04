import { Bar, Line } from "react-chartjs-2";
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";

ChartJS.register(ArcElement, BarElement, CategoryScale, Filler, Legend, LineElement, LinearScale, PointElement, Tooltip);

const SEVERITY_TONE = {
  Critical: "#b82e37",
  Poor: "#d3542c",
  Moderate: "#c48216",
  Good: "#17715b",
  Excellent: "#17715b",
};

export default function Dashboard({ summary, trends, onRetry }) {
  if (!summary || !trends) {
    return (
      <section className="view active">
        <div className="dashboard-error">
          <span>{onRetry ? "Dashboard data has not loaded yet." : "Loading dashboard data…"}</span>
          {onRetry && <button className="secondary-action" onClick={onRetry}>Retry</button>}
        </div>
      </section>
    );
  }

  const forecast = trends.forecast?.forecast ?? [];
  const npk = {
    labels: ["Nitrogen", "Phosphorus", "Potassium"],
    datasets: [
      {
        label: "Average ppm",
        data: [summary.avg_n, summary.avg_p, summary.avg_k],
        backgroundColor: ["#2f7d5c", "#4c9f70", "#7ab88a"],
        borderRadius: 6,
      },
    ],
  };
  const trendSeries = {
    labels: forecast.map((point) => point.year),
    datasets: [
      {
        label: "pH",
        data: forecast.map((point) => point.ph ?? null),
        borderColor: "#2f7d5c",
        backgroundColor: "rgba(47, 125, 92, 0.15)",
        fill: true,
        tension: 0.35,
        spanGaps: true,
      },
      {
        label: "Nitrate (mg/L)",
        data: forecast.map((point) => point.nitrate ?? null),
        borderColor: "#c48216",
        backgroundColor: "rgba(196, 130, 22, 0.12)",
        tension: 0.35,
        spanGaps: true,
      },
    ],
  };

  const metrics = [
    { label: "Soil samples", value: summary.soil_sample_size },
    { label: "Avg pH", value: summary.avg_soil_ph },
    { label: "Avg N (ppm)", value: summary.avg_n },
    { label: "Avg P (ppm)", value: summary.avg_p },
    { label: "Avg K (ppm)", value: summary.avg_k },
    { label: "Organic matter %", value: summary.avg_organic_matter },
    { label: "Pollution cases", value: summary.pollution_cases },
    { label: "Severe cases", value: summary.severe_pollution_cases, tone: SEVERITY_TONE.Critical },
    { label: "Potable water %", value: summary.potable_water_rate },
    { label: "Groundwater sites", value: summary.groundwater_sites },
  ];

  return (
    <section className="view active">
      <section className="metric-grid">
        {metrics.map((metric) => (
          <article className="metric-card" key={metric.label}>
            <span className="metric-label">{metric.label}</span>
            <strong style={metric.tone ? { color: metric.tone } : undefined}>{metric.value}</strong>
          </article>
        ))}
      </section>
      <section className="panel-grid">
        <article className="panel wide">
          <div className="panel-heading">
            <h2>Groundwater Trend</h2>
            <span className={`badge ${trends.forecast?.direction === "degrading" ? "severity-high" : "severity-good"}`}>
              {trends.forecast?.direction ?? "unknown"}
            </span>
          </div>
          <div className="chart-wrap">
            <Line data={trendSeries} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        </article>
        <article className="panel">
          <div className="panel-heading">
            <h2>NPK Baseline</h2>
            <span>soil sample</span>
          </div>
          <div className="chart-wrap">
            <Bar data={npk} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        </article>
      </section>
      <p className="muted dashboard-footer">Snapshot: {summary.last_updated} · {summary.groundwater_sites} groundwater monitoring sites</p>
    </section>
  );
}
