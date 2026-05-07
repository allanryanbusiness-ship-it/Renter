const state = {
  criteria: null,
  listings: [],
  scores: [],
  selectedListingId: null,
};

const heroStats = document.getElementById("hero-stats");
const criteriaSummary = document.getElementById("criteria-summary");
const rankingGrid = document.getElementById("ranking-grid");
const cardsGrid = document.getElementById("cards-grid");
const detailPanel = document.getElementById("detail-panel");
const comparisonTable = document.getElementById("comparison-table");
const boardSummary = document.getElementById("board-summary");
const criteriaForm = document.getElementById("criteria-form");
const filterForm = document.getElementById("filter-form");
const manualForm = document.getElementById("manual-form");
const pasteForm = document.getElementById("paste-form");
const csvForm = document.getElementById("csv-form");
const urlForm = document.getElementById("url-form");
const csvStatus = document.getElementById("csv-status");
const discoveryForm = document.getElementById("discovery-form");
const discoveryProviders = document.getElementById("discovery-providers");
const discoveryRuns = document.getElementById("discovery-runs");
const discoveryStatus = document.getElementById("discovery-status");
const savedSearchSelector = document.getElementById("saved-search-selector");
const mockDiscoveryButton = document.getElementById("mock-discovery-button");
const bookmarkletLink = document.getElementById("bookmarklet-link");
const bookmarkletCode = document.getElementById("bookmarklet-code");
const clipForm = document.getElementById("clip-form");
const clipStatus = document.getElementById("clip-status");
const systemStatus = document.getElementById("system-status");
const dataQuality = document.getElementById("data-quality");
const backupButton = document.getElementById("backup-button");
const fullImportForm = document.getElementById("full-import-form");
const systemStatusMessage = document.getElementById("system-status-message");
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
  }).format(value || 0);
}

