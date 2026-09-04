export function formToPayload(form) {
  const payload = {};
  new FormData(form).forEach((value, key) => {
    const numeric = Number(value);
    payload[key] = Number.isFinite(numeric) && value !== "" ? numeric : value;
  });
  return payload;
}

export function renderPredictionSummary(target, result) {
  const score = result.soil_health.score;
  const scoreColor = score < 50 ? "#b82e37" : score < 68 ? "#c48216" : "#17715b";
  target.innerHTML = `
    <h2>Condition Prediction</h2>
    <div class="score-ring" style="--score:${score}%; background: conic-gradient(${scoreColor} ${score}%, #eef4ee 0)">
      <strong style="background:${scoreColor}">${score}</strong>
    </div>
    <div class="badge-row">
      <span class="badge">Soil: ${result.soil_health.class}</span>
      <span class="badge">Contamination: ${result.contamination.class}</span>
      <span class="badge">Water: ${result.water_quality.class}</span>
      <span class="badge">Overall: ${result.ensemble.class}</span>
      <span class="badge">Confidence: ${Math.round(result.ensemble.confidence * 100)}%</span>
      ${result.location_match ? `<span class="badge">Nearest: ${result.location_match.village}, ${result.location_match.distance_km} km</span>` : ""}
    </div>
    <p>${result.contamination.drivers.join("; ")}.</p>
  `;
}
