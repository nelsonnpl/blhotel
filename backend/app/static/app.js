const presets = [
  {
    id: "gran-canaria-sur",
    name: "Gran Canaria (Sur)",
    cluster: "Canarias · Resort",
    description: "Todo incluido, hoteles, piscina. Base Maspalomas / Sur de Gran Canaria.",
    baseUrl:
      "https://www.booking.com/searchresults.es.html?label=gog235jc-10CAEoggI46AdIClgDaEaIAQGYATO4ARfIAQzYAQPoAQH4AQGIAgGoAgG4AsSSyNAGwAIB0gIkZDIxZjM3ZTUtODFkYS00YzRkLWI2OGEtY2YxZjg4MWFkZDAz2AIB4AIB&aid=397594&ss=Sur+de+Gran+Canaria%2C+Espa%C3%B1a&ssne=Maspalomas&ssne_untouched=Maspalomas&lang=es&src=searchresults&dest_id=14200&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=es&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=188e8fde361a0301&checkin=2026-07-06&checkout=2026-07-12&group_adults=2&no_rooms=1&group_children=0&nflt=mealplan%3D4%3Bht_id%3D204%3Bhotelfacility%3D433",
  },
  {
    id: "gran-canaria-general",
    name: "Gran Canaria (General)",
    cluster: "Canarias · Isla",
    description: "Todo incluido, hoteles, piscina. Mercado completo de Gran Canaria.",
    baseUrl:
      "https://www.booking.com/searchresults.es.html?label=gog235jc-10CAEoggI46AdIClgDaEaIAQGYATO4ARfIAQzYAQPoAQH4AQGIAgGoAgG4As_aytAGwAIB0gIkYTZjZmM4YjUtM2FjMC00ODgyLTljNmItZjQzMTZmMjkwMWU22AIB4AIB&aid=397594&ss=Gran+Canaria&ssne=Gran+Canaria&ssne_untouched=Gran+Canaria&efdco=1&lang=es&src=searchresults&dest_id=754&dest_type=region&checkin=2026-08-24&checkout=2026-08-30&group_adults=2&no_rooms=1&group_children=0&nflt=hotelfacility%3D433%3Bmealplan%3D4%3Bht_id%3D204",
  },
  {
    id: "tenerife-sur",
    name: "Tenerife (Sur)",
    cluster: "Canarias · Resort",
    description: "Todo incluido, hoteles, piscina. Mercado Tenerife Sur.",
    baseUrl:
      "https://www.booking.com/searchresults.es.html?label=gog235jc-10CAEoggI46AdIClgDaEaIAQGYATO4ARfIAQzYAQPoAQH4AQGIAgGoAgG4As_aytAGwAIB0gIkYTZjZmM4YjUtM2FjMC00ODgyLTljNmItZjQzMTZmMjkwMWU22AIB4AIB&aid=397594&ss=Tenerife+Sur%2C+Espa%C3%B1a&ssne=Gran+Canaria&ssne_untouched=Gran+Canaria&lang=es&src=searchresults&dest_id=13444&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=es&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=8aeb36fb3fdd01f3&checkin=2026-08-24&checkout=2026-08-30&group_adults=2&no_rooms=1&group_children=0&nflt=hotelfacility%3D433%3Bmealplan%3D4%3Bht_id%3D204",
  },
  {
    id: "lanzarote",
    name: "Lanzarote",
    cluster: "Canarias · Isla",
    description: "Todo incluido, hoteles, piscina. Mercado Lanzarote.",
    baseUrl:
      "https://www.booking.com/searchresults.es.html?label=gog235jc-10CAEoggI46AdIClgDaEaIAQGYATO4ARfIAQzYAQPoAQH4AQGIAgGoAgG4As_aytAGwAIB0gIkYTZjZmM4YjUtM2FjMC00ODgyLTljNmItZjQzMTZmMjkwMWU22AIB4AIB&aid=397594&ss=Tenerife+Sur%2C+Espa%C3%B1a&ssne=Gran+Canaria&ssne_untouched=Gran+Canaria&lang=es&src=searchresults&dest_id=13444&dest_type=region&ac_position=0&ac_click_type=b&ac_langcode=es&ac_suggestion_list_length=5&search_selected=true&search_pageview_id=8aeb36fb3fdd01f3&checkin=2026-08-24&checkout=2026-08-30&group_adults=2&no_rooms=1&group_children=0&nflt=hotelfacility%3D433%3Bmealplan%3D4%3Bht_id%3D204",
  },
  {
    id: "fuerteventura",
    name: "Fuerteventura",
    cluster: "Canarias · Isla",
    description: "Todo incluido, hoteles, piscina. Mercado Fuerteventura.",
    baseUrl:
      "https://www.booking.com/searchresults.es.html?label=gog235jc-10CAEoggI46AdIClgDaEaIAQGYATO4ARfIAQzYAQPoAQH4AQGIAgGoAgG4As_aytAGwAIB0gIkYTZjZmM4YjUtM2FjMC00ODgyLTljNmItZjQzMTZmMjkwMWU22AIB4AIB&aid=397594&ss=fuerteventura&ssne=Lanzarote&ssne_untouched=Lanzarote&lang=es&src=searchresults&checkin=2026-08-24&checkout=2026-08-30&group_adults=2&no_rooms=1&group_children=0&nflt=hotelfacility%3D433%3Bmealplan%3D4%3Bht_id%3D204",
  },
];

const widgetLabels = {
  kpis: "KPIs de foto",
  heatmap: "Heatmap precios",
  trend: "Evolucion semanal",
  ranking: "Ranking competitivo",
  insights: "Senales revenue",
  distribution: "Distribucion rating",
  photos: "Timeline de fotos",
  table: "Vista tabla",
};

const widgetOrder = ["kpis", "heatmap", "trend", "ranking", "insights", "distribution", "photos", "table"];

const state = {
  targets: [],
  activeTargetId: null,
  latest: null,
  metrics: null,
  photos: [],
  activePhotoId: null,
  photoDetail: null,
  rows: [],
  heatmap: { photosUsed: 6, points: [], scale: { minPricePerNight: 0, maxPricePerNight: 0 } },
  query: "",
  widgets: loadWidgets(),
  captureConfig: {
    presetId: "gran-canaria-sur",
    presetIds: ["gran-canaria-sur"],
    checkIn: "2026-08-24",
    nights: 6,
    weeks: 4,
    limit: 200,
  },
  darkMode: true,
  sortKey: "position",
  sortAsc: true,
  filterOnlyRiu: false,
  filterCriticalGaps: false,
};
const mapRegistry = new Map();
let statusTimer = null;

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

window.addEventListener("DOMContentLoaded", async () => {
  loadTheme();
  initNavigation();
  initPresets();
  initWorkspaceControls();
  bindEvents();
  renderAll();
  
  // Live Bloomberg widgets
  setInterval(updateUtcClock, 1000);
  updateUtcClock();
  setInterval(checkConnectionHealth, 30000);
  checkConnectionHealth();
  window.addEventListener("keydown", handleKeyboardShortcuts);

  await boot();
});

async function boot() {
  try {
    await api("/api/health");
    await refreshTargets();
    setStatus("Servidor Flask listo. Selecciona mercado y captura cuando quieras.", "ok");
  } catch (error) {
    setStatus(readableError(error), "error");
  }
}

function initNavigation() {
  $$(".nav__item").forEach((button) => {
    button.addEventListener("click", () => showView(button.dataset.view));
  });
}

function showView(view) {
  $$(".nav__item").forEach((item) => item.classList.toggle("is-active", item.dataset.view === view));
  $$(".view").forEach((section) => section.classList.toggle("is-visible", section.id === view));
  const meta = {
    dashboard: ["Dashboard", "Lectura ejecutiva del mercado hotelero, presión competitiva y evolución de precios."],
    riu: ["Análisis RIU", "Gap, ranking y oportunidades de acción para propiedades RIU dentro del set activo."],
    workspace: ["Area de trabajo", "Módulos personalizables para construir una mesa de análisis propia."],
    scraping: ["Capturas", "Lanza nuevas fotos semanales y audita el flujo operativo de Decodo."],
    map: ["Mapa", "Mapa de calor por ADR, pines de tarifa y ficha analítica por hotel."],
    explorer: ["Explorador", "Tabla completa con filtros instantáneos, gaps y exportación."],
  }[view] || ["Revenue Intelligence", "Panel operativo de análisis revenue."];
  $("#viewTitle").textContent = meta[0];
  const subtitle = document.querySelector(".page-subtitle");
  if (subtitle) subtitle.textContent = meta[1];
}

function initPresets() {
  if (!Array.isArray(state.captureConfig.presetIds) || !state.captureConfig.presetIds.length) {
    state.captureConfig.presetIds = [presets[0].id];
  }
  state.captureConfig.presetId = state.captureConfig.presetIds[0];
}

function bindEvents() {
  $("#runScrapeTop")?.addEventListener("click", openCaptureModal);
  $("#zoneSelect")?.addEventListener("change", async (event) => {
    const selectedIds = Array.from(event.target.selectedOptions || []).map((option) => option.value).filter(Boolean);
    if (!selectedIds.length) return;
    state.captureConfig.presetIds = selectedIds;
    state.captureConfig.presetId = selectedIds[0];
    saveAppSettings();
    try {
      await loadTargetsForSelection();
    } catch (error) {
      setStatus(readableError(error), "error");
    }
  });

  $("#search").addEventListener("input", (event) => {
    state.query = event.target.value;
    renderExplorer();
  });

  $("#exportCsv").addEventListener("click", exportCsv);

  $("#resetWorkspace").addEventListener("click", () => {
    state.widgets = [...widgetOrder];
    saveWidgets();
    initWorkspaceControls();
    renderWorkspace();
  });

  $("#closeCaptureModal")?.addEventListener("click", closeCaptureModal);
  $("#cancelCaptureModal")?.addEventListener("click", closeCaptureModal);
  $("#confirmCaptureModal")?.addEventListener("click", async () => {
    applyModalCaptureConfig();
    closeCaptureModal();
    await runWeeklyScrape();
  });
  $("#captureModal")?.addEventListener("click", (event) => {
    if (event.target?.id === "captureModal") closeCaptureModal();
  });
  $("#openSettingsTop")?.addEventListener("click", () => {
    openSettingsModal();
  });
  $("#closeSettingsModal")?.addEventListener("click", closeSettingsModal);
  $("#cancelSettingsModal")?.addEventListener("click", closeSettingsModal);
  $("#confirmSettingsModal")?.addEventListener("click", async () => {
    const valid = applySettingsFromModal();
    if (!valid) return;
    closeSettingsModal();
    try {
      await loadHeatmap();
      renderAll();
    } catch (error) {
      setStatus(readableError(error), "error");
    }
  });
  $("#settingsModal")?.addEventListener("click", (event) => {
    if (event.target?.id === "settingsModal") closeSettingsModal();
  });

  // Table header sorting listeners
  document.querySelectorAll("#explorer table th[data-sort]").forEach((th) => {
    th.addEventListener("click", () => {
      const key = th.dataset.sort;
      if (state.sortKey === key) {
        state.sortAsc = !state.sortAsc;
      } else {
        state.sortKey = key;
        state.sortAsc = true;
      }
      renderExplorer();
    });
  });

  // Advanced filters inside Explorer
  $("#filterRating")?.addEventListener("change", () => {
    updateRatingQuickButtons();
    renderExplorer();
  });
  $("#filterMaxPrice")?.addEventListener("input", () => {
    renderExplorer();
  });

  // Command bar interactive terminal
  const cmdBar = $("#cmdBar");
  const cmdInput = $("#cmdInput");
  cmdBar?.addEventListener("click", () => {
    cmdInput?.focus();
  });
  cmdInput?.addEventListener("keyup", (event) => {
    if (event.key === "Enter") {
      executeCommand(cmdInput.value);
      cmdInput.value = "";
    }
  });

  // Map drawer close action
  $("#closeMapDrawer")?.addEventListener("click", () => {
    $("#mapDrawer")?.classList.remove("is-visible");
  });

  // Quick boolean filter toggle buttons
  $("#btnFilterRiu")?.addEventListener("click", (event) => {
    state.filterOnlyRiu = !state.filterOnlyRiu;
    event.target.classList.toggle("is-active", state.filterOnlyRiu);
    renderExplorer();
  });

  $("#btnFilterGaps")?.addEventListener("click", (event) => {
    state.filterCriticalGaps = !state.filterCriticalGaps;
    event.target.classList.toggle("is-active", state.filterCriticalGaps);
    renderExplorer();
  });

  $$("[data-rating-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      const select = $("#filterRating");
      if (!select) return;
      select.value = select.value === button.dataset.ratingFilter ? "" : button.dataset.ratingFilter;
      updateRatingQuickButtons();
      renderExplorer();
    });
  });

  $$("[data-riu-action]").forEach((button) => {
    button.addEventListener("click", () => {
      executeRiuAction(button.dataset.riuAction);
    });
  });
}

