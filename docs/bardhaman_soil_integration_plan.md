# Bardhaman Village Soil Dataset Integration Plan

## 1. Source Files

This plan covers two new village-level soil workbooks:

- `extracted_data/paschim_bardhaman_village_soil_dataset_lat_long.xlsx`
- `extracted_data/purba_bardhaman_soil_dataset_lat_long.xlsx`

Both files contain geocoded West Bengal village soil records and can improve the existing bioremediation platform by adding a high-resolution local soil layer for Bardhaman districts.

## 2. Data Understanding

### Paschim Bardhaman

- Rows: 61 villages
- Blocks: 8
- Coordinates: present for every row
- Extra risk feature: `Is_Mining_Zone`
- Soil chemistry: pH, EC, organic carbon, N, P, K
- Micronutrients: Zn, Fe, Cu, Mn, B
- Observed profile:
  - Average pH: 6.11
  - Average EC: 0.31 dS/m
  - Average organic carbon: 0.54%
  - Average N/P/K: 202.1 / 18.0 / 174.3 kg/ha
  - Acidic villages, pH below 5.5: 12
  - Low organic carbon villages, below 0.5%: 23
  - Mining-zone rows: 41

### Purba Bardhaman

- Rows: 25 villages
- Blocks: 9
- Coordinates: present for every row
- Soil chemistry: pH, EC, organic carbon, N, P, K
- No mining-zone or micronutrient columns in the workbook
- Observed profile:
  - Average pH: 6.91
  - Average EC: 0.26 dS/m
  - Average organic carbon: 0.76%
  - Average N/P/K: 272.6 / 32.7 / 245.5 kg/ha
  - Acidic villages, pH below 5.5: 0
  - Low organic carbon villages, below 0.5%: 0

## 3. Why These Files Matter

The current platform already has large generic soil, pollution, crop, and water datasets. These two workbooks add a missing layer: village-scale, geocoded soil reality for a specific target region.

They should be used for:

- A West Bengal village soil map layer.
- Village-level soil health scoring.
- Local remediation recommendations.
- Mining-zone risk prioritization in Paschim Bardhaman.
- Crop-readiness scoring after remediation.
- District and block comparison dashboards.

They should not be treated as direct heavy-metal contamination measurements. Paschim Bardhaman has mining-zone flags and micronutrients, but it does not include Pb, Cd, Hg, As, hydrocarbons, pesticides, or measured pollutant concentration.

## 4. Schema Mapping Into Existing Feature Store

The existing platform feature store uses normalized fields such as `n`, `p`, `k`, `ph`, `organic_matter`, `ec`, `texture`, `latitude`, and `longitude`.

Map the workbook columns as follows:

| Workbook column | Platform field | Notes |
|---|---|---|
| State | state | Keep for filtering |
| District | district | New geography field |
| Block | block | New geography field |
| Village | village | New geography field |
| Latitude | latitude | Direct map coordinate |
| Longitude | longitude | Direct map coordinate |
| Is_Mining_Zone | mining_zone | Paschim only; default false for Purba |
| Soil Depth | soil_depth | Keep as categorical site descriptor |
| Texture | texture | Existing compatible field |
| Slope Class | slope_class | Add erosion/runoff risk feature |
| Erosion Class | erosion_class | Add erosion/runoff risk feature |
| pH | ph | Direct mapping |
| EC (dS/m) | ec | Direct mapping |
| Organic Carbon (%) | organic_carbon | Direct mapping |
| Organic Carbon (%) | organic_matter | Estimate as organic carbon * 1.724 |
| Nitrogen (N - kg/ha) | n_kg_ha | Preserve original units |
| Phosphorus (P - kg/ha) | p_kg_ha | Preserve original units |
| Potassium (K - kg/ha) | k_kg_ha | Preserve original units |
| Nitrogen (N - kg/ha) | n | Optional ppm estimate: kg/ha / 2.24 |
| Phosphorus (P - kg/ha) | p | Optional ppm estimate: kg/ha / 2.24 |
| Potassium (K - kg/ha) | k | Optional ppm estimate: kg/ha / 2.24 |
| Zinc (Zn - ppm) | zinc | Paschim only |
| Iron (Fe - ppm) | iron | Paschim only |
| Copper (Cu - ppm) | copper | Paschim only |
| Manganese (Mn - ppm) | manganese | Paschim only |
| Boron (B - ppm) | boron | Paschim only |

Keep both original `kg/ha` values and ppm estimates. The ppm conversion should be flagged as approximate because soil-depth and bulk-density assumptions can change the conversion.

## 5. Backend Implementation Plan

### Phase 1: Data Loader

Add `api/preprocessing/bardhaman_pipeline.py`.

Responsibilities:

- Read both `.xlsx` files with the bundled Python runtime.
- Normalize column names into platform fields.
- Add `source_file`, `district`, `block`, `village`, `state`.
- Add missing Paschim-only fields to Purba rows with null/default values.
- Add `dataset_region = "Bardhaman"`.
- Convert organic carbon to estimated organic matter.
- Preserve original nutrient units and add approximate ppm versions.
- Cache loaded rows with `lru_cache` because the files are static and small.

### Phase 2: Feature Store Updates

Update `api/preprocessing/feature_store.py`.

Add aliases for:

- `organic_carbon`
- `n_kg_ha`, `p_kg_ha`, `k_kg_ha`
- `district`, `block`, `village`, `state`
- `mining_zone`
- `soil_depth`
- `slope_class`
- `erosion_class`
- `zinc`, `iron`, `copper`, `manganese`, `boron`

Add a helper:

```python
def normalize_bardhaman_row(row: dict) -> dict:
    ...
```

