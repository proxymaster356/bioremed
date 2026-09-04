# API Reference

## `POST /api/predict`

Example payload:

```json
{
  "n": 72,
  "p": 38,
  "k": 190,
  "ph": 6.6,
  "organic_matter": 2.4,
  "moisture": 24,
  "pollutant_type": "Lead",
  "pollutant_concentration": 95,
  "ec": 2.8,
  "cec": 18,
  "tds": 720,
  "nitrate": 32,
  "temperature": 28,
  "humidity": 62,
  "rainfall": 88,
  "texture": "loamy",
  "latitude": 19.5,
  "longitude": 78.5
}
```

Response sections:

- `soil_health`: score, class, component scores, and limiting factors.
- `contamination`: pollutant class, confidence, and drivers.
- `sensor_pattern`: anomaly class and channel activations.
- `water_quality`: class and reason.
- `trend`: groundwater direction and forecast.
- `ensemble`: final class, risk score, and confidence.
- `recommendations`: remediation actions.
- `crop_plan`: crop suggestions from `Crop_recommendation.csv`.

## Local Run

```powershell
python api/server.py
```

Then open `http://127.0.0.1:8000`.

## Bardhaman Location Lookup

`POST /api/bardhaman/nearest` accepts manual or browser-captured coordinates:

```json
{
  "latitude": 23.78745,
  "longitude": 86.91507
}
```

The response returns the nearest Bardhaman village soil row from the Excel workbooks plus a prediction generated from that row. The frontend uses this endpoint for both `Use Current Location` and `Load Nearest Village Soil`.

