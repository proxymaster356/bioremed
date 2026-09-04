import numpy as np
from scipy.optimize import nnls

RISK_INDEX = {
    "Critical": 4,
    "Poor": 3,
    "Moderate": 2,
    "Good": 1,
    "Excellent": 0,
    "Clean": 0,
    "Low": 1,
    "High": 3,
    "Severe": 4,
    "Stable": 0,
    "Watch": 1,
    "Elevated": 2,
}

CLASS_RANK = {"Excellent": 0, "Good": 1, "Moderate": 2, "Poor": 3, "Critical": 4}

CONTAMINATION_OVERRIDE = {"High": "Poor", "Severe": "Critical"}

class EnsembleModel:
    """
    Weighted meta-learner. Upgraded to support constrained optimization (NNLS/Bates-Granger)
    using out-of-fold predictions, as per ensemble-ml-for-soil guidelines.
    """
    def __init__(self):
        # In a fully deployed ML system, these weights are fitted via NNLS
        # using the out-of-fold predictions matrix (Z) to find optimal constrained weights.
        # Fallback to the domain-expert weights if not fitted:
        self.weights = np.array([0.35, 0.40, 0.20, 0.05])
        
    def fit_weights(self, Z: np.ndarray, y: np.ndarray):
        """
        Fit weights using Non-Negative Least Squares to ensure convexity and stability.
        Z: Out-of-fold predictions matrix of shape (n_samples, n_models)
        y: True target vector
        """
        w, _ = nnls(Z, y)
        self.weights = w / np.sum(w)
        return self.weights

    def predict(self, soil: dict, contamination: dict, sensor: dict, trend: dict | None = None) -> dict:
        soil_risk = RISK_INDEX.get(soil.get("class", "Moderate"), 2)
        contamination_risk = RISK_INDEX.get(contamination.get("class", "Moderate"), 2)
        sensor_risk = RISK_INDEX.get(sensor.get("pattern_class", "Watch"), 1)
        trend_risk = 1 if trend and trend.get("direction") == "degrading" else 0
        
        inputs = np.array([soil_risk, contamination_risk, sensor_risk, trend_risk])
        risk = np.dot(inputs, self.weights)
        
        if risk >= 3.25:
            final = "Critical"
        elif risk >= 2.4:
            final = "Poor"
        elif risk >= 1.5:
            final = "Moderate"
        elif risk >= 0.7:
            final = "Good"
        else:
            final = "Excellent"
            
        final = self._escalate(final, contamination.get("class", "Clean"))
        confidence = min(0.96, 0.62 + abs(risk - 2) * 0.08)
        
        return {"class": final, "risk_score": round(float(risk) * 25, 1), "confidence": round(confidence, 2)}

    def _escalate(self, final: str, contamination_class: str) -> str:
        override = CONTAMINATION_OVERRIDE.get(contamination_class)
        if override is None:
            return final
        return override if CLASS_RANK[override] > CLASS_RANK[final] else final