function initWorkspaceControls() {
  $("#widgetToggles").innerHTML = widgetOrder
    .map((key) => `<button class="widget-toggle ${state.widgets.includes(key) ? "is-active" : ""}" data-widget="${key}">${escapeHtml(widgetLabels[key])}</button>`)
    .join("");

  $$(".widget-toggle").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.widget;
      state.widgets = state.widgets.includes(key) ? state.widgets.filter((item) => item !== key) : [...state.widgets, key];
      saveWidgets();
      initWorkspaceControls();
      renderWorkspace();
    });
  });
}

async function refreshTargets() {
  const data = await api("/api/targets");
  state.targets = Array.isArray(data.targets) ? data.targets : [];
  $("#targetCount").textContent = `${state.targets.length} mercados configurados`;
  renderTargets();
  await loadTargetsForSelection();
}

async function loadTargetsForSelection() {
  const selectedPresets = activePresets();
  const selectedTargets = selectedPresets.map((preset) => findTargetForPreset(preset.name)).filter(Boolean);
  if (!selectedTargets.length) {
    state.activeTargetId = null;
    state.latest = null;
    state.metrics = null;
    state.photos = [];
    state.activePhotoId = null;
    state.photoDetail = null;
    state.rows = [];
    renderAll();
    return;
  }

  if (selectedTargets.length === 1) {
    await loadTarget(selectedTargets[0].id);
    return;
  }

  await loadAggregateTargets(selectedTargets.map((target) => target.id));
}

async function loadTarget(targetId) {
  state.activeTargetId = targetId;
  const [latestData, metrics, photoHistory] = await Promise.all([
    api(`/api/snapshots/latest?targetId=${targetId}`),
    api(`/api/dashboard/metrics?targetId=${targetId}`),
    api(`/api/photos/history?targetId=${targetId}&limit=40`),
  ]);

  state.latest = latestData.latest;
  state.metrics = metrics;
  state.photos = Array.isArray(photoHistory.photos) ? photoHistory.photos : [];

  if (!state.photos.length) {
    state.activePhotoId = null;
    state.photoDetail = null;
    state.rows = [];
  } else {
    const selectedExists = state.activePhotoId && state.photos.some((photo) => photo.id === state.activePhotoId);
    state.activePhotoId = selectedExists ? state.activePhotoId : state.photos[0].id;
    await loadPhoto(state.activePhotoId, false);
  }

  await loadHeatmap();
  renderAll();
}

async function loadAggregateTargets(targetIds) {
  const latestChunks = await Promise.all(
    targetIds.map(async (targetId) => {
      try {
        return await api(`/api/snapshots/latest?targetId=${targetId}`);
      } catch {
        return null;
      }
    })
  );

  const chunkRows = latestChunks
    .map((chunk) => chunk?.latest)
    .filter(Boolean)
    .map((latest) => ({ snapshot: latest.snapshot, rows: latest.rows || [] }));

  if (!chunkRows.length) {
    state.activeTargetId = null;
    state.latest = null;
    state.metrics = null;
    state.photos = [];
    state.activePhotoId = null;
    state.photoDetail = null;
    state.rows = [];
    renderAll();
    return;
  }

  const mergedRows = mergeRows(chunkRows.flatMap((chunk) => chunk.rows));
  const mergedSummary = summarizeRows(mergedRows);
  const mergedCompetitive = buildCompetitiveSet(mergedRows);

  state.activeTargetId = targetIds[0];
  state.latest = {
    snapshot: { id: 0, scrapedAt: chunkRows[0].snapshot.scrapedAt },
    rows: mergedRows,
  };
  state.metrics = {
    locationCoverage: buildLocationCoverage(mergedRows),
    ratingDistribution: buildRatingDistribution(mergedRows),
    competitiveSet: mergedCompetitive,
    insights: buildInsights(mergedSummary, mergedCompetitive),
  };
  state.rows = mergedRows;
  state.photoDetail = { summary: mergedSummary, rows: mergedRows };
  state.photos = chunkRows
    .map((chunk) => ({
      id: chunk.snapshot.id,
      scrapedAt: chunk.snapshot.scrapedAt,
      avgPricePerNight: summarizeRows(chunk.rows).avgPricePerNight,
      avgPricePerPersonNight: summarizeRows(chunk.rows).avgPricePerPersonNight,
      minPricePerNight: summarizeRows(chunk.rows).minPricePerNight,
      maxPricePerNight: summarizeRows(chunk.rows).maxPricePerNight,
      comparableRows: summarizeRows(chunk.rows).comparableRows,
      capturedRows: chunk.rows.length,
    }))
    .sort((a, b) => String(b.scrapedAt).localeCompare(String(a.scrapedAt)));
  state.activePhotoId = state.photos[0]?.id ?? null;
  state.heatmap = buildHeatmapFromRows(mergedRows);
  renderAll();
}

async function loadPhoto(snapshotId, shouldRender = true) {
  const detail = await api(`/api/photos/${snapshotId}`);
  state.activePhotoId = snapshotId;
  state.photoDetail = detail;
  state.rows = detail.rows || [];
  if (shouldRender) {
    renderAll();
  }
}

async function loadHeatmap() {
  if (!state.activeTargetId) {
    state.heatmap = { photosUsed: state.heatmap.photosUsed || 6, points: [], scale: { minPricePerNight: 0, maxPricePerNight: 0 } };
    return;
  }
  const photos = Number(state.heatmap.photosUsed || 6);
  state.heatmap = await api(`/api/hotels/heatmap?targetId=${state.activeTargetId}&photos=${photos}`);
}

async function runWeeklyScrape() {
  const validation = validateCaptureInputs();
  if (!validation.ok) {
    setStatus(validation.message, "error");
    return;
  }

  const consoleBox = document.getElementById("scrapeConsole");
  if (consoleBox) {
    consoleBox.innerHTML = "";
  }
  
  addConsoleLog("RIU Scraper Engine v2.0 - Iniciando tarea de captura semanal...", "sys");
  
  const button = $("#runScrapeTop");
  button.disabled = true;
  setStatus("Capturando Booking semana a semana mediante Decodo...", "busy");

  try {
    const presetsToRun = activePresets();
    addConsoleLog(`Zonas seleccionadas para scraping: ${presetsToRun.map(p => p.name).join(", ")}`, "info");
    addConsoleLog(`Parámetros: ${validation.weeks} semanas de histórico · ${validation.nights} noches de estancia · Límite ${validation.limit} hoteles por foto`, "info");
    
    for (const preset of presetsToRun) {
      let targetId = findTargetForPreset(preset.name)?.id || null;
      addConsoleLog(`Procesando zona: ${preset.name} (Target ID actual: ${targetId || "NUEVO"})`, "sys");

      for (let index = 0; index < validation.weeks; index += 1) {
        const weeklyCheckIn = addWeeks(validation.checkIn, index);
        const url = buildBookingUrl(preset.baseUrl, weeklyCheckIn, validation.nights);

        addConsoleLog(`[SEMANA ${index + 1}/${validation.weeks}] Generando túnel residencial premium España...`, "info");
        addConsoleLog(`[DECODO API] Solicitando captura Booking: Check-in ${weeklyCheckIn} · Estancia ${validation.nights}n`, "warning");
        
        setStatus(`Semana ${index + 1}/${validation.weeks}: ${preset.name} · entrada ${weeklyCheckIn}`, "busy");

        const result = await api("/api/scrape/search", {
          method: "POST",
          body: JSON.stringify({ targetId, targetName: preset.name, url, limit: validation.limit }),
        });

        addConsoleLog(`[DECODO API] Captura completada con éxito. Resultados disponibles: ${result.snapshot.availableResults} · Guardados: ${result.snapshot.capturedRows} hoteles`, "success");
        addConsoleLog(`[SQLITE] Guardando snapshot ID #${result.snapshot.id} en base de datos local...`, "success");

        targetId = result.target.id;
        state.activeTargetId = targetId;
        state.activePhotoId = result.snapshot.id;
      }
    }

    addConsoleLog("Actualizando listados de mercados y bases históricas...", "info");
    await refreshTargets();
    addConsoleLog("Cargando nuevos datos unificados en el panel central...", "info");
    await loadTargetsForSelection();

    addConsoleLog("¡Proceso de captura completado correctamente en todas las zonas!", "success");
    setStatus("Captura completada para todas las zonas seleccionadas.", "ok");
  } catch (error) {
    addConsoleLog(`[CRITICAL ERROR] El scraper Decodo falló: ${readableError(error)}`, "error");
    setStatus(readableError(error), "error");
  } finally {
    button.disabled = false;
  }
}

async function api(url, init = {}) {
  const response = await fetch(url, {
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...(init.headers || {}) },
    ...init,
  });

  const text = await response.text();
  const data = text ? safeJson(text) : {};

  if (!response.ok) {
    throw new Error(data?.error || data?.detail || `HTTP ${response.status}: ${text.slice(0, 220)}`);
  }

  return data;
}

