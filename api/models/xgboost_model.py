from __future__ import annotations


POLLUTANT_THRESHOLDS = {
    "lead": [40, 80, 150, 300],
    "cadmium": [1, 3, 6, 12],
    "arsenic": [10, 20, 40, 80],
    "mercury": [0.5, 1, 2, 5],
    "chromium": [50, 100, 180, 320],
    "pesticide": [5, 20, 60, 120],
    "hydrocarbon": [100, 500, 1000, 2500],
}


class ContaminationModel:
    """Tabular contamination predictor used as the prototype XGBoost adapter."""

    classes = ["Clean", "Low", "Moderate", "High", "Severe"]

    def predict(self, features: dict) -> dict:
        pollutant = str(features.get("pollutant_type", "Lead")).lower()
        thresholds = next((values for key, values in POLLUTANT_THRESHOLDS.items() if key in pollutant), [25, 75, 150, 300])
        concentration = float(features.get("pollutant_concentration", 0.0))
        idx = sum(concentration > threshold for threshold in thresholds)
        idx = min(idx, len(self.classes) - 1)
        environmental_pressure = 0
        environmental_pressure += 1 if features["ph"] < 5.5 or features["ph"] > 8.5 else 0
        environmental_pressure += 1 if features["organic_matter"] < 2.0 else 0
        environmental_pressure += 1 if features["ec"] > 4.0 else 0
        adjusted_idx = min(idx + (1 if environmental_pressure >= 2 else 0), len(self.classes) - 1)
        confidence = min(0.95, 0.55 + 0.08 * adjusted_idx + 0.04 * environmental_pressure)
        return {
            "pollutant": features.get("pollutant_type", "Lead"),
            "concentration_mg_kg": round(concentration, 2),
            "class": self.classes[adjusted_idx],
            "confidence": round(confidence, 2),
            "drivers": self._drivers(features, thresholds),
        }

    def _drivers(self, features: dict, thresholds: list[float]) -> list[str]:
        drivers = []
        if features["pollutant_concentration"] > thresholds[1]:
            drivers.append("pollutant concentration exceeds moderate threshold")
        if features["ph"] < 5.5:
            drivers.append("acidic pH increases contaminant mobility")
        if features["ph"] > 8.5:
            drivers.append("alkaline pH can reduce nutrient availability")
        if features["organic_matter"] < 2:
            drivers.append("low organic matter limits microbial degradation")
        if features["ec"] > 4:
            drivers.append("salinity stress indicated by high EC")
        return drivers or ["contamination pressure is within expected operating range"]

