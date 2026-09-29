/**
 * AeroPulse - Real-Time Airfare Intelligence Client Application
 * Light-theme optimized, data-first aviation analytics workspace.
 */

const API_BASE = "";

// Global App State
const AppState = {
  currentView: "view-welcome", // Entry page
  trendDays: 30,
  kpis: null,
  trendData: null,
  routesData: null,
  selectedRoute: "ALL",
  alertsSeverity: "ALL",
  explorer: {
    search: "",
    origin: "ALL",
    destination: "ALL",
    airline: "ALL",
    window: "ALL",
    source: "ALL",
    page: 1,
    limit: 15
  }
};

document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initEventListeners();
  loadInitialData();
});

function initNavigation() {
  // Sidebar navigation links
  const navItems = document.querySelectorAll(".nav-item[data-view]");
  navItems.forEach(item => {
    item.addEventListener("click", (e) => {
      e.preventDefault();
      const targetView = item.getAttribute("data-view");
      navigateTo(targetView);
    });
  });

  // Action buttons with data-navigate
  document.querySelectorAll("[data-navigate]").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const target = btn.getAttribute("data-navigate");
      navigateTo(target);
    });
  });

  // Brand logo click
  const brandLogo = document.getElementById("sidebar-brand-logo");
  if (brandLogo) {
    brandLogo.addEventListener("click", () => {
      navigateTo("view-welcome");
    });
  }
}

function navigateTo(viewId) {
  AppState.currentView = viewId;
  
  // Update sidebar active classes
  document.querySelectorAll(".nav-item").forEach(el => {
    if (el.getAttribute("data-view") === viewId) el.classList.add("active");
    else el.classList.remove("active");
  });

  // Update view containers
  document.querySelectorAll(".view-section").forEach(sec => {
    if (sec.id === viewId) sec.classList.add("active");
    else sec.classList.remove("active");
  });

  window.scrollTo({ top: 0, behavior: "smooth" });
  renderCurrentView();
}

function initEventListeners() {
  // Simulate Batch Button
  const simBtn = document.getElementById("btn-simulate-batch");
  if (simBtn) {
    simBtn.addEventListener("click", handleSimulateBatch);
  }

  // Trend Chart Time Range Pills (7D, 30D, 60D, 90D)
  document.querySelectorAll(".time-pill-btn[data-days]").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".time-pill-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const days = parseInt(btn.getAttribute("data-days"));
      AppState.trendDays = days;
      loadIndexTrend(days);
    });
  });

  // Airline comparison route selector
  const compRouteSel = document.getElementById("comp-route-select");
  if (compRouteSel) {
    compRouteSel.addEventListener("change", (e) => {
      AppState.selectedRoute = e.target.value;
      loadAirlineComparison(e.target.value);
    });
  }

  // Booking window route selector
  const bwRouteSel = document.getElementById("bw-route-select");
  if (bwRouteSel) {
    bwRouteSel.addEventListener("change", (e) => {
      loadBookingWindowAnalysis(e.target.value);
    });
  }

  // Alerts severity filter
  const alertSevSel = document.getElementById("alert-severity-filter");
  if (alertSevSel) {
    alertSevSel.addEventListener("change", (e) => {
      AppState.alertsSeverity = e.target.value;
      loadSpikeAlerts(e.target.value);
    });
  }

  // Explorer search & filter debounce
  const expSearch = document.getElementById("explorer-search");
  if (expSearch) {
    let debounceTimer;
    expSearch.addEventListener("input", (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        AppState.explorer.search = e.target.value;
        AppState.explorer.page = 1;
        loadExplorerData();
      }, 250);
    });
  }

  ["origin", "destination", "airline", "window", "source"].forEach(filterName => {
    const el = document.getElementById(`explorer-filter-${filterName}`);
    if (el) {
      el.addEventListener("change", (e) => {
        AppState.explorer[filterName] = e.target.value;
        AppState.explorer.page = 1;
        loadExplorerData();
      });
    }
  });

  // Export CSV button
  const exportBtn = document.getElementById("btn-export-csv");
  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      window.location.href = `${API_BASE}/api/export-csv?limit=5000`;
    });
  }

  // Modal Close
  const modalClose = document.getElementById("modal-drilldown-close");
  const modalBackdrop = document.getElementById("modal-drilldown-backdrop");
  if (modalClose && modalBackdrop) {
    modalClose.addEventListener("click", () => modalBackdrop.classList.remove("active"));
    modalBackdrop.addEventListener("click", (e) => {
      if (e.target === modalBackdrop) modalBackdrop.classList.remove("active");
    });
  }
}

