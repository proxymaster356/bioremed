from __future__ import annotations

from api.recommendation.crop_advisor import recommend_crops


def build_recommendations(features: dict, soil: dict, contamination: dict, water: dict, ensemble: dict) -> list[dict]:
    actions: list[dict] = []
    final_class = ensemble["class"]
    if final_class in {"Critical", "Poor"}:
        actions.append(
            {
                "priority": "High",
                "title": "Start active remediation",
                "action": "Combine containment, bioaugmentation, and biostimulation before any crop transition.",
                "reason": f"Overall condition is {final_class.lower()} with {ensemble['risk_score']} risk score.",
            }
        )
    if features["n"] < 50:
        actions.append(
            {
                "priority": "Medium",
                "title": "Correct nitrogen deficiency",
                "action": "Apply a nitrogen amendment and add a legume cover crop to improve biological fixation.",
                "reason": f"Nitrogen is {features['n']:.1f} ppm.",
            }
        )
    if features["ph"] < 5.5:
        actions.append(
            {
                "priority": "High",
                "title": "Buffer acidic soil",
                "action": "Apply agricultural lime and re-test pH after incorporation.",
                "reason": "Low pH increases metal mobility and suppresses microbial activity.",
            }
        )
    if features["ph"] > 8.5:
        actions.append(
            {
                "priority": "High",
                "title": "Reduce alkalinity pressure",
                "action": "Use elemental sulfur or gypsum and avoid alkaline irrigation sources.",
                "reason": "High pH can reduce nutrient availability and affect remediation kinetics.",
            }
        )
    if features["moisture"] < 15:
        actions.append(
            {
                "priority": "Medium",
                "title": "Restore soil moisture",
                "action": "Add mulch, compost, and drip irrigation scheduling to support microbial degradation.",
                "reason": f"Moisture is only {features['moisture']:.1f}%.",
            }
        )
    if features["organic_matter"] < 2.5:
        actions.append(
            {
                "priority": "Medium",
                "title": "Increase organic matter",
                "action": "Apply mature compost or biochar to improve sorption, porosity, and microbial habitat.",
                "reason": f"Organic matter is {features['organic_matter']:.1f}%.",
            }
        )
    if contamination["class"] in {"High", "Severe"}:
        actions.append(
            {
                "priority": "High",
                "title": "Deploy contaminant-specific treatment",
                "action": "Use phytoremediation with mustard or sunflower for metals; use mycoremediation for hydrocarbons and PAHs.",
                "reason": f"{contamination['pollutant']} is classified as {contamination['class'].lower()}.",
            }
        )
    if water["class"] in {"Poor", "Unsafe"}:
        actions.append(
            {
                "priority": "High",
                "title": "Treat water-quality pathway",
                "action": "Add activated carbon filtration, constructed wetland polishing, or denitrification media as appropriate.",
                "reason": water["reason"],
            }
        )
    if not actions:
        actions.append(
            {
                "priority": "Low",
                "title": "Maintain monitoring mode",
                "action": "Continue quarterly sensor readings, annual soil tests, and crop rotation with organic amendments.",
                "reason": "Current readings are inside the operating envelope.",
            }
        )
    return actions[:7]


def build_crop_plan(features: dict, ensemble: dict) -> dict:
    crops = recommend_crops(features)
    status = "ready" if ensemble["class"] in {"Good", "Excellent"} else "after-remediation"
    return {"status": status, "crops": crops}

