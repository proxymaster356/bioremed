import { useEffect, useMemo } from "react";
import L from "leaflet";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// Fixes the gray-void tile bug: the old map was initialized while its
// container was hidden, so Leaflet computed a wrong size. React-leaflet
// mounts per-view, and this keeps the size in sync on tab switches/resizes.
function MapSizeSync() {
  const map = useMap();
  useEffect(() => {
    const sync = () => map.invalidateSize();
    const timeout = setTimeout(sync, 150);
    window.addEventListener("resize", sync);
    return () => {
      clearTimeout(timeout);
      window.removeEventListener("resize", sync);
    };
  }, [map]);
  return null;
}

function FitToBounds({ points }) {
  const map = useMap();
  useEffect(() => {
    if (points.length === 1) {
      map.setView(points[0], 11);
    } else if (points.length > 1) {
      map.fitBounds(L.latLngBounds(points), { padding: [35, 35] });
    }
  }, [map, points]);
  return null;
}

export function riskColor(risk) {
  if (risk >= 66) return "#b82e37";
  if (risk >= 40) return "#c48216";
  return "#17715b";
}

export default function SiteMap({ sites }) {
  const points = useMemo(() => sites.map((site) => [site.lat, site.lng]), [sites]);
  if (!sites.length) {
    return <section className="view active"><p className="muted">Loading village soil survey sites…</p></section>;
  }
  return (
    <section className="view active">
      <article className="panel full">
        <div className="panel-heading">
          <h2>Village Soil Risk — Bardhaman Districts</h2>
          <span>{sites.length} villages mapped</span>
        </div>
        <MapContainer center={[23.8, 86.9]} zoom={9} scrollWheelZoom className="site-map">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapSizeSync />
          <FitToBounds points={points} />
          {sites.map((site) => (
            <CircleMarker
              key={site.id}
              center={[site.lat, site.lng]}
              radius={8}
              pathOptions={{
                color: riskColor(site.risk),
                fillColor: riskColor(site.risk),
                fillOpacity: 0.65,
                weight: 1.5,
              }}
            >
              <Popup>
                <strong>{site.village}</strong> — {site.block}, {site.district}
                <br />
                pH {site.ph} · Organic C {site.organic_carbon}% · EC {site.ec} dS/m
                <br />
                N {site.n} · P {site.p} · K {site.k} kg/ha ({site.texture})
                {site.mining_zone && (
                  <>
                    <br />
                    <strong style={{ color: "#b82e37" }}>⚠ Mining / industrial zone</strong>
                  </>
                )}
                <br />
                Site risk: <strong style={{ color: riskColor(site.risk) }}>{site.risk} / 100</strong>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
        <div className="map-legend">
          <span style={{ color: "#17715b" }}>● Low risk (&lt;40)</span>
          <span style={{ color: "#c48216" }}>● Moderate risk (40–65)</span>
          <span style={{ color: "#b82e37" }}>● High risk (≥66)</span>
        </div>
      </article>
    </section>
  );
}