// Initial Data Loading
async function loadInitialData() {
  await loadKPIs();
  await loadIndexTrend(AppState.trendDays);
  await loadTopRoutes();
  await loadRouteAnalytics();
  await loadAirlineComparison("ALL");
  await loadSpikeAlerts();
  await loadBookingWindowAnalysis("ALL");
  await loadSubsectors();
  await loadQualityMetrics();
  await loadExplorerData();
}

function renderCurrentView() {
  if (AppState.currentView === "view-dashboard") {
    if (AppState.trendData) renderTrendChart(AppState.trendData);
    if (AppState.routesData) renderIndiaNetworkMap(AppState.routesData, "india-routes-svg");
  } else if (AppState.currentView === "view-index") {
    if (AppState.trendData) renderIndexDeepdiveChart(AppState.trendData);
  } else if (AppState.currentView === "view-routes") {
    if (AppState.routesData) {
      renderIndiaNetworkMap(AppState.routesData, "india-routes-svg-full");
      renderRouteCards(AppState.routesData.routes);
    }
  } else if (AppState.currentView === "view-comparison") {
    loadAirlineComparison(AppState.selectedRoute);
  } else if (AppState.currentView === "view-booking") {
    loadBookingWindowAnalysis(document.getElementById("bw-route-select")?.value || "ALL");
  } else if (AppState.currentView === "view-welcome") {
    if (AppState.routesData) renderIndiaNetworkMap(AppState.routesData, "welcome-map-svg");
  }
}

// 1. Load Master KPIs
async function loadKPIs() {
  try {
    const res = await fetch(`${API_BASE}/api/kpis`);
    const data = await res.json();
    AppState.kpis = data;

    const kpi = data.kpis;
    
    // Header Ticker
    const tickerIndex = document.getElementById("header-ticker-index");
    if (tickerIndex) tickerIndex.innerText = kpi.airfare_index.toFixed(1);
    
    const deltaEl = document.getElementById("header-ticker-delta");
    if (deltaEl) {
      const isUp = kpi.percentage_change >= 0;
      deltaEl.innerText = `${isUp ? "+" : ""}${kpi.percentage_change.toFixed(1)}%`;
      deltaEl.className = `ticker-delta ${isUp ? "delta-up" : "delta-down"}`;
    }

    const tickerAvg = document.getElementById("header-ticker-avgfare");
    if (tickerAvg) tickerAvg.innerText = AeroCharts.formatCurrency(kpi.current_avg_fare);

    // Dashboard KPI Cards
    const elIndex = document.getElementById("kpi-airfare-index");
    if (elIndex) elIndex.innerText = kpi.airfare_index.toFixed(1);

    const elChange = document.getElementById("kpi-index-change");
    if (elChange) elChange.innerText = `+${kpi.percentage_change.toFixed(1)}% vs Base`;

    const elAvg = document.getElementById("kpi-avg-fare");
    if (elAvg) elAvg.innerText = AeroCharts.formatCurrency(kpi.current_avg_fare);

    const elBase = document.getElementById("kpi-base-fare");
    if (elBase) elBase.innerText = `Base: ${AeroCharts.formatCurrency(kpi.base_avg_fare)}`;

    const elRoutes = document.getElementById("kpi-routes-count");
    if (elRoutes) elRoutes.innerText = kpi.active_routes_count || 26;

    const elAirlines = document.getElementById("kpi-airlines-count");
    if (elAirlines) elAirlines.innerText = kpi.active_airlines_count || 6;

    const elObs = document.getElementById("kpi-obs-count");
    if (elObs) elObs.innerText = (kpi.total_observations || 11000).toLocaleString("en-IN");

    const elAlerts = document.getElementById("kpi-alerts-count");
    if (elAlerts) elAlerts.innerText = data.active_alerts_count || 18;

    // Sidebar alert count
    const sidebarBadge = document.getElementById("sidebar-alert-badge");
    if (sidebarBadge) sidebarBadge.innerText = data.active_alerts_count;

    // Welcome page preview cards
    const wpIndex = document.getElementById("wp-kpi-index");
    if (wpIndex) wpIndex.innerText = kpi.airfare_index.toFixed(1);
    const wpAvg = document.getElementById("wp-kpi-avgfare");
    if (wpAvg) wpAvg.innerText = AeroCharts.formatCurrency(kpi.current_avg_fare);
    const wpRoutes = document.getElementById("wp-kpi-routes");
    if (wpRoutes) wpRoutes.innerText = kpi.active_routes_count || 26;
    const wpAlerts = document.getElementById("wp-kpi-alerts");
    if (wpAlerts) wpAlerts.innerText = data.active_alerts_count || 18;

    renderDashboardAlertsPreview(data.recent_alerts);
  } catch (err) {
    console.error("Error loading KPIs:", err);
  }
}