function formatDate(value) {
  if (!value) return "None";
  return new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function scoreOf(listing) {
  return listing.score_breakdown || listing.score || {};
}

function scoreValue(listing, key) {
  const score = scoreOf(listing);
  return Number(score[key] ?? listing[key] ?? 0);
}

function statusLabel(value) {
  return String(value || "unknown").replaceAll("_", " ");
}

function marketLabel(value) {
  const labels = {
    below_typical_low: "below typical low",
    below_market: "below market",
    near_market: "near market",
    above_typical_high: "above typical high",
    unknown: "market unknown",
  };
  return labels[value] || statusLabel(value);
}

function rentDeltaText(score) {
  if (!score?.benchmark_used || score.rent_delta_vs_median == null) return "No benchmark";
  const amount = currency(Math.abs(score.rent_delta_vs_median));
  const direction = score.rent_delta_vs_median < 0 ? "below" : score.rent_delta_vs_median > 0 ? "above" : "at";
  if (direction === "at") return `At ${score.benchmark_city} median`;
  return `${amount} ${direction} ${score.benchmark_city} median`;
}

function decodeBase64Url(value) {
  const normalized = value.replaceAll("-", "+").replaceAll("_", "/");
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
  const binary = atob(padded);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

function parseClipPayload(rawValue) {
  const raw = rawValue.trim();
  if (!raw) throw new Error("Paste clipped JSON first.");
  const hashMatch = raw.match(/browser-clip=([^&\s]+)/);
  if (hashMatch) return JSON.parse(decodeBase64Url(hashMatch[1]));
  return JSON.parse(raw);
}

function setClipStatus(message, tone = "normal") {
  if (!clipStatus) return;
  clipStatus.textContent = message;
  clipStatus.dataset.tone = tone;
}

function setSystemStatus(message, tone = "normal") {
  if (!systemStatusMessage) return;
  systemStatusMessage.textContent = message;
  systemStatusMessage.dataset.tone = tone;
}

function setDiscoveryStatus(message, tone = "normal") {
  if (!discoveryStatus) return;
  discoveryStatus.textContent = message;
  discoveryStatus.dataset.tone = tone;
}

function appendEmptyState(node) {
  node.innerHTML = "";
  node.appendChild(emptyStateTemplate.content.cloneNode(true));
}

function renderSummary() {
  if (!state.criteria) return;
  const total = state.listings.length;
  const strongMatches = state.listings.filter((listing) => scoreValue(listing, "match_score") >= 90).length;
  const needsReview = state.listings.filter((listing) => listing.decision_status === "needs_review" || scoreOf(listing).needs_review_badges?.length).length;
  const watched = state.listings.filter((listing) => ["shortlist", "tour"].includes(listing.watchlist_status)).length;
  const priced = state.listings.filter((listing) => listing.price > 0);
  const averageRent = priced.length ? priced.reduce((sum, listing) => sum + listing.price, 0) / priced.length : 0;
  const lowestRent = priced.length ? Math.min(...priced.map((listing) => listing.price)) : 0;
  const bestDeal = state.listings.length ? Math.max(...state.listings.map((listing) => scoreValue(listing, "deal_score"))) : 0;

  criteriaSummary.textContent = `${state.criteria.county} ${state.criteria.state} · ${state.criteria.min_bedrooms}+ bedrooms · backyard required · garage required`;
  heroStats.innerHTML = `
    <div class="stat-card"><span>Total</span><strong>${total}</strong></div>
    <div class="stat-card"><span>Strong matches</span><strong>${strongMatches}</strong></div>
    <div class="stat-card"><span>Needs review</span><strong>${needsReview}</strong></div>
    <div class="stat-card"><span>Average rent</span><strong>${currency(averageRent)}</strong></div>
    <div class="stat-card"><span>Lowest rent</span><strong>${currency(lowestRent)}</strong></div>
    <div class="stat-card"><span>Best deal</span><strong>${bestDeal.toFixed(0)}</strong></div>
    <div class="stat-card"><span>Watched</span><strong>${watched}</strong></div>
  `;
  boardSummary.textContent = `${total} listings ranked by explainable score. Unknown backyard/garage ranks below confirmed yes and above confirmed no.`;
}

function signalBadge(label, status) {
  return `<span class="signal signal-${escapeHtml(status)}">${escapeHtml(label)}: ${escapeHtml(statusLabel(status))}</span>`;
}

function renderQueue() {
  if (!state.listings.length) {
    appendEmptyState(rankingGrid);
    return;
  }

  if (!state.selectedListingId || !state.listings.some((listing) => listing.id === state.selectedListingId)) {
    state.selectedListingId = state.listings[0].id;
  }

  rankingGrid.innerHTML = state.listings
    .map((listing, index) => {
      const score = scoreOf(listing);
      const badges = score.needs_review_badges || [];
      const selected = listing.id === state.selectedListingId ? " selected" : "";
      return `
        <button class="queue-item${selected}" type="button" data-listing-id="${listing.id}">
          <div class="queue-rank">#${index + 1}</div>
          <div class="queue-main">
            <div class="queue-title-row">
              <h3>${escapeHtml(listing.title)}</h3>
              <span class="badge score">${score.overall_score?.toFixed?.(0) ?? score.total_score?.toFixed?.(0) ?? "0"}</span>
            </div>
            <p>${escapeHtml(listing.address_line1 || "Address pending")} · ${escapeHtml(listing.city)}</p>
            <div class="metric-row">
              <span>${currency(listing.price)}</span>
              <span>${listing.bedrooms} bd / ${listing.bathrooms} ba</span>
              <span>${listing.square_feet || "?"} sqft</span>
              <span>${escapeHtml(rentDeltaText(score))}</span>
              <span>Match ${score.match_score?.toFixed?.(0) ?? "0"}</span>
              <span>Deal ${score.deal_score?.toFixed?.(0) ?? "0"}</span>
              <span>Confidence ${score.confidence_score?.toFixed?.(0) ?? "0"}</span>
            </div>
            <div class="signal-row">
              ${signalBadge("Backyard", listing.backyard_status)}
              ${signalBadge("Garage", listing.garage_status)}
              <span class="badge">${escapeHtml(statusLabel(listing.decision_status))}</span>
              ${badges.map((badge) => `<span class="badge warning">${escapeHtml(badge)}</span>`).join("")}
            </div>
            <p class="next-action">${escapeHtml(listing.next_action || score.next_actions?.[0] || "No next action set")}</p>
          </div>
        </button>
      `;
    })
    .join("");
}

function renderCards() {
  if (!state.listings.length) {
    appendEmptyState(cardsGrid);
    return;
  }

  cardsGrid.innerHTML = state.listings
    .slice(0, 6)
    .map((listing) => {
      const score = scoreOf(listing);
      return `
        <article class="listing-card">
          <div class="listing-card-top">
            <div>
              <div class="card-meta">
                <span class="source-badge">${escapeHtml(listing.source_name)} · ${escapeHtml(listing.source_type)}</span>
                <span class="badge score">Overall ${score.overall_score?.toFixed?.(0) ?? "0"}</span>
                <span class="badge">Priority ${escapeHtml(listing.priority)}</span>
              </div>
              <h3>${escapeHtml(listing.title)}</h3>
              <p>${escapeHtml(listing.city)} · ${currency(listing.price)} · ${listing.bedrooms} bd</p>
            </div>
          </div>
          <div class="signal-row">
            ${signalBadge("Backyard", listing.backyard_status)}
            ${signalBadge("Garage", listing.garage_status)}
            <span>${escapeHtml(statusLabel(listing.decision_status))}</span>
          </div>
          <p>${escapeHtml(score.reasons?.[0] || listing.description || "No explanation available.")}</p>
        </article>
      `;
    })
    .join("");
}

function renderDetail() {
  const listing = state.listings.find((item) => item.id === state.selectedListingId);
  if (!listing) {
    detailPanel.innerHTML = `<div class="empty-state"><h3>Select a listing</h3><p>The score breakdown and workflow controls will appear here.</p></div>`;
    return;
  }
  const score = scoreOf(listing);
  const sourceLink = listing.source_url
    ? `<a class="pill" href="${escapeHtml(listing.source_url)}" target="_blank" rel="noreferrer">Open source</a>`
    : `<span class="pill">No source URL</span>`;
  const benchmarkBadge = score.benchmark_used
    ? `<span class="badge ${score.market_label === "below_market" || score.market_label === "below_typical_low" ? "score" : ""}">${escapeHtml(marketLabel(score.market_label))}</span>`
    : `<span class="badge warning">No benchmark</span>`;
  const benchmarkSection = score.benchmark_used
    ? `
      <div class="detail-section benchmark-section">
        <h3>Market Benchmark</h3>
        <div class="benchmark-grid">
          <div><span>City</span><strong>${escapeHtml(score.benchmark_city)}</strong></div>
          <div><span>3BR median</span><strong>${currency(score.median_rent_3br)}</strong></div>
          <div><span>Typical range</span><strong>${currency(score.typical_low_3br)}-${currency(score.typical_high_3br)}</strong></div>
          <div><span>Delta</span><strong>${escapeHtml(rentDeltaText(score))}</strong></div>
          <div><span>Delta %</span><strong>${score.rent_delta_percent?.toFixed?.(1) ?? "0"}%</strong></div>
          <div><span>Confidence</span><strong>${escapeHtml(score.benchmark_confidence || "unknown")}</strong></div>
        </div>
        <p>${escapeHtml(score.benchmark_notes || "Editable benchmark. Verify manually before deciding.")}</p>
        ${
          score.benchmark_used_fallback
            ? `<p class="benchmark-warning">Using county fallback because no city benchmark was found.</p>`
            : ""
        }
      </div>
    `
    : `
      <div class="detail-section benchmark-section">
        <h3>Market Benchmark</h3>
        <p>No city or county benchmark was available. Deal score used fallback price heuristics.</p>
      </div>
    `;
  detailPanel.innerHTML = `
    <div class="detail-header">
      <div>
        <p class="eyebrow">Listing intelligence</p>
        <h2>${escapeHtml(listing.title)}</h2>
        <p>${escapeHtml(listing.city)} · ${currency(listing.price)} · ${listing.bedrooms} bd / ${listing.bathrooms} ba</p>
      </div>
      <div class="detail-badges">
        <span class="badge score">${score.overall_score?.toFixed?.(0) ?? "0"}</span>
        ${benchmarkBadge}
      </div>
    </div>
    <div class="score-grid">
      <div><span>Match</span><strong>${score.match_score?.toFixed?.(0) ?? "0"}</strong></div>
      <div><span>Deal</span><strong>${score.deal_score?.toFixed?.(0) ?? "0"}</strong></div>
      <div><span>Confidence</span><strong>${score.confidence_score?.toFixed?.(0) ?? "0"}</strong></div>
      <div><span>Complete</span><strong>${score.completeness_score?.toFixed?.(0) ?? "0"}</strong></div>
      <div><span>Fresh</span><strong>${score.freshness_score?.toFixed?.(0) ?? "0"}</strong></div>
      <div><span>Source</span><strong>${score.source_reliability_score?.toFixed?.(0) ?? "0"}</strong></div>
    </div>
    <div class="detail-section">
      <h3>Reasons</h3>
      <ul>${(score.reasons || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No positive reasons yet.</li>"}</ul>
    </div>
    <div class="detail-section">
      <h3>Warnings</h3>
      <ul>${(score.warnings || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No warnings.</li>"}</ul>
    </div>
    <div class="detail-section">
      <h3>Evidence</h3>
      <p><strong>Backyard:</strong> ${escapeHtml(listing.backyard_evidence || "No evidence stored")}</p>
      <p><strong>Garage:</strong> ${escapeHtml(listing.garage_evidence || "No evidence stored")}</p>
      <p><strong>Raw text:</strong> ${escapeHtml(listing.raw_text || "No raw pasted text")}</p>
      ${sourceLink}
    </div>
    ${benchmarkSection}
    <form class="detail-form" id="decision-form">
      <h3>Decision</h3>
      <div class="split-fields">
        <label>Decision status
          <select name="decision_status">
            ${["new", "promising", "needs_review", "contacted", "tour_scheduled", "rejected", "archived"]
              .map((status) => `<option value="${status}" ${listing.decision_status === status ? "selected" : ""}>${statusLabel(status)}</option>`)
              .join("")}
          </select>
        </label>
        <label>Priority
          <select name="priority">
            ${["low", "medium", "high"].map((priority) => `<option value="${priority}" ${listing.priority === priority ? "selected" : ""}>${priority}</option>`).join("")}
          </select>
        </label>
      </div>
      <label>Next action
        <input type="text" name="next_action" value="${escapeHtml(listing.next_action || score.next_actions?.[0] || "")}" />
      </label>
      <label>Decision reason
        <textarea name="decision_reason" rows="2">${escapeHtml(listing.decision_reason || "")}</textarea>
      </label>
      <button type="submit" class="button-primary">Save Decision</button>
    </form>
    <form class="detail-form" id="watchlist-form">
      <h3>Watchlist</h3>
      <div class="split-fields">
        <label>Watch status
          <select name="watchlist_status">
            ${["review", "shortlist", "tour", "needs_manual_review", "rejected", "archived"]
              .map((status) => `<option value="${status}" ${listing.watchlist_status === status ? "selected" : ""}>${statusLabel(status)}</option>`)
              .join("")}
          </select>
        </label>
        <label>Reason
          <input type="text" name="reason" placeholder="Optional reason" />
        </label>
      </div>
      <button type="submit" class="button-secondary">Save Watchlist</button>
    </form>
    <form class="detail-form" id="notes-form">
      <h3>Private Notes</h3>
      <textarea name="note" rows="3" placeholder="Add a note">${escapeHtml(listing.private_notes || "")}</textarea>
      <button type="submit" class="button-secondary">Add Note</button>
    </form>
  `;
}

function renderTable() {
  if (!state.listings.length) {
    comparisonTable.innerHTML = `<tr><td colspan="17">No listings match the current filters.</td></tr>`;
    return;
  }

  comparisonTable.innerHTML = state.listings
    .map((listing, index) => {
      const score = scoreOf(listing);
      return `
        <tr>
          <td>#${index + 1}</td>
          <td>${escapeHtml(listing.title)}</td>
          <td>${currency(listing.price)}</td>
          <td>${listing.bedrooms} / ${listing.bathrooms}</td>
          <td>${listing.square_feet || "?"}</td>
          <td>${score.price_per_bedroom ? currency(score.price_per_bedroom) : "?"}</td>
          <td>${score.price_per_sqft ? `$${score.price_per_sqft.toFixed(2)}` : "?"}</td>
          <td>${escapeHtml(listing.city)}</td>
          <td>${escapeHtml(rentDeltaText(score))}</td>
          <td>${escapeHtml(listing.neighborhood || "-")}</td>
          <td>${escapeHtml(listing.backyard_status)}</td>
          <td>${escapeHtml(listing.garage_status)}</td>
          <td>${listing.pets_allowed ? "Yes" : "No / ?"}</td>
          <td>${escapeHtml(listing.source_name)}</td>
          <td>${score.confidence_score?.toFixed?.(0) ?? 0}</td>
          <td>${escapeHtml(statusLabel(listing.decision_status))}</td>
          <td>${escapeHtml(listing.watchlist_status)}</td>
        </tr>
      `;
    })
    .join("");
}

function populateCriteriaForm() {
  if (!state.criteria) return;
  const criteria = state.criteria;
  criteriaForm.elements.county.value = criteria.county || "";
  criteriaForm.elements.city.value = criteria.city || "";
  criteriaForm.elements.preferred_cities.value = (criteria.preferred_cities || []).join(", ");
  criteriaForm.elements.min_bedrooms.value = criteria.min_bedrooms || 0;
  criteriaForm.elements.min_bathrooms.value = criteria.min_bathrooms || 0;
  criteriaForm.elements.max_price.value = criteria.max_price || "";
  criteriaForm.elements.min_sqft.value = criteria.min_sqft || "";
  criteriaForm.elements.require_backyard.checked = criteria.require_backyard;
  criteriaForm.elements.require_garage.checked = criteria.require_garage;
  criteriaForm.elements.allow_unknown_backyard.checked = criteria.allow_unknown_backyard;
  criteriaForm.elements.allow_unknown_garage.checked = criteria.allow_unknown_garage;
  criteriaForm.elements.pets_required.checked = criteria.pets_required;
  criteriaForm.elements.notes.value = criteria.notes || "";

  filterForm.elements.min_bedrooms.value = criteria.min_bedrooms || 0;
  filterForm.elements.max_price.value = criteria.max_price || "";
  filterForm.elements.backyard.value = criteria.allow_unknown_backyard ? "yes_unknown" : "yes";
  filterForm.elements.garage.value = criteria.allow_unknown_garage ? "yes_unknown" : "yes";
}

function populateFilterSelects() {
  const citySelect = filterForm.elements.city;
  const sourceSelect = filterForm.elements.source_name;
  const currentCity = citySelect.value;
  const currentSource = sourceSelect.value;
  const cities = [...new Set(state.listings.map((listing) => listing.city).filter(Boolean))].sort();
  const sources = [...new Set(state.listings.map((listing) => listing.source_name).filter(Boolean))].sort();
  citySelect.innerHTML = `<option value="">All Orange County</option>${cities.map((city) => `<option value="${escapeHtml(city)}">${escapeHtml(city)}</option>`).join("")}`;
  sourceSelect.innerHTML = `<option value="">All sources</option>${sources.map((source) => `<option value="${escapeHtml(source)}">${escapeHtml(source)}</option>`).join("")}`;
  if (cities.includes(currentCity)) citySelect.value = currentCity;
  if (sources.includes(currentSource)) sourceSelect.value = currentSource;
}

function renderAll() {
  renderSummary();
  renderQueue();
  renderCards();
  renderDetail();
  renderTable();
  populateCriteriaForm();
  populateFilterSelects();
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

async function loadSystemPanel() {
  if (!systemStatus || !dataQuality) return;
  try {
    const [status, quality] = await Promise.all([fetchJson("/api/admin/status"), fetchJson("/api/admin/data-quality")]);
    const statusData = status.data;
    const qualityData = quality.data;
    systemStatus.innerHTML = `
      <div><span>Database</span><strong>${escapeHtml(statusData.database_path)}</strong></div>
      <div><span>Listings</span><strong>${statusData.total_listings}</strong></div>
      <div><span>Last backup</span><strong>${escapeHtml(statusData.last_backup_at || "No backup yet")}</strong></div>
      <div><span>Version</span><strong>${escapeHtml(statusData.app_version)}</strong></div>
    `;
    const counts = qualityData.counts || {};
    const warnings = qualityData.warnings || [];
    dataQuality.innerHTML = `
      <strong>Data quality</strong>
      <p>${counts.needs_review || 0} need review · ${counts.unknown_backyard || 0} unknown backyard · ${counts.unknown_garage || 0} unknown garage · ${counts.potential_duplicate_groups || 0} duplicate groups</p>
      <p>Benchmark reviewed: ${escapeHtml(qualityData.benchmark_last_reviewed || "unknown")}</p>
      ${warnings.length ? `<p class="benchmark-warning">${warnings.map(escapeHtml).join(" ")}</p>` : "<p>No system warnings.</p>"}
    `;
  } catch (error) {
    dataQuality.textContent = `System status failed: ${error.message}`;
  }
}

async function loadDiscoveryProviders() {
  if (!discoveryProviders) return;
  try {
    const providers = await fetchJson("/api/discovery/providers");
    const missingKeyProviders = providers.filter((provider) => provider.requires_api_key && !provider.configured);
    discoveryProviders.innerHTML = providers
      .map((provider) => {
        const disabled = provider.configured ? "" : " disabled";
        const checked = provider.enabled_by_default && provider.configured ? " checked" : "";
        const statusTone = provider.configured ? "success" : "warning";
        return `
          <label class="provider-option${disabled}">
            <input type="checkbox" name="provider_keys" value="${escapeHtml(provider.key)}"${checked}${disabled} />
            <span>
              <strong>${escapeHtml(provider.source_name)}</strong>
              <small>${escapeHtml(provider.key)} · ${escapeHtml(provider.source_type)} · <em class="tone-${statusTone}">${escapeHtml(provider.status)}</em></small>
              <small>${escapeHtml(provider.compliance_notes)}</small>
            </span>
          </label>
        `;
      })
      .join("") +
      (missingKeyProviders.length
        ? `<p class="provider-warning">API providers not configured: ${missingKeyProviders
            .map((provider) => escapeHtml(provider.key))
            .join(", ")}. Use mock discovery or set provider keys locally.</p>`
        : "");
  } catch (error) {
    discoveryProviders.textContent = `Could not load discovery providers: ${error.message}`;
  }
}

async function loadSavedSearches() {
  if (!savedSearchSelector) return;
  try {
    const searches = await fetchJson("/api/saved-searches");
    const activeSearches = searches.filter((search) => search.is_active);
    savedSearchSelector.innerHTML = activeSearches
      .map(
        (search) => `
          <option value="${search.id}">${escapeHtml(search.name)} · ${search.min_bedrooms}+ BR · ${search.cities.length} cities</option>
        `,
      )
      .join("");
  } catch (error) {
    savedSearchSelector.innerHTML = `<option value="">Could not load saved searches</option>`;
  }
}

async function loadDiscoveryRuns() {
  if (!discoveryRuns) return;
  try {
    const runs = await fetchJson("/api/discovery/runs?limit=5");
    if (!runs.length) {
      discoveryRuns.innerHTML = "<p>No discovery runs recorded yet.</p>";
      return;
    }
    discoveryRuns.innerHTML = runs
      .map(
        (run) => `
          <div class="run-row">
            <span>${escapeHtml(run.source_name)}</span>
            <strong>${escapeHtml(run.status)}</strong>
            <small>${run.dry_run ? "dry run" : "import"} · ${run.rows_imported} candidates · ${run.records_created} new · ${run.records_updated} updated · ${run.possible_duplicates} duplicate warnings</small>
          </div>
        `,
      )
      .join("");
  } catch (error) {
    discoveryRuns.textContent = `Could not load discovery run history: ${error.message}`;
  }
}

async function initializeBookmarklet() {
  if (!bookmarkletLink || !bookmarkletCode) return;
  const source = await fetch("/static/js/bookmarklet.js").then((response) => response.text());
  const code = `javascript:${source.trim().replace(/\s*\n\s*/g, " ")}`;
  bookmarkletLink.href = code;
  bookmarkletCode.value = code;

  if (window.location.hash.startsWith("#browser-clip=") && clipForm) {
    try {
      const payload = parseClipPayload(window.location.hash.slice(1));
      clipForm.elements.clip_payload.value = JSON.stringify(payload, null, 2);
      setClipStatus("Fallback clip loaded. Review the JSON, then import it.", "warning");
    } catch (error) {
      setClipStatus(`Could not read fallback clip from URL hash: ${error.message}`, "error");
    }
  }
}

rankingGrid.addEventListener("click", (event) => {
  const button = event.target.closest("[data-listing-id]");
  if (!button) return;
  state.selectedListingId = Number(button.dataset.listingId);
  renderAll();
});

criteriaForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = {
    name: state.criteria?.name || "Orange County 3BR Yard + Garage",
    county: criteriaForm.elements.county.value,
    state: "CA",
    city: criteriaForm.elements.city.value || null,
    preferred_cities: criteriaForm.elements.preferred_cities.value
      .split(",")
      .map((city) => city.trim())
      .filter(Boolean),
    min_bedrooms: Number(criteriaForm.elements.min_bedrooms.value || 0),
    min_bathrooms: Number(criteriaForm.elements.min_bathrooms.value || 0),
    max_price: criteriaForm.elements.max_price.value ? Number(criteriaForm.elements.max_price.value) : null,
    min_sqft: criteriaForm.elements.min_sqft.value ? Number(criteriaForm.elements.min_sqft.value) : null,
    require_backyard: criteriaForm.elements.require_backyard.checked,
    require_garage: criteriaForm.elements.require_garage.checked,
    allow_unknown_backyard: criteriaForm.elements.allow_unknown_backyard.checked,
    allow_unknown_garage: criteriaForm.elements.allow_unknown_garage.checked,
    pets_required: criteriaForm.elements.pets_required.checked,
    notes: criteriaForm.elements.notes.value || null,
    weights: state.criteria?.weights || undefined,
  };
  await fetchJson("/api/search-criteria", { method: "POST", body: JSON.stringify(payload) });
  await loadDashboard();
});

filterForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const params = new URLSearchParams();
  for (const field of ["city", "source_name", "min_bedrooms", "max_price", "backyard", "garage", "watchlist_status", "decision_status", "sort_by"]) {
    if (filterForm.elements[field]?.value) params.set(field, filterForm.elements[field].value);
  }
  if (filterForm.elements.needs_review.value) params.set("needs_review", filterForm.elements.needs_review.value);
  if (filterForm.elements.require_backyard.checked) params.set("require_backyard", "true");
  if (filterForm.elements.require_garage.checked) params.set("require_garage", "true");
  if (filterForm.elements.pets_required.checked) params.set("pets_required", "true");
  await loadDashboard(params.toString() ? `?${params.toString()}` : "");
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
  const listing = await fetchJson("/api/listings/manual", { method: "POST", body: JSON.stringify(payload) });
  state.selectedListingId = listing.id;
  manualForm.reset();
  await loadDashboard();
});

pasteForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const listing = await fetchJson("/api/import/paste", {
    method: "POST",
    body: JSON.stringify({
      raw_text: pasteForm.elements.raw_text.value,
      source_name: pasteForm.elements.source_name.value || null,
      source_url: pasteForm.elements.source_url.value || null,
      notes: pasteForm.elements.notes.value || null,
    }),
  });
  state.selectedListingId = listing.id;
  pasteForm.reset();
  await loadDashboard();
});

csvForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  let csvText = csvForm.elements.csv_text.value;
  const file = csvForm.elements.csv_file.files[0];
  if (file) csvText = await file.text();
  const summary = await fetchJson("/api/import/csv", {
    method: "POST",
    body: JSON.stringify({
      csv_text: csvText,
      source_name: csvForm.elements.source_name.value || "CSV Import",
    }),
  });
  csvStatus.textContent = `${summary.rows_imported} imported, ${summary.rows_skipped} skipped`;
  if (summary.listings?.[0]) state.selectedListingId = summary.listings[0].id;
  csvForm.reset();
  await loadDashboard();
});

urlForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const listing = await fetchJson("/api/listings/url-reference", {
    method: "POST",
    body: JSON.stringify({
      url: urlForm.elements.url.value,
      title: urlForm.elements.title.value || null,
      notes: urlForm.elements.notes.value || null,
    }),
  });
  state.selectedListingId = listing.id;
  urlForm.reset();
  await loadDashboard();
});