This helper should output a full platform feature vector suitable for soil scoring, map rendering, and recommendations.

### Phase 3: Soil Health Model Adjustments

Update `api/models/random_forest.py` or add a Bardhaman-specific wrapper.

New scoring inputs:

- pH band: ideal 6.2 to 7.5
- EC: low salinity risk in both workbooks, but keep threshold monitoring
- Organic carbon: flag below 0.5% as low
- NPK in kg/ha: use local agricultural sufficiency bands
- Mining-zone flag: risk modifier, not direct contamination proof
- Erosion class: increase runoff vulnerability for moderate or severe erosion
- Slope class: increase erosion/runoff vulnerability where slope is higher
- Micronutrients: only score when present

Suggested Bardhaman soil-health components:

- 22% pH
- 18% organic carbon
- 25% NPK balance
- 10% EC/salinity
- 10% erosion/slope vulnerability
- 10% mining-zone risk modifier
- 5% micronutrient sufficiency when available

### Phase 4: Recommendation Engine Updates

Update `api/recommendation/engine.py`.

Add localized rules:

- pH below 5.5: apply agricultural lime and retest.
- Organic carbon below 0.5%: add compost, green manure, biochar, and crop residue return.
- Low P in Paschim: phosphate amendment with organic matter support.
- Low K: potash amendment or crop-residue recycling.
- Mining zone true: recommend confirmatory heavy-metal testing before food-crop decisions.
- Moderate erosion: cover crops, contour bunding, mulching, and drainage stabilization.
- Micronutrient deficiency:
  - Low Zn: zinc sulfate recommendation.
  - Low B: boron correction with strict dose control.

### Phase 5: API Endpoints

Add these endpoints to `api/server.py`:

- `GET /api/bardhaman/summary`
  - District totals, averages, risk counts, mining-zone count.
- `GET /api/bardhaman/sites`
  - Village map points with lat, long, district, block, village, pH, OC, NPK, mining-zone flag, health score.
- `GET /api/bardhaman/districts`
  - Aggregated district comparison.
- `GET /api/bardhaman/blocks?district=Paschim%20Bardhaman`
  - Block-level averages and village counts.
- `GET /api/bardhaman/villages?district=...&block=...`
  - Filtered village table.
- `POST /api/bardhaman/predict-village`
  - Accepts district/block/village or a direct row payload and returns soil health, risk, recommendations, and crop plan.

### Phase 6: Frontend Dashboard Updates

Update the dashboard to include a Bardhaman-focused view.

Recommended UI changes:

- Add a `Bardhaman` tab in the sidebar.
- Add district filters: Paschim Bardhaman, Purba Bardhaman, All.
- Add block and village dropdowns.
- Add map markers colored by:
  - Critical/Poor/Moderate/Good/Excellent soil score.
  - Optional overlay for mining-zone villages.
- Add district comparison cards:
  - Average pH
  - Average organic carbon
  - Average N/P/K kg/ha
  - Low organic carbon count
  - Acidic village count
  - Mining-zone count
- Add a village detail panel:
  - pH, EC, organic carbon
  - NPK original kg/ha
  - Texture, soil depth, erosion class
  - Micronutrients when available
  - Recommended remediation actions

### Phase 7: Reports

Extend JSON export and future PDF reporting to support:

- District summary report.
- Block summary report.
- Village soil-health report.
- Mining-zone priority list.
- Low-organic-carbon action list.
- Acidic-soil lime-priority list.

## 6. Integration With Existing Models

### Random Forest / Soil Health

Use these workbooks as local inference inputs immediately. Later, append normalized rows to model training data as a region-specific calibration set.

### XGBoost / Contamination

Do not train contamination concentration directly from these workbooks because pollutant concentration is absent. Use `Is_Mining_Zone`, pH, organic carbon, erosion, and micronutrients as risk indicators only.

### CNN / Sensor Pattern

Use village rows as static baseline points. Future sensor readings can be compared against the nearest village baseline.

### LSTM / Temporal Forecasting

These files are cross-sectional, not temporal. They should not feed LSTM training unless future yearly village soil surveys are added.

### Ensemble

Add a `local_soil_risk` component to the ensemble. Mining-zone risk should raise monitoring priority but should not automatically classify a village as contaminated.

## 7. Data Quality Checks

Before enabling these files in production logic:

- Validate latitude and longitude within West Bengal bounds.
- Confirm all villages are unique within district/block.
- Confirm no missing required columns.
- Confirm pH between 3.5 and 10.
- Confirm EC between 0 and 10 dS/m.
- Confirm organic carbon between 0 and 5%.
- Confirm N/P/K values are treated as kg/ha, not ppm.
- Confirm Purba missing mining-zone and micronutrient fields are handled safely.

## 8. Suggested Build Order

1. Add `bardhaman_pipeline.py` loader and schema normalization.
2. Add unit conversion and row-level soil score helper.
3. Add `/api/bardhaman/summary` and `/api/bardhaman/sites`.
4. Add Bardhaman map layer and district filters in frontend.
5. Add village detail panel and recommendation cards.
6. Add `/api/bardhaman/predict-village`.
7. Add report export fields.
8. Add tests for loader, scoring, endpoint shape, and no-missing-field behavior.

## 9. Acceptance Criteria

The integration is complete when:

- Both Excel files load without manual conversion.
- All 86 villages appear in `/api/bardhaman/sites`.
- Paschim Bardhaman mining-zone villages are visible as a distinct map overlay.
- Purba Bardhaman rows work even without micronutrient columns.
- Village-level soil health and recommendations are generated.
- District and block summaries reconcile with the source workbooks.
- Existing generic dashboard and prediction endpoints continue to work.