// 2. Load Index Trend
async function loadIndexTrend(days = 30) {
  try {
    const res = await fetch(`${API_BASE}/api/index-trend?days=${days}`);
    const data = await res.json();
    AppState.trendData = data.timeseries;
    renderTrendChart(data.timeseries);
  } catch (err) {
    console.error("Error loading trend data:", err);
  }
}

function renderTrendChart(timeseries) {
  AeroCharts.renderLineChart("chart-index-trend", {
    data: timeseries,
    xKey: "display_date",
    yKey: "airfare_index",
    benchmarkValue: 100.0,
    lineColor: "#0284c7",
    fillColor: "rgba(2, 132, 199, 0.12)"
  });
}

function renderIndexDeepdiveChart(timeseries) {
  AeroCharts.renderLineChart("chart-index-deepdive", {
    data: timeseries,
    xKey: "display_date",
    yKey: "airfare_index",
    benchmarkValue: 100.0,
    lineColor: "#0284c7",
    fillColor: "rgba(2, 132, 199, 0.15)"
  });

  AeroCharts.renderLineChart("chart-fare-breakdown-trend", {
    data: timeseries,
    xKey: "display_date",
    yKey: "average_fare",
    isCurrency: true,
    lineColor: "#10b981",
    fillColor: "rgba(16, 185, 129, 0.12)"
  });
}