if (discoveryForm) {
  const discoveryPayload = (providerKeys = null) => {
    const selectedProviders = providerKeys || [...discoveryForm.querySelectorAll('input[name="provider_keys"]:checked')].map((item) => item.value);
    const savedSearchId = Number(discoveryForm.elements.saved_search_id?.value || 0);
    return {
      saved_search_id: savedSearchId || null,
      provider_keys: selectedProviders,
      limit: Number(discoveryForm.elements.limit.value || 25),
      dry_run: discoveryForm.elements.dry_run.checked,
      import_results: !discoveryForm.elements.dry_run.checked,
    };
  };

  const submitDiscoveryPayload = async (payload, label = "Running approved-provider discovery...") => {
    setDiscoveryStatus(label, "warning");
    const result = await fetchJson("/api/discovery/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const summaries = result.data.summaries || [];
    const created = summaries.reduce((sum, item) => sum + (item.records_created || 0), 0);
    const updated = summaries.reduce((sum, item) => sum + (item.records_updated || 0), 0);
    const duplicates = summaries.reduce((sum, item) => sum + (item.possible_duplicates || 0), 0);
    const candidates = summaries.reduce((sum, item) => sum + (item.rows_imported || item.candidates?.length || 0), 0);
    const warnings = summaries.flatMap((item) => item.warnings || []);
    if (result.data.listings?.[0]) state.selectedListingId = result.data.listings[0].id;
    setDiscoveryStatus(
      payload.dry_run
        ? `Dry run found ${candidates} matching candidates.`
        : `Discovery imported ${created} new and updated ${updated} existing listings. ${duplicates} duplicate warnings. ${warnings.slice(0, 2).join(" ")}`,
      warnings.length || result.errors?.length ? "warning" : "success",
    );
    await loadDashboard();
    await loadSystemPanel();
    await loadDiscoveryRuns();
  };

  discoveryForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await submitDiscoveryPayload(discoveryPayload());
    } catch (error) {
      setDiscoveryStatus(`Discovery failed: ${error.message}`, "error");
    }
  });

  mockDiscoveryButton?.addEventListener("click", async () => {
    try {
      await submitDiscoveryPayload(discoveryPayload(["mock"]), "Running mock discovery...");
    } catch (error) {
      setDiscoveryStatus(`Mock discovery failed: ${error.message}`, "error");
    }
  });

  discoveryForm.querySelectorAll("[data-discovery-filter]").forEach((button) => {
    button.addEventListener("click", async () => {
      const filter = button.dataset.discoveryFilter;
      const query =
        filter === "needs-review"
          ? "?needs_review_from_discovery=true&sort_by=newest"
          : "?new_from_discovery=true&sort_by=newest";
      await loadDashboard(query);
      setDiscoveryStatus(`Showing ${button.textContent.toLowerCase()}.`, "normal");
    });
  });
}

clipForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = parseClipPayload(clipForm.elements.clip_payload.value);
    const result = await fetchJson("/api/import/clip", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.selectedListingId = result.data.listing_id;
    clipForm.reset();
    setClipStatus(
      `Imported listing #${result.data.listing_id} from ${result.data.source_name}. ${result.data.warnings.join(" ")}`,
      result.data.warnings.length ? "warning" : "success",
    );
    await loadDashboard();
  } catch (error) {
    setClipStatus(`Browser clip import failed: ${error.message}`, "error");
  }
});

backupButton.addEventListener("click", async () => {
  try {
    const result = await fetchJson("/api/admin/backup", { method: "POST", body: JSON.stringify({}) });
    setSystemStatus(`Backup created: ${result.data.backup_path}`, "success");
    await loadSystemPanel();
  } catch (error) {
    setSystemStatus(`Backup failed: ${error.message}`, "error");
  }
});

fullImportForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const payload = JSON.parse(fullImportForm.elements.full_json.value);
    const result = await fetchJson("/api/import/full-json", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    const summary = result.data;
    setSystemStatus(
      `Import complete: ${summary.records_imported} imported, ${summary.records_updated} updated, ${summary.records_skipped} skipped.`,
      summary.errors?.length ? "warning" : "success",
    );
    fullImportForm.reset();
    await loadDashboard();
    await loadSystemPanel();
  } catch (error) {
    setSystemStatus(`Import failed: ${error.message}`, "error");
  }
});

