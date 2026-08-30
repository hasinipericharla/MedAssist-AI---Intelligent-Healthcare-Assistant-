// ---------------------------------------------------------------------
// Module 9: Nearby Hospital Finder
// Real implementation: browser Geolocation API + OpenStreetMap's public
// Overpass API. No backend route or API key required -- this runs
// entirely in the user's browser.
// ---------------------------------------------------------------------

const locateBtn = document.getElementById("locateBtn");
const status = document.getElementById("locateStatus");
const hospitalList = document.getElementById("hospitalList");
const clinicList = document.getElementById("clinicList");

locateBtn.addEventListener("click", () => {
  if (!navigator.geolocation) {
    status.textContent = "Your browser doesn't support geolocation.";
    return;
  }
  status.textContent = "Getting your location…";
  navigator.geolocation.getCurrentPosition(onLocation, onLocationError, { timeout: 10000 });
});

function onLocationError() {
  status.textContent = "Couldn't get your location. Check browser location permissions.";
}

async function onLocation(pos) {
  const { latitude, longitude } = pos.coords;
  status.textContent = "Searching nearby facilities…";

  const radius = 5000; // meters
  const query = `
    [out:json][timeout:15];
    (
      node["amenity"="hospital"](around:${radius},${latitude},${longitude});
      node["amenity"="clinic"](around:${radius},${latitude},${longitude});
    );
    out body 20;
  `;

  try {
    const res = await fetch("https://overpass-api.de/api/interpreter", {
      method: "POST",
      body: query,
    });
    const data = await res.json();
    const hospitals = data.elements.filter((e) => e.tags?.amenity === "hospital");
    const clinics = data.elements.filter((e) => e.tags?.amenity === "clinic");

    renderList(hospitalList, hospitals, latitude, longitude);
    renderList(clinicList, clinics, latitude, longitude);
    status.textContent = `Found ${hospitals.length} hospitals and ${clinics.length} clinics within 5km.`;
  } catch (err) {
    status.textContent = "Couldn't reach the location service. Try again shortly.";
  }
}

function distanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function renderList(container, places, lat, lon) {
  if (places.length === 0) {
    container.innerHTML = `<p class="hint">None found within 5km.</p>`;
    return;
  }
  container.innerHTML = places
    .map((p) => {
      const name = p.tags?.name || "Unnamed facility";
      const dist = distanceKm(lat, lon, p.lat, p.lon).toFixed(1);
      const mapUrl = `https://www.openstreetmap.org/?mlat=${p.lat}&mlon=${p.lon}#map=17/${p.lat}/${p.lon}`;
      return `
        <div class="result-card" style="margin-bottom:8px;">
          <div class="result-top">
            <span class="result-disease" style="font-size:0.92rem;">${name}</span>
            <span class="result-confidence">${dist} km</span>
          </div>
          <a href="${mapUrl}" target="_blank" rel="noopener" style="font-size:0.82rem;">View on map ↗</a>
        </div>`;
    })
    .join("");
}