function renderAll() {
  renderPreset();
  renderTicker();
  renderDashboard();
  renderWorkspace();
  renderScrapingSummary();
  renderTargets();
  renderPhotoTable();
  renderMap();
  renderExplorer();
  renderRiuAnalysis();
  
  // Update portfolio status label in bottom status bar
  const activeZoneText = document.getElementById("activeZoneText");
  if (activeZoneText) {
    const selected = activePresets();
    activeZoneText.textContent = selected.map(preset => preset.name).join(", ");
  }
}

function renderPreset() {
  const select = $("#zoneSelect");
  if (!select) return;
  select.innerHTML = presets
    .map((preset) => `<option value="${preset.id}" ${state.captureConfig.presetIds.includes(preset.id) ? "selected" : ""}>${escapeHtml(preset.name)}</option>`)
    .join("");
}

function renderPhotoSelector() {
  const select = $("#photoSelect");
  if (!select) return;

  if (!state.photos.length) {
    select.innerHTML = `<option value="">Sin fotos</option>`;
    return;
  }

  select.innerHTML = state.photos
    .map((photo) => {
      const label = `Foto #${photo.id} · ${formatDateTime(photo.scrapedAt)} · ADR ${currency(photo.avgPricePerNight)}`;
      return `<option value="${photo.id}" ${photo.id === state.activePhotoId ? "selected" : ""}>${escapeHtml(label)}</option>`;
    })
    .join("");
}

function renderDashboard() {
  const summary = state.photoDetail?.summary || null;
  const movement = movementAgainstPreviousPhoto();
  const market = state.metrics?.market || {};
  const median = summary?.medianPricePerNight ?? market.medianPricePerNight ?? null;

  const cards = [
    {
      label: "Precio hab / noche",
      value: currency(summary?.avgPricePerNight),
      trend: pct(movement?.avgPricePerNightChangePct),
      tone: trendTone(movement?.avgPricePerNightChangePct),
      meta: `Mediana ${currency(median)} · Rango ${currency(summary?.minPricePerNight)}-${currency(summary?.maxPricePerNight)}`,
      spark: sparkFromPhotos("avgPricePerNight"),
    },
    {
      label: "Precio pers / noche",
      value: currency(summary?.avgPricePerPersonNight),
      trend: pct(movement?.avgPricePerPersonNightChangePct),
      tone: trendTone(movement?.avgPricePerPersonNightChangePct),
      meta: `Pax normalizado · ${summary?.comparableRows || 0} comparables`,
      spark: sparkFromPhotos("avgPricePerPersonNight"),
    },
    {
      label: "Rango ADR",
      value: `${currency(summary?.minPricePerNight)} - ${currency(summary?.maxPricePerNight)}`,
      trend: spreadLabel(summary),
      tone: "neutral",
      meta: `Mediana ${currency(median)} · dispersión competitiva`,
      spark: sparkFromPhotos("maxPricePerNight"),
    },
    {
      label: "Comparabilidad",
      value: `${summary?.comparableRows || 0}/${summary?.rows || 0}`,
      trend: `${comparabilityPct(summary)}% comparable`,
      tone: comparabilityPct(summary) >= 85 ? "up" : "down",
      meta: `${state.metrics?.dataQuality?.missingPriceRows || 0} filas sin precio · QA operativo`,
      spark: sparkFromPhotos("comparableRows"),
    },
    {
      label: "Mapa cobertura",
      value: `${state.metrics?.locationCoverage?.pct || 0}%`,
      trend: `${state.metrics?.locationCoverage?.located || 0}/${state.metrics?.locationCoverage?.total || 0} hoteles`,
      tone: "neutral",
      meta: "Pines listos para análisis territorial",
      spark: sparkFromPhotos("capturedRows"),
    },
  ];

  $("#kpis").innerHTML = cards.map(renderMetric).join("");

  renderHeatmapElement($("#dashboardHeatmap"), { compact: true });
  renderTrendElement($("#trendChart"), [...state.photos].reverse(), "avgPricePerNight");
  renderInsightsElement($("#insights"), mixedInsights());
}

function renderRiuAnalysis() {
  const summaryContainer = $("#riuSummary");
  const comparisonContainer = $("#riuComparison");
  const cardsContainer = $("#riuCards");
  const alertsContainer = $("#riuAlerts");
  if (!summaryContainer || !comparisonContainer || !cardsContainer || !alertsContainer) return;

  const rows = riuRows();
  const marketSummary = state.photoDetail?.summary || summarizeRows(state.rows);
  const marketPrices = state.rows
    .map((row) => row.pricePerNight ?? (row.price && row.nights ? row.price / row.nights : null))
    .filter((value) => Number.isFinite(value) && value > 0)
    .sort((a, b) => a - b);
  const marketMedian = marketSummary?.medianPricePerNight ?? medianOf(marketPrices);

  if (!rows.length) {
    const message = empty("No hay hoteles RIU en la foto activa. Cambia de zona o ejecuta una captura con propiedades RIU.");
    summaryContainer.innerHTML = message;
    comparisonContainer.innerHTML = message;
    cardsContainer.innerHTML = message;
    alertsContainer.innerHTML = message;
    return;
  }

  const pricedRiu = rows
    .map((row) => ({ ...row, effectivePrice: row.pricePerNight ?? (row.price && row.nights ? row.price / row.nights : null) }))
    .filter((row) => Number.isFinite(row.effectivePrice) && row.effectivePrice > 0);
  const avgRiu = pricedRiu.length ? round(pricedRiu.reduce((sum, row) => sum + row.effectivePrice, 0) / pricedRiu.length) : null;
  const avgGap = marketMedian ? round(((avgRiu - marketMedian) / marketMedian) * 100) : null;
  const mapped = rows.filter((row) => row.latitude !== null && row.longitude !== null).length;
  const critical = rows.filter((row) => Math.abs(gapFor(row.hotelKey) ?? 0) >= 15).length;
  const premium = rows.filter((row) => (gapFor(row.hotelKey) ?? 0) > 10).length;

  const summaryCards = [
    ["Hoteles RIU", rows.length, `${mapped}/${rows.length} geolocalizados`, "neutral"],
    ["ADR RIU medio", currency(avgRiu), `vs mediana ${pct(avgGap)}`, trendTone(avgGap)],
    ["Gap crítico", critical, ">= 15% vs mercado", critical ? "down" : "up"],
    ["Prima RIU", premium, "hoteles sobre +10%", premium ? "neutral" : "up"],
  ];
  summaryContainer.innerHTML = summaryCards
    .map(
      ([label, value, hint, tone]) => `<article class="riu-stat ${tone}">
        <span>${escapeHtml(label)}</span>
        <strong>${escapeHtml(value)}</strong>
        <small>${escapeHtml(hint)}</small>
      </article>`
    )
    .join("");

  comparisonContainer.innerHTML = renderRiuComparison(pricedRiu, marketPrices, marketMedian);
  cardsContainer.innerHTML = rows.map(renderRiuHotelCard).join("");
  bindRiuCards(cardsContainer);
  renderInsightsElement(alertsContainer, buildRiuAlerts(rows, avgGap));
}

function renderRiuComparison(rows, marketPrices, marketMedian) {
  if (!rows.length || !marketPrices.length) return empty("Necesitamos precios comparables para construir la banda RIU vs mercado.");
  const min = marketPrices[0];
  const max = marketPrices[marketPrices.length - 1];
  const spread = max - min || 1;
  const markerFor = (value) => Math.max(0, Math.min(100, ((value - min) / spread) * 100));
  return `
    <div class="riu-band" aria-label="Banda de posicionamiento RIU frente al mercado">
      <div class="riu-band__track">
        <span class="riu-band__marker riu-band__marker--median" style="left:${markerFor(marketMedian)}%"><b>MED</b></span>
        ${rows
          .map((row) => `<button class="riu-band__marker riu-band__marker--hotel" style="left:${markerFor(row.effectivePrice)}%" title="${escapeHtml(row.hotelName)} · ${escapeHtml(currency(row.effectivePrice))}" type="button">${escapeHtml(shortHotelName(row.hotelName))}</button>`)
          .join("")}
      </div>
      <div class="riu-band__scale">
        <span>Min ${currency(min)}</span>
        <span>Mediana ${currency(marketMedian)}</span>
        <span>Max ${currency(max)}</span>
      </div>
    </div>`;
}

function renderRiuHotelCard(row) {
  const price = row.pricePerNight ?? (row.price && row.nights ? row.price / row.nights : null);
  const gap = gapFor(row.hotelKey);
  const rank = competitiveRank(row.hotelKey);
  const tone = gap === null || gap === undefined ? "neutral" : gap >= 15 ? "critical" : gap <= -10 ? "opportunity" : "stable";
  const action = riuActionFor(gap);
  return `<article class="riu-card ${tone}">
    <div class="riu-card__top">
      <span class="riu-tag">RIU</span>
      <small>#${rank || "-"} set</small>
    </div>
    <h3>${escapeHtml(row.hotelName)}</h3>
    <div class="riu-card__metrics">
      <div><span>ADR</span><strong>${currency(price)}</strong></div>
      <div><span>Gap</span><strong>${pct(gap)}</strong></div>
      <div><span>Rating</span><strong>${row.rating ?? "-"}</strong></div>
    </div>
    <p>${escapeHtml(action)}</p>
    <button class="filter-btn" type="button" data-riu-hotel-key="${escapeHtml(row.hotelKey)}">Abrir ficha</button>
  </article>`;
}

function bindRiuCards(container) {
  container.querySelectorAll("[data-riu-hotel-key]").forEach((button) => {
    button.addEventListener("click", () => openMapDrawerForHotelByKey(button.dataset.riuHotelKey));
  });
}

function renderTicker() {
  const track = $("#tickerTrack");
  if (!track) return;
  const ranking = state.metrics?.competitiveSet?.slice(0, 10) || [];
  if (!ranking.length) {
    track.textContent = "Sin ranking competitivo disponible.";
    return;
  }
  const items = ranking
    .map(
      (row, index) =>
        `<span class="ticker-item"><strong>${index + 1}. ${escapeHtml(row.hotelName)}</strong>${currency(row.pricePerNight)} <span class="${row.gapVsMarketPct >= 0 ? "up" : "down"}">${pct(row.gapVsMarketPct)}</span></span>`
    )
    .join("");
  track.innerHTML = `${items}${items}`;
}

