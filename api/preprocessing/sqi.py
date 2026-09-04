import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from typing import Tuple, List, Dict

def pca_select_mds(df: pd.DataFrame, variance_threshold: float = 0.05, within: float = 0.10) -> Tuple[List[str], Dict[str, float]]:
    """
    Select the Minimum Data Set (MDS) using PCA.
    Retains PCs with eigenvalue >= 1 and >= variance_threshold (5%).
    Within each PC, keeps indicators with |loading| >= (1 - within) * max|loading|.
    Returns selected columns and their PCA-derived weights (communality / sum).
    """
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df)
    
    pca = PCA()
    pca.fit(scaled_data)
    
    eigenvalues = pca.explained_variance_
    variance_ratios = pca.explained_variance_ratio_
    
    # Retain PCs
    valid_pcs = np.where((eigenvalues >= 1.0) & (variance_ratios >= variance_threshold))[0]
    
    selected_indicators = set()
    loadings = pca.components_
    
    # For weights, compute communality of selected indicators across valid PCs
    communalities = np.sum(loadings[valid_pcs, :] ** 2, axis=0)
    
    indicator_weights = {}
    cols = df.columns
    
    for i in valid_pcs:
        pc_loadings = np.abs(loadings[i])
        max_loading = np.max(pc_loadings)
        threshold = max_loading * (1 - within)
        
        candidates = np.where(pc_loadings >= threshold)[0]
        # To avoid multicollinearity in a real pipeline, we'd check for correlation > 0.6.
        for c in candidates:
            selected_indicators.add(c)
            
    selected_cols = [cols[i] for i in selected_indicators]
    
    # Weights = communality / sum(communalities)
    total_communality = np.sum([communalities[i] for i in selected_indicators])
    for i in selected_indicators:
        indicator_weights[cols[i]] = communalities[i] / total_communality
        
    return selected_cols, indicator_weights


def score_sigmoid(x: pd.Series, direction: str, x0: float, b: float = 2.5) -> pd.Series:
    """
    Non-linear sigmoidal scoring.
    direction: 'higher' (more is better) or 'lower' (less is better)
    x0: mean or baseline
    """
    b_val = -b if direction == 'higher' else b
    # Avoid zero division and negative power issues
    epsilon = 1e-6
    x = x + epsilon
    x0 = x0 + epsilon
    x_ratio = x / x0
    return 1.0 / (1.0 + np.power(x_ratio, b_val))


def compute_sqi_weighted(df: pd.DataFrame, mds_columns: List[str], weights: Dict[str, float], directions: Dict[str, str]) -> pd.Series:
    """
    Compute the Weighted Additive Index (WAI) SQI.
    """
    sqi = pd.Series(0.0, index=df.index)
    for col in mds_columns:
        x0 = df[col].mean()
        direction = directions.get(col, "higher")
        scored = score_sigmoid(df[col], direction=direction, x0=x0)
        sqi += scored * weights[col]
    return sqi
