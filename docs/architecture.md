# Bioremediation Intelligence Platform Architecture

This prototype implements the plan as a local, CSV-backed intelligence system.

## Runtime

- `api/server.py` serves both the JSON API and the static frontend.
- `index.html`, `index.css`, and `js/` provide the dashboard SPA.
- `extracted_data/` remains the raw data source.
- `models/sensor_events.jsonl` stores ingested sensor payloads during demos.

## API

- `GET /api/health` checks service status.
- `GET /api/summary` returns soil, pollution, water, and groundwater summary metrics.
- `GET /api/sites` returns sampled geospatial soil points for the map.
- `GET /api/trends` returns groundwater trend points and one-step forecast.
- `POST /api/predict` accepts soil, water, contaminant, and climate readings.
- `POST /api/sensor` records a sensor event and returns the same prediction bundle.

## Model Adapters

The model files expose the output contracts from the implementation plan while staying lightweight:

- `random_forest.py`: interpretable soil-health scoring and class labels.
- `xgboost_model.py`: pollutant thresholding with environmental pressure adjustment.
- `cnn_model.py`: multi-sensor anomaly pattern adapter.
- `lstm_model.py`: groundwater trend direction and next-period forecast.
- `ensemble.py`: weighted overall condition and confidence.

These adapters can be replaced with trained `.pkl`, `.json`, or `.pt` models later without changing the frontend API contract.