function renderWorkspace() {
  const grid = $("#workspaceGrid");
  if (!state.widgets.length) {
    grid.innerHTML = `<div class="empty empty--large">Activa algun modulo para construir tu espacio de trabajo.</div>`;
    return;
  }

  grid.innerHTML = state.widgets
    .map(
      (key) => `
    <article class="panel workspace-card" data-widget-panel="${key}">
      <div class="panel__header"><h2>${escapeHtml(widgetLabels[key])}</h2><p>Vista personal del analista.</p></div>
      <div class="widget-body"></div>
    </article>
  `
    )
    .join("");

  state.widgets.forEach((key) => {
    const body = document.querySelector(`[data-widget-panel="${key}"] .widget-body`);
    if (!body) return;

    if (key === "kpis") body.innerHTML = $("#kpis").innerHTML || empty("Sin KPIs todavia.");
    if (key === "heatmap") renderHeatmapElement(body, { compact: false });
    if (key === "trend") renderTrendElement(body, [...state.photos].reverse(), "avgPricePerNight");
    if (key === "ranking") renderRankingElement(body, state.metrics?.competitiveSet?.slice(0, 10) || []);
    if (key === "insights") renderInsightsElement(body, mixedInsights());
    if (key === "distribution") renderDistribution(body, state.metrics?.ratingDistribution || []);
    if (key === "photos") renderPhotosTimeline(body, state.photos);
    if (key === "table") renderTablePreview(body, filteredRows().slice(0, 8));
  });
}

function renderScrapingSummary() {
  const selected = activePresets();
  const zoneNames = selected.map((preset) => preset.name).join(", ");
  $("#scrapeSummary").innerHTML = `
    <strong>${escapeHtml(zoneNames || "Sin zonas seleccionadas")}</strong>
    <span>Primera entrada: ${escapeHtml(state.captureConfig.checkIn)}</span>
    <span>${escapeHtml(state.captureConfig.weeks)} semanas · ${escapeHtml(state.captureConfig.nights)} noches · hasta ${escapeHtml(state.captureConfig.limit)} hoteles por foto</span>
    <span>Servidor unico Flask: ${escapeHtml(location.origin)}</span>
  `;
}
function renderTargets() {
  const container = $("#targets");
  container.innerHTML = state.targets.length
    ? state.targets
        .map(
          (target) => `
      <button class="target-card ${target.id === state.activeTargetId ? "is-active" : ""}" data-target-id="${target.id}">
        <strong>${escapeHtml(target.name)}</strong>
        <span>${escapeHtml(readSearchParam(target.url, "ss") || "Booking")}</span>
      </button>
    `
        )
        .join("")
    : empty("Todavia no hay mercados capturados.");

  $$(".target-card").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await loadTarget(Number(button.dataset.targetId));
        setStatus("Mercado cargado correctamente.", "ok");
      } catch (error) {
        setStatus(readableError(error), "error");
      }
    });
  });
}

function renderPhotoTable() {
  const tbody = $("#photoRows");
  if (!tbody) return;

  if (!state.photos.length) {
    tbody.innerHTML = `<tr><td colspan="7">${empty("Aun no hay fotos. Ejecuta una captura semanal.")}</td></tr>`;
    return;
  }

  tbody.innerHTML = state.photos
    .map((photo) => {
      const isActive = photo.id === state.activePhotoId;
      return `<tr>
        <td><strong>${isActive ? "Activa" : "Foto"} #${photo.id}</strong></td>
        <td>${formatDateTime(photo.scrapedAt)}</td>
        <td>${currency(photo.avgPricePerNight)}</td>
        <td>${currency(photo.avgPricePerPersonNight)}</td>
        <td>${currency(photo.minPricePerNight)} - ${currency(photo.maxPricePerNight)}</td>
        <td>${photo.comparableRows}/${photo.capturedRows}</td>
        <td><button class="button button--secondary photo-load" data-photo-id="${photo.id}">Cargar</button></td>
      </tr>`;
    })
    .join("");

  $$(".photo-load").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = Number(button.dataset.photoId);
      await loadPhoto(id);
      renderPhotoSelector();
      setStatus(`Foto #${id} cargada en dashboard, mapa y explorador.`, "ok");
    });
  });
}

function renderMap() {
  const rowsWithCoords = state.rows.filter((row) => row.latitude !== null && row.longitude !== null);
  const pending = state.rows.length - rowsWithCoords.length;
  $("#mapPending").textContent = `${pending} pendientes`;
  renderHeatmapElement($("#marketMap"), { compact: false, overlayRows: rowsWithCoords });
}

