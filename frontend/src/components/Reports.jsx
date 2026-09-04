import { severityColor, worstClass } from "../lib/severity.js";

export default function Reports({ report }) {
  const exportReport = () => {
    const blob = new Blob([JSON.stringify(report ?? {}, null, 2)], { type: "application/json" });
    const anchor = document.createElement("a");
    anchor.href = URL.createObjectURL(blob);
    anchor.download = "bioremediation-assessment.json";
    anchor.click();
    URL.revokeObjectURL(anchor.href);
  };

  const overall = report && !report.error ? report.ensemble.class : null;
  const tone = overall ? { color: severityColor(worstClass([overall, report.contamination.class])) } : undefined;

  return (
    <section className="view active">
      <article className="panel full">
        <div className="panel-heading">
          <h2>Assessment Report</h2>
          <div>
            {overall && (
              <span className="badge" style={{ backgroundColor: severityColor(overall), marginRight: "0.6rem" }}>
                Overall: {overall}
              </span>
            )}
            <button className="secondary-action" type="button" onClick={exportReport}>Export JSON</button>
          </div>
        </div>
        {overall && (
          <p className="muted" style={tone}>
            Latest assessment: soil <strong>{report.soil_health.class}</strong>, contamination{" "}
            <strong style={tone}>{report.contamination.class}</strong> ({report.contamination.pollutant} at{" "}
            {report.contamination.concentration_mg_kg} mg/kg), overall <strong style={tone}>{overall}</strong>.
          </p>
        )}
        <pre className="report-box">
          {report && !report.error ? JSON.stringify(report, null, 2) : "Run an assessment to generate a report."}
        </pre>
      </article>
    </section>
  );
}
