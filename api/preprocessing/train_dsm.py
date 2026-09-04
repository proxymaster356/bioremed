import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import root_mean_squared_error, r2_score
import sys
import warnings
warnings.filterwarnings('ignore')

# Optional: MLflow tracking (skip gracefully if not installed)
try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    print("[INFO] mlflow not installed — skipping experiment tracking. Model will still be saved.")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.preprocessing.sqi import pca_select_mds, compute_sqi_weighted

DATA_PATH = ROOT.parent / "new data set" / "soil_data.csv"

def prepare_data(sample_size=50000):
    print(f"Loading data from {DATA_PATH}...")
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at: {DATA_PATH}\nPlease verify the path to your soil_data.csv")

    df = pd.read_csv(DATA_PATH)
    print(f"  -> Loaded {len(df):,} total rows.")

    if len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)
        print(f"  -> Sampled {sample_size:,} rows for training.")

    # Rename columns to match what our system expects internally
    rename_map = {
        'pH': 'ph',
        'Organic_Matter_%': 'organic_matter',
        'Moisture_Content_%': 'moisture',
        'Bulk_Density_g/cm³': 'bulk_density',
        'Nitrogen_N_ppm': 'n',
        'Phosphorus_P_ppm': 'p',
        'Potassium_K_ppm': 'k',
        'Cation_Exchange_Capacity_meq/100g': 'cec',
        'Electrical_Conductivity_dS/m': 'ec'
    }
    df = df.rename(columns=rename_map)

    soil_cols = ['ph', 'n', 'p', 'k', 'organic_matter', 'moisture', 'bulk_density', 'ec', 'cec']

    # Only keep columns that actually exist in the dataset
    available = [c for c in soil_cols if c in df.columns]
    missing = [c for c in soil_cols if c not in df.columns]
    if missing:
        print(f"  [WARN] These columns were not found in the dataset: {missing}")
        print(f"         Available columns: {list(df.columns)}")

    df_soil = df[available].dropna()
    print(f"  -> {len(df_soil):,} clean rows after dropping NaN.")
    return df_soil, available


def run_training():
    df_soil, soil_cols = prepare_data()

    print("\nComputing PCA-based SQI (Ground Truth Generation)...")
    mds_cols, weights = pca_select_mds(df_soil)
    print(f"  -> MDS selected features: {mds_cols}")

    directions = {
        'ph': 'higher', 'n': 'higher', 'p': 'higher', 'k': 'higher',
        'organic_matter': 'higher', 'moisture': 'higher', 'cec': 'higher',
        'bulk_density': 'lower', 'ec': 'lower'
    }

    # 0-100 scale
    sqi_scores = compute_sqi_weighted(df_soil, mds_cols, weights, directions) * 100
    df_soil['sqi_target'] = sqi_scores
    print(f"  -> SQI scores: min={sqi_scores.min():.1f}, max={sqi_scores.max():.1f}, mean={sqi_scores.mean():.1f}")

    X = df_soil[soil_cols]
    y = df_soil['sqi_target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"\nTraining Random Forest ({len(X_train):,} samples, {len(soil_cols)} features)...")

    rf = RandomForestRegressor(n_estimators=100, min_samples_leaf=5, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)

    preds = rf.predict(X_test)
    rmse = root_mean_squared_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    print(f"\n=== Training Complete ===")
    print(f"  Validation RMSE : {rmse:.2f}")
    print(f"  R2 Score        : {r2:.3f}")

    # Optional MLflow logging
    if MLFLOW_AVAILABLE:
        mlflow.set_tracking_uri(f"file://{ROOT / 'mlruns'}")
        mlflow.set_experiment("soil-quality-index-prediction")
        with mlflow.start_run():
            mlflow.log_params({"n_estimators": 100, "min_samples_leaf": 5,
                               "sample_size": len(df_soil), "mds_features": mds_cols})
            mlflow.log_metrics({"rmse": rmse, "r2": r2})
        print("  MLflow metrics logged.")

    # Save model and SQI params
    model_dir = ROOT / 'api' / 'models'
    model_dir.mkdir(parents=True, exist_ok=True)

    rf_path = model_dir / 'soil_rf_model.joblib'
    joblib.dump(rf, rf_path)
    print(f"  Model saved to   : {rf_path}")

    params_path = model_dir / 'sqi_params.joblib'
    joblib.dump({'mds': mds_cols, 'weights': weights, 'directions': directions}, params_path)
    print(f"  SQI params saved : {params_path}")
    print("\nDone! Restart the API server to load the new model.")


if __name__ == '__main__':
    run_training()