function renderExplorer() {
  const tbody = $("#hotelRows");
  const rows = filteredRows();

  const total = state.rows.length;
  const filtered = rows.length;
  const counter = document.getElementById("filteredCount");
  if (counter) {
    counter.textContent = `Filas: ${filtered} / ${total}`;
  }

  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="11">${empty("No hay datos para esta vista. Ejecuta una captura o carga una foto o ajusta filtros.")}</td></tr>`;
    return;
  }

  tbody.innerHTML = rows
    .map((row) => {
      const gap = gapFor(row.hotelKey);
      const ppn = row.pricePerNight ?? (row.price && row.nights ? row.price / row.nights : null);
      const isRiu = row.hotelName.toLowerCase().includes("riu");
      
      return `<tr class="${isRiu ? 'riu-row' : ''}">
      <td>${row.position}</td>
      <td>
        ${isRiu ? '<span class="riu-tag">RIU</span>' : ''}
        <strong>${escapeHtml(row.hotelName)}</strong>
        <small>${escapeHtml(row.address || "Direccion pendiente")}</small>
      </td>
      <td>${escapeHtml(row.roomType || "No identificado")}</td>
      <td>${row.rating ?? "-"}</td>
      <td>${currency(row.price)}</td>
      <td>${currency(ppn)}</td>
      <td>${currency(row.pricePerPersonPerNight)}</td>
      <td><span class="${badgeClass(gap)}">${pct(gap)}</span></td>
      <td>${row.pax ?? "-"}</td>
      <td>${row.checkIn || "-"} → ${row.checkOut || "-"}</td>
      <td>${row.locationStatus === "ready" ? "OK" : "Pendiente"}</td>
    </tr>`;
    })
    .join("");
}

function renderMetric(card) {
  const spark = Array.isArray(card.spark) && card.spark.length
    ? `<div class="metric__spark" aria-hidden="true">${card.spark
        .map((height) => `<span class="metric__spark-bar" style="height:${height}%"></span>`)
        .join("")}</div>`
    : "";
  return `<article class="metric">
    <span>${escapeHtml(card.label)}</span>
    <strong>${escapeHtml(card.value)}</strong>
    <small class="${card.tone}">${escapeHtml(card.trend)}</small>
    <em>${escapeHtml(card.meta || "")}</em>
    ${spark}
  </article>`;
}

function renderTrendElement(container, rows, key) {
  if (!rows.length) {
    container.innerHTML = empty("Aun no hay historico suficiente. Captura varias semanas para ver tendencia.");
    return;
  }

  const values = rows.map((row) => Number(row[key] || 0));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const width = 640;
  const height = 220;
  const pad = { top: 22, right: 28, bottom: 34, left: 54 };
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;
  const pointAt = (value, index) => ({
    x: pad.left + (rows.length === 1 ? plotWidth / 2 : (index / (rows.length - 1)) * plotWidth),
    y: pad.top + (1 - ((value - min) / range)) * plotHeight,
  });
  const points = values.map(pointAt);
  const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
  const areaPath = `${path} L ${points[points.length - 1].x} ${height - pad.bottom} L ${points[0].x} ${height - pad.bottom} Z`;
  const gridLines = [0, 0.25, 0.5, 0.75, 1]
    .map((ratio) => {
      const y = pad.top + ratio * plotHeight;
      const label = max - ratio * range;
      return `<line class="trend-grid-line" x1="${pad.left}" x2="${width - pad.right}" y1="${y}" y2="${y}"></line>
        <text class="trend-axis-text" x="${pad.left - 8}" y="${y + 3}" text-anchor="end">${currency(label)}</text>`;
    })
    .join("");

  container.innerHTML = `
    <svg class="trend-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Evolucion historica del ADR">
      <defs>
        <linearGradient id="trend-area-grad" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="rgba(225, 29, 72, 0.34)"></stop>
          <stop offset="100%" stop-color="rgba(225, 29, 72, 0.02)"></stop>
        </linearGradient>
      </defs>
      ${gridLines}
      <line class="trend-axis-line" x1="${pad.left}" x2="${width - pad.right}" y1="${height - pad.bottom}" y2="${height - pad.bottom}"></line>
      <path class="trend-path-area" d="${areaPath}"></path>
      <path class="trend-path" d="${path}"></path>
      ${points
        .map((point, index) => {
          const row = rows[index];
          const label = formatShortDate(row.scrapedAt);
          return `<g>
            <circle class="trend-dot" cx="${point.x}" cy="${point.y}" r="4" tabindex="0" data-label="${escapeHtml(label)}" data-value="${escapeHtml(currency(values[index]))}" data-rows="${row.capturedRows || row.comparableRows || 0}"></circle>
            <text class="trend-axis-text" x="${point.x}" y="${height - 12}" text-anchor="middle">${escapeHtml(label)}</text>
          </g>`;
        })
        .join("")}
    </svg>
    <div class="chart-tooltip" role="tooltip"></div>`;
  bindTrendTooltip(container);
}

function bindTrendTooltip(container) {
  const tooltip = container.querySelector(".chart-tooltip");
  if (!tooltip) return;

  container.querySelectorAll(".trend-dot").forEach((dot) => {
    const show = (event) => {
      const target = event.currentTarget;
      tooltip.innerHTML = `<strong>${escapeHtml(target.dataset.value || "-")}</strong><span>${escapeHtml(target.dataset.label || "")} · ${escapeHtml(target.dataset.rows || "0")} filas</span>`;
      tooltip.style.display = "block";
      const bounds = container.getBoundingClientRect();
      const x = (event.clientX || bounds.left + Number(target.getAttribute("cx"))) - bounds.left + 12;
      const y = (event.clientY || bounds.top + Number(target.getAttribute("cy"))) - bounds.top - 12;
      tooltip.style.left = `${Math.min(Math.max(8, x), bounds.width - 130)}px`;
      tooltip.style.top = `${Math.max(8, y)}px`;
    };
    const hide = () => {
      tooltip.style.display = "none";
      dot.classList.remove("is-active");
    };
    dot.addEventListener("mouseenter", (event) => {
      dot.classList.add("is-active");
      show(event);
    });
    dot.addEventListener("mousemove", show);
    dot.addEventListener("focus", show);
    dot.addEventListener("mouseleave", hide);
    dot.addEventListener("blur", hide);
  });
}

function renderInsightsElement(container, rows) {
  container.innerHTML = rows.length
    ? rows.map((item) => `<article class="insight ${item.severity || "info"}"><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.message)}</p></article>`).join("")
    : empty("Sin senales accionables. Necesitamos al menos una foto y, para movimiento, dos fotos.");
}

function renderRankingElement(container, rows) {
  container.innerHTML = rows.length
    ? rows
        .map(
          (row, index) =>
            `<div class="ranking-row"><b>${index + 1}</b><strong>${escapeHtml(row.hotelName)}</strong><span>${currency(row.pricePerNight)}</span><small class="${badgeClass(row.gapVsMarketPct)}">${pct(row.gapVsMarketPct)}</small></div>`
        )
        .join("")
    : empty("Sin ranking comparable todavia.");
}

function renderQualityElement(container, metrics, summary) {
  const quality = metrics?.dataQuality;
  const comparablePct = summary ? comparabilityPct(summary) : quality?.comparablePct || 0;
  const notes = quality?.notes?.length ? quality.notes : ["Sin avisos de calidad."];

  container.innerHTML = `
    <div class="quality-ring" style="--pct:${comparablePct}%"><strong>${comparablePct}%</strong><span>Comparable</span></div>
    <div>${notes.map((note) => `<p>${escapeHtml(note)}</p>`).join("")}</div>
  `;
}

function renderDistribution(container, rows) {
  if (!rows.length) {
    container.innerHTML = empty("Sin distribucion de rating.");
    return;
  }

  const max = Math.max(...rows.map((row) => row.count || 0), 1);
  container.innerHTML = `<div class="chart-bars chart-bars--compact">${rows
    .map((row) => `<div class="chart-bar" style="height:${Math.max(7, (row.count / max) * 100)}%"><span>${escapeHtml(row.bucket)} · ${row.count}</span></div>`)
    .join("")}</div>`;
}

function renderPhotosTimeline(container, photos) {
  if (!photos.length) {
    container.innerHTML = empty("Sin fotos para timeline.");
    return;
  }

  container.innerHTML = photos
    .slice(0, 12)
    .map((photo) => {
      const active = photo.id === state.activePhotoId ? "is-active" : "";
      return `<button class="timeline-row ${active}" data-timeline-photo="${photo.id}">
        <strong>Foto #${photo.id}</strong>
        <span>${formatDateTime(photo.scrapedAt)}</span>
        <small>ADR ${currency(photo.avgPricePerNight)}</small>
      </button>`;
    })
    .join("");

  container.querySelectorAll(".timeline-row").forEach((button) => {
    button.addEventListener("click", async () => {
      const id = Number(button.dataset.timelinePhoto);
      await loadPhoto(id);
      renderPhotoSelector();
    });
  });
}

function renderTablePreview(container, rows) {
  if (!rows.length) {
    container.innerHTML = empty("Sin filas para mostrar.");
    return;
  }

  container.innerHTML = `<div class="mini-table">${rows
    .map((row) => `<div><strong>${escapeHtml(row.hotelName)}</strong><span>${currency(row.pricePerNight)}</span></div>`)
    .join("")}</div>`;
}

function mergeRows(rows) {
  const byHotel = new Map();
  rows.forEach((row) => {
    const existing = byHotel.get(row.hotelKey);
    if (!existing) {
      byHotel.set(row.hotelKey, { ...row });
      return;
    }
    const existingPrice = existing.pricePerNight ?? Number.POSITIVE_INFINITY;
    const nextPrice = row.pricePerNight ?? Number.POSITIVE_INFINITY;
    if (nextPrice < existingPrice) {
      byHotel.set(row.hotelKey, { ...row });
    }
  });
  return Array.from(byHotel.values()).map((row, index) => ({ ...row, position: index + 1 }));
}

function summarizeRows(rows) {
  const comparable = rows.filter((row) => row.pricePerNight !== null && row.pricePerNight !== undefined);
  const prices = comparable.map((row) => row.pricePerNight).sort((a, b) => a - b);
  const ppn = rows.filter((row) => row.pricePerPersonPerNight !== null && row.pricePerPersonPerNight !== undefined).map((row) => row.pricePerPersonPerNight);
  const avg = prices.length ? round(prices.reduce((sum, value) => sum + value, 0) / prices.length) : null;
  const avgPpn = ppn.length ? round(ppn.reduce((sum, value) => sum + value, 0) / ppn.length) : null;
  return {
    rows: rows.length,
    comparableRows: comparable.length,
    avgPricePerNight: avg,
    avgPricePerPersonNight: avgPpn,
    minPricePerNight: prices.length ? Math.min(...prices) : null,
    maxPricePerNight: prices.length ? Math.max(...prices) : null,
    medianPricePerNight: medianOf(prices),
  };
}

function buildLocationCoverage(rows) {
  const located = rows.filter((row) => row.latitude !== null && row.longitude !== null).length;
  return {
    located,
    total: rows.length,
    pct: rows.length ? round((located / rows.length) * 100) : 0,
  };
}

function buildRatingDistribution(rows) {
  const buckets = [
    { bucket: "9+", count: 0 },
    { bucket: "8-8.9", count: 0 },
    { bucket: "7-7.9", count: 0 },
    { bucket: "<7", count: 0 },
    { bucket: "N/A", count: 0 },
  ];
  rows.forEach((row) => {
    if (row.rating === null || row.rating === undefined) {
      buckets[4].count += 1;
      return;
    }
    if (row.rating >= 9) buckets[0].count += 1;
    else if (row.rating >= 8) buckets[1].count += 1;
    else if (row.rating >= 7) buckets[2].count += 1;
    else buckets[3].count += 1;
  });
  return buckets;
}

function buildCompetitiveSet(rows) {
  const comparable = rows.filter((row) => row.pricePerNight !== null && row.pricePerNight !== undefined);
  if (!comparable.length) return [];
  const marketAvg = comparable.reduce((sum, row) => sum + row.pricePerNight, 0) / comparable.length;
  return comparable
    .map((row) => {
      const gapVsMarketPct = marketAvg > 0 ? round(((row.pricePerNight - marketAvg) / marketAvg) * 100) : 0;
      return {
        hotelKey: row.hotelKey,
        hotelName: row.hotelName,
        pricePerNight: row.pricePerNight,
        gapVsMarketPct,
      };
    })
    .sort((a, b) => b.pricePerNight - a.pricePerNight)
    .slice(0, 20);
}

function buildInsights(summary, competitiveSet) {
  const insights = [];
  if (competitiveSet.length) {
    const leader = competitiveSet[0];
    insights.push({
      severity: "info",
      title: "Lider de precio identificado",
      message: `${leader.hotelName} está ${pct(leader.gapVsMarketPct)} frente a la media del set.`,
    });
    const low = [...competitiveSet].sort((a, b) => a.pricePerNight - b.pricePerNight)[0];
    insights.push({
      severity: "warning",
      title: "Precio agresivo en el mercado",
      message: `${low.hotelName} se sitúa en ${currency(low.pricePerNight)} (${pct(low.gapVsMarketPct)} vs mercado).`,
    });
  }
  if (summary.rows && summary.comparableRows < summary.rows) {
    insights.push({
      severity: "warning",
      title: "Comparabilidad parcial",
      message: `${summary.comparableRows}/${summary.rows} hoteles tienen precio comparable.`,
    });
  }
  return insights.slice(0, 6);
}

function buildHeatmapFromRows(rows) {
  const points = rows
    .filter((row) => row.latitude !== null && row.longitude !== null && row.pricePerNight !== null && row.pricePerNight !== undefined)
    .map((row) => ({
      hotelName: row.hotelName,
      latitude: row.latitude,
      longitude: row.longitude,
      pricePerNight: row.pricePerNight,
      intensity: 0.6,
    }));
  const prices = points.map((point) => point.pricePerNight);
  return {
    photosUsed: state.heatmap.photosUsed || 6,
    points,
    scale: {
      minPricePerNight: prices.length ? Math.min(...prices) : 0,
      maxPricePerNight: prices.length ? Math.max(...prices) : 0,
    },
  };
}

function renderHeatmapElement(container, options = {}) {
  const points = state.heatmap?.points || [];
  if (!points.length) {
    destroyMapInstance(container);
    container.innerHTML = empty("Sin puntos geolocalizados para mapa de calor.");
    return;
  }
  if (!window.maplibregl) {
    container.innerHTML = empty("MapLibre no disponible en este navegador.");
    return;
  }

  const mapContainer = ensureMapContainer(container);
  const map = ensureMapInstance(mapContainer);
  const overlayRows = options.overlayRows || [];
  const featureCollection = buildMapFeatureCollection(points, overlayRows);
  updateMapData(map, mapContainer.id, featureCollection, !options.compact);
  
  if (!options.compact) {
    renderCustomMapMarkers(map, overlayRows, mapContainer.id);
  } else {
    clearMarkersForMap(mapContainer.id);
  }
}

function exportCsv() {
  const rows = filteredRows();
  if (!rows.length) {
    setStatus("No hay filas para exportar.", "error");
    return;
  }

  const header = [
    "Foto",
    "Hotel",
    "Habitacion",
    "Rating",
    "PrecioTotal",
    "Moneda",
    "Pax",
    "CheckIn",
    "CheckOut",
    "Noches",
    "PrecioHabNoche",
    "PrecioPersNoche",
    "GapMercado",
  ];

  const body = rows.map((row) => [
    state.activePhotoId || "",
    row.hotelName,
    row.roomType || "",
    row.rating ?? "",
    row.price ?? "",
    row.currency || "",
    row.pax ?? "",
    row.checkIn || "",
    row.checkOut || "",
    row.nights ?? "",
    row.pricePerNight ?? "",
    row.pricePerPersonPerNight ?? "",
    gapFor(row.hotelKey) ?? "",
  ]);

  const csv = [header, ...body]
    .map((line) => line.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(","))
    .join("\n");

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `revenue-foto-${state.activePhotoId || "na"}-${Date.now()}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

function validateCaptureInputs() {
  const checkIn = state.captureConfig.checkIn;
  const nights = Number(state.captureConfig.nights);
  const weeks = Number(state.captureConfig.weeks);
  const limit = Number(state.captureConfig.limit);
  if (!checkIn) return { ok: false, message: "Selecciona una fecha de check-in." };
  if (!Number.isInteger(nights) || nights < 1 || nights > 30) return { ok: false, message: "Noches debe estar entre 1 y 30." };
  if (!Number.isInteger(weeks) || weeks < 1 || weeks > 26) return { ok: false, message: "Semanas debe estar entre 1 y 26." };
  if (!Number.isInteger(limit) || limit < 1 || limit > 500) return { ok: false, message: "Hoteles debe estar entre 1 y 500." };
  return { ok: true, checkIn, nights, weeks, limit };
}
function openCaptureModal() {
  const modal = $("#captureModal");
  if (!modal) return;
  const zoneSelect = $("#modalZones");
  if (zoneSelect) {
    zoneSelect.innerHTML = presets.map((preset) => `<option value="${preset.id}" ${state.captureConfig.presetIds.includes(preset.id) ? "selected" : ""}>${escapeHtml(preset.name)}</option>`).join("");
  }
  $("#modalCheckIn").value = state.captureConfig.checkIn;
  $("#modalNights").value = String(state.captureConfig.nights);
  $("#modalWeeks").value = String(state.captureConfig.weeks);
  $("#modalLimit").value = String(state.captureConfig.limit);
  modal.classList.remove("is-hidden");
}
function closeCaptureModal() {
  const modal = $("#captureModal");
  if (!modal) return;
  modal.classList.add("is-hidden");
}

