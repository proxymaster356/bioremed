import { useState } from "react";
import PredictionResults from "./PredictionResults.jsx";
import { nearestSoil, sendSensorEvent } from "../lib/api.js";

const INITIAL_FORM = {
  n: "72", p: "38", k: "190", ph: "6.6", organic_matter: "2.4", moisture: "24",
  pollutant_type: "Lead", pollutant_concentration: "95", ec: "2.8", cec: "18",
  tds: "720", nitrate: "32", temperature: "28", humidity: "62", rainfall: "88",
  texture: "loamy", latitude: "23.78745", longitude: "86.91507",
};

function formToPayload(form) {
  const payload = {};
  new FormData(form).forEach((value, key) => {
    const numeric = Number(value);
    payload[key] = Number.isFinite(numeric) && value !== "" ? numeric : value;
  });
  return payload;
}

export default function PredictionForm({ latestReport, onAssess }) {
  const [locationStatus, setLocationStatus] = useState("Manual coordinates ready.");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const applySite = (result) => {
    const form = document.querySelector("#assessment-form");
    const setField = (name, value) => {
      if (value === undefined || value === null || value === "") return;
      const field = form.elements[name];
      if (!field) return;
      if (field.tagName === "SELECT" && !Array.from(field.options).some((option) => option.value === String(value))) {
        field.add(new Option(String(value), String(value)));
      }
      field.value = value;
    };
    const features = result.site.features;
    ["latitude", "longitude", "n", "p", "k", "ph", "organic_matter", "ec", "texture"].forEach((key) => setField(key, features[key]));
    setLocationStatus(`Loaded ${result.site.village}, ${result.site.block}, ${result.site.district} (${result.site.distance_km} km away).`);
  };

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await onAssess(formToPayload(event.currentTarget));
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setBusy(false);
    }
  };

  const loadNearestSoil = async () => {
    const form = document.querySelector("#assessment-form");
    const payload = formToPayload(form);
    if (!Number.isFinite(Number(payload.latitude)) || !Number.isFinite(Number(payload.longitude))) {
      setLocationStatus("Enter valid latitude and longitude first.");
      return;
    }
    setLocationStatus("Finding nearest Bardhaman village soil record…");
    try {
      applySite(await nearestSoil(payload));
    } catch (loadError) {
      setLocationStatus(loadError.message);
    }
  };

  const useCurrentLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus("Current location is not available in this browser.");
      return;
    }
    setLocationStatus("Requesting current location…");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const form = document.querySelector("#assessment-form");
        form.elements.latitude.value = position.coords.latitude.toFixed(6);
        form.elements.longitude.value = position.coords.longitude.toFixed(6);
        setLocationStatus("Location captured. Click 'Load Nearest Village Soil' to enrich the assessment.");
      },
      (geoError) => setLocationStatus(geoError.message || "Location permission was not granted."),
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 },
    );
  };

  const sendSensor = async () => {
    setError("");
    try {
      const form = document.querySelector("#assessment-form");
      await sendSensorEvent(formToPayload(form));
      setLocationStatus("Sensor event stored.");
    } catch (sensorError) {
      setError(sensorError.message);
    }
  };

  const numberField = (name, label) => (
    <label>{label}<input name={name} type="number" defaultValue={INITIAL_FORM[name]} step="any" /></label>
  );

  return (
    <section className="view active">
      <form className="assessment-form" id="assessment-form" onSubmit={submit}>
        <section className="form-section">
          <h2>Soil Chemistry</h2>
          {numberField("n", "Nitrogen ppm")}
          {numberField("p", "Phosphorus ppm")}
          {numberField("k", "Potassium ppm")}
          {numberField("ph", "pH")}
          {numberField("organic_matter", "Organic matter %")}
          {numberField("moisture", "Moisture %")}
        </section>

        <section className="form-section">
          <h2>Contamination &amp; Water</h2>
          <label>Pollutant
            <select name="pollutant_type" defaultValue={INITIAL_FORM.pollutant_type}>
              <option>Lead</option><option>Cadmium</option><option>Arsenic</option>
              <option>Mercury</option><option>Hydrocarbon</option><option>Pesticide</option>
            </select>
          </label>
          {numberField("pollutant_concentration", "Concentration mg/kg")}
          {numberField("ec", "Electrical conductivity")}
          {numberField("cec", "CEC")}
          {numberField("tds", "TDS")}
          {numberField("nitrate", "Nitrate")}
        </section>

        <section className="form-section">
          <h2>Climate &amp; Site</h2>
          {numberField("temperature", "Temperature C")}
          {numberField("humidity", "Humidity %")}
          {numberField("rainfall", "Rainfall mm")}
          <label>Soil texture
            <select name="texture" defaultValue={INITIAL_FORM.texture}>
              <option>loamy</option><option>sandy</option><option>clay</option><option>silty</option>
              <option>Loam</option><option>Silt Loam</option><option>Gravelly Loam</option>
            </select>
          </label>
          {numberField("latitude", "Latitude")}
          {numberField("longitude", "Longitude")}
          <div className="location-actions">
            <button className="secondary-action" type="button" onClick={useCurrentLocation}>Use Current Location</button>
            <button className="secondary-action" type="button" onClick={loadNearestSoil}>Load Nearest Village Soil</button>
          </div>
          <div className="location-status">{locationStatus}</div>
        </section>

        <div className="form-actions">
          <button className="primary-action" type="submit" disabled={busy}>{busy ? "Assessing…" : "Assess Site"}</button>
          <button className="secondary-action" type="button" onClick={sendSensor}>Send Sensor Event</button>
        </div>
      </form>

      {error && <p className="error-text">{error}</p>}
      <PredictionResults result={latestReport} />
    </section>
  );
}
