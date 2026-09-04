const BASE = "";

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = `${response.status}`;
    try {
      const body = await response.json();
      if (body && body.error) detail = body.error;
    } catch {
      /* keep status code */
    }
    throw new Error(`${path} failed: ${detail}`);
  }
  return response.json();
}

export const checkHealth = () => request("/api/health");
export const getSummary = () => request("/api/summary");
export const getTrends = () => request("/api/trends");
export const getSites = () => request("/api/sites");
export const predict = (payload) => request("/api/predict", { method: "POST", body: JSON.stringify(payload) });
export const sendSensorEvent = (payload) => request("/api/sensor", { method: "POST", body: JSON.stringify(payload) });
export const nearestSoil = (payload) => request("/api/bardhaman/nearest", { method: "POST", body: JSON.stringify(payload) });
