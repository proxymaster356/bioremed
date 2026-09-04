import { isDangerous, severityColor, worstClass } from "../lib/severity.js";

function StatusBadge({ label, className }) {
  return (
    <span className="badge" style={{ backgroundColor: severityColor(className) }}>
      {label}: {className}
    </span>
  );
}

export default function PredictionResults({ result }) {
  if (!result) {
    return (
      <section className="results-layout">
        <article className="result-card">
          <p className="muted">Run an assessment to see predictions, recommendations, and a crop plan.</p>
        </article>
      </section>
    );
  }
  if (result.error) {
    return (
      <section className="results-layout">
        <article className="result-card"><p className="error-text">{result.error}</p></article>
      </section>
    );
  }

  const contaminationClass = result.contamination.class;
  const ensembleClass = result.ensemble.class;
  const critical = contaminationClass === "Severe" || ensembleClass === "Critical";
  const showAlert = critical || isDangerous(contaminationClass) || isDangerous(ensembleClass);
  const ringScore = result.soil_health.score;
  const ringColor = severityColor(worstClass([ensembleClass, contaminationClass]));

  return (
    <section className="results-layout">
      {showAlert && (
        <div className={`alert-banner ${critical ? "critical" : "warning"}`} role="alert">
          <strong>{critical ? "⛔ Danger:" : "⚠ Warning:"}</strong>{" "}
          {result.contamination.pollutant} contamination is <strong>{contaminationClass.toLowerCase()}</strong> at{" "}
          {result.contamination.concentration_mg_kg} mg/kg — overall site condition is <strong>{ensembleClass}</strong>{" "}
          (risk {result.ensemble.risk_score}/100). Start remediation before any agricultural use.
        </div>
      )}

      <article className="result-card">
        <h2>Condition Prediction</h2>
        <div
          className="score-ring"
          style={{ "--score": `${ringScore}%`, background: `conic-gradient(${ringColor} ${ringScore}%, #eef4ee 0)` }}
        >
          <strong style={{ backgroundColor: ringColor }}>{ringScore}</strong>
        </div>
        <div className="badge-row">
          <StatusBadge label="Soil" className={result.soil_health.class} />
          <StatusBadge label="Contamination" className={contaminationClass} />
          <StatusBadge label="Water" className={result.water_quality.class} />
          <StatusBadge label="Overall" className={ensembleClass} />
          <span className="badge neutral">Confidence: {Math.round(result.ensemble.confidence * 100)}%</span>
          {result.location_match && (
            <span className="badge neutral">
              Nearest: {result.location_match.village}, {result.location_match.distance_km} km
            </span>
          )}
        </div>
        <p>{result.contamination.drivers.join("; ")}.</p>
      </article>

      <article className="result-card">
        <h2>Recommendations</h2>
        <ul className="recommendation-list">
          {result.recommendations.map((rec) => (
            <li key={rec.title} className={`priority-${rec.priority.toLowerCase()}`}>
              <strong>{rec.title}</strong>
              <span>{rec.action}</span>
              <em>{rec.reason}</em>
            </li>
          ))}
        </ul>
      </article>

      <article className="result-card">
        <h2>Crop Plan</h2>
        <p className={`badge ${result.crop_plan.status === "ready" ? "severity-good" : "severity-high"}`}>
          {result.crop_plan.status}
        </p>
        <ul className="crop-list">
          {result.crop_plan.crops.map((crop) => (
            <li key={crop.crop}>
              <strong>{crop.crop}</strong> <span>{crop.match}% match</span>
            </li>
          ))}
        </ul>
      </article>
    </section>
  );
}
