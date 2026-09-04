import joblib
from pathlib import Path
import numpy as np
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

class SoilHealthModel:
    """Interpretable soil-health classifier using a trained Random Forest model predicting a PCA-based SQI."""

    classes = ["Critical", "Poor", "Moderate", "Good", "Excellent"]

    def __init__(self):
        model_dir = ROOT / 'api' / 'models'
        self.rf = None
        self.sqi_params = None
        
        rf_path = model_dir / 'soil_rf_model.joblib'
        params_path = model_dir / 'sqi_params.joblib'
        if rf_path.exists() and params_path.exists():
            self.rf = joblib.load(rf_path)
            self.sqi_params = joblib.load(params_path)

    def predict(self, features: dict) -> dict:
        soil_cols = ['ph', 'n', 'p', 'k', 'organic_matter', 'moisture', 'bulk_density', 'ec', 'cec']
        
        if not self.rf or not self.sqi_params:
            return {
                "score": 50.0,
                "class": "Moderate",
                "component_scores": {},
                "top_factors": []
            }

        import pandas as pd
        input_data = np.array([features.get(col, 0.0) for col in soil_cols]).reshape(1, -1)
        input_df = pd.DataFrame(input_data, columns=soil_cols)
        
        # Predict the SQI using the trained Random Forest
        score = self.rf.predict(input_df)[0]
        score = round(max(0.0, min(100.0, score)), 1)
        
        health_class = self._class_from_score(score)
        
        factors = []
        for col in self.sqi_params['mds']:
            factors.append({"factor": col, "score": round(float(self.sqi_params['weights'].get(col, 0.0)) * 100, 1)})
            
        factors = sorted(factors, key=lambda item: item['score'], reverse=True)[:5]

        return {
            "score": score,
            "class": health_class,
            "component_scores": {col: features.get(col, 0.0) for col in soil_cols},
            "top_factors": factors,
        }

    def _class_from_score(self, score: float) -> str:
        if score < 35:
            return "Critical"
        if score < 50:
            return "Poor"
        if score < 68:
            return "Moderate"
        if score < 85:
            return "Good"
        return "Excellent"
