export function renderRecommendations(target, recommendations) {
  target.innerHTML = `
    <h2>Remediation Actions</h2>
    <div class="recommendation-list">
      ${recommendations
        .map(
          (item) => `
            <div class="recommendation">
              <span class="badge">${item.priority}</span>
              <strong>${item.title}</strong>
              <p>${item.action}</p>
              <p>${item.reason}</p>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

export function renderCropPlan(target, cropPlan) {
  const status = cropPlan.status === "ready" ? "Ready for crop transition" : "Use after remediation";
  target.innerHTML = `
    <h2>Crop Advisor</h2>
    <span class="badge">${status}</span>
    <div class="crop-list">
      ${(cropPlan.crops || [])
        .map(
          (crop) => `
            <div class="crop">
              <strong>${crop.crop}</strong>
              <p>${crop.match}% match to current soil and climate profile.</p>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