function applyModalCaptureConfig() {
  const selectedIds = Array.from($("#modalZones")?.selectedOptions || []).map((option) => option.value).filter(Boolean);
  if (selectedIds.length) {
    state.captureConfig.presetIds = selectedIds;
    state.captureConfig.presetId = selectedIds[0];
  }
  state.captureConfig.checkIn = $("#modalCheckIn").value;
  state.captureConfig.nights = Number($("#modalNights").value || state.captureConfig.nights);
  state.captureConfig.weeks = Number($("#modalWeeks").value || state.captureConfig.weeks);
  state.captureConfig.limit = Number($("#modalLimit").value || state.captureConfig.limit);
  saveAppSettings();
}

function openSettingsModal() {
  const modal = $("#settingsModal");
  if (!modal) return;
  $("#settingsTheme").value = state.darkMode ? "dark" : "light";
  $("#settingsHeatmapPhotos").value = String(state.heatmap.photosUsed || 6);
  $("#settingsNights").value = String(state.captureConfig.nights);
  $("#settingsWeeks").value = String(state.captureConfig.weeks);
  $("#settingsLimit").value = String(state.captureConfig.limit);
  modal.classList.remove("is-hidden");
}

function closeSettingsModal() {
  const modal = $("#settingsModal");
  if (!modal) return;
  modal.classList.add("is-hidden");
}

function applySettingsFromModal() {
  const heatmapPhotos = Number($("#settingsHeatmapPhotos").value || state.heatmap.photosUsed || 6);
  const nights = Number($("#settingsNights").value || state.captureConfig.nights);
  const weeks = Number($("#settingsWeeks").value || state.captureConfig.weeks);
  const limit = Number($("#settingsLimit").value || state.captureConfig.limit);

  if (!Number.isInteger(heatmapPhotos) || heatmapPhotos < 1 || heatmapPhotos > 24) {
    setStatus("Fotos heatmap debe estar entre 1 y 24.", "error");
    return false;
  }
  if (!Number.isInteger(nights) || nights < 1 || nights > 30) {
    setStatus("Noches por defecto debe estar entre 1 y 30.", "error");
    return false;
  }
  if (!Number.isInteger(weeks) || weeks < 1 || weeks > 26) {
    setStatus("Semanas por defecto debe estar entre 1 y 26.", "error");
    return false;
  }
  if (!Number.isInteger(limit) || limit < 1 || limit > 500) {
    setStatus("Hoteles por defecto debe estar entre 1 y 500.", "error");
    return false;
  }

  state.darkMode = true;
  state.heatmap.photosUsed = heatmapPhotos;
  state.captureConfig.nights = nights;
  state.captureConfig.weeks = weeks;
  state.captureConfig.limit = limit;
  applyTheme();
  saveAppSettings();
  return true;
}
function movementAgainstPreviousPhoto() {
  if (!state.activePhotoId || !state.photos.length) return null;
  const index = state.photos.findIndex((photo) => photo.id === state.activePhotoId);
  if (index < 0) return null;
  const current = state.photos[index];
  const previous = state.photos[index + 1];
  if (!previous) return null;
  return {
    avgPricePerNightChangePct: pctChange(current.avgPricePerNight, previous.avgPricePerNight),
    avgPricePerPersonNightChangePct: pctChange(current.avgPricePerPersonNight, previous.avgPricePerPersonNight),
  };
}

function mixedInsights() {
  const insights = [...(state.metrics?.insights || [])];
  const movement = movementAgainstPreviousPhoto();

  if (movement?.avgPricePerNightChangePct !== null && movement?.avgPricePerNightChangePct !== undefined) {
    const change = movement.avgPricePerNightChangePct;
    if (Math.abs(change) >= 5) {
      insights.unshift({
        severity: Math.abs(change) >= 12 ? "critical" : "warning",
        title: change > 0 ? "Subida relevante en la foto activa" : "Bajada relevante en la foto activa",
        message: `El precio por habitacion/noche cambia ${pct(change)} respecto a la foto anterior.`,
      });
    }
  }

  return insights.slice(0, 7);
}

function activePresets() {
  const selected = presets.filter((preset) => state.captureConfig.presetIds.includes(preset.id));
  return selected.length ? selected : [presets[0]];
}

function activePreset() {
  return activePresets()[0];
}

function findTargetForPreset(name) {
  return state.targets.find((target) => target.name === name) || null;
}

function buildBookingUrl(baseUrl, checkIn, nights) {
  const url = new URL(baseUrl);
  const start = new Date(`${checkIn}T00:00:00`);
  const end = new Date(start);
  end.setDate(start.getDate() + nights);
  url.searchParams.set("checkin", toDate(start));
  url.searchParams.set("checkout", toDate(end));
  return url.toString();
}

function addWeeks(checkIn, weeks) {
  const date = new Date(`${checkIn}T00:00:00`);
  date.setDate(date.getDate() + weeks * 7);
  return toDate(date);
}

function toDate(date) {
  return date.toISOString().slice(0, 10);
}

function filteredRows() {
  const clean = state.query.trim().toLowerCase();
  let rows = state.rows;
  if (clean) {
    rows = state.rows.filter((row) => [row.hotelName, row.roomType, row.currency, row.address].some((value) => value && value.toLowerCase().includes(clean)));
  }

  // Apply Explorer advanced filters
  const ratingMin = $("#filterRating")?.value;
  if (ratingMin) {
    const min = Number(ratingMin);
    rows = rows.filter(row => row.rating !== null && row.rating >= min);
  }

  const maxPriceVal = $("#filterMaxPrice")?.value;
  if (maxPriceVal) {
    const max = Number(maxPriceVal);
    rows = rows.filter(row => {
      const ppn = row.pricePerNight ?? (row.price && row.nights ? row.price / row.nights : null);
      return ppn !== null && ppn <= max;
    });
  }

  // Apply quick boolean filters
  if (state.filterOnlyRiu) {
    rows = rows.filter(row => row.hotelName.toLowerCase().includes("riu"));
  }

  if (state.filterCriticalGaps) {
    rows = rows.filter(row => {
      const gap = gapFor(row.hotelKey);
      return gap !== null && Math.abs(gap) >= 15;
    });
  }

  // Apply column sorting
  if (state.sortKey) {
    rows = [...rows].sort((a, b) => {
      let valA = a[state.sortKey];
      let valB = b[state.sortKey];

      // Special dynamic fields
      if (state.sortKey === "gap") {
        valA = gapFor(a.hotelKey) ?? -9999;
        valB = gapFor(b.hotelKey) ?? -9999;
      } else if (state.sortKey === "pricePerNight") {
        valA = a.pricePerNight ?? (a.price && a.nights ? a.price / a.nights : 0);
        valB = b.pricePerNight ?? (b.price && b.nights ? b.price / b.nights : 0);
      }

      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      if (typeof valA === "string") {
        return state.sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
      } else {
        return state.sortAsc ? valA - valB : valB - valA;
      }
    });
  }

  return rows;
}

function updateRatingQuickButtons() {
  const rating = $("#filterRating")?.value || "";
  $$("[data-rating-filter]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.ratingFilter === rating);
  });
}

function executeRiuAction(action) {
  if (action === "filter-riu") {
    state.filterOnlyRiu = true;
    state.filterCriticalGaps = false;
    $("#btnFilterRiu")?.classList.add("is-active");
    $("#btnFilterGaps")?.classList.remove("is-active");
    showView("explorer");
    renderExplorer();
    setStatus("Explorador filtrado por hoteles RIU.", "ok");
    return;
  }
  if (action === "filter-gaps") {
    state.filterOnlyRiu = true;
    state.filterCriticalGaps = true;
    $("#btnFilterRiu")?.classList.add("is-active");
    $("#btnFilterGaps")?.classList.add("is-active");
    showView("explorer");
    renderExplorer();
    setStatus("Mostrando RIU con gaps críticos.", "ok");
    return;
  }
  if (action === "open-map") {
    showView("map");
    const first = riuRows().find((row) => row.latitude !== null && row.longitude !== null);
    if (first) {
      openMapDrawerForHotel(first);
      setStatus(`Ficha RIU abierta: ${first.hotelName}`, "ok");
    } else {
      setStatus("No hay hoteles RIU geolocalizados en la foto activa.", "error");
    }
  }
}

function riuRows() {
  return state.rows.filter((row) => isRiuHotel(row.hotelName));
}

function isRiuHotel(name) {
  return String(name || "").toLowerCase().includes("riu");
}

function shortHotelName(name) {
  return String(name || "RIU")
    .replace(/hotel\s+/i, "")
    .replace(/\s+-\s+.*$/, "")
    .replace(/\s+gran canaria/i, "")
    .slice(0, 16);
}

function competitiveRank(hotelKey) {
  const ranking = [...state.rows]
    .map((row) => ({ hotelKey: row.hotelKey, price: row.pricePerNight ?? (row.price && row.nights ? row.price / row.nights : null) }))
    .filter((row) => Number.isFinite(row.price) && row.price > 0)
    .sort((a, b) => b.price - a.price);
  const index = ranking.findIndex((row) => row.hotelKey === hotelKey);
  return index >= 0 ? index + 1 : null;
}

function riuActionFor(gap) {
  if (gap === null || gap === undefined) return "Completar datos antes de recomendar acción.";
  if (gap >= 15) return "Revisar elasticidad: RIU está claramente por encima del mercado.";
  if (gap <= -10) return "Oportunidad: margen para reposicionar tarifa si la demanda acompaña.";
  return "Mantener vigilancia: posición razonablemente alineada con el set.";
}

function buildRiuAlerts(rows, avgGap) {
  const alerts = [];
  if (avgGap !== null && avgGap !== undefined && Math.abs(avgGap) >= 12) {
    alerts.push({
      severity: avgGap > 0 ? "warning" : "info",
      title: avgGap > 0 ? "Prima RIU elevada" : "RIU bajo mediana",
      message: `El ADR medio RIU está ${pct(avgGap)} frente a la mediana del mercado.`,
    });
  }
  rows.forEach((row) => {
    const gap = gapFor(row.hotelKey);
    if (gap !== null && gap >= 15) {
      alerts.push({
        severity: "critical",
        title: "Gap superior crítico",
        message: `${row.hotelName} está ${pct(gap)} sobre el mercado. Revisar pick-up antes de sostener prima.`,
      });
    }
    if (gap !== null && gap <= -10) {
      alerts.push({
        severity: "warning",
        title: "Posible oportunidad de tarifa",
        message: `${row.hotelName} está ${pct(gap)} bajo mercado. Revisar inventario y demanda.`,
      });
    }
    if (row.latitude === null || row.longitude === null) {
      alerts.push({
        severity: "info",
        title: "Coordenadas pendientes",
        message: `${row.hotelName} no aparecerá como pin RIU hasta completar geolocalización.`,
      });
    }
  });
  return alerts.length ? alerts.slice(0, 8) : [{ severity: "info", title: "RIU estable", message: "No hay alertas críticas para los hoteles RIU en la foto activa." }];
}

