from __future__ import annotations

import csv
from functools import lru_cache
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any

from api.preprocessing.feature_store import safe_float


DATA_DIR = Path(__file__).resolve().parents[2] / "extracted_data"
NORMALIZED_CSV = DATA_DIR / "bardhaman_village_soil_normalized.csv"
FILES = [
    DATA_DIR / "paschim_bardhaman_village_soil_dataset_lat_long.xlsx",
    DATA_DIR / "purba_bardhaman_soil_dataset_lat_long.xlsx",
]


def _value(row: dict[str, Any], key: str, default: Any = None) -> Any:
    value = row.get(key, default)
    if value in (None, ""):
        return default
    return value


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _nutrient_ppm(kg_ha: float) -> float:
    return round(kg_ha / 2.24, 2)


def _normalize_row(row: dict[str, Any], source_file: str) -> dict[str, Any]:
    n_kg_ha = safe_float(_value(row, "Nitrogen (N - kg/ha)"))
    p_kg_ha = safe_float(_value(row, "Phosphorus (P - kg/ha)"))
    k_kg_ha = safe_float(_value(row, "Potassium (K - kg/ha)"))
    organic_carbon = safe_float(_value(row, "Organic Carbon (%)"))
    mining_zone = _bool_value(_value(row, "Is_Mining_Zone", False))
    features = {
        "n": _nutrient_ppm(n_kg_ha),
        "p": _nutrient_ppm(p_kg_ha),
        "k": _nutrient_ppm(k_kg_ha),
        "n_kg_ha": round(n_kg_ha, 2),
        "p_kg_ha": round(p_kg_ha, 2),
        "k_kg_ha": round(k_kg_ha, 2),
        "ph": safe_float(_value(row, "pH"), 6.8),
        "ec": safe_float(_value(row, "EC (dS/m)"), 0.0),
        "organic_carbon": round(organic_carbon, 3),
        "organic_matter": round(organic_carbon * 1.724, 3),
        "texture": str(_value(row, "Texture", "loamy")),
        "latitude": safe_float(_value(row, "Latitude")),
        "longitude": safe_float(_value(row, "Longitude")),
        "mining_zone": mining_zone,
        "soil_depth": str(_value(row, "Soil Depth", "")),
        "slope_class": str(_value(row, "Slope Class", "")),
        "erosion_class": str(_value(row, "Erosion Class", "")),
        "zinc": safe_float(_value(row, "Zinc (Zn - ppm)"), 0.0),
        "iron": safe_float(_value(row, "Iron (Fe - ppm)"), 0.0),
        "copper": safe_float(_value(row, "Copper (Cu - ppm)"), 0.0),
        "manganese": safe_float(_value(row, "Manganese (Mn - ppm)"), 0.0),
        "boron": safe_float(_value(row, "Boron (B - ppm)"), 0.0),
    }
    return {
        "id": f"{_value(row, 'District')}-{_value(row, 'Block')}-{_value(row, 'Village')}",
        "state": str(_value(row, "State", "")),
        "district": str(_value(row, "District", "")),
        "block": str(_value(row, "Block", "")),
        "village": str(_value(row, "Village", "")),
        "source_file": source_file,
        "features": features,
        **features,
    }


@lru_cache(maxsize=1)
def load_bardhaman_rows() -> list[dict[str, Any]]:
    if NORMALIZED_CSV.exists():
        return _load_normalized_csv()

    rows: list[dict[str, Any]] = []
    for path in FILES:
        if not path.exists():
            continue
        try:
            import pandas as pd

            frame = pd.read_excel(path)
            frame = frame.where(pd.notnull(frame), None)
            rows.extend(_normalize_row(row, path.name) for row in frame.to_dict(orient="records"))
        except ImportError:
            continue
    return rows


def _load_normalized_csv() -> list[dict[str, Any]]:
    with NORMALIZED_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [_normalize_row(row, row.get("source_file", NORMALIZED_CSV.name)) for row in reader]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return radius * 2 * asin(sqrt(a))


def nearest_bardhaman_site(latitude: float, longitude: float) -> dict[str, Any] | None:
    rows = load_bardhaman_rows()
    if not rows:
        return None
    nearest = min(rows, key=lambda row: haversine_km(latitude, longitude, row["latitude"], row["longitude"]))
    distance = haversine_km(latitude, longitude, nearest["latitude"], nearest["longitude"])
    return {**nearest, "distance_km": round(distance, 2)}


def bardhaman_sites() -> list[dict[str, Any]]:
    return [
        {
            "id": row["id"],
            "district": row["district"],
            "block": row["block"],
            "village": row["village"],
            "lat": row["latitude"],
            "lng": row["longitude"],
            "ph": row["ph"],
            "ec": row["ec"],
            "organic_carbon": row["organic_carbon"],
            "n_kg_ha": row["n_kg_ha"],
            "p_kg_ha": row["p_kg_ha"],
            "k_kg_ha": row["k_kg_ha"],
            "mining_zone": row["mining_zone"],
            "texture": row["texture"],
        }
        for row in load_bardhaman_rows()
    ]


def bardhaman_summary() -> dict[str, Any]:
    rows = load_bardhaman_rows()
    districts: dict[str, dict[str, Any]] = {}
    for row in rows:
        district = row["district"]
        item = districts.setdefault(
            district,
            {
                "district": district,
                "villages": 0,
                "blocks": set(),
                "ph": [],
                "organic_carbon": [],
                "n_kg_ha": [],
                "p_kg_ha": [],
                "k_kg_ha": [],
                "acidic_villages": 0,
                "low_organic_carbon_villages": 0,
                "mining_zone_villages": 0,
            },
        )
        item["villages"] += 1
        item["blocks"].add(row["block"])
        for key in ["ph", "organic_carbon", "n_kg_ha", "p_kg_ha", "k_kg_ha"]:
            item[key].append(row[key])
        item["acidic_villages"] += 1 if row["ph"] < 5.5 else 0
        item["low_organic_carbon_villages"] += 1 if row["organic_carbon"] < 0.5 else 0
        item["mining_zone_villages"] += 1 if row["mining_zone"] else 0
    clean = []
    for item in districts.values():
        clean.append(
            {
                "district": item["district"],
                "villages": item["villages"],
                "blocks": len(item["blocks"]),
                "avg_ph": round(sum(item["ph"]) / len(item["ph"]), 2),
                "avg_organic_carbon": round(sum(item["organic_carbon"]) / len(item["organic_carbon"]), 2),
                "avg_n_kg_ha": round(sum(item["n_kg_ha"]) / len(item["n_kg_ha"]), 1),
                "avg_p_kg_ha": round(sum(item["p_kg_ha"]) / len(item["p_kg_ha"]), 1),
                "avg_k_kg_ha": round(sum(item["k_kg_ha"]) / len(item["k_kg_ha"]), 1),
                "acidic_villages": item["acidic_villages"],
                "low_organic_carbon_villages": item["low_organic_carbon_villages"],
                "mining_zone_villages": item["mining_zone_villages"],
            }
        )
    return {"total_villages": len(rows), "districts": sorted(clean, key=lambda item: item["district"])}
