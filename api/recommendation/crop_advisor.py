from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parents[2] / "extracted_data"


@lru_cache(maxsize=1)
def load_crop_rows() -> list[dict]:
    path = DATA_DIR / "Crop_recommendation.csv"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def recommend_crops(features: dict, limit: int = 4) -> list[dict]:
    rows = load_crop_rows()
    scored = []
    for row in rows:
        try:
            distance = (
                abs(float(row["N"]) - features["n"]) / 140
                + abs(float(row["P"]) - features["p"]) / 140
                + abs(float(row["K"]) - features["k"]) / 220
                + abs(float(row["ph"]) - features["ph"]) / 4
                + abs(float(row["temperature"]) - features["temperature"]) / 30
                + abs(float(row["humidity"]) - features["humidity"]) / 100
                + abs(float(row["rainfall"]) - features["rainfall"]) / 300
            )
        except (KeyError, TypeError, ValueError):
            continue
        scored.append((distance, row["label"]))
    unique = []
    seen = set()
    for distance, crop in sorted(scored, key=lambda item: item[0]):
        if crop not in seen:
            seen.add(crop)
            unique.append({"crop": crop, "match": round(max(0, 100 - distance * 22), 1)})
        if len(unique) >= limit:
            break
    return unique