function openMapDrawerForHotelByKey(hotelKey) {
  const hotel = state.rows.find((row) => row.hotelKey === hotelKey);
  if (!hotel) {
    setStatus("No se encontró la ficha RIU solicitada.", "error");
    return;
  }
  showView("map");
  openMapDrawerForHotel(hotel);
}

function gapFor(hotelKey) {
  return state.metrics?.competitiveSet?.find((item) => item.hotelKey === hotelKey)?.gapVsMarketPct ?? null;
}

function badgeClass(value) {
  if (value === null || value === undefined) return "badge";
  return value > 10 ? "badge high" : value < -10 ? "badge low" : "badge";
}

function trendTone(value) {
  if (value === null || value === undefined) return "neutral";
  return value >= 0 ? "up" : "down";
}

function pct(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "sin comparativa";
  return `${value > 0 ? "▲ +" : value < 0 ? "▼ " : ""}${round(Math.abs(value))}%`;
}

function pctChange(current, previous) {
  if (!previous || previous === 0 || current === null || current === undefined) return null;
  return round(((current - previous) / previous) * 100);
}

function spreadLabel(summary) {
  if (!summary?.minPricePerNight || !summary?.maxPricePerNight) return "habitacion / noche";
  const spread = summary.maxPricePerNight - summary.minPricePerNight;
  const pctSpread = summary.minPricePerNight ? round((spread / summary.minPricePerNight) * 100) : 0;
  return `spread ${currency(spread)} · ${pctSpread}%`;
}

function sparkFromPhotos(key) {
  const values = [...state.photos]
    .reverse()
    .slice(-8)
    .map((photo) => Number(photo[key] || 0))
    .filter((value) => Number.isFinite(value) && value > 0);
  return normalizeSpark(values);
}

function normalizeSpark(values) {
  if (!values.length) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  return values.map((value) => Math.max(18, Math.round(18 + ((value - min) / range) * 82)));
}

function medianOf(values) {
  if (!values.length) return null;
  const middle = Math.floor(values.length / 2);
  return values.length % 2 ? values[middle] : round((values[middle - 1] + values[middle]) / 2);
}

function currency(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value);
}

function round(value) {
  return Math.round(Number(value) * 100) / 100;
}

function comparabilityPct(summary) {
  if (!summary || !summary.rows) return 0;
  return round((summary.comparableRows / summary.rows) * 100);
}

function boundsOf(rows) {
  const latitudes = rows.map((row) => row.latitude);
  const longitudes = rows.map((row) => row.longitude);
  return {
    minLat: Math.min(...latitudes),
    maxLat: Math.max(...latitudes),
    minLng: Math.min(...longitudes),
    maxLng: Math.max(...longitudes),
  };
}

function project(row, bounds) {
  const xRange = bounds.maxLng - bounds.minLng || 1;
  const yRange = bounds.maxLat - bounds.minLat || 1;
  return {
    x: 8 + ((row.longitude - bounds.minLng) / xRange) * 84,
    y: 8 + ((bounds.maxLat - row.latitude) / yRange) * 84,
  };
}

