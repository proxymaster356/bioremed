from __future__ import annotations


class TrendModel:
    """Forecast adapter for historical groundwater indicators."""

    def predict(self, yearly_points: list[dict]) -> dict:
        if len(yearly_points) < 2:
            return {"direction": "stable", "forecast": yearly_points, "confidence": 0.45}
        first = yearly_points[0]
        last = yearly_points[-1]
        ec_delta = last.get("ec", 0) - first.get("ec", 0)
        ph_delta = abs(last.get("ph", 7) - 7) - abs(first.get("ph", 7) - 7)
        if ec_delta > 100 or ph_delta > 0.25:
            direction = "degrading"
        elif ec_delta < -100 and ph_delta <= 0:
            direction = "improving"
        else:
            direction = "stable"
        next_year = int(last["year"]) + 1
        slope_ec = ec_delta / max(1, len(yearly_points) - 1)
        slope_ph = (last.get("ph", 7) - first.get("ph", 7)) / max(1, len(yearly_points) - 1)
        forecast = yearly_points + [
            {
                "year": next_year,
                "ph": round(last.get("ph", 7) + slope_ph, 2),
                "ec": round(max(0, last.get("ec", 0) + slope_ec), 1),
                "forecast": True,
            }
        ]
        return {"direction": direction, "forecast": forecast, "confidence": 0.68}

