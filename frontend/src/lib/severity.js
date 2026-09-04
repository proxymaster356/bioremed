// Severity ordering and color mapping shared by badges, banner, ring, and map.
export const DANGER_CLASSES = new Set(["Critical", "Poor", "Severe", "High", "Unsafe"]);

export const CLASS_COLOR = {
  Critical: "#b82e37",
  Severe: "#b82e37",
  High: "#d3542c",
  Unsafe: "#b82e37",
  Poor: "#d3542c",
  Elevated: "#c48216",
  Moderate: "#c48216",
  Watch: "#c48216",
  Low: "#5a8f3d",
  Good: "#17715b",
  Stable: "#17715b",
  Clean: "#17715b",
  Excellent: "#17715b",
};

const FALLBACK = "#5f6f65";

export function severityColor(className) {
  return CLASS_COLOR[className] || FALLBACK;
}

export function isDangerous(className) {
  return DANGER_CLASSES.has(className);
}

// Picks the worst class from a list, using the overall soil/ensemble ranking.
const RANKING = ["Excellent", "Good", "Clean", "Low", "Stable", "Moderate", "Watch", "Elevated", "Poor", "High", "Unsafe", "Critical", "Severe"];

export function worstClass(classes) {
  let worst = classes[0];
  for (const cls of classes) {
    if (RANKING.indexOf(cls) > RANKING.indexOf(worst)) worst = cls;
  }
  return worst;
}
