import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.preprocessing.data_pipeline import soil_sample
from api.preprocessing.feature_store import build_feature_vector
from api.preprocessing.sqi import pca_select_mds, compute_sqi_weighted

def train_sqi_model():
    print("Loading soil samples...")
    raw_data = soil_sample()
    if not raw_data:
        print("No data found in soil_data.csv")
        return

    features_list = [build_feature_vector(row) for row in raw_data]
    df = pd.DataFrame(features_list)
    
    soil_cols = ['ph', 'n', 'p', 'k', 'organic_matter', 'moisture', 'bulk_density', 'ec', 'cec']
    df_soil = df[soil_cols].dropna()
    
    if len(df_soil) == 0:
        print("No valid rows after dropping NAs")
        return

    print("Computing PCA-based SQI...")
    mds_cols, weights = pca_select_mds(df_soil)
    print(f"Selected MDS: {mds_cols}")
    print(f"Weights: {weights}")
    
    directions = {
        'ph': 'higher',
        'n': 'higher',
        'p': 'higher',
        'k': 'higher',
        'organic_matter': 'higher',
        'moisture': 'higher',
        'cec': 'higher',
        'bulk_density': 'lower',
        'ec': 'lower'
    }
    
    # Compute SQI (range approx 0 to 1) -> multiply by 100 for 0-100 scale
    sqi_scores = compute_sqi_weighted(df_soil, mds_cols, weights, directions) * 100
    df_soil['sqi_target'] = sqi_scores
    
    print("Training Random Forest Regressor...")
    X = df_soil[soil_cols]
    y = df_soil['sqi_target']
    
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X, y)
    
    model_dir = ROOT / 'api' / 'models'
    model_dir.mkdir(parents=True, exist_ok=True)
    
    rf_path = model_dir / 'soil_rf_model.joblib'
    joblib.dump(rf, rf_path)
    
    params_path = model_dir / 'sqi_params.joblib'
    joblib.dump({'mds': mds_cols, 'weights': weights, 'directions': directions}, params_path)
    
    print(f"Model saved to {rf_path}")
    print("Training complete.")

if __name__ == '__main__':
    train_sqi_model()
