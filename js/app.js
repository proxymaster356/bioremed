import { drawBarChart, drawLineChart, renderMetrics } from "./dashboard.js";
import { renderMap } from "./map.js";
import { formToPayload, renderPredictionSummary } from "./prediction.js";
import { renderCropPlan, renderRecommendations } from "./recommendations.js";

const apiStatus = document.querySelector("#api-status");
const reportBox = document.querySelector("#report-box");
const form = document.querySelector("#assessment-form");
const locationStatus = document.querySelector("#location-status");
let latestReport = null;

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}

async function loadDashboard() {
  const [summary, trends, sites] = await Promise.all([api("/api/summary"), api("/api/trends"), api("/api/sites")]);
  renderMetrics(summary);
  drawBarChart(document.querySelector("#npk-chart"), summary);
  drawLineChart(document.querySelector("#trend-chart"), trends.forecast.forecast);
  document.querySelector("#trend-direction").textContent = trends.forecast.direction;
  renderMap(document.querySelector("#site-map"), sites.sites);
  document.querySelector("#site-count").textContent = `${sites.sites.length} sampled sites`;
}

async function runAssessment(payload) {
  const result = await api("/api/predict", { method: "POST", body: JSON.stringify(payload) });
  latestReport = result;
  renderPredictionSummary(document.querySelector("#prediction-summary"), result);
  renderRecommendations(document.querySelector("#recommendations"), result.recommendations);
  renderCropPlan(document.querySelector("#crop-plan"), result.crop_plan);
  reportBox.textContent = JSON.stringify(result, null, 2);
  return result;
}

function setField(name, value) {
  const field = form.elements[name];
  if (!field || value === undefined || value === null || value === "") return;
  if (field.tagName === "SELECT" && !Array.from(field.options).some((option) => option.value === String(value))) {
    field.add(new Option(String(value), String(value)));
  }
  field.value = value;
}

function applyBardhamanSite(result) {
  const features = result.site.features;
  setField("latitude", features.latitude);
  setField("longitude", features.longitude);
  setField("n", features.n);
  setField("p", features.p);
  setField("k", features.k);
  setField("ph", features.ph);
  setField("organic_matter", features.organic_matter);
  setField("ec", features.ec);
  setField("texture", features.texture);
  latestReport = result.prediction;
  renderPredictionSummary(document.querySelector("#prediction-summary"), result.prediction);
  renderRecommendations(document.querySelector("#recommendations"), result.prediction.recommendations);
  renderCropPlan(document.querySelector("#crop-plan"), result.prediction.crop_plan);
  reportBox.textContent = JSON.stringify(result.prediction, null, 2);
  locationStatus.textContent = `Loaded ${result.site.village}, ${result.site.block}, ${result.site.district} from ${result.site.distance_km} km away.`;
}

async function loadNearestSoil() {
  const payload = formToPayload(form);
  if (!Number.isFinite(Number(payload.latitude)) || !Number.isFinite(Number(payload.longitude))) {
    locationStatus.textContent = "Enter valid latitude and longitude first.";
    return;
  }
  locationStatus.textContent = "Finding nearest Bardhaman village soil record...";
  const result = await api("/api/bardhaman/nearest", { method: "POST", body: JSON.stringify(payload) });
  applyBardhamanSite(result);
}

function useCurrentLocation() {
  if (!navigator.geolocation) {
    locationStatus.textContent = "Current location is not available in this browser.";
    return;
  }
  locationStatus.textContent = "Requesting current location...";
  navigator.geolocation.getCurrentPosition(
    async (position) => {
      setField("latitude", position.coords.latitude.toFixed(6));
      setField("longitude", position.coords.longitude.toFixed(6));
      locationStatus.textContent = "Location captured. Loading nearest village soil record...";
      try {
        await loadNearestSoil();
      } catch (error) {
        locationStatus.textContent = error.message;
      }
    },
    (error) => {
      locationStatus.textContent = error.message || "Location permission was not granted.";
    },
    { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 },
  );
}

function bindNavigation() {
  document.querySelectorAll(".nav-tabs button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".nav-tabs button").forEach((item) => item.classList.remove("active"));
      document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
      button.classList.add("active");
      document.querySelector(`#${button.dataset.view}-view`).classList.add("active");
    });
  });
}

function bindActions() {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await runAssessment(formToPayload(form));
  });
  document.querySelector("#sample-run").addEventListener("click", async () => {
    await runAssessment({});
    document.querySelector('[data-view="prediction"]').click();
  });
  document.querySelector("#send-sensor").addEventListener("click", async () => {
    const result = await api("/api/sensor", { method: "POST", body: JSON.stringify(formToPayload(form)) });
    latestReport = result.prediction;
    reportBox.textContent = JSON.stringify(result, null, 2);
    renderPredictionSummary(document.querySelector("#prediction-summary"), result.prediction);
    renderRecommendations(document.querySelector("#recommendations"), result.prediction.recommendations);
    renderCropPlan(document.querySelector("#crop-plan"), result.prediction.crop_plan);
  });
  document.querySelector("#load-nearest-soil").addEventListener("click", async () => {
    try {
      await loadNearestSoil();
    } catch (error) {
      locationStatus.textContent = error.message;
    }
  });
  document.querySelector("#use-current-location").addEventListener("click", useCurrentLocation);
  document.querySelector("#download-report").addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(latestReport || {}, null, 2)], { type: "application/json" });
    const anchor = document.createElement("a");
    anchor.href = URL.createObjectURL(blob);
    anchor.download = "bioremediation-assessment.json";
    anchor.click();
    URL.revokeObjectURL(anchor.href);
  });
}

async function boot() {
  bindNavigation();
  bindActions();
  try {
    await api("/api/health");
    apiStatus.textContent = "API online";
    await loadDashboard();
    await runAssessment(formToPayload(form));
  } catch (error) {
    apiStatus.textContent = "API offline";
    reportBox.textContent = error.message;
  }
}

boot();
