from __future__ import annotations


class SensorPatternModel:
    """Lightweight sensor-pattern adapter mirroring the planned 1D-CNN output."""

    def predict(self, features: dict) -> dict:
        anomalies = []
        if features["moisture"] < 15:
            anomalies.append("dry-soil stress")
        if features["ec"] > 4:
            anomalies.append("salinity spike")
        if features["temperature"] > 38 and features["humidity"] < 35:
            anomalies.append("heat and low-humidity stress")
        if features["tds"] > 1000:
            anomalies.append("high dissolved solids")
        if features["nitrate"] > 45:
            anomalies.append("nitrate pressure")
        severity = min(len(anomalies), 4)
        return {
            "pattern_class": ["Stable", "Watch", "Elevated", "High", "Severe"][severity],
            "anomalies": anomalies,
            "activation_channels": self._activation_channels(features),
        }

    def _activation_channels(self, features: dict) -> dict:
        return {
            "soil": round(min(1.0, (abs(features["ph"] - 7.0) / 2.5 + features["ec"] / 8.0) / 2), 2),
            "nutrients": round(min(1.0, (abs(features["n"] - 100) / 160 + abs(features["p"] - 45) / 80) / 2), 2),
            "water": round(min(1.0, (features["tds"] / 1800 + features["turbidity"] / 8) / 2), 2),
        }

