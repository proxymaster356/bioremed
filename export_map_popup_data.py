from __future__ import annotations

import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import urlopen

OUTPUT_PATH = Path("map_popup_sites.csv")
WMS_BASE_URL = (
    "https://soilhealth.dac.gov.in/"
    "jW8X3zM5Y7pQvLr4K2Tn6HqPbD0tZmN9R6JfO1wCiG8xV5eTk2CdMoF9YsQr0Z7LmN1YxU4pTb2K5LvHqX7F3aCmGzR4Pw0D8UtYnJ9oZ2SvNlQ7Tz1PjR5LcX0Qf8HkV9OrG4V7YxU3pJk6TnMm5CdX8B9tRi1Lw2Qn7F4ZzJk8WvP1GrZ6Sx0JoH5C3oV7fNi2/shc/wms"
)


def fetch_json(url: str) -> dict:
    with urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8", "ignore"))


def get_public_layers(state_code: str, district_code: str) -> dict:
    url = (
        "https://soilhealth.dac.gov.in/q8ZdH3f0mX1y7nJrP2K5BvW9aQpLb-6TsFcYzC4oUtN_"
        "MwRiDgGZ0xVsJe7Xy8nMk2TjPqFbD1C5LvOr9WQ6Xa3lYsN7V1sRmJez4OtUbY0Qn9hPk6WfLd2Y8oSvK3UtGmX5C7bT9Pn6xV0JfZ1TzQm8LrV9aGkM2JpXeN4fUoQ8SwCiRzN7VtPk1XgW5/public/layers?"
        f"state_code={state_code}&district_code={district_code}"
    )
    return fetch_json(url)


def select_cycle_layer(metadata: dict, cycle: str) -> str:
    for item in metadata.get("shcLayers", []):
        if str(item) == cycle:
            return f"{metadata['state']}_{metadata['district']}_shc_{cycle}"
    raise SystemExit(f"Cycle {cycle!r} is not available for the selected district.")


def build_feature_info_url(layer_name: str, bbox: tuple[float, float, float, float], width: int, height: int, i: int, j: int, style: str) -> str:
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "FORMAT": "image/png",
        "STYLES": "",
        "TRANSPARENT": "true",
        "layers": layer_name,
        "styles": style,
        "WIDTH": str(width),
        "HEIGHT": str(height),
        "CRS": "EPSG:4326",
        "BBOX": ",".join(map(str, bbox)),
        "REQUEST": "GetFeatureInfo",
        "QUERY_LAYERS": layer_name,
        "INFO_FORMAT": "application/json",
        "I": str(i),
        "J": str(j),
    }
    return f"{WMS_BASE_URL}?{urlencode(params)}"


def scan_features(layer_name: str, bbox: tuple[float, float, float, float], width: int = 1024, height: int = 1024, step: int = 8, style: str = "N") -> list[dict]:
    hits: dict[str, dict] = {}

    def probe(i: int, j: int) -> list[dict]:
        url = build_feature_info_url(layer_name, bbox, width, height, i, j, style)
        try:
            payload = fetch_json(url)
            return payload.get("features", [])
        except Exception:
            return []

    coords = [(i, j) for i in range(0, width, step) for j in range(0, height, step)]
    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = [executor.submit(probe, i, j) for i, j in coords]
        for future in as_completed(futures):
            for feature in future.result():
                feature_id = feature.get("id") or json.dumps(feature.get("properties", {}), sort_keys=True)
                hits[feature_id] = feature

    return list(hits.values())


def flatten_feature(feature: dict, metadata: dict, cycle: str, layer_name: str) -> dict[str, str]:
    properties = feature.get("properties", {})
    row = {
        "feature_id": str(feature.get("id", "")),
        "state_code": str(metadata.get("state", "")),
        "district_code": str(metadata.get("district", "")),
        "cycle": cycle,
        "layer_name": layer_name,
    }
    for key, value in properties.items():
        row[key] = str(value)
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Export live SLUSI popup data to CSV.")
    parser.add_argument("--state-code", default="19")
    parser.add_argument("--district-code", default="704")
    parser.add_argument("--cycle", default="2024-25")
    parser.add_argument("--style", default="N")
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--step", type=int, default=8)
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    args = parser.parse_args()

    metadata = get_public_layers(args.state_code, args.district_code)
    layer_name = select_cycle_layer(metadata, args.cycle)
    bbox_raw = metadata.get("bbox", {})
    bbox = (
        float(bbox_raw["miny"]),
        float(bbox_raw["minx"]),
        float(bbox_raw["maxy"]),
        float(bbox_raw["maxx"]),
    )

    features = scan_features(layer_name, bbox, width=args.width, height=args.height, step=args.step, style=args.style)
    if not features:
        raise SystemExit("No live popup features were found for the selected district.")

    rows = [flatten_feature(feature, metadata, args.cycle, layer_name) for feature in features]
    fieldnames = ["feature_id", "state_code", "district_code", "cycle", "layer_name"]
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    print(f"Exported {len(rows)} live popup records to {output_path}")


if __name__ == "__main__":
    main()