detailPanel.addEventListener("submit", async (event) => {
  event.preventDefault();
  const listingId = state.selectedListingId;
  if (!listingId) return;
  if (event.target.id === "decision-form") {
    await fetchJson(`/api/listings/${listingId}/decision`, {
      method: "PATCH",
      body: JSON.stringify({
        decision_status: event.target.elements.decision_status.value,
        priority: event.target.elements.priority.value,
        next_action: event.target.elements.next_action.value || null,
        decision_reason: event.target.elements.decision_reason.value || null,
      }),
    });
  }
  if (event.target.id === "watchlist-form") {
    await fetchJson(`/api/listings/${listingId}/watchlist`, {
      method: "PATCH",
      body: JSON.stringify({
        watchlist_status: event.target.elements.watchlist_status.value,
        reason: event.target.elements.reason.value || null,
      }),
    });
  }
  if (event.target.id === "notes-form") {
    await fetchJson(`/api/listings/${listingId}/notes`, {
      method: "PATCH",
      body: JSON.stringify({ note: event.target.elements.note.value }),
    });
  }
  await loadDashboard();
});

initializeBookmarklet()
  .then(() => Promise.all([loadDashboard(), loadSystemPanel(), loadDiscoveryProviders(), loadSavedSearches(), loadDiscoveryRuns()]))
  .catch((error) => {
    boardSummary.textContent = `Failed to load dashboard: ${error.message}`;
  });