function formatDateTime(iso) {
  if (!iso) return "-";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat("es-ES", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatShortDate(iso) {
  if (!iso) return "-";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return String(iso).slice(0, 5);
  return new Intl.DateTimeFormat("es-ES", { day: "2-digit", month: "2-digit" }).format(date);
}

function readSearchParam(rawUrl, key) {
  try {
    return new URL(rawUrl).searchParams.get(key);
  } catch {
    return null;
  }
}

function setStatus(text, mode = "info") {
  const status = $("#status");
  if (!status) return;
  if (statusTimer) {
    clearTimeout(statusTimer);
    statusTimer = null;
  }
  status.textContent = text;
  status.className = `status status--${mode} is-visible`;
  statusTimer = setTimeout(() => {
    status.classList.remove("is-visible");
  }, mode === "error" ? 6800 : 3800);
}

function safeJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function readableError(error) {
  return error instanceof Error ? error.message : String(error);
}

function empty(text) {
  return `<div class="empty">${escapeHtml(text)}</div>`;
}

function loadWidgets() {
  try {
    const parsed = JSON.parse(localStorage.getItem("revenue-flask-widgets") || "[]");
    if (!Array.isArray(parsed)) return [...widgetOrder];
    const clean = parsed.filter((key) => widgetOrder.includes(key));
    return clean.length ? clean : [...widgetOrder];
  } catch {
    return [...widgetOrder];
  }
}

function saveWidgets() {
  localStorage.setItem("revenue-flask-widgets", JSON.stringify(state.widgets));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
}

function ensureMapContainer(container) {
  if (container.firstElementChild && container.firstElementChild.classList.contains("maplibre-canvas-host")) {
    return container.firstElementChild;
  }
  container.innerHTML = "";
  const host = document.createElement("div");
  host.className = "maplibre-canvas-host";
  host.id = `${container.id || "map"}-host`;
  container.appendChild(host);
  return host;
}

function buildMapStyle() {
  const cartoLayer = state.darkMode ? "dark_all" : "light_all";
  return {
    version: 8,
    glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
    sources: {
      positron: {
        type: "raster",
        tiles: [
          `https://a.basemaps.cartocdn.com/${cartoLayer}/{z}/{x}/{y}.png`,
          `https://b.basemaps.cartocdn.com/${cartoLayer}/{z}/{x}/{y}.png`,
          `https://c.basemaps.cartocdn.com/${cartoLayer}/{z}/{x}/{y}.png`,
          `https://d.basemaps.cartocdn.com/${cartoLayer}/{z}/{x}/{y}.png`,
        ],
        tileSize: 256,
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>',
      },
    },
    layers: [{ id: "positron", type: "raster", source: "positron" }],
  };
}

function ensureMapInstance(host) {
  const known = mapRegistry.get(host.id);
  if (known) {
    known.resize();
    return known;
  }
  const map = new window.maplibregl.Map({
    container: host,
    style: buildMapStyle(),
    center: [-15.56, 27.78],
    zoom: 9.4,
    attributionControl: true,
  });
  map.addControl(new window.maplibregl.NavigationControl({ visualizePitch: false }), "top-right");
  mapRegistry.set(host.id, map);
  return map;
}

function sourceIdFor(hostId) {
  return `${hostId}-source`;
}

function ensureMapLayers(map, sourceId) {
  if (map.getSource(sourceId)) return;

  map.addSource(sourceId, {
    type: "geojson",
    data: { type: "FeatureCollection", features: [] },
  });

  map.addLayer({
    id: `${sourceId}-heat`,
    type: "heatmap",
    source: sourceId,
    filter: ["==", ["get", "kind"], "heat"],
    maxzoom: 14,
    paint: {
      "heatmap-weight": ["interpolate", ["linear"], ["get", "intensity"], 0, 0.1, 1, 1],
      "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 5, 0.6, 10, 1.2, 13, 1.8],
      "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 4, 10, 9, 22, 13, 34],
      "heatmap-opacity": 0.62,
      "heatmap-color": [
        "interpolate",
        ["linear"],
        ["heatmap-density"],
        0,
        "rgba(197,17,47,0)",
        0.3,
        "rgba(197,17,47,0.35)",
        0.6,
        "rgba(197,17,47,0.55)",
        1,
        "rgba(133,10,31,0.86)",
      ],
    },
  });

  map.addLayer({
    id: `${sourceId}-points`,
    type: "circle",
    source: sourceId,
    filter: ["==", ["get", "kind"], "pin"],
    paint: {
      "circle-color": "#2563eb",
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 3, 12, 6],
      "circle-stroke-color": "#ffffff",
      "circle-stroke-width": 1.3,
      "circle-opacity": 0.95,
    },
  });

  map.addLayer({
    id: `${sourceId}-labels`,
    type: "symbol",
    source: sourceId,
    filter: ["==", ["get", "kind"], "pin"],
    layout: {
      "text-field": ["get", "label"],
      "text-size": 11,
      "text-offset": [0, 1.35],
      "text-anchor": "top",
      "text-allow-overlap": false,
    },
    paint: {
      "text-color": "#0f172a",
      "text-halo-color": "#ffffff",
      "text-halo-width": 1,
    },
  });

  map.on("click", `${sourceId}-points`, (event) => {
    const feature = event.features?.[0];
    if (!feature || feature.geometry.type !== "Point") return;
    const coordinates = feature.geometry.coordinates;
    const hotelName = String(feature.properties?.hotelName || "Hotel");
    const priceLabel = String(feature.properties?.label || "-");
    const hotelKey = String(feature.properties?.hotelKey || "");
    const selectedHotel = state.rows.find((row) => row.hotelKey === hotelKey) || state.rows.find((row) => row.hotelName === hotelName);
    if (selectedHotel) {
      openMapDrawerForHotel(selectedHotel);
    }
    new window.maplibregl.Popup({ closeButton: false, offset: 14 })
      .setLngLat(coordinates)
      .setHTML(`<strong>${escapeHtml(hotelName)}</strong><br/>ADR: ${escapeHtml(priceLabel)}`)
      .addTo(map);
  });

  map.on("mouseenter", `${sourceId}-points`, () => {
    map.getCanvas().style.cursor = "pointer";
  });
  map.on("mouseleave", `${sourceId}-points`, () => {
    map.getCanvas().style.cursor = "";
  });
}

function buildMapFeatureCollection(points, overlayRows) {
  const heatFeatures = points
    .filter((point) => Number.isFinite(point.latitude) && Number.isFinite(point.longitude))
    .map((point) => ({
      type: "Feature",
      properties: {
        kind: "heat",
        hotelName: point.hotelName || "Hotel",
        intensity: Number(point.intensity ?? 0.5),
      },
      geometry: {
        type: "Point",
        coordinates: [Number(point.longitude), Number(point.latitude)],
      },
    }));

  const pinFeatures = overlayRows
    .filter((row) => Number.isFinite(row.latitude) && Number.isFinite(row.longitude))
    .map((row) => {
      const ppn = row.pricePerNight ?? (row.price && row.nights ? row.price / row.nights : null);
      return {
        type: "Feature",
        properties: {
          kind: "pin",
          hotelKey: row.hotelKey,
          hotelName: row.hotelName || "Hotel",
          label: currency(ppn),
        },
        geometry: {
          type: "Point",
          coordinates: [Number(row.longitude), Number(row.latitude)],
        },
      };
    });

  return {
    type: "FeatureCollection",
    features: [...heatFeatures, ...pinFeatures],
  };
}

function fitMapToFeatures(map, featureCollection) {
  const points = featureCollection.features.filter((feature) => feature.geometry?.type === "Point");
  if (!points.length) return;
  const bounds = new window.maplibregl.LngLatBounds();
  points.forEach((feature) => bounds.extend(feature.geometry.coordinates));
  map.fitBounds(bounds, { padding: 36, maxZoom: 12, duration: 420 });
}

function updateMapData(map, hostId, featureCollection, fit) {
  const sourceId = sourceIdFor(hostId);
  const update = () => {
    ensureMapLayers(map, sourceId);
    const source = map.getSource(sourceId);
    if (source) source.setData(featureCollection);
    map.resize();
    if (fit) fitMapToFeatures(map, featureCollection);
  };

  if (map.isStyleLoaded()) {
    update();
  } else {
    map.once("load", update);
  }
}

function destroyMapInstance(container) {
  const host = container?.firstElementChild;
  if (!host?.id) return;
  const known = mapRegistry.get(host.id);
  if (!known) return;
  known.remove();
  mapRegistry.delete(host.id);
}

function loadTheme() {
  loadAppSettings();
  state.darkMode = true; // Always true for Bloomberg style
  applyTheme();
}

function applyTheme() {
  document.body.classList.toggle("is-dark", state.darkMode);
  destroyAllMaps();
}

function destroyAllMaps() {
  mapRegistry.forEach((map) => map.remove());
  mapRegistry.clear();
}

function saveAppSettings() {
  localStorage.setItem("revenue-app-settings", JSON.stringify({
    darkMode: state.darkMode,
    heatmapPhotos: state.heatmap.photosUsed,
    presetIds: state.captureConfig.presetIds,
    nights: state.captureConfig.nights,
    weeks: state.captureConfig.weeks,
    limit: state.captureConfig.limit,
  }));
}

function loadAppSettings() {
  try {
    const raw = localStorage.getItem("revenue-app-settings");
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (typeof parsed.darkMode === "boolean") state.darkMode = parsed.darkMode;
    if (Number.isInteger(parsed.heatmapPhotos) && parsed.heatmapPhotos >= 1 && parsed.heatmapPhotos <= 24) state.heatmap.photosUsed = parsed.heatmapPhotos;
    if (Array.isArray(parsed.presetIds) && parsed.presetIds.length) {
      const cleanPresetIds = parsed.presetIds.filter((presetId) => presets.some((preset) => preset.id === presetId));
      if (cleanPresetIds.length) state.captureConfig.presetIds = cleanPresetIds;
    }
    if (Number.isInteger(parsed.nights) && parsed.nights >= 1 && parsed.nights <= 30) state.captureConfig.nights = parsed.nights;
    if (Number.isInteger(parsed.weeks) && parsed.weeks >= 1 && parsed.weeks <= 26) state.captureConfig.weeks = parsed.weeks;
    if (Number.isInteger(parsed.limit) && parsed.limit >= 1 && parsed.limit <= 500) state.captureConfig.limit = parsed.limit;
  } catch {
    // noop
  }
}

// ==========================================
// Bloomberg Terminal Live Widgets Helpers
// ==========================================
function updateUtcClock() {
  const clock = document.getElementById("utcClock");
  if (!clock) return;
  const now = new Date();
  const timeString = now.toISOString().replace("T", " ").substring(0, 19);
  clock.textContent = `UTC ${timeString}`;
}

async function checkConnectionHealth() {
  const indicator = document.getElementById("connectionStatus");
  const text = document.getElementById("connectionText");
  if (!indicator || !text) return;
  try {
    await api("/api/health");
    indicator.className = "indicator online";
    indicator.style.backgroundColor = "var(--bb-green)";
    indicator.style.boxShadow = "0 0 4px var(--bb-green)";
    text.textContent = "SYS: ONLINE";
  } catch (error) {
    indicator.className = "indicator offline";
    indicator.style.backgroundColor = "var(--bb-red)";
    indicator.style.boxShadow = "0 0 4px var(--bb-red)";
    text.textContent = "SYS: OFFLINE";
  }
}

function handleKeyboardShortcuts(event) {
  if (["F1", "F2", "F3", "F4", "F5", "F6"].includes(event.key)) {
    event.preventDefault();
    const viewMap = {
      "F1": "dashboard",
      "F2": "workspace",
      "F3": "scraping",
      "F4": "map",
      "F5": "explorer",
      "F6": "riu"
    };
    showView(viewMap[event.key]);
    setStatus(`Terminal cambiada a: ${viewMap[event.key].toUpperCase()}`, "info");
  }
  if (event.key === "Escape") {
    closeCaptureModal();
    closeSettingsModal();
  }
  if (event.ctrlKey && event.key.toLowerCase() === "e") {
    event.preventDefault();
    showView("explorer");
    const search = document.getElementById("search");
    if (search) {
      search.focus();
      search.select();
    }
  }
}

function executeCommand(val) {
  const clean = val.trim().toLowerCase();
  if (!clean) return;
  
  if (clean.startsWith("/dash")) {
    showView("dashboard");
    setStatus("Terminal cambiada a: DASHBOARD", "ok");
  } else if (clean.startsWith("/riu")) {
    showView("riu");
    setStatus("Terminal cambiada a: ANÁLISIS RIU", "ok");
  } else if (clean.startsWith("/work")) {
    showView("workspace");
    setStatus("Terminal cambiada a: WORKSPACE", "ok");
  } else if (clean.startsWith("/scrap") || clean.startsWith("/capturas")) {
    showView("scraping");
    setStatus("Terminal cambiada a: CAPTURAS", "ok");
  } else if (clean.startsWith("/map") || clean.startsWith("/heatmap")) {
    showView("map");
    setStatus("Terminal cambiada a: MAPA", "ok");
  } else if (clean.startsWith("/exp") || clean.startsWith("/tabla")) {
    showView("explorer");
    setStatus("Terminal cambiada a: EXPLORADOR", "ok");
  } else if (clean.startsWith("/run")) {
    openCaptureModal();
    setStatus("Abriendo configurador de captura...", "info");
  } else if (clean.startsWith("/help")) {
    setStatus("Cmds: /dash, /riu, /work, /scrap, /map, /exp, /run, /help", "info");
  } else {
    setStatus(`Comando no reconocido: ${val}. Escribe /help`, "error");
  }
}

function addConsoleLog(message, type = "info") {
  const consoleBox = document.getElementById("scrapeConsole");
  if (!consoleBox) return;
  
  const timestamp = new Date().toISOString().substring(11, 19);
  const line = document.createElement("div");
  line.className = `console-line console-line--${type}`;
  line.textContent = `[${timestamp}] ${message}`;
  
  consoleBox.appendChild(line);
  consoleBox.scrollTop = consoleBox.scrollHeight;
}

function openMapDrawerForHotel(hotel) {
  const drawer = document.getElementById("mapDrawer");
  const body = document.getElementById("mapDrawerBody");
  if (!drawer || !body) return;
  
  const gap = gapFor(hotel.hotelKey);
  const isRiu = hotel.hotelName.toLowerCase().includes("riu");
  const ppn = hotel.pricePerNight ?? (hotel.price && hotel.nights ? hotel.price / hotel.nights : 0);
  const pppn = hotel.pricePerPersonPerNight ?? (ppn / (hotel.pax || 2));
  
  body.innerHTML = `
    <div class="map-drawer__section">
      <span>Hotel</span>
      <strong style="color: ${isRiu ? 'var(--bb-amber)' : '#fff'};">${escapeHtml(hotel.hotelName)}</strong>
      ${isRiu ? '<span class="riu-tag" style="margin-top: 4px; display: inline-block; width: max-content;">Propiedad RIU</span>' : ''}
    </div>
    
    <div class="map-drawer__section">
      <span>Dirección</span>
      <p>${escapeHtml(hotel.address || "Dirección no disponible")}</p>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
      <div class="map-drawer__section">
        <span>Precio / Noche</span>
        <div class="metric-badge">${currency(ppn)}</div>
      </div>
      <div class="map-drawer__section">
        <span>Precio / Persona</span>
        <div class="metric-badge" style="color: var(--bb-amber);">${currency(pppn)}</div>
      </div>
    </div>
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
      <div class="map-drawer__section">
        <span>Rating</span>
        <strong style="color: var(--bb-green);">${hotel.rating ?? "Sin rating"} / 10</strong>
      </div>
      <div class="map-drawer__section">
        <span>Gap Competitivo</span>
        <strong class="${gap >= 0 ? (gap > 10 ? 'high' : 'neutral') : 'low'}" style="color: ${gap >= 0 ? (gap > 10 ? 'var(--bb-red)' : 'var(--muted)') : 'var(--bb-green)'};">
          ${pct(gap)}
        </strong>
      </div>
    </div>
    
    <div class="map-drawer__section">
      <span>Estancia contratada</span>
      <p><b>Check-In:</b> ${hotel.checkIn || "-"}</p>
      <p><b>Check-Out:</b> ${hotel.checkOut || "-"}</p>
      <p><b>Duración:</b> ${hotel.nights ?? "-"} noches</p>
      <p><b>Pax:</b> ${hotel.pax ?? "-"} huéspedes</p>
    </div>
    
    <div class="map-drawer__section">
      <span>Habitación</span>
      <p style="font-style: italic;">${escapeHtml(hotel.roomType || "No identificado")}</p>
    </div>
  `;
  
  drawer.classList.add("is-visible");
}

let activeMarkers = new Map();

function clearMarkersForMap(mapId) {
  const list = activeMarkers.get(mapId);
  if (list) {
    list.forEach(m => m.remove());
  }
  activeMarkers.set(mapId, []);
}

function renderCustomMapMarkers(map, rows, mapId) {
  clearMarkersForMap(mapId);
  const list = [];
  
  if (!rows || !rows.length) return;
  
  // Calculate average price for thresholds
  const prices = rows.map(r => r.pricePerNight ?? (r.price / r.nights)).filter(p => p > 0);
  const avgPrice = prices.length ? prices.reduce((sum, p) => sum + p, 0) / prices.length : 150;
  
  rows.forEach(row => {
    if (row.latitude === null || row.longitude === null) return;
    
    const ppn = row.pricePerNight ?? (row.price && row.nights ? row.price / row.nights : null);
    if (!ppn) return;
    
    const el = document.createElement("div");
    el.className = "maplibre-marker-price";
    
    const isRiu = row.hotelName.toLowerCase().includes("riu");
    if (isRiu) {
      el.classList.add("riu");
      el.innerHTML = `★ €${Math.round(ppn)}`;
    } else {
      el.textContent = `€${Math.round(ppn)}`;
      if (ppn < avgPrice * 0.85) {
        el.classList.add("low");
      } else if (ppn > avgPrice * 1.15) {
        el.classList.add("high");
      } else {
        el.classList.add("mid");
      }
    }
    
    el.addEventListener("click", (e) => {
      e.stopPropagation();
      openMapDrawerForHotel(row);
    });
    
    const marker = new window.maplibregl.Marker({ element: el })
      .setLngLat([row.longitude, row.latitude])
      .addTo(map);
      
    list.push(marker);
  });
  
  activeMarkers.set(mapId, list);
}