// 3. Load Top Routes for Dashboard
async function loadTopRoutes() {
  try {
    const res = await fetch(`${API_BASE}/api/top-routes?limit=8`);
    const data = await res.json();
    const container = document.getElementById("dashboard-top-routes-grid");
    if (!container) return;

    container.innerHTML = data.top_routes.map(r => `
      <div class="top-route-item" onclick="openRouteFromDashboard('${r.route_key}')">
        <div class="top-route-header">
          <span>${r.route_label}</span>
          <span style="font-size:0.75rem; color:${r.percentage_change >= 0 ? '#dc2626' : '#059669'}; font-weight:700;">
            ${r.percentage_change >= 0 ? '+' : ''}${r.percentage_change}%
          </span>
        </div>
        <div class="top-route-fare">${AeroCharts.formatCurrency(r.avg_fare)}</div>
        <div class="top-route-meta">
          <span>Index: <strong>${r.airfare_index}</strong></span>
          <span>${r.observations} obs</span>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Error loading top routes:", err);
  }
}

window.openRouteFromDashboard = function(routeKey) {
  navigateTo("view-routes");
  setTimeout(() => {
    openRouteDrilldown(routeKey);
  }, 100);
};

// 4. Load Subsectors
async function loadSubsectors() {
  try {
    const res = await fetch(`${API_BASE}/api/subsectors`);
    const data = await res.json();
    const container = document.getElementById("subsectors-grid");
    if (!container) return;

    container.innerHTML = data.subsectors.map(s => `
      <div class="kpi-card" style="border-left: 4px solid var(--color-primary);">
        <div class="kpi-top">
          <span class="kpi-title">${s.sector}</span>
          <span class="badge ${s.change_pct >= 0 ? 'badge-red' : 'badge-green'}">${s.change_pct >= 0 ? '+' : ''}${s.change_pct}%</span>
        </div>
        <div class="kpi-value">${s.index.toFixed(1)}</div>
        <div class="kpi-subtitle">Avg Fare: ${AeroCharts.formatCurrency(s.average_fare)} • ${s.records} obs</div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Error loading subsectors:", err);
  }
}

// 5. Load Route Analytics & India Network Map
async function loadRouteAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/api/routes`);
    const data = await res.json();
    AppState.routesData = data;
    renderIndiaNetworkMap(data, "india-routes-svg");
    renderIndiaNetworkMap(data, "welcome-map-svg");
    renderRouteCards(data.routes);
  } catch (err) {
    console.error("Error loading route analytics:", err);
  }
}

function renderIndiaNetworkMap(data, svgElementId = "india-routes-svg") {
  const svg = document.getElementById(svgElementId);
  if (!svg || !data || !data.routes) return;

  const width = 600;
  const height = 650;
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

  function project(lat, lng) {
    const minLat = 7.5, maxLat = 33.5;
    const minLng = 68.0, maxLng = 93.5;
    const x = ((lng - minLng) / (maxLng - minLng)) * (width - 100) + 50;
    const y = ((maxLat - lat) / (maxLat - minLat)) * (height - 100) + 40;
    return { x, y };
  }

  let html = `
    <defs>
      <filter id="node-shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="1" stdDeviation="1.5" flood-color="#0f172a" flood-opacity="0.12"/>
      </filter>
    </defs>
  `;

  // Draw routes
  data.routes.forEach(r => {
    const p1 = project(r.origin_lat, r.origin_lng);
    const p2 = project(r.dest_lat, r.dest_lng);
    const strokeColor = r.tier === "High" ? "#ef4444" : r.tier === "Medium" ? "#f59e0b" : "#10b981";
    const strokeWidth = r.tier === "High" ? 2.0 : 1.4;

    const midX = (p1.x + p2.x) / 2;
    const midY = (p1.y + p2.y) / 2 - 20;

    html += `
      <path d="M ${p1.x} ${p1.y} Q ${midX} ${midY} ${p2.x} ${p2.y}"
            class="map-link"
            stroke="${strokeColor}"
            stroke-width="${strokeWidth}"
            fill="none"
            opacity="0.75"
            onclick="openRouteDrilldown('${r.route_key}')">
        <title>${r.origin_city} → ${r.destination_city} | Avg: ${AeroCharts.formatCurrency(r.avg_fare)} | Index: ${r.airfare_index}</title>
      </path>
    `;
  });

  // Draw Airport Hub Nodes
  Object.keys(data.airports).forEach(code => {
    const ap = data.airports[code];
    const pos = project(ap.lat, ap.lng);

    html += `
      <g class="map-node" transform="translate(${pos.x}, ${pos.y})">
        <circle r="7" fill="#ffffff" stroke="#0284c7" stroke-width="2.5" filter="url(#node-shadow)"></circle>
        <circle r="3" fill="#0284c7"></circle>
        <text x="9" y="3.5" fill="#0f172a" font-size="9.5" font-weight="700" font-family="Inter, sans-serif">${code}</text>
        <title>${ap.city} (${code})
${ap.name}</title>
      </g>
    `;
  });

  svg.innerHTML = html;
}

function renderRouteCards(routes) {
  const container = document.getElementById("route-cards-container");
  if (!container) return;

  container.innerHTML = routes.map(r => `
    <div class="top-route-item" style="padding: 16px;" onclick="openRouteDrilldown('${r.route_key}')">
      <div class="top-route-header">
        <span style="font-size: 0.92rem;">${r.origin_city} → ${r.destination_city}</span>
        <span class="badge badge-${r.badge_color}">${r.tier} Fare</span>
      </div>
      <div class="top-route-fare" style="font-size: 1.25rem;">${AeroCharts.formatCurrency(r.avg_fare)}</div>
      <div class="top-route-meta">
        <span>Index: <strong>${r.airfare_index}</strong></span>
        <span>${r.airlines_count} Carriers • ${r.observations_count} obs</span>
      </div>
    </div>
  `).join("");
}

// 6. Open Route Drilldown Modal
window.openRouteDrilldown = async function(routeKey) {
  try {
    const res = await fetch(`${API_BASE}/api/route-drilldown/${routeKey}`);
    const data = await res.json();

    document.getElementById("modal-route-title").innerText = `${data.origin_city} (${routeKey.split('-')[0]}) → ${data.destination_city} (${routeKey.split('-')[1]})`;
    document.getElementById("modal-route-avgfare").innerText = AeroCharts.formatCurrency(data.average_fare);
    document.getElementById("modal-route-index").innerText = data.airfare_index;

    const airContainer = document.getElementById("modal-airline-list");
    airContainer.innerHTML = data.airline_breakdown.map(a => `
      <div style="display: flex; justify-content: space-between; padding: 8px 12px; background: #f8fafc; border-radius: 6px; margin-bottom: 6px; border: 1px solid #e2e8f0;">
        <span style="font-weight: 600; font-size: 0.84rem;">${a.airline}</span>
        <span style="font-family: var(--font-mono); color: #0284c7; font-weight: 700;">${AeroCharts.formatCurrency(a.avg_fare)} (min ${AeroCharts.formatCurrency(a.min_fare)})</span>
      </div>
    `).join("");

    const winContainer = document.getElementById("modal-window-curve");
    winContainer.innerHTML = data.window_curve.map(w => `
      <div style="display: flex; justify-content: space-between; padding: 6px 10px; border-bottom: 1px solid #f1f5f9; font-size: 0.82rem;">
        <span>Advance: <strong>${w.window}</strong></span>
        <span style="font-family: var(--font-mono); font-weight: bold; color: #0f172a;">${AeroCharts.formatCurrency(w.avg_fare)}</span>
      </div>
    `).join("");

    document.getElementById("modal-drilldown-backdrop").classList.add("active");
  } catch (err) {
    console.error("Error loading route drilldown:", err);
  }
};

// 7. Airline Comparison
async function loadAirlineComparison(routeKey = "ALL") {
  try {
    const res = await fetch(`${API_BASE}/api/airline-comparison?route_key=${routeKey}`);
    const data = await res.json();

    const sel = document.getElementById("comp-route-select");
    if (sel && sel.children.length <= 1) {
      sel.innerHTML = data.all_available_routes.map(r => `<option value="${r}" ${r === routeKey ? "selected" : ""}>${r === "ALL" ? "All Domestic Routes" : r}</option>`).join("");
    }

    const routeNameEl = document.getElementById("comp-route-name");
    if (routeNameEl) routeNameEl.innerText = `${data.origin_city} → ${data.destination_city}`;
    
    const routeAvgEl = document.getElementById("comp-route-avg");
    if (routeAvgEl) routeAvgEl.innerText = AeroCharts.formatCurrency(data.overall_route_avg);

    // Render Airline cards
    const airCardsContainer = document.getElementById("airline-comp-cards");
    if (airCardsContainer) {
      airCardsContainer.innerHTML = data.airlines.map(a => `
        <div class="kpi-card" style="padding: 16px;">
          <div class="kpi-top">
            <span class="kpi-title">${a.airline}</span>
            <span class="badge badge-blue">${a.observations} obs</span>
          </div>
          <div class="kpi-value" style="font-size: 1.45rem; color: #0284c7;">${AeroCharts.formatCurrency(a.avg_fare)}</div>
          <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 6px; line-height: 1.5;">
            <div>Base Fare: <strong>${AeroCharts.formatCurrency(a.base_fare)}</strong></div>
            <div>GST (5%): <strong>${AeroCharts.formatCurrency(a.taxes)}</strong></div>
            <div>Airport & Security: <strong>${AeroCharts.formatCurrency(a.airport_fees)}</strong></div>
            <div>Convenience Fee: <strong>${AeroCharts.formatCurrency(a.convenience_fee)}</strong></div>
          </div>
        </div>
      `).join("");
    }

    // Render Dashboard Airline preview cards
    const dashAirContainer = document.getElementById("dashboard-airline-comp-container");
    if (dashAirContainer) {
      dashAirContainer.innerHTML = data.airlines.slice(0, 6).map(a => `
        <div class="top-route-item">
          <div class="top-route-header">
            <span>${a.airline}</span>
            <span class="badge badge-blue">Index ${a.airfare_index}</span>
          </div>
          <div class="top-route-fare">${AeroCharts.formatCurrency(a.avg_fare)}</div>
          <div class="top-route-meta">
            <span>Base: ${AeroCharts.formatCurrency(a.base_fare)}</span>
            <span>${a.observations} obs</span>
          </div>
        </div>
      `).join("");
    }

    // Stacked chart
    AeroCharts.renderStackedFareChart("chart-airline-breakdown", data.airlines);
  } catch (err) {
    console.error("Error loading airline comparison:", err);
  }
}

// 8. Price Spike Alerts
async function loadSpikeAlerts(severity = "ALL") {
  try {
    const res = await fetch(`${API_BASE}/api/price-spikes?severity=${severity}`);
    const data = await res.json();
    renderSpikeAlertsFeed(data.alerts);
  } catch (err) {
    console.error("Error loading price spike alerts:", err);
  }
}

function renderSpikeAlertsFeed(alerts) {
  const container = document.getElementById("spike-alerts-feed-full");
  if (!container) return;

  if (alerts.length === 0) {
    container.innerHTML = `<div style="padding: 24px; text-align: center; color: var(--text-muted);">No active price spikes detected for current filters.</div>`;
    return;
  }

  container.innerHTML = alerts.map(a => `
    <div class="alert-item severity-${a.severity}">
      <div class="alert-header">
        <div class="alert-route">
          <span>🚨 ${a.origin_city} → ${a.destination_city}</span>
          <span class="badge badge-${a.severity === 'HIGH' ? 'red' : a.severity === 'MEDIUM' ? 'orange' : 'blue'}">${a.severity}</span>
        </div>
        <div class="alert-surge">+${a.percentage_change}% Surge</div>
      </div>
      <div class="alert-reason">${a.explanation_details}</div>
      <div class="alert-meta">
        <span>Carrier: <strong>${a.airline_name}</strong></span>
        <span>Window: <strong>${a.advance_window_tier}</strong></span>
        <span>Baseline: <strong>${AeroCharts.formatCurrency(a.baseline_fare)}</strong> → Current: <strong style="color:#dc2626;">${AeroCharts.formatCurrency(a.current_fare)}</strong></span>
        <span>Z-Score: <strong>${a.z_score}</strong></span>
      </div>
    </div>
  `).join("");
}

function renderDashboardAlertsPreview(alerts) {
  const container = document.getElementById("dashboard-alerts-preview");
  if (!container || !alerts) return;

  container.innerHTML = alerts.slice(0, 4).map(a => `
    <div class="alert-item severity-${a.severity}" onclick="navigateTo('view-spikes')">
      <div class="alert-header">
        <div class="alert-route" style="font-size: 0.84rem;">
          <span>${a.origin_city} → ${a.destination_city}</span>
        </div>
        <div class="alert-surge">+${a.percentage_change}%</div>
      </div>
      <div class="alert-reason" style="font-size: 0.75rem;">${a.primary_reason}</div>
      <div class="alert-meta" style="font-size: 0.7rem;">
        <span>${a.airline_name} (${a.advance_window_tier})</span>
        <span>${AeroCharts.formatCurrency(a.current_fare)}</span>
      </div>
    </div>
  `).join("");
}

// 9. Advance Booking Window Analysis
async function loadBookingWindowAnalysis(routeKey = "ALL") {
  try {
    const res = await fetch(`${API_BASE}/api/booking-window?route_key=${routeKey}`);
    const data = await res.json();

    const sel = document.getElementById("bw-route-select");
    if (sel && sel.children.length <= 1) {
      sel.innerHTML = data.available_routes.map(r => `<option value="${r}">${r === "ALL" ? "All Domestic Routes Combined" : r}</option>`).join("");
    }

    const insightEl = document.getElementById("bw-insight-text");
    if (insightEl) insightEl.innerText = data.key_insight;

    const dashInsightEl = document.getElementById("dash-bw-insight-text");
    if (dashInsightEl) dashInsightEl.innerText = data.key_insight;

    const tableBody = document.getElementById("bw-table-body");
    if (tableBody) {
      tableBody.innerHTML = data.booking_windows.map(w => `
        <tr>
          <td><strong>${w.tier}</strong> (${w.days_in_advance} days prior)</td>
          <td style="font-family: var(--font-mono); color: #0284c7; font-weight: 700;">${AeroCharts.formatCurrency(w.avg_total_fare)}</td>
          <td style="font-family: var(--font-mono);">${AeroCharts.formatCurrency(w.avg_base_fare)}</td>
          <td><span class="badge ${w.escalation_vs_t45_pct > 30 ? 'badge-red' : w.escalation_vs_t45_pct > 10 ? 'badge-orange' : 'badge-green'}">${w.escalation_vs_t45_pct > 0 ? '+' : ''}${w.escalation_vs_t45_pct}%</span></td>
          <td>${w.observations.toLocaleString()}</td>
        </tr>
      `).join("");
    }

    // Line chart
    AeroCharts.renderLineChart("chart-booking-window", {
      data: data.booking_windows.map(w => ({ label: w.tier, value: w.avg_total_fare })),
      xKey: "label",
      yKey: "value",
      isCurrency: true,
      lineColor: "#f59e0b",
      fillColor: "rgba(245, 158, 11, 0.12)"
    });
  } catch (err) {
    console.error("Error loading booking window analysis:", err);
  }
}

// 10. Data Quality Metrics
async function loadQualityMetrics() {
  try {
    const res = await fetch(`${API_BASE}/api/data-quality`);
    const data = await res.json();

    const scoreEl = document.getElementById("dq-score-val");
    if (scoreEl) scoreEl.innerText = `${data.data_quality_pct}%`;

    const totEl = document.getElementById("dq-total-records");
    if (totEl) totEl.innerText = data.records_collected.toLocaleString("en-IN");

    const valEl = document.getElementById("dq-valid-records");
    if (valEl) valEl.innerText = data.valid_records.toLocaleString("en-IN");

    const dupEl = document.getElementById("dq-dup-records");
    if (dupEl) dupEl.innerText = data.duplicate_records_removed.toLocaleString("en-IN");

    const misEl = document.getElementById("dq-missing-records");
    if (misEl) misEl.innerText = data.missing_values_handled.toLocaleString("en-IN");
  } catch (err) {
    console.error("Error loading data quality metrics:", err);
  }
}

// 11. Data Explorer
async function loadExplorerData() {
  try {
    const p = AppState.explorer;
    const url = `${API_BASE}/api/data-explorer?search=${encodeURIComponent(p.search)}&origin=${p.origin}&destination=${p.destination}&airline=${encodeURIComponent(p.airline)}&window=${p.window}&source=${encodeURIComponent(p.source)}&page=${p.page}&limit=${p.limit}`;
    
    const res = await fetch(url);
    const data = await res.json();

    populateFilterSelects(data.filters);

    const tbody = document.getElementById("explorer-table-body");
    if (!tbody) return;

    if (data.records.length === 0) {
      tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; padding: 24px; color: var(--text-muted);">No records found matching query parameters.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.records.map(r => `
      <tr>
        <td style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted);">${r.observation_id}</td>
        <td><strong>${r.flight_date}</strong></td>
        <td>${r.origin_city} (${r.origin_code}) → ${r.destination_city} (${r.destination_code})</td>
        <td><strong>${r.airline_name}</strong> <span style="font-size:0.72rem; color:var(--text-muted);">${r.flight_number}</span></td>
        <td><span class="badge badge-blue">${r.advance_window_tier}</span></td>
        <td style="font-family: var(--font-mono);">${AeroCharts.formatCurrency(r.base_fare)}</td>
        <td style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted);">${AeroCharts.formatCurrency(r.taxes)}</td>
        <td style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted);">${AeroCharts.formatCurrency(r.airport_fees + r.convenience_fee)}</td>
        <td style="font-family: var(--font-mono); font-weight: 700; color: #0284c7;">${AeroCharts.formatCurrency(r.total_fare)}</td>
        <td style="font-size: 0.78rem;">${r.data_source}</td>
        <td><span class="badge ${r.is_clean === 1 ? 'badge-green' : 'badge-orange'}">${r.quality_flags}</span></td>
      </tr>
    `).join("");

    const pag = data.pagination;
    const pagInfo = document.getElementById("explorer-pag-info");
    if (pagInfo) pagInfo.innerText = `Showing page ${pag.page} of ${pag.total_pages} (${pag.total_records.toLocaleString()} total records)`;

    const prevBtn = document.getElementById("explorer-btn-prev");
    const nextBtn = document.getElementById("explorer-btn-next");
    if (prevBtn) {
      prevBtn.disabled = pag.page <= 1;
      prevBtn.onclick = () => { if (AppState.explorer.page > 1) { AppState.explorer.page--; loadExplorerData(); } };
    }
    if (nextBtn) {
      nextBtn.disabled = pag.page >= pag.total_pages;
      nextBtn.onclick = () => { if (AppState.explorer.page < pag.total_pages) { AppState.explorer.page++; loadExplorerData(); } };
    }
  } catch (err) {
    console.error("Error loading explorer data:", err);
  }
}

function populateFilterSelects(filters) {
  if (!filters) return;
  
  const origSel = document.getElementById("explorer-filter-origin");
  if (origSel && origSel.children.length <= 1) {
    filters.origins.forEach(o => { origSel.innerHTML += `<option value="${o}">${o}</option>`; });
  }

  const destSel = document.getElementById("explorer-filter-destination");
  if (destSel && destSel.children.length <= 1) {
    filters.destinations.forEach(d => { destSel.innerHTML += `<option value="${d}">${d}</option>`; });
  }

  const airSel = document.getElementById("explorer-filter-airline");
  if (airSel && airSel.children.length <= 1) {
    filters.airlines.forEach(a => { airSel.innerHTML += `<option value="${a}">${a}</option>`; });
  }
}

// 12. Simulate Live Batch
async function handleSimulateBatch() {
  const btn = document.getElementById("btn-simulate-batch");
  if (!btn) return;
  const origText = btn.innerHTML;
  btn.innerHTML = `<span>⏳ Ingesting 50 Live Records...</span>`;
  btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/simulate-ingestion`, { method: "POST" });
    const data = await res.json();
    alert(`⚡ Ingestion Batch Processed!
• 50 observations cleaned and normalized.
• Updated Real-Time Index: ${data.new_airfare_index}
• Total Records: ${data.total_observations.toLocaleString()}`);
    await loadInitialData();
  } catch (err) {
    console.error("Error simulating ingestion:", err);
  } finally {
    btn.innerHTML = origText;
    btn.disabled = false;
  }
}
