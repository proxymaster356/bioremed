from __future__ import annotations

from typing import Any


ALIASES = {
    "n": ["n", "nitrogen", "nitrogen_n_ppm", "Nitrogen_N_ppm", "N"],
    "p": ["p", "phosphorus", "phosphorus_p_ppm", "Phosphorus_P_ppm", "P"],
    "k": ["k", "potassium", "potassium_k_ppm", "Potassium_K_ppm", "K"],
    "ph": ["ph", "pH", "Soil_pH", "soil_ph"],
    "organic_matter": ["organic_matter", "organic_matter_percent", "Organic_Matter_%", "Soil_Organic_Matter_%"],
    "moisture": ["moisture", "moisture_percent", "Moisture_Content_%", "Moisture"],
    "bulk_density": ["bulk_density", "Bulk_Density_g/cm³", "Bulk_Density_g/cmÂ³"],
    "ec": ["ec", "electrical_conductivity", "Electrical_Conductivity_dS/m", "E.C", "Conductivity"],
    "cec": ["cec", "Cation_Exchange_Capacity_meq/100g"],
    "temperature": ["temperature", "Temperature_C", "temperature_c", "Temperature"],
    "humidity": ["humidity", "Humidity_%", "humidity_percent", "Humidity"],
    "rainfall": ["rainfall", "Rainfall_mm", "rainfall_mm", "Rainfall"],
    "pollutant_type": ["pollutant_type", "Pollutant_Type"],
    "pollutant_concentration": ["pollutant_concentration", "Pollutant_Concentration_mg_kg"],
    "texture": ["texture", "Texture", "Soil_Texture", "soil_type"],
    "tds": ["tds", "TDS", "Solids"],
    "turbidity": ["turbidity", "Turbidity"],
    "nitrate": ["nitrate", "NO3", "NO3 "],
    "latitude": ["latitude", "lat", "Location_Latitude", "lat_gis"],
    "longitude": ["longitude", "long", "lng", "Location_Longitude", "long_gis"],
}


DEFAULT_FEATURES = {
    "n": 80.0,
    "p": 35.0,
    "k": 180.0,
    "ph": 6.8,
    "organic_matter": 3.2,
    "moisture": 28.0,
    "bulk_density": 1.25,
    "ec": 1.2,
    "cec": 18.0,
    "temperature": 27.0,
    "humidity": 62.0,
    "rainfall": 90.0,
    "pollutant_type": "Lead",
    "pollutant_concentration": 45.0,
    "texture": "loamy",
    "tds": 500.0,
    "turbidity": 3.0,
    "nitrate": 35.0,
    "latitude": 19.5,
    "longitude": 78.5,
}


def safe_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def first_present(data: dict[str, Any], names: list[str]) -> Any:
    for name in names:
        if name in data and data[name] not in (None, ""):
            return data[name]
    return None


def build_feature_vector(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize API payloads or CSV rows into one feature dictionary."""
    features: dict[str, Any] = {}
    for key, aliases in ALIASES.items():
        value = first_present(payload, aliases)
        if value is None:
            value = DEFAULT_FEATURES[key]
        if isinstance(DEFAULT_FEATURES[key], float):
            value = safe_float(value, DEFAULT_FEATURES[key])
        features[key] = value
    return features


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def band_score(value: float, ideal_low: float, ideal_high: float, hard_low: float, hard_high: float) -> float:
    """Score a value from 0 to 100 based on ideal and tolerable bands."""
    if ideal_low <= value <= ideal_high:
        return 100.0
    if value < ideal_low:
        return clamp((value - hard_low) / (ideal_low - hard_low) * 100.0, 0.0, 100.0)
    return clamp((hard_high - value) / (hard_high - ideal_high) * 100.0, 0.0, 100.0)

