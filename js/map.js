let mapInstance = null;

export function renderMap(container, sites) {
  if (mapInstance) {
    mapInstance.remove();
  }
  
  container.innerHTML = '';
  
  if (!sites || sites.length === 0) {
    return;
  }
  
  const avgLat = sites.reduce((sum, site) => sum + site.lat, 0) / sites.length;
  const avgLng = sites.reduce((sum, site) => sum + site.lng, 0) / sites.length;

  mapInstance = L.map(container).setView([avgLat, avgLng], 8);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(mapInstance);

  sites.forEach((site) => {
    let color = '#23845b';
    if (site.risk > 70) {
      color = '#b82e37';
    } else if (site.risk > 42) {
      color = '#c48216';
    }

    const marker = L.circleMarker([site.lat, site.lng], {
      color: color,
      fillColor: color,
      fillOpacity: 0.8,
      radius: 6,
      weight: 2
    }).addTo(mapInstance);
    
    const popupContent = `<strong>Site ${site.id}</strong><br>Risk ${site.risk}<br>pH ${site.ph}<br>NPK ${site.n}/${site.p}/${site.k}<br>${site.texture}`;
    marker.bindTooltip(popupContent);
  });
}
