from __future__ import annotations

import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "static"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.models.cnn_model import SensorPatternModel
from api.models.ensemble import EnsembleModel
from api.models.lstm_model import TrendModel
from api.models.random_forest import SoilHealthModel
from api.models.xgboost_model import ContaminationModel
from api.preprocessing.bardhaman_pipeline import bardhaman_sites, bardhaman_summary, nearest_bardhaman_site
from api.preprocessing.data_pipeline import assess_water, build_sites, build_summary, build_trends, record_sensor_event
from api.preprocessing.feature_store import build_feature_vector
from api.recommendation.engine import build_crop_plan, build_recommendations


soil_model = SoilHealthModel()
contamination_model = ContaminationModel()
sensor_model = SensorPatternModel()
trend_model = TrendModel()
ensemble_model = EnsembleModel()


def make_prediction(payload: dict) -> dict:
    features = build_feature_vector(payload)
    soil = soil_model.predict(features)
    contamination = contamination_model.predict(features)
    sensor = sensor_model.predict(features)
    water = assess_water(features)
    trends = build_trends()
    trend = trend_model.predict(trends)
    ensemble = ensemble_model.predict(soil, contamination, sensor, trend)
    recommendations = build_recommendations(features, soil, contamination, water, ensemble)
    crop_plan = build_crop_plan(features, ensemble)
    result = {
        "features": features,
        "soil_health": soil,
        "contamination": contamination,
        "sensor_pattern": sensor,
        "water_quality": water,
        "trend": trend,
        "ensemble": ensemble,
        "recommendations": recommendations,
        "crop_plan": crop_plan,
    }
    if "location_match" in payload:
        result["location_match"] = payload["location_match"]
    return result


class Handler(BaseHTTPRequestHandler):
    server_version = "BioremediationHTTP/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/api/health":
            self.send_json({"ok": True, "service": "bioremediation-platform"})
        elif path == "/api/summary":
            self.send_json(build_summary())
        elif path == "/api/sites":
            self.send_json({"sites": build_sites()})
        elif path == "/api/trends":
            trends = build_trends()
            self.send_json({"trends": trends, "forecast": trend_model.predict(trends)})
        elif path == "/api/sample-prediction":
            self.send_json(make_prediction({}))
        elif path == "/api/bardhaman/summary":
            self.send_json(bardhaman_summary())
        elif path == "/api/bardhaman/sites":
            self.send_json({"sites": bardhaman_sites()})
        elif path == "/api/bardhaman/nearest":
            latitude = self.query_float(query, "latitude")
            longitude = self.query_float(query, "longitude")
            self.send_nearest_bardhaman(latitude, longitude)
        else:
            self.serve_static(path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        payload = self.read_json()
        if path == "/api/predict":
            self.send_json(make_prediction(payload))
        elif path == "/api/bardhaman/nearest":
            latitude = self.payload_float(payload, "latitude")
            longitude = self.payload_float(payload, "longitude")
            self.send_nearest_bardhaman(latitude, longitude)
        elif path == "/api/sensor":
            event = record_sensor_event(payload)
            event["prediction"] = make_prediction(payload)
            self.send_json(event, status=201)
        else:
            self.send_json({"error": "Not found"}, status=404)

    def send_nearest_bardhaman(self, latitude: float | None, longitude: float | None) -> None:
        if latitude is None or longitude is None:
            self.send_json({"error": "latitude and longitude are required"}, status=400)
            return
        site = nearest_bardhaman_site(latitude, longitude)
        if site is None:
            self.send_json({"error": "Bardhaman workbooks were not found or could not be loaded"}, status=404)
            return
        location_match = {
            "district": site["district"],
            "block": site["block"],
            "village": site["village"],
            "distance_km": site["distance_km"],
            "source_file": site["source_file"],
            "mining_zone": site["mining_zone"],
            "requested_latitude": latitude,
            "requested_longitude": longitude,
        }
        prediction_payload = {**site["features"], "location_match": location_match}
        self.send_json({"site": site, "prediction": make_prediction(prediction_payload)})

    def query_float(self, query: dict, key: str) -> float | None:
        values = query.get(key)
        if not values:
            return None
        return self.parse_float(values[0])

    def payload_float(self, payload: dict, key: str) -> float | None:
        return self.parse_float(payload.get(key))

    def parse_float(self, value: object) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, path: str) -> None:
        if path in {"", "/"}:
            target = STATIC_DIR / "index.html"
            if not target.is_file():
                target = ROOT / "index.html"
        else:
            static_candidate = (STATIC_DIR / path.lstrip("/")).resolve()
            if (STATIC_DIR in static_candidate.parents or static_candidate == STATIC_DIR) and static_candidate.is_file():
                target = static_candidate
            else:
                target = (ROOT / path.lstrip("/")).resolve()
        if ROOT not in target.parents and target != ROOT:
            self.send_json({"error": "Forbidden"}, status=403)
            return
        if not target.exists() or not target.is_file():
            self.send_json({"error": "Not found"}, status=404)
            return
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Bioremediation platform running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
