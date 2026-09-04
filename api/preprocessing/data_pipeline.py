from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path
from statistics import mean
from typing import Any

from api.preprocessing.bardhaman_pipeline import bardhaman_sites as bardhaman_site_rows
from api.preprocessing.feature_store import build_feature_vector, safe_float


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "extracted_data"
SENSOR_LOG = ROOT / "models" / "sensor_events.jsonl"


def read_csv_rows(name: str, limit: int | None = None) -> list[dict[str, Any]]:
    path = DATA_DIR / name
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader):
            rows.append(row)
            if limit is not None and index + 1 >= limit:
                break
    return rows


@lru_cache(maxsize=1)
def soil_sample() -> list[dict[str, Any]]:
    return read_csv_rows("soil_data.csv", limit=2500)


@lru_cache(maxsize=1)
def pollution_rows() -> list[dict[str, Any]]:
    return read_csv_rows("soil_pollution_diseases.csv")


@lru_cache(maxsize=1)
def water_rows() -> list[dict[str, Any]]:
    return read_csv_rows("water_potability.csv")


@lru_cache(maxsize=1)
def groundwater_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for year in [2018, 2019, 2020]:
        for row in read_csv_rows(f"ground_water_quality_{year}_post.csv"):
            row["year"] = year
            rows.append(row)
    return rows


def avg(values: list[float], fallback: float = 0.0) -> float:
    clean = [value for value in values if value == value]
    return round(mean(clean), 2) if clean else fallback


def build_summary() -> dict[str, Any]:
    soil = [build_feature_vector(row) for row in soil_sample()]
    pollution = [build_feature_vector(row) for row in pollution_rows()]
    water = water_rows()
    gw = groundwater_rows()
    severe_cases = sum(1 for row in pollution_rows() if str(row.get("Disease_Severity", "")).lower() == "severe")
    potable = sum(1 for row in water if str(row.get("Potability", "")) == "1")
    return {
        "soil_sample_size": len(soil),
        "avg_soil_ph": avg([row["ph"] for row in soil], 7.0),
        "avg_n": avg([row["n"] for row in soil]),
        "avg_p": avg([row["p"] for row in soil]),
        "avg_k": avg([row["k"] for row in soil]),
        "avg_organic_matter": avg([row["organic_matter"] for row in soil]),
        "pollution_cases": len(pollution),
        "severe_pollution_cases": severe_cases,
        "potable_water_rate": round((potable / len(water)) * 100, 1) if water else 0,
        "groundwater_sites": len(gw),
        "last_updated": "local CSV snapshot",
    }


def _site_risk(site: dict[str, Any]) -> float:
    """Composite site-risk score (0-100) from real soil-health drivers."""
    ph = site["ph"]
    oc = site["organic_carbon"]
    ec = site["ec"]
    n, p, k = site["n_kg_ha"], site["p_kg_ha"], site["k_kg_ha"]
    risk = 0.0
    # pH pressure: ideal band centred on 6.75, up to 25 points
    risk += min(25.0, abs(ph - 6.75) * 14)
    # Organic carbon deficit: 0.75% target, up to 25 points
    risk += min(25.0, max(0.0, 0.75 - oc) * 60)
    # Salinity: up to 15 points
    risk += min(15.0, ec * 12)
    # Nutrient fertility bands (kg/ha): N<280 low, P<10 low, K<110 low
    risk += min(15.0, max(0.0, (280 - n) / 280 * 15))
    risk += min(10.0, max(0.0, (10 - p) / 10 * 10))
    risk += min(10.0, max(0.0, (110 - k) / 110 * 10))
    # Industrial/mining pressure
    if site["mining_zone"]:
        risk += 15.0
    return round(min(100.0, risk), 1)


def build_sites(limit: int | None = None) -> list[dict[str, Any]]:
    """Map sites come from the real Bardhaman village soil survey (West Bengal)."""
    rows = bardhaman_site_rows()
    if limit is not None:
        rows = rows[:limit]
    sites = []
    for row in rows:
        sites.append(
            {
                "id": row["id"],
                "village": row["village"],
                "block": row["block"],
                "district": row["district"],
                "lat": row["lat"],
                "lng": row["lng"],
                "ph": round(row["ph"], 2),
                "ec": row["ec"],
                "organic_carbon": row["organic_carbon"],
                "n": round(row["n_kg_ha"], 1),
                "p": round(row["p_kg_ha"], 1),
                "k": round(row["k_kg_ha"], 1),
                "risk": _site_risk(row),
                "mining_zone": row["mining_zone"],
                "texture": row["texture"],
            }
        )
    return sites


def _column(row: dict[str, Any], names: list[str], fallback: float | None = None) -> float | None:
    """Read the first parseable value among column-name variants (e.g. E.C / EC, NO3 / NO3-)."""
    for name in names:
        value = row.get(name)
        if value is None or value == "":
            continue
        parsed = safe_float(value, None)
        if parsed is not None:
            return parsed
    return fallback


def build_trends() -> list[dict[str, Any]]:
    grouped: dict[int, dict[str, list[float]]] = {}
    for row in groundwater_rows():
        year = int(row["year"])
        grouped.setdefault(year, {"ph": [], "ec": [], "tds": [], "nitrate": []})
        ph = _column(row, ["pH"])
        ec = _column(row, ["E.C", "EC", "Conductivity"])
        tds = _column(row, ["TDS"])
        nitrate = _column(row, ["NO3 ", "NO3- ", "NO3", "NO3-"])
        if ph is not None:
            grouped[year]["ph"].append(ph)
        if ec is not None:
            grouped[year]["ec"].append(ec)
        if tds is not None:
            grouped[year]["tds"].append(tds)
        if nitrate is not None:
            grouped[year]["nitrate"].append(nitrate)
    return [
        {
            "year": year,
            "ph": avg(values["ph"], 7.0),
            "ec": avg(values["ec"]),
            "tds": avg(values["tds"]),
            "nitrate": avg(values["nitrate"]),
        }
        for year, values in sorted(grouped.items())
    ]


def assess_water(features: dict[str, Any]) -> dict[str, Any]:
    problems = []
    if features["ph"] < 6.5 or features["ph"] > 8.5:
        problems.append("pH outside drinking-water comfort range")
    if features["tds"] > 1000:
        problems.append("high dissolved solids")
    if features["turbidity"] > 5:
        problems.append("high turbidity")
    if features["nitrate"] > 45:
        problems.append("nitrate exceeds common safety threshold")
    if len(problems) >= 2:
        cls = "Unsafe"
    elif problems:
        cls = "Poor"
    else:
        cls = "Good"
    return {"class": cls, "reason": "; ".join(problems) if problems else "Water indicators are within target bands."}


def record_sensor_event(payload: dict[str, Any]) -> dict[str, Any]:
    SENSOR_LOG.parent.mkdir(parents=True, exist_ok=True)
    event = {"features": build_feature_vector(payload), "raw": payload}
    with SENSOR_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event) + "\n")
    return {"stored": True, "path": str(SENSOR_LOG), "event": event}

