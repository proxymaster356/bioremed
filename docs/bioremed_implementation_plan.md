# Data Processing System & Prediction Upgrade Plan

## Current System State
Upon reviewing the codebase (`api/preprocessing/data_pipeline.py`, `api/models/random_forest.py`, and `api/models/ensemble.py`), here is how the data processing system is currently operating:
1. **Data Ingestion**: Reads static CSVs (e.g., `soil_data.csv`, `ground_water_quality_*.csv`) and real soil survey data from Bardhaman. 
2. **Feature Extraction (`build_feature_vector`)**: Mappings extract standard soil metrics (pH, N, P, K, organic matter, bulk density, CEC, EC).
3. **Soil Health Prediction (`SoilHealthModel`)**: Despite being located in `random_forest.py`, it is currently a **hardcoded rule-based Weighted Additive Index**. It maps values using arbitrary band scoring and sums them with hardcoded weights (e.g., pH: 0.16, N: 0.11). It is not a trained ML model.
4. **Ensemble Prediction (`EnsembleModel`)**: It does not use ensemble ML (like Bates-Granger or NNLS). Instead, it applies a simple, hardcoded weighted sum of categorical risk indices from the component models (35% soil + 40% contamination + 20% sensor + 5% trend), alongside a manual escalation rule for severe contamination.

## Upgrade Roadmap Based on Skills

### 1. Soil Quality Index (`/soil-quality-index`)
The current Soil Health Model relies on arbitrary weights and includes all features without a selection strategy.
**Upgrade**: Implement a defensible, data-driven SQI.
- **Minimum Data Set (MDS)**: Use PCA or Network Analysis to select independent indicators, ensuring they are grouped by the five ecosystem functions (EMDS).
- **Scoring**: Define explicit linear or non-linear scoring functions (e.g., `score_sigmoid` with `b=2.5`).
- **Aggregation**: Replace the hardcoded weights with data-derived weights (e.g., from CFA/PCA).

### 2. Soil Prediction Models (`/ml-for-soil-prediction`)
For predicting soil properties or classifying soil health from covariates:
**Upgrade**: Replace the mock rule-based classes with actual trained ML models.
- **Model Choice**: Use a tuned Random Forest (RF) or Quantile Regression Forest (QRF) to provide robust predictions and per-pixel uncertainty (prediction intervals).
- **Validation**: Implement spatial cross-validation (e.g., block CV) to avoid overfitting due to spatial autocorrelation. Stop relying on in-sample R².

### 3. Ensemble ML (`/ensemble-ml-for-soil`)
The current ensemble is an unvalidated simple average which is blind to the error covariance of the underlying models.
**Upgrade**: Compute the honest gain of ensembling before blindly stacking.
- **Evaluate Diversity**: Evaluate the out-of-fold error correlation matrix to see if the base models actually disagree in a way that an ensemble can exploit.
- **Combiner**: If sufficient diversity exists, cross-fit a constrained combiner like full Bates-Granger or Non-Negative Least Squares (NNLS). Never use an unconstrained linear regression (Granger-Ramanathan).

## User Review Required

> [!IMPORTANT]
> The current system uses mock/hardcoded rules instead of actual Machine Learning. Upgrading to real ML models will require defining training datasets, targets, and cross-validation folds. Please review the upgrade roadmap above.

## Open Questions (Grill Me)

> [!NOTE]
> To execute your `/grill-me` request, we need to resolve the design tree step-by-step. I will ask questions one at a time. Let's start with the most consequential decision regarding the Soil Quality Index (SQI).

**Question 1: What is the primary objective of our Soil Quality Index?**
The objective dictates our entire Minimum Data Set (MDS) selection and critical limits strategy. Are we trying to:
- **A)** Compare land uses / management practices across the sites.
- **B)** Quantify soil degradation as a fraction of function lost (requires a known, non-degraded reference soil).
- **C)** Optimize balanced fertilization (which we would validate against crop yield).

*(Recommended: **A**, since the current system assesses generalized risk/health across varying sites. If we choose A, we will proceed with PCA-MDS and non-linear scoring.)*

Please let me know your choice or thoughts, and we will proceed to the next design decision.
