const state = {
  criteria: null,
  listings: [],
  scores: [],
};

const heroStats = document.getElementById("hero-stats");
const rankingGrid = document.getElementById("ranking-grid");
const cardsGrid = document.getElementById("cards-grid");
const comparisonTable = document.getElementById("comparison-table");
const boardSummary = document.getElementById("board-summary");
const criteriaForm = document.getElementById("criteria-form");
const filterForm = document.getElementById("filter-form");
const manualForm = document.getElementById("manual-form");
const emptyStateTemplate = document.getElementById("empty-state-template");

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  return response.json();
}

function currency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(value) {
  if (!value) {
    return "Unknown";
  }
  return new Date(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function summarize() {
  if (!state.listings.length) {
    boardSummary.textContent = "No listings available.";
    return;
  }

  const averagePrice =
    state.listings.reduce((sum, listing) => sum + listing.price, 0) / state.listings.length;
  const best = state.listings[0];
  boardSummary.textContent = `${state.listings.length} listings loaded. Avg price ${currency(
    averagePrice
  )}. Current leader: ${best.title}.`;
}

function renderHeroStats() {
  const shortlistCount = state.listings.filter((item) =>
    ["shortlist", "tour"].includes(item.watchlist_status)
  ).length;
  const garageMatches = state.listings.filter((item) => item.has_garage).length;
  const backyardMatches = state.listings.filter((item) => item.has_backyard).length;
  const bestScore = state.listings[0]?.score?.total_score ?? 0;

  heroStats.innerHTML = `
    <div class="stat-card">
      <span class="pill">Best score</span>
      <strong>${bestScore.toFixed(1)}</strong>
    </div>
    <div class="stat-card">
      <span class="pill">Shortlist + tour</span>
      <strong>${shortlistCount}</strong>
    </div>
    <div class="stat-card">
      <span class="pill">Garage matches</span>
      <strong>${garageMatches}</strong>
    </div>
    <div class="stat-card">
      <span class="pill">Backyard matches</span>
      <strong>${backyardMatches}</strong>
    </div>
  `;
}

function appendEmptyState(node) {
  node.innerHTML = "";
  node.appendChild(emptyStateTemplate.content.cloneNode(true));
}

function renderRanking() {
  if (!state.listings.length) {
    appendEmptyState(rankingGrid);
    return;
  }

  rankingGrid.innerHTML = state.listings
    .slice(0, 3)
    .map(
      (listing, index) => `
        <article class="ranking-card">
          <div class="ranking-head">
            <span class="rank">0${index + 1}</span>
            <span class="badge score">${listing.score?.total_score?.toFixed(1) ?? "0.0"}</span>
          </div>
          <h3>${listing.title}</h3>
          <p>${listing.city}${listing.neighborhood ? ` · ${listing.neighborhood}` : ""}</p>
          <div class="metric-row">
            <span>${currency(listing.price)}</span>
            <span>${listing.bedrooms} bd / ${listing.bathrooms} ba</span>
            <span>${listing.square_feet ?? "?"} sqft</span>
          </div>
          <div class="signal-row">
            <span>${listing.has_backyard ? "Backyard" : "No backyard"}</span>
            <span>${listing.has_garage ? "Garage" : "No garage"}</span>
            <span>${listing.pets_allowed ? "Pets" : "Pets unknown"}</span>
          </div>
        </article>
      `
    )
    .join("");
}

function renderCards() {
  if (!state.listings.length) {
    appendEmptyState(cardsGrid);
    return;
  }

  cardsGrid.innerHTML = state.listings
    .map(
      (listing) => `
        <article class="listing-card">
          <div class="listing-card-top">
            <div>
              <div class="card-meta">
                <span class="source-badge">${listing.source_name}</span>
                <span class="badge score">${listing.score?.total_score?.toFixed(1) ?? "0.0"}</span>
              </div>
              <h3>${listing.title}</h3>
              <p>${listing.address_line1 ?? "Address pending"} · ${listing.city}, ${listing.state}</p>
            </div>
            <span class="badge watch-${listing.watchlist_status}">${listing.watchlist_status}</span>
          </div>
          <div class="metric-row">
            <span>${currency(listing.price)}</span>
            <span>${listing.bedrooms} bd / ${listing.bathrooms} ba</span>
            <span>${listing.square_feet ?? "?"} sqft</span>
            <span>Fresh since ${formatDate(listing.listed_at)}</span>
          </div>
          <p>${listing.description ?? "No description provided yet."}</p>
          <div class="signal-row">
            ${listing.feature_tags.map((tag) => `<span>${tag}</span>`).join("")}
          </div>
          <div class="notes-list">
            ${listing.notes.map((note) => `<span>${note.note}</span>`).join("")}
          </div>
          <div class="comparison-link">
            <span>Confidence ${(listing.confidence * 100).toFixed(0)}%</span>
            ${
              listing.listing_url
                ? `<a class="pill" href="${listing.listing_url}" target="_blank" rel="noreferrer">Open source URL</a>`
                : `<span class="pill">No URL</span>`
            }
          </div>
        </article>
      `
    )
    .join("");
}

function renderTable() {
  if (!state.listings.length) {
    comparisonTable.innerHTML = `<tr><td colspan="12">No listings match the current filters.</td></tr>`;
    return;
  }

  comparisonTable.innerHTML = state.listings
    .map(
      (listing, index) => `
        <tr>
          <td>#${index + 1}</td>
          <td>${listing.title}</td>
          <td>${currency(listing.price)}</td>
          <td>${listing.bedrooms} / ${listing.bathrooms}</td>
          <td>${listing.square_feet ?? "?"}</td>
          <td>${listing.city}</td>
          <td>${listing.neighborhood ?? "-"}</td>
          <td>${listing.has_backyard ? "Yes" : "No"}</td>
          <td>${listing.has_garage ? "Yes" : "No"}</td>
          <td>${listing.pets_allowed ? "Yes" : "No / ?"}</td>
          <td>${listing.source_name}</td>
          <td>${listing.watchlist_status}</td>
        </tr>
      `
    )
    .join("");
}

function populateCriteriaForm() {
  if (!state.criteria) {
    return;
  }

  const criteria = state.criteria;
  criteriaForm.elements.county.value = criteria.county ?? "";
  criteriaForm.elements.city.value = criteria.city ?? "";
  criteriaForm.elements.min_bedrooms.value = criteria.min_bedrooms ?? 0;
  criteriaForm.elements.min_bathrooms.value = criteria.min_bathrooms ?? 0;
  criteriaForm.elements.max_price.value = criteria.max_price ?? "";
  criteriaForm.elements.min_sqft.value = criteria.min_sqft ?? "";
  criteriaForm.elements.require_backyard.checked = criteria.require_backyard;
  criteriaForm.elements.require_garage.checked = criteria.require_garage;
  criteriaForm.elements.pets_required.checked = criteria.pets_required;
  criteriaForm.elements.notes.value = criteria.notes ?? "";

  filterForm.elements.min_bedrooms.value = criteria.min_bedrooms ?? 0;
  filterForm.elements.require_backyard.checked = criteria.require_backyard;
  filterForm.elements.require_garage.checked = criteria.require_garage;
  filterForm.elements.pets_required.checked = criteria.pets_required;
}

function populateCityFilter() {
  const select = filterForm.elements.city;
  const current = select.value;
  const cities = [...new Set(state.listings.map((listing) => listing.city))].sort();
  select.innerHTML = `<option value="">All Orange County</option>${cities
    .map((city) => `<option value="${city}">${city}</option>`)
    .join("")}`;

  if (cities.includes(current)) {
    select.value = current;
  } else if (state.criteria?.city && cities.includes(state.criteria.city)) {
    select.value = state.criteria.city;
  }
}

function renderAll() {
  summarize();
  renderHeroStats();
  renderRanking();
  renderCards();
  renderTable();
  populateCriteriaForm();
  populateCityFilter();
}

async function loadDashboard(query = "") {
  const [criteria, listings, scores] = await Promise.all([
    fetchJson("/api/search-criteria"),
    fetchJson(`/api/listings${query}`),
    fetchJson("/api/scores"),
  ]);

  state.criteria = criteria;
  state.listings = listings;
  state.scores = scores;
  renderAll();
}

criteriaForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    name: "Orange County Family Rental Search",
    county: criteriaForm.elements.county.value,
    state: "CA",
    city: criteriaForm.elements.city.value || null,
    min_bedrooms: Number(criteriaForm.elements.min_bedrooms.value || 0),
    min_bathrooms: Number(criteriaForm.elements.min_bathrooms.value || 0),
    max_price: criteriaForm.elements.max_price.value ? Number(criteriaForm.elements.max_price.value) : null,
    min_sqft: criteriaForm.elements.min_sqft.value ? Number(criteriaForm.elements.min_sqft.value) : null,
    require_backyard: criteriaForm.elements.require_backyard.checked,
    require_garage: criteriaForm.elements.require_garage.checked,
    pets_required: criteriaForm.elements.pets_required.checked,
    notes: criteriaForm.elements.notes.value || null,
    weights: state.criteria?.weights ?? undefined,
  };

  await fetchJson("/api/search-criteria", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  await loadDashboard();
});

filterForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const params = new URLSearchParams();
  if (filterForm.elements.city.value) params.set("city", filterForm.elements.city.value);
  if (filterForm.elements.min_bedrooms.value) params.set("min_bedrooms", filterForm.elements.min_bedrooms.value);
  if (filterForm.elements.require_backyard.checked) params.set("require_backyard", "true");
  if (filterForm.elements.require_garage.checked) params.set("require_garage", "true");
  if (filterForm.elements.pets_required.checked) params.set("pets_required", "true");
  params.set("sort_by", filterForm.elements.sort_by.value);

  const query = params.toString() ? `?${params.toString()}` : "";
  await loadDashboard(query);
});

manualForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    title: manualForm.elements.title.value,
    city: manualForm.elements.city.value,
    neighborhood: manualForm.elements.neighborhood.value || null,
    county: state.criteria?.county || "Orange County",
    state: "CA",
    price: Number(manualForm.elements.price.value),
    bedrooms: Number(manualForm.elements.bedrooms.value),
    bathrooms: Number(manualForm.elements.bathrooms.value),
    square_feet: manualForm.elements.square_feet.value ? Number(manualForm.elements.square_feet.value) : null,
    has_backyard: manualForm.elements.has_backyard.checked,
    has_garage: manualForm.elements.has_garage.checked,
    pets_allowed: manualForm.elements.pets_allowed.checked,
    listing_url: manualForm.elements.listing_url.value || null,
    note: manualForm.elements.note.value || null,
  };

  await fetchJson("/api/listings/manual", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  manualForm.reset();
  await loadDashboard();
});

loadDashboard().catch((error) => {
  boardSummary.textContent = `Failed to load dashboard: ${error.message}`;
});
