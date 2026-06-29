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

const presetAirAreaMap = {
  "gran-canaria-sur": "gran-canaria",
  "gran-canaria-general": "gran-canaria",
  "tenerife-sur": "tenerife",
  lanzarote: "lanzarote",
  fuerteventura: "fuerteventura",
};

const fallbackAirAreaDefinitions = [
  { id: "gran-canaria", name: "Gran Canaria", destination: "LPA" },
  { id: "tenerife", name: "Tenerife", destination: "TFS" },
  { id: "lanzarote", name: "Lanzarote", destination: "ACE" },
  { id: "fuerteventura", name: "Fuerteventura", destination: "FUE" },
];

const fallbackAirMarketDefinitions = [
  { country: "Espana", origin: "MAD", market: "Madrid" },
  { country: "Espana", origin: "BCN", market: "Barcelona" },
  { country: "Alemania", origin: "DUS", market: "Dusseldorf" },
  { country: "Alemania", origin: "FRA", market: "Frankfurt" },
  { country: "Reino Unido", origin: "LHR", market: "Londres Heathrow" },
  { country: "Reino Unido", origin: "MAN", market: "Manchester" },
  { country: "Paises Bajos", origin: "AMS", market: "Amsterdam" },
  { country: "Francia", origin: "CDG", market: "Paris Charles de Gaulle" },
];

function buildFallbackAirCatalog() {
  const countries = fallbackAirMarketDefinitions
    .filter((market, index, markets) => markets.findIndex((item) => item.country === market.country) === index)
    .map((market) => market.country);
  const routes = fallbackAirAreaDefinitions.flatMap((area) =>
    fallbackAirMarketDefinitions.map((market) => ({
      areaId: area.id,
      areaName: area.name,
      country: market.country,
      market: market.market,
      origin: market.origin,
      destination: area.destination,
      routeKey: `${market.origin}_${area.destination}`,
      label: `${market.market} (${market.origin}) -> ${area.name} (${area.destination})`,
    })),
  );
  return { areas: fallbackAirAreaDefinitions, countries, routes };
}

const fallbackAirCatalog = buildFallbackAirCatalog();

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
    airAreaIds: ["gran-canaria"],
    airCountryIds: [],
    airRouteKeys: [],
    airDirect: "",
    airTripType: "one_way",
    airReturnDate: "",
    captureHotels: true,
    captureFlights: true,
  },
  captureModalStep: "hotels",
  mapViewMode: "hotels",
  darkMode: true,
  sortKey: "position",
  sortAsc: true,
  filterOnlyRiu: false,
  filterCriticalGaps: false,
  airData: {
    flights: [],
    routes: [],
    summary: null,
    source: "mock",
    isLive: false,
    warning: "",
    airports: {},
    geojson: null,
    activeTab: "overview",
    selectedRouteKey: null,
    routeHistory: {},
    page: 1,
    pageSize: 10,
    filters: {
      query: "",
      market: "",
      origin: "",
      destination: "",
      airline: "",
      connection: "",
      price: "",
      signal: "",
      dateFrom: "",
      dateTo: "",
    },
  },
  hotelData: {
    activeTab: "table",
    filters: { query: "", board: "", rating: "", riu: "", cancel: "" },
  },
  ai: { active: false, pending: false, messages: [] },
  airCatalog: { areas: [], countries: [], routes: [] },
  hotelHistory: {},
  runtime: {
    airBootPromise: null,
    airBootReady: false,
    activeView: "dashboard",
  },
};
const mapRegistry = new Map();
let statusTimer = null;

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

window.addEventListener("DOMContentLoaded", async () => {
  loadTheme();
  loadExplorerFilters();
  initNavigation();
  initPresets();
  initWorkspaceControls();
  initHotelControls();
  bindEvents();
  showView("dashboard");
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
    // Air_Data is not needed for the landing dashboard, so we warm it in the background.
    void ensureAirDataBoot();
    setStatus("Servidor Flask listo. Selecciona mercado y captura cuando quieras.", "ok");
  } catch (error) {
    setStatus(readableError(error), "error");
  }
}

// Keeps the hotel dashboard interactive first and loads air intelligence only once on demand.
function ensureAirDataBoot() {
  if (state.runtime.airBootPromise) return state.runtime.airBootPromise;
  state.runtime.airBootPromise = (async () => {
    await loadAirCatalog();
    await loadAirData();
    state.runtime.airBootReady = true;
    renderAirData();
  })().catch((error) => {
    state.runtime.airBootPromise = null;
    throw error;
  });
  return state.runtime.airBootPromise;
}

function initNavigation() {
  $$(".nav__item").forEach((button) => {
    if (button.classList.contains("nav__group-toggle")) {
      button.addEventListener("click", () => toggleNavGroup(button.closest(".nav__group")));
      return;
    }
    if (!button.dataset.view) return;
    button.addEventListener("click", () => showView(button.dataset.view));
  });
}

function toggleNavGroup(group) {
  if (!group) return;
  const open = group.classList.toggle("is-open");
  group.querySelector(".nav__group-toggle")?.setAttribute("aria-expanded", open ? "true" : "false");
}

function showView(view) {
  state.runtime.activeView = view;
  $$(".nav__item").forEach((item) => item.classList.toggle("is-active", item.dataset.view === view));
  $$(".view").forEach((section) => section.classList.toggle("is-visible", section.id === view));
  // Keep the "Datos" group expanded + highlighted while one of its sub-views is active.
  const datosGroup = document.querySelector('.nav__group[data-nav-group="datos"]');
  if (datosGroup) {
    const inDatos = view === "airData" || view === "hotelData";
    datosGroup.classList.toggle("is-active", inDatos);
    if (inDatos) datosGroup.classList.add("is-open");
  }
  const meta = {
    dashboard: ["Dashboard", "Lectura ejecutiva del mercado hotelero, presión competitiva y evolución de precios."],
    riu: ["Análisis RIU", "Gap, ranking y oportunidades de acción para propiedades RIU dentro del set activo."],
    workspace: ["Area de trabajo", "Módulos personalizables para construir una mesa de análisis propia."],
    scraping: ["Capturas", "Lanza nuevas fotos semanales y audita el flujo operativo de Decodo."],
    map: ["Mapa", "Mapa de calor por ADR, pines de tarifa y ficha analítica por hotel."],
    explorer: ["Explorador", "Tabla completa con filtros instantáneos, gaps y exportación."],
    hotelData: ["Datos Hoteleros", "Inteligencia hotelera del mercado: KPIs, tabla competitiva y mapa de calor por ADR."],
    airData: ["Air_Data", "Inteligencia aérea para revenue hotelero, conectividad, precios, horarios y riesgo por mercado emisor."],
    revenue: ["Revenue Management", "Optimización de tarifas, curvas de demanda y oportunidades de pickup."],
  }[view] || ["Revenue Intelligence", "Panel operativo de análisis revenue."];
  $("#viewTitle").textContent = meta[0];
  const subtitle = document.querySelector(".page-subtitle");
  if (subtitle) subtitle.textContent = meta[1] || "";
  renderViewActions(view);
  if (view === "airData") {
    void ensureAirDataBoot().catch((error) => setStatus(readableError(error), "error"));
  }
  // Render the now-visible view a frame later so its layout is settled (matters for MapLibre sizing).
  window.requestAnimationFrame(() => {
    renderActiveView();
    if (view === "airData" && state.airData.activeTab === "map") renderAirMap();
  });
}

function renderViewActions(view) {
  const actions = $("#viewActions");
  if (!actions) return;
  if (view === "hotelData") {
    actions.classList.add("is-visible");
    actions.innerHTML = `
      <button class="filter-btn ${state.hotelData.activeTab === "table" ? "is-active" : ""}" data-hotel-tab="table">Tabla</button>
      <button class="filter-btn ${state.hotelData.activeTab === "map" ? "is-active" : ""}" data-hotel-tab="map">Mapa</button>
      <button id="hotelExportCsvHeader" class="button button--secondary" type="button">Exportar CSV</button>`;
    actions.querySelectorAll("[data-hotel-tab]").forEach((button) => {
      button.addEventListener("click", () => {
        state.hotelData.activeTab = button.dataset.hotelTab;
        renderViewActions("hotelData");
        renderHotelData();
      });
    });
    actions.querySelector("#hotelExportCsvHeader")?.addEventListener("click", exportCsv);
    return;
  }
  if (view !== "airData") {
    actions.innerHTML = "";
    actions.classList.remove("is-visible");
    return;
  }
  actions.classList.add("is-visible");
  actions.innerHTML = `
    <button class="filter-btn ${state.airData.activeTab === "overview" ? "is-active" : ""}" data-air-tab="overview">Overview</button>
    <button class="filter-btn ${state.airData.activeTab === "table" ? "is-active" : ""}" data-air-tab="table">Tabla</button>
    <button class="filter-btn ${state.airData.activeTab === "map" ? "is-active" : ""}" data-air-tab="map">Mapa inteligente</button>
    <button class="filter-btn ${state.airData.activeTab === "charts" ? "is-active" : ""}" data-air-tab="charts">Visualizaciones</button>
    <button class="filter-btn ${state.airData.activeTab === "detail" ? "is-active" : ""}" data-air-tab="detail">Detalle ruta</button>
    <button id="airExportCsvHeader" class="button button--secondary">Exportar CSV</button>
  `;
  actions.querySelectorAll("[data-air-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      state.airData.activeTab = button.dataset.airTab;
      renderAirData();
      if (state.airData.activeTab === "map") {
        window.requestAnimationFrame(() => renderAirMap());
      }
    });
  });
  actions.querySelector("#airExportCsvHeader")?.addEventListener("click", exportAirCsv);
}

function initPresets() {
  if (!Array.isArray(state.captureConfig.presetIds) || !state.captureConfig.presetIds.length) {
    state.captureConfig.presetIds = [presets[0].id];
  }
  state.captureConfig.presetId = state.captureConfig.presetIds[0];
}

function bindEvents() {
  $("#runScrapeTop")?.addEventListener("click", () => {
    void openCaptureModal();
  });
  $("#zoneSelect")?.addEventListener("change", async (event) => {
    const selectedIds = Array.from(event.target.selectedOptions || []).map((option) => option.value).filter(Boolean);
    if (!selectedIds.length) return;
    state.captureConfig.presetIds = selectedIds;
    state.captureConfig.presetId = selectedIds[0];
    syncAirAreasFromSelectedZones();
    saveAppSettings();
    try {
      await loadTargetsForSelection();
    } catch (error) {
      setStatus(readableError(error), "error");
    }
  });

  const debouncedExplorer = debounce(() => renderExplorer(), 150);
  $("#search").addEventListener("input", (event) => {
    state.query = event.target.value;
    debouncedExplorer();
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
  $("#backCaptureStep")?.addEventListener("click", () => setCaptureModalStep("hotels"));
  $("#nextCaptureStep")?.addEventListener("click", () => {
    applyModalCaptureConfig();
    const validation = validateHotelCaptureInputs();
    if (!validation.ok) {
      setStatus(validation.message, "error");
      return;
    }
    syncAirAreasFromSelectedZones();
    renderCaptureAirControls();
    setCaptureModalStep("flights");
  });
  $("#confirmCaptureModal")?.addEventListener("click", async () => {
    applyModalCaptureConfig();
    const validation = validateCaptureInputs();
    if (!validation.ok) {
      setStatus(validation.message, "error");
      setCaptureModalStep(validation.step || "flights");
      return;
    }
    closeCaptureModal();
    await runWeeklyScrape(validation);
  });
  $$("[data-capture-step-target]").forEach((button) => {
    button.addEventListener("click", () => {
      const targetStep = button.dataset.captureStepTarget;
      if (targetStep === "hotels") {
        setCaptureModalStep("hotels");
        return;
      }
      applyModalCaptureConfig();
      const validation = validateHotelCaptureInputs();
      if (!validation.ok) {
        setStatus(validation.message, "error");
        return;
      }
      syncAirAreasFromSelectedZones();
      renderCaptureAirControls();
      setCaptureModalStep("flights");
    });
  });
  $("#captureModal")?.addEventListener("click", (event) => {
    if (event.target?.id === "captureModal") {
      /* no cerramos el modal de captura con click fuera — el usuario puede perder configuración */
    }
  });
  $("#modalZones")?.addEventListener("change", () => {
    applyModalCaptureConfig();
    syncAirAreasFromSelectedZones();
    renderCaptureAirControls();
    renderCaptureModalSummary();
  });
  $("#modalAirAreas")?.addEventListener("change", () => {
    state.captureConfig.airAreaIds = selectedValues("#modalAirAreas");
    reconcileAirRouteSelection();
    renderCaptureAirControls();
  });
  $("#modalAirCountries")?.addEventListener("change", () => {
    state.captureConfig.airCountryIds = selectedValues("#modalAirCountries");
    reconcileAirRouteSelection();
    renderCaptureAirControls();
  });
  $("#modalAirRoutes")?.addEventListener("change", () => {
    state.captureConfig.airRouteKeys = selectedValues("#modalAirRoutes");
    renderCaptureAirControls();
  });
  $("#modalAirDirect")?.addEventListener("change", (event) => {
    state.captureConfig.airDirect = event.target.value;
  });
  $$("[data-air-direct-value]").forEach((button) => {
    button.addEventListener("click", () => {
      state.captureConfig.airDirect = button.dataset.airDirectValue;
      renderCaptureAirControls();
    });
  });
  $$("[data-air-trip-type]").forEach((button) => {
    button.addEventListener("click", () => {
      state.captureConfig.airTripType = button.dataset.airTripType === "round_trip" ? "round_trip" : "one_way";
      if (state.captureConfig.airTripType === "round_trip" && !state.captureConfig.airReturnDate) {
        state.captureConfig.airReturnDate = addDays(state.captureConfig.checkIn, Number(state.captureConfig.nights || 6));
      }
      renderCaptureAirControls();
    });
  });
  $("#modalAirReturnDate")?.addEventListener("input", (event) => {
    state.captureConfig.airReturnDate = event.target.value;
    renderCaptureModalSummary();
  });
  ["modalCheckIn", "modalNights", "modalWeeks", "modalLimit"].forEach((id) => {
    $(`#${id}`)?.addEventListener("input", () => {
      state.captureConfig.checkIn = $("#modalCheckIn")?.value || state.captureConfig.checkIn;
      state.captureConfig.nights = Number($("#modalNights")?.value || state.captureConfig.nights);
      state.captureConfig.weeks = Number($("#modalWeeks")?.value || state.captureConfig.weeks);
      state.captureConfig.limit = Number($("#modalLimit")?.value || state.captureConfig.limit);
      if (state.captureConfig.airTripType === "round_trip") {
        state.captureConfig.airReturnDate = addDays(state.captureConfig.checkIn, Number(state.captureConfig.nights || 6));
      }
      renderCaptureModalSummary();
    });
  });
  $("#openSettingsTop")?.addEventListener("click", () => {
    openSettingsModal();
  });
  $("#dashboardHeatmapFullscreen")?.addEventListener("click", () => {
    toggleDashboardHeatmapFullscreen();
  });
  $("#airTableFullscreen")?.addEventListener("click", () => {
    toggleAirTableFullscreen();
  });
  $("#airMapFullscreen")?.addEventListener("click", () => {
    toggleAirMapFullscreen();
  });
  $("#hotelTableFullscreen")?.addEventListener("click", () => {
    toggleHotelTableFullscreen();
  });
  $("#hotelMapFullscreen")?.addEventListener("click", () => {
    toggleHotelMapFullscreen();
  });
  document.addEventListener("fullscreenchange", handleDashboardHeatmapFullscreenChange);
  document.addEventListener("fullscreenchange", handleAirTableFullscreenChange);
  document.addEventListener("fullscreenchange", handleAirMapFullscreenChange);
  document.addEventListener("fullscreenchange", handleHotelTableFullscreenChange);
  document.addEventListener("fullscreenchange", handleHotelMapFullscreenChange);
  window.addEventListener("resize", () => {
    if (isAirTableFullscreen()) renderAirTable();
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
      updateSortIndicators();
    });
  });
  updateSortIndicators();

  // Advanced filters inside Explorer
  $("#filterRating")?.addEventListener("change", () => {
    updateRatingQuickButtons();
    saveExplorerFilters();
    renderExplorer();
  });
  $("#filterMaxPrice")?.addEventListener("input", debounce(() => {
    saveExplorerFilters();
    renderExplorer();
  }, 150));

  // Command bar interactive terminal
  const cmdBar = $("#cmdBar");
  const cmdInput = $("#cmdInput");
  const commandDock = $("#commandDock");
  const dockCmdInput = $("#dockCmdInput");
  cmdBar?.addEventListener("click", () => {
    cmdInput?.focus();
  });
  cmdInput?.addEventListener("keyup", (event) => {
    if (event.key === "Enter") {
      executeCommand(cmdInput.value);
      cmdInput.value = "";
    }
  });
  commandDock?.addEventListener("click", (event) => {
    if (event.target === commandDock) closeCommandDock();
  });
  dockCmdInput?.addEventListener("keyup", (event) => {
    if (event.key === "Enter") {
      const value = dockCmdInput.value;
      dockCmdInput.value = "";
      executeCommand(value);
      renderDockSuggestions("");
      if (!state.ai.active) closeCommandDock();
    }
    if (event.key === "Escape") closeCommandDock();
  });
  dockCmdInput?.addEventListener("input", (event) => renderDockSuggestions(event.target.value));
  $("#dockSuggest")?.addEventListener("click", (event) => {
    const row = event.target.closest("[data-cmd]");
    if (!row) return;
    if (dockCmdInput) dockCmdInput.value = "";
    executeCommand(row.dataset.cmd);
    if (!state.ai.active) {
      renderDockSuggestions("");
      dockCmdInput?.focus();
    }
  });
  $("#aiChatForm")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const input = $("#aiChatInput");
    const value = input?.value || "";
    if (input) input.value = "";
    sendAiMessage(value);
  });
  $("#aiChatClose")?.addEventListener("click", () => exitAiMode());
  $("#aiChatInput")?.addEventListener("keydown", (event) => {
    if (event.key === "Escape") exitAiMode();
  });
  $("#dashboardTableExport")?.addEventListener("click", exportCsv);
  initTickerControls();

  // Map drawer close action
  $("#closeMapDrawer")?.addEventListener("click", () => {
    $("#mapDrawer")?.classList.remove("is-visible");
  });

  // Hamburger sidebar toggle (mobile)
  const sidebarToggle = $("#sidebarToggle");
  const sidebarOverlay = $("#sidebarOverlay");
  const shell = $(".shell");
  sidebarToggle?.addEventListener("click", () => {
    shell?.classList.toggle("sidebar-open");
    const isOpen = shell?.classList.contains("sidebar-open");
    sidebarToggle.setAttribute("aria-expanded", String(isOpen));
  });
  sidebarOverlay?.addEventListener("click", () => {
    shell?.classList.remove("sidebar-open");
    sidebarToggle?.setAttribute("aria-expanded", "false");
  });

  // Capture type toggle cards (modal)
  $$("[data-capture-type]").forEach((card) => {
    card.addEventListener("click", () => {
      const type = card.dataset.captureType;
      if (type === "hotels") {
        state.captureConfig.captureHotels = !state.captureConfig.captureHotels;
      } else if (type === "flights") {
        state.captureConfig.captureFlights = !state.captureConfig.captureFlights;
      }
      updateCaptureTypeCards();
    });
  });

  // Map view mode selector
  $$("[data-map-view]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.mapViewMode = button.dataset.mapView;
      $$("[data-map-view]").forEach((btn) => btn.classList.toggle("is-active", btn === button));
      if (state.mapViewMode !== "hotels") {
        await ensureAirDataBoot().catch(() => {});
      }
      renderMarketMapView();
    });
  });

  // Quick boolean filter toggle buttons
  $("#btnFilterRiu")?.addEventListener("click", (event) => {
    state.filterOnlyRiu = !state.filterOnlyRiu;
    event.target.classList.toggle("is-active", state.filterOnlyRiu);
    saveExplorerFilters();
    renderExplorer();
  });

  $("#btnFilterGaps")?.addEventListener("click", (event) => {
    state.filterCriticalGaps = !state.filterCriticalGaps;
    event.target.classList.toggle("is-active", state.filterCriticalGaps);
    saveExplorerFilters();
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

  const debouncedAirFilters = debounce(updateAirFilters, 150);
  ["airSearch", "airMarketFilter", "airOriginFilter", "airDestinationFilter", "airAirlineFilter", "airConnectionFilter", "airPriceFilter", "airSignalFilter", "airDateFrom", "airDateTo"].forEach((id) => {
    const el = $(`#${id}`);
    if (!el) return;
    el.addEventListener("input", debouncedAirFilters);
    el.addEventListener("change", updateAirFilters);
  });
  $("#airPrevPage")?.addEventListener("click", () => {
    state.airData.page = Math.max(1, state.airData.page - 1);
    renderAirTable();
  });
  $("#airNextPage")?.addEventListener("click", () => {
    state.airData.page += 1;
    renderAirTable();
  });
  $("#airMapColorMode")?.addEventListener("change", renderAirMap);

  // Global copy-to-clipboard for [data-copy] buttons
  document.addEventListener("click", (event) => {
    const btn = event.target?.closest("[data-copy]");
    if (!btn) return;
    const value = btn.dataset.copy;
    if (!value) return;
    navigator.clipboard?.writeText(value).then(() => {
      setStatus(`Copiado: ${value}`, "ok");
    }).catch(() => {
      setStatus("No se pudo copiar al portapapeles", "error");
    });
  });

  // Clear all explorer filters
  $("#clearFilters")?.addEventListener("click", () => {
    const searchEl = $("#search");
    const ratingEl = $("#filterRating");
    const maxPriceEl = $("#filterMaxPrice");
    if (searchEl) searchEl.value = "";
    if (ratingEl) ratingEl.value = "";
    if (maxPriceEl) maxPriceEl.value = "";
    state.filterOnlyRiu = false;
    state.filterCriticalGaps = false;
    $("#btnFilterRiu")?.classList.remove("is-active");
    $("#btnFilterGaps")?.classList.remove("is-active");
    updateRatingQuickButtons();
    saveExplorerFilters();
    renderExplorer();
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
    if (state.targets.length) {
      await loadTarget(state.targets[0].id);
      return;
    }
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
  setStatus("Cargando mercado…", "busy");
  const [latestData, metrics, photoHistory, heatmap] = await Promise.all([
    api(`/api/snapshots/latest?targetId=${targetId}`),
    api(`/api/dashboard/metrics?targetId=${targetId}`),
    api(`/api/photos/history?targetId=${targetId}&limit=40`),
    api(`/api/hotels/heatmap?targetId=${targetId}&photos=${Number(state.heatmap.photosUsed || 6)}`),
  ]);

  state.latest = latestData.latest;
  state.metrics = metrics;
  state.photos = Array.isArray(photoHistory.photos) ? photoHistory.photos : [];
  state.heatmap = heatmap || { photosUsed: state.heatmap.photosUsed || 6, points: [], scale: { minPricePerNight: 0, maxPricePerNight: 0 } };

  if (!state.photos.length) {
    state.activePhotoId = null;
    state.photoDetail = null;
    state.rows = [];
  } else {
    const selectedExists = state.activePhotoId && state.photos.some((photo) => photo.id === state.activePhotoId);
    state.activePhotoId = selectedExists ? state.activePhotoId : state.photos[0].id;
    await loadPhoto(state.activePhotoId, false);
  }

  renderAll();
  setStatus("Mercado actualizado", "ok");
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

async function runWeeklyScrape(prevalidated = null) {
  const validation = prevalidated || validateCaptureInputs();
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

  const { captureHotels, captureFlights } = state.captureConfig;
  try {
    if (captureHotels) {
      const presetsToRun = activePresets();
      addConsoleLog(`[HOTELES] Zonas seleccionadas: ${presetsToRun.map(p => p.name).join(", ")}`, "info");
      addConsoleLog(`Parámetros: ${validation.weeks} semanas · ${validation.nights} noches · Límite ${validation.limit} hoteles/foto`, "info");

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

          addConsoleLog(`[DECODO API] Captura completada. Disponibles: ${result.snapshot.availableResults} · Guardados: ${result.snapshot.capturedRows} hoteles`, "success");
          addConsoleLog(`[SQLITE] Snapshot ID #${result.snapshot.id} guardado.`, "success");

          targetId = result.target.id;
          state.activeTargetId = targetId;
          state.activePhotoId = result.snapshot.id;
        }
      }
    } else {
      addConsoleLog("[HOTELES] Captura hotelera desactivada — omitiendo Booking/Decodo.", "warning");
    }

    if (captureFlights) {
      addConsoleLog(`[VUELOS] Iniciando captura Air_Data SerpApi · Directo: ${validation.airDirect ? "Si" : "No"}`, "sys");
      const returnOffsetDays = validation.airTripType === "round_trip" ? dayDiff(validation.checkIn, validation.airReturnDate) : null;
      for (let index = 0; index < validation.weeks; index += 1) {
        const outboundDate = addWeeks(validation.checkIn, index);
        const returnDate = validation.airTripType === "round_trip" ? addDays(outboundDate, returnOffsetDays) : null;
        setStatus(`Air_Data semana ${index + 1}/${validation.weeks}: salida ${outboundDate}`, "busy");
        const airResult = await api("/api/air-data/capture", {
          method: "POST",
          body: JSON.stringify({
            areaIds: state.captureConfig.airAreaIds,
            countryIds: state.captureConfig.airCountryIds,
            routeKeys: state.captureConfig.airRouteKeys,
            direct: validation.airDirect,
            tripType: validation.airTripType,
            outboundDate,
            returnDate,
            nights: validation.nights,
          }),
        });
        addConsoleLog(`[SERPAPI] Run #${airResult.run.id}: ${airResult.run.capturedRoutes}/${airResult.run.requestedRoutes} rutas · ${airResult.run.capturedFlights} vuelos guardados`, "success");
      }
    } else {
      addConsoleLog("[VUELOS] Captura aérea desactivada — omitiendo SerpApi/Google Flights.", "warning");
    }

    addConsoleLog("Actualizando listados de mercados y bases históricas...", "info");
    await loadAirData();
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
  // Always-on chrome (sidebar, ticker, zone selector).
  renderPreset();
  renderTicker();
  renderTargets();
  // Heavy per-view renders only run for the visible view (the rest render on view switch).
  renderActiveView();

  // Update portfolio status label in bottom status bar
  const activeZoneText = document.getElementById("activeZoneText");
  if (activeZoneText) {
    const selected = activePresets();
    activeZoneText.textContent = selected.map(preset => preset.name).join(", ");
  }
}

function isViewVisible(id) {
  return Boolean(document.getElementById(id)?.classList.contains("is-visible"));
}

// Render only the currently visible view — avoids rebuilding (and re-creating MapLibre maps for)
// the 7 hidden views on every state change. showView() calls this when switching views.
function renderActiveView() {
  if (isViewVisible("dashboard")) renderDashboard();
  if (isViewVisible("workspace")) renderWorkspace();
  if (isViewVisible("scraping")) { renderScrapingSummary(); renderPhotoTable(); }
  if (isViewVisible("map")) renderMap();
  if (isViewVisible("explorer")) renderExplorer();
  if (isViewVisible("riu")) renderRiuAnalysis();
  if (isViewVisible("airData")) renderAirData();
  if (isViewVisible("hotelData")) renderHotelData();
  if (isViewVisible("revenue")) renderRevenuePanel();
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
      tooltip: "ADR hab/noche — Average Daily Rate por habitación. Media del set competitivo en la última captura.",
    },
    {
      label: "Precio pers / noche",
      value: currency(summary?.avgPricePerPersonNight),
      trend: pct(movement?.avgPricePerPersonNightChangePct),
      tone: trendTone(movement?.avgPricePerPersonNightChangePct),
      meta: `Pax normalizado · ${summary?.comparableRows || 0} comparables`,
      tooltip: "Precio por persona y noche — normaliza la tarifa por ocupación para comparar habitaciones dobles vs individuales.",
    },
    {
      label: "Rango ADR",
      value: `${currency(summary?.minPricePerNight)} - ${currency(summary?.maxPricePerNight)}`,
      trend: spreadLabel(summary),
      tone: "neutral",
      meta: `Mediana ${currency(median)} · dispersión competitiva`,
      tooltip: "Rango de precios por noche del set competitivo: mínimo y máximo detectados en esta captura.",
    },
    {
      label: "Comparabilidad",
      value: `${summary?.comparableRows || 0}/${summary?.rows || 0}`,
      trend: `${comparabilityPct(summary)}% comparable`,
      tone: comparabilityPct(summary) >= 85 ? "up" : "down",
      meta: `${state.metrics?.dataQuality?.missingPriceRows || 0} filas sin precio · QA operativo`,
      tooltip: "Filas con precio + noches válidas sobre el total. Cuanto más alto, más fiable el análisis de ADR.",
    },
    demandPressureCard(),
  ];

  $("#kpis").innerHTML = cards.map((card, i) => renderMetric(card, i)).join("");

  renderPriceTiers($("#dashboardPriceTiers"), state.metrics?.priceTierDistribution || []);
  renderRatingPrice($("#dashboardRatingPrice"), state.metrics?.ratingPriceCorrelation || []);

  const dashboardMapRows = state.rows.filter(hasValidCanaryCoordinates);
  const dashboardHeatmap = buildHeatmapFromRows(dashboardMapRows);
  renderDashboardRelevantRows();
  renderHeatmapElement($("#dashboardHeatmap"), {
    compact: true,
    points: dashboardHeatmap.points,
    overlayRows: dashboardMapRows,
  });
  renderTrendElement($("#trendChart"), [...state.photos].reverse(), "avgPricePerNight");
  renderInsightsElement($("#insights"), mixedInsights());
}

// Decision-driving KPI built from demandIndicators (replaces the QA "coverage" card).
function demandPressureCard() {
  const di = state.metrics?.demandIndicators || {};
  const labels = { alta: "Alta", baja: "Baja", neutral: "Neutral" };
  const tone = di.bookingPressure === "alta" ? "up" : di.bookingPressure === "baja" ? "down" : "neutral";
  const cov = state.metrics?.locationCoverage?.pct ?? 0;
  return {
    label: "Presión de demanda",
    value: labels[di.bookingPressure] || "Neutral",
    trend: `${di.competitorIncreases || 0}↑ / ${di.competitorDrops || 0}↓ competidores`,
    tone,
    meta: `Mercado ${di.priceDirection || "estable"} · cobertura geo ${cov}%`,
    tooltip: "Señal de demanda del set: combina la dirección de precios y cuántos competidores suben o bajan tarifa entre capturas.",
  };
}

// Price-tier quartile bars (data computed in dashboard_metrics but previously unrendered).
function renderPriceTiers(container, tiers) {
  if (!container) return;
  if (!tiers.length) {
    container.innerHTML = empty("Sin distribución de tiers para esta captura.");
    return;
  }
  const max = Math.max(...tiers.map((t) => t.count), 1);
  container.innerHTML = tiers
    .map((t) => {
      const h = Math.round((t.count / max) * 100);
      return `<div class="tier-bar">
        <div class="tier-bar__track"><div class="tier-bar__fill tier-bar__fill--${escapeHtml(t.tier)}" style="height:${h}%"><span>${t.count}</span></div></div>
        <strong>${escapeHtml(t.label)}</strong>
        <small>${currency(t.avgAdr)} · ${number(t.pct, 0)}%</small>
      </div>`;
    })
    .join("");
}

// Rating→ADR correlation table (data computed in dashboard_metrics but previously unrendered).
function renderRatingPrice(tbody, rows) {
  if (!tbody) return;
  tbody.innerHTML = rows.length
    ? rows
        .map(
          (r) => `<tr>
          <td><strong>${escapeHtml(r.ratingBucket)}</strong></td>
          <td>${number(r.hotelCount, 0)}</td>
          <td>${currency(r.avgAdr)}</td>
          <td>${currency(r.minAdr)} - ${currency(r.maxAdr)}</td>
        </tr>`
        )
        .join("")
    : `<tr><td colspan="4">${empty("Sin correlación rating/precio disponible.")}</td></tr>`;
}

function renderDashboardRelevantRows() {
  const tbody = $("#dashboardRelevantRows");
  if (!tbody) return;
  const rows = [...state.rows]
    .map((row) => {
      const ppn = row.pricePerNight ?? (row.price && row.nights ? row.price / row.nights : null);
      return { ...row, effectivePrice: ppn, gap: gapFor(row.hotelKey) };
    })
    .filter((row) => Number.isFinite(row.effectivePrice))
    .sort((a, b) => Math.abs(b.gap ?? 0) - Math.abs(a.gap ?? 0))
    .slice(0, 12);

  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="9">${empty("No hay datos comparables para la foto activa.")}</td></tr>`;
    return;
  }

  tbody.innerHTML = rows
    .map((row, index) => {
      const isRiu = isRiuHotel(row.hotelName);
      const status = row.locationStatus === "ready" ? "OK" : "Geo pendiente";
      return `<tr class="clickable-row" data-hotel-key="${escapeHtml(row.hotelKey)}" title="Ver en mapa" role="button" tabindex="0" aria-label="Ver ${escapeHtml(row.hotelName)} en el mapa">
        <td>${index + 1}</td>
        <td><strong>${isRiu ? '<span class="riu-tag">RIU</span>' : ""}${escapeHtml(row.hotelName)}</strong></td>
        <td>${currency(row.effectivePrice)}</td>
        <td>${currency(row.pricePerPersonPerNight)}</td>
        <td><span class="${badgeClass(row.gap)}">${pct(row.gap)}</span></td>
        <td>${currency(row.price)}</td>
        <td>${row.rating ?? "-"}</td>
        <td>${row.nights ?? "-"}</td>
        <td>${escapeHtml(status)}</td>
      </tr>`;
    })
    .join("");

  tbody.querySelectorAll("tr[data-hotel-key]").forEach((tr) => {
    const open = () => {
      const key = tr.dataset.hotelKey;
      if (key) {
        showView("map");
        openMapDrawerForHotelByKey(key);
      }
    };
    tr.addEventListener("click", open);
    tr.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        open();
      }
    });
  });
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
        `<span class="ticker-item"><strong>${index + 1}. ${escapeHtml(row.hotelName)}</strong> ${currency(row.pricePerNight)} <span class="${row.gapVsMarketPct >= 0 ? "up" : "down"}">${pct(row.gapVsMarketPct)}</span></span>`
    )
    .join("");
  track.innerHTML = `<span class="ticker-seq">${items}</span><span class="ticker-seq" aria-hidden="true">${items}</span>`;
}

function initTickerControls() {
  const ticker = $("#marketTicker");
  const track = $("#tickerTrack");
  if (!ticker || !track) return;
  ticker.addEventListener("mouseenter", () => {
    ticker.classList.add("is-interacting");
  });
  ticker.addEventListener("mouseleave", () => {
    ticker.classList.remove("is-interacting");
    track.style.animationDuration = "";
    track.style.animationPlayState = "";
  });
  ticker.addEventListener("mousemove", (event) => {
    const rect = ticker.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width;
    const distanceFromCenter = Math.abs(x - 0.5) * 2;
    if (distanceFromCenter < 0.16) {
      track.style.animationPlayState = "paused";
      return;
    }
    track.style.animationPlayState = "running";
    const duration = 42 - distanceFromCenter * 30;
    track.style.animationDuration = `${Math.max(10, duration)}s`;
  });
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
  renderMarketMapView();
}

function renderMarketMapView() {
  const container = $("#marketMap");
  if (!container) return;

  const mode = state.mapViewMode || "hotels";
  const rowsWithAnyCoords = state.rows.filter(hasNumericCoordinates);
  const rowsWithCoords = rowsWithAnyCoords.filter(hasValidCanaryCoordinates);
  const pending = state.rows.length - rowsWithAnyCoords.length;
  const discarded = rowsWithAnyCoords.length - rowsWithCoords.length;

  const titles = {
    hotels: "Mapa de mercado",
    flights: "Conectividad aérea",
    both: "Mercado integrado",
  };
  const subtitles = {
    hotels: "Mapa de calor por ADR + pines de tarifa por hotel.",
    flights: "Rutas activas con señal revenue y opciones disponibles.",
    both: "Heatmap ADR hotelero + rutas aéreas combinadas en un solo mapa.",
  };

  const titleEl = $("#mapPanelTitle");
  const subtitleEl = $("#mapPanelSubtitle");
  if (titleEl) titleEl.textContent = titles[mode] || titles.hotels;
  if (subtitleEl) subtitleEl.textContent = subtitles[mode] || subtitles.hotels;

  const mapPendingEl = $("#mapPending");
  if (mapPendingEl) {
    mapPendingEl.textContent = discarded
      ? `${pending} pendientes · ${discarded} fuera de mapa`
      : `${pending} pendientes`;
  }

  const legendEl = document.querySelector(".map-panel-legend");
  if (legendEl) {
    if (mode === "flights") {
      legendEl.innerHTML = `<span class="dot" style="background:var(--bb-green)"></span>Oportunidad <span class="dot" style="background:var(--bb-amber)"></span>Mercado estable <span class="dot dot--high"></span>Riesgo demanda`;
    } else if (mode === "both") {
      legendEl.innerHTML = `<span class="dot dot--low"></span>ADR bajo <span class="dot"></span>ADR medio <span class="dot dot--high"></span>ADR alto &nbsp;·&nbsp; <span style="display:inline-block;width:18px;height:3px;background:var(--bb-cyan);vertical-align:middle;border-radius:2px;margin-right:4px"></span>Rutas aéreas`;
    } else {
      const scale = state.heatmap?.scale;
      if (scale?.minPricePerNight && scale?.maxPricePerNight) {
        const lo = Math.round(scale.minPricePerNight);
        const hi = Math.round(scale.maxPricePerNight);
        const mid = Math.round((lo + hi) / 2);
        const threshold = Math.round(lo + (hi - lo) * 0.67);
        legendEl.innerHTML = `<span class="dot dot--low"></span>Bajo (&le;${lo}&nbsp;&euro;) <span class="dot"></span>Medio (~${mid}&nbsp;&euro;) <span class="dot dot--high"></span>Alto (&ge;${threshold}&nbsp;&euro;)`;
      } else {
        legendEl.innerHTML = `<span class="dot dot--low"></span>ADR bajo <span class="dot"></span>ADR medio <span class="dot dot--high"></span>ADR alto`;
      }
    }
  }

  destroyMapInstance(container);

  if (mode === "hotels") {
    renderHeatmapElement(container, { compact: false, overlayRows: rowsWithCoords });
  } else if (mode === "flights") {
    renderAirRoutesInContainer(container);
  } else {
    renderHeatmapElement(container, { compact: false, overlayRows: rowsWithCoords });
    window.requestAnimationFrame(() => overlayAirRoutesOnMap(container));
  }
}

function renderAirRoutesInContainer(container) {
  if (!container) return;
  const routes = state.airData.routes || [];
  if (!window.maplibregl || !routes.length) {
    container.innerHTML = empty("Sin rutas aéreas disponibles. Captura datos vuelos primero o cambia a modo Hoteles.");
    return;
  }
  const geojson = buildAirRouteGeoJsonForContainer(routes);
  if (!geojson.features.length) {
    container.innerHTML = empty("Sin coordenadas de aeropuertos disponibles.");
    return;
  }
  const host = ensureMapContainer(container);
  const map = ensureMapInstance(host);
  updateAirRouteMapData(map, host.id, geojson);
}

function overlayAirRoutesOnMap(container) {
  if (!container) return;
  const host = container.firstElementChild;
  if (!host?.id) return;
  const map = mapRegistry.get(host.id);
  if (!map) return;
  const routes = state.airData.routes || [];
  if (!routes.length) return;
  const geojson = buildAirRouteGeoJsonForContainer(routes);
  if (!geojson.features.length) return;
  const sourceId = `${sourceIdFor(host.id)}-air-overlay`;
  const pointSourceId = `${sourceIdFor(host.id)}-airports-overlay`;
  const add = () => {
    if (!map.getSource(sourceId)) map.addSource(sourceId, { type: "geojson", data: geojson });
    if (!map.getLayer(`${sourceId}-line`)) {
      map.addLayer({ id: `${sourceId}-line`, type: "line", source: sourceId, paint: { "line-color": ["get", "route_color"], "line-width": 2.5, "line-opacity": 0.72 } });
      map.on("click", `${sourceId}-line`, (event) => {
        const route = routes.find((r) => r.route_key === event.features?.[0]?.properties?.route_key);
        if (!route) return;
        const flights = state.airData.flights.filter((f) => f.route_key === route.route_key);
        const stats = airRoutePriceStats(route, flights);
        new window.maplibregl.Popup({ closeButton: true, maxWidth: "360px", offset: 18 })
          .setLngLat(event.lngLat)
          .setHTML(renderAirRouteMapPopup(route, flights, stats))
          .addTo(map);
      });
    }
    if (!map.getSource(pointSourceId)) map.addSource(pointSourceId, { type: "geojson", data: buildAirAirportGeoJson(geojson) });
    if (!map.getLayer(`${pointSourceId}-circle`)) {
      map.addLayer({ id: `${pointSourceId}-circle`, type: "circle", source: pointSourceId, paint: { "circle-radius": 5, "circle-color": "#64d2ff", "circle-stroke-color": "#fff", "circle-stroke-width": 1.5 } });
    }
    map.getSource(sourceId)?.setData(geojson);
    map.getSource(pointSourceId)?.setData(buildAirAirportGeoJson(geojson));
  };
  if (map.isStyleLoaded()) add();
  else map.once("load", add);
}

function buildAirRouteGeoJsonForContainer(routes) {
  return {
    type: "FeatureCollection",
    features: routes.map((route) => {
      const origin = state.airData.airports[route.origin];
      const destination = state.airData.airports[route.destination];
      if (!origin || !destination) return null;
      return {
        type: "Feature",
        properties: { ...route, route_color: airRouteColor(route, "revenue_signal") },
        geometry: { type: "LineString", coordinates: [[origin.lng, origin.lat], [destination.lng, destination.lat]] },
      };
    }).filter(Boolean),
  };
}

async function toggleDashboardHeatmapFullscreen() {
  const panel = $("#dashboardHeatmapPanel");
  if (!panel) return;
  try {
    if (document.fullscreenElement === panel) {
      await document.exitFullscreen();
    } else if (panel.requestFullscreen) {
      await panel.requestFullscreen();
    } else {
      panel.classList.toggle("is-pseudo-fullscreen");
      handleDashboardHeatmapFullscreenChange();
    }
  } catch (error) {
    panel.classList.toggle("is-pseudo-fullscreen");
    handleDashboardHeatmapFullscreenChange();
  }
}

function handleDashboardHeatmapFullscreenChange() {
  const panel = $("#dashboardHeatmapPanel");
  const button = $("#dashboardHeatmapFullscreen");
  if (!panel) return;
  const isFullscreen = document.fullscreenElement === panel || panel.classList.contains("is-pseudo-fullscreen");
  panel.classList.toggle("is-fullscreen", isFullscreen);
  if (button) {
    button.textContent = isFullscreen ? "Salir" : "Pantalla completa";
    button.setAttribute("aria-label", isFullscreen ? "Salir de pantalla completa" : "Ver mapa en pantalla completa");
  }
  window.requestAnimationFrame(() => {
    const dashboardMapRows = state.rows.filter(hasValidCanaryCoordinates);
    const dashboardHeatmap = buildHeatmapFromRows(dashboardMapRows);
    destroyMapInstance($("#dashboardHeatmap"));
    renderHeatmapElement($("#dashboardHeatmap"), {
      compact: true,
      points: dashboardHeatmap.points,
      overlayRows: dashboardMapRows,
      fit: false,
    });
  });
}

async function toggleAirTableFullscreen() {
  const panel = $("#airFlightTablePanel");
  if (!panel) return;
  try {
    if (document.fullscreenElement === panel) {
      await document.exitFullscreen();
    } else if (panel.requestFullscreen) {
      await panel.requestFullscreen();
    } else {
      panel.classList.toggle("is-pseudo-fullscreen");
      handleAirTableFullscreenChange();
    }
  } catch (error) {
    panel.classList.toggle("is-pseudo-fullscreen");
    handleAirTableFullscreenChange();
  }
}

function handleAirTableFullscreenChange() {
  const panel = $("#airFlightTablePanel");
  const button = $("#airTableFullscreen");
  if (!panel) return;
  const isFullscreen = document.fullscreenElement === panel || panel.classList.contains("is-pseudo-fullscreen");
  panel.classList.toggle("is-fullscreen", isFullscreen);
  if (button) {
    button.textContent = isFullscreen ? "Salir" : "Pantalla completa";
    button.setAttribute("aria-label", isFullscreen ? "Salir de pantalla completa" : "Ver tabla de vuelos en pantalla completa");
  }
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(renderAirTable);
  });
  window.setTimeout(renderAirTable, 160);
}

async function loadAirCatalog() {
  try {
    const catalog = await api("/api/air-data/catalog");
    state.airCatalog = normalizeAirCatalog(catalog);
  } catch (error) {
    state.airCatalog = normalizeAirCatalog(fallbackAirCatalog);
    setStatus("Catalogo Air_Data local activo. Reinicia Flask para cargar la ruta nueva del backend.", "error");
  }
  syncAirAreasFromSelectedZones();
}

function normalizeAirCatalog(catalog) {
  if (!catalog || typeof catalog !== "object") return { areas: [], countries: [], routes: [] };
  return {
    areas: Array.isArray(catalog.areas) ? catalog.areas : [],
    countries: Array.isArray(catalog.countries) ? catalog.countries : [],
    routes: Array.isArray(catalog.routes)
      ? catalog.routes.map((route) => ({
          areaId: route.areaId || route.area_id || "",
          areaName: route.areaName || route.area_name || "",
          country: route.country || route.country_id || route.country_name || "",
          market: route.market || "",
          origin: route.origin || "",
          destination: route.destination || "",
          routeKey: route.routeKey || route.route_key || route.key || "",
          label: route.label || `${route.origin || ""} -> ${route.destination || ""}`,
        }))
      : [],
  };
}

function ensureAirCatalog() {
  if (state.airCatalog.areas.length) return;
  state.airCatalog = {
    areas: fallbackAirCatalog.areas.slice(),
    countries: fallbackAirCatalog.countries.slice(),
    routes: fallbackAirCatalog.routes.slice(),
  };
}

async function loadAirData() {
  const payload = await api("/api/air-data");
  state.airData.flights = Array.isArray(payload.flights) ? payload.flights : [];
  state.airData.routes = Array.isArray(payload.routes) ? payload.routes : [];
  state.airData.summary = payload.summary || null;
  state.airData.source = payload.source || "mock";
  state.airData.isLive = Boolean(payload.is_live);
  state.airData.warning = payload.warning || "";
  state.airData.airports = payload.airports || {};
  state.airData.geojson = payload.geojson || null;
  state.airData.selectedRouteKey = state.airData.routes[0]?.route_key || null;
  if (state.airData.selectedRouteKey) {
    void loadAirRouteHistory(state.airData.selectedRouteKey).then(() => {
      if ($("#airData")?.classList.contains("is-visible")) renderAirDetail();
    });
  }
}

async function loadAirRouteHistory(routeKey) {
  if (!routeKey) return;
  const directValue = state.captureConfig.airDirect === "true" ? "true" : state.captureConfig.airDirect === "false" ? "false" : "";
  const query = new URLSearchParams({ routeKey, limit: "24" });
  if (directValue) query.set("direct", directValue);
  const payload = await api(`/api/air-data/history?${query.toString()}`);
  state.airData.routeHistory[routeKey] = Array.isArray(payload.history) ? payload.history : [];
}

// ---------------------------------------------------------------------------
// Datos Hoteleros — hotel intelligence terminal (KPIs + table + map)
// ---------------------------------------------------------------------------
function renderHotelData() {
  if (!$("#hotelData")?.classList.contains("is-visible")) return;
  renderHotelKpis();
  renderHotelFilters();
  const tab = state.hotelData.activeTab;
  $("#hotelTableView")?.classList.toggle("is-visible", tab === "table");
  $("#hotelMapView")?.classList.toggle("is-visible", tab === "map");
  if (tab === "map") {
    window.requestAnimationFrame(() => renderHotelMap());
  } else {
    renderHotelTable();
  }
}

function filteredHotelRows() {
  const f = state.hotelData.filters;
  const query = (f.query || "").trim().toLowerCase();
  return (state.rows || []).filter((row) => {
    if (query && !`${row.hotelName || ""} ${row.roomType || ""}`.toLowerCase().includes(query)) return false;
    if (f.board && row.board !== f.board) return false;
    if (f.rating && (row.rating == null || row.rating < Number(f.rating))) return false;
    if (f.riu === "1" && !isRiuHotel(row.hotelName)) return false;
    if (f.cancel === "1" && row.freeCancellation !== true) return false;
    return true;
  });
}

function hotelMarketMedian() {
  return state.metrics?.market?.medianPricePerNight || state.photoDetail?.summary?.medianPricePerNight || null;
}

function renderHotelKpis() {
  const host = $("#hotelKpis");
  if (!host) return;
  const rows = state.rows || [];
  const summary = state.photoDetail?.summary || {};
  const market = state.metrics?.market || {};
  const aiCount = rows.filter((row) => row.board === "Todo incluido").length;
  const withBoard = rows.filter((row) => row.board).length;
  const avgRating = averageValue(rows.map((row) => row.rating).filter((value) => value != null));
  const totalReviews = rows.reduce((sum, row) => sum + (row.reviewCount || 0), 0);
  const freeCancel = rows.filter((row) => row.freeCancellation === true).length;
  const pctOf = (n) => (rows.length ? `${Math.round((n / rows.length) * 100)}%` : "—");
  const cards = [
    { label: "Hoteles en mercado", value: String(rows.length), meta: `${withBoard} con régimen detectado`, tone: "neutral", tooltip: "Hoteles del set competitivo en la captura activa." },
    { label: "ADR hab / noche", value: currency(summary.avgPricePerNight), meta: `Mediana ${currency(market.medianPricePerNight)}`, tone: "neutral", tooltip: "Tarifa media por habitación y noche del set." },
    { label: "ADR pers / noche", value: currency(summary.avgPricePerPersonNight), meta: "Pax normalizado", tone: "neutral", tooltip: "Tarifa por persona y noche (normaliza ocupación)." },
    { label: "% Todo incluido", value: pctOf(aiCount), meta: `${aiCount}/${rows.length} hoteles`, tone: "neutral", tooltip: "Proporción del set en régimen Todo incluido." },
    { label: "Rating medio", value: avgRating ? number(avgRating, 1) : "—", meta: `${number(totalReviews, 0)} reseñas totales`, tone: "neutral", tooltip: "Nota media de reseñas + total de reseñas del set." },
    { label: "Cancelación gratis", value: pctOf(freeCancel), meta: `${freeCancel}/${rows.length} la ofrecen`, tone: "neutral", tooltip: "Hoteles con tarifa de cancelación gratuita detectada." },
  ];
  host.innerHTML = cards.map((card, index) => renderMetric(card, index)).join("");
}

function renderHotelFilters() {
  const boardSelect = $("#hotelBoardFilter");
  if (boardSelect) {
    const boards = Array.from(new Set((state.rows || []).map((row) => row.board).filter(Boolean))).sort();
    const current = state.hotelData.filters.board;
    boardSelect.innerHTML = `<option value="">Régimen: Todos</option>` + boards.map((board) => `<option value="${escapeHtml(board)}" ${board === current ? "selected" : ""}>${escapeHtml(board)}</option>`).join("");
  }
  const reflect = (selector, value) => { const el = $(selector); if (el && el.value !== value) el.value = value; };
  reflect("#hotelSearch", state.hotelData.filters.query);
  reflect("#hotelRatingFilter", state.hotelData.filters.rating);
  reflect("#hotelRiuFilter", state.hotelData.filters.riu);
  reflect("#hotelCancelFilter", state.hotelData.filters.cancel);
}

function renderHotelTable() {
  const tbody = $("#hotelDataRows");
  if (!tbody) return;
  const rows = filteredHotelRows();
  const median = hotelMarketMedian();
  const countEl = $("#hotelTableCount");
  if (countEl) countEl.textContent = `Hoteles: ${rows.length} / ${(state.rows || []).length}`;
  tbody.innerHTML = rows.length
    ? rows.map((row, index) => {
        const isRiu = isRiuHotel(row.hotelName);
        const gap = (row.pricePerNight != null && median) ? ((row.pricePerNight - median) / median) * 100 : null;
        return `<tr>
          <td>${index + 1}</td>
          <td><strong>${isRiu ? '<span class="riu-tag">RIU</span>' : ""}${escapeHtml(row.hotelName)}</strong></td>
          <td>${currency(row.pricePerNight)}</td>
          <td>${currency(row.pricePerPersonPerNight)}</td>
          <td>${row.board ? `<span class="badge ${row.board === "Todo incluido" ? "low" : ""}">${escapeHtml(row.board)}</span>` : "—"}</td>
          <td>${row.rating ?? "-"}</td>
          <td>${row.reviewCount != null ? number(row.reviewCount, 0) : "-"}</td>
          <td>${row.freeCancellation === true ? '<span class="badge low">Sí</span>' : "—"}</td>
          <td>${gap == null ? "—" : `<span class="${badgeClass(gap)}">${pct(gap)}</span>`}</td>
          <td>${row.nights ?? "-"}</td>
        </tr>`;
      }).join("")
    : `<tr><td colspan="10">${empty("Sin hoteles para los filtros seleccionados.")}</td></tr>`;
}

function renderHotelMap() {
  if (!$("#hotelDataMap")) return;
  renderHotelMapControls();
  applyHotelMapData();
}

// Re-render only the map layers (heatmap + pins) for the current filters, without rebuilding
// the floating controls — so typing in the overlay search doesn't lose focus.
function applyHotelMapData() {
  const container = $("#hotelDataMap");
  if (!container) return;
  const rows = filteredHotelRows().filter(hasValidCanaryCoordinates);
  const legend = $("#hotelMapLegend");
  if (!rows.length) {
    destroyMapInstance(container);
    container.innerHTML = empty("Sin hoteles geolocalizados para los filtros seleccionados.");
    if (legend) legend.innerHTML = "";
    return;
  }
  const heat = buildHeatmapFromRows(rows);
  renderHeatmapElement(container, { compact: false, points: heat.points, overlayRows: rows });
  if (legend) {
    legend.innerHTML =
      `<span><i class="map-legend-dot" style="background:var(--bb-green)"></i>ADR bajo</span>` +
      `<span><i class="map-legend-dot" style="background:var(--bb-amber)"></i>ADR medio</span>` +
      `<span><i class="map-legend-dot" style="background:var(--bb-red)"></i>ADR alto</span>`;
  }
}

// Floating filter overlay shown over the hotel map in fullscreen (the main filter bar is hidden there).
function renderHotelMapControls() {
  const host = $("#hotelMapControls");
  if (!host) return;
  const f = state.hotelData.filters;
  const boards = Array.from(new Set((state.rows || []).map((row) => row.board).filter(Boolean))).sort();
  const opt = (value, label, selected) => `<option value="${escapeHtml(value)}" ${value === selected ? "selected" : ""}>${escapeHtml(label)}</option>`;
  const field = (label, id, optionsHtml) => `<label class="map-controls__field"><span>${escapeHtml(label)}</span><select data-hotel-map-filter="${id}">${optionsHtml}</select></label>`;
  host.innerHTML = `
    <strong class="map-controls__title">Filtros del mapa</strong>
    <label class="map-controls__field"><span>Buscar</span><input data-hotel-map-filter="query" type="search" value="${escapeHtml(f.query || "")}" placeholder="Hotel..." /></label>
    ${field("Régimen", "board", opt("", "Todos", f.board) + boards.map((board) => opt(board, board, f.board)).join(""))}
    ${field("Rating mín.", "rating", [["", "Todos"], ["9", "9+"], ["8", "8+"], ["7", "7+"]].map(([value, label]) => opt(value, label, f.rating)).join(""))}
    ${field("Solo RIU", "riu", [["", "No"], ["1", "Sí"]].map(([value, label]) => opt(value, label, f.riu)).join(""))}
    ${field("Cancelación", "cancel", [["", "Todas"], ["1", "Gratis"]].map(([value, label]) => opt(value, label, f.cancel)).join(""))}`;
  const debouncedSearch = debounce(() => applyHotelMapData(), 150);
  host.querySelectorAll("[data-hotel-map-filter]").forEach((element) => {
    const key = element.dataset.hotelMapFilter;
    if (element.tagName === "INPUT") {
      element.addEventListener("input", (event) => { state.hotelData.filters[key] = event.target.value; debouncedSearch(); });
    } else {
      element.addEventListener("change", (event) => { state.hotelData.filters[key] = event.target.value; applyHotelMapData(); });
    }
  });
}

async function toggleHotelMapFullscreen() {
  const panel = $("#hotelMapPanel");
  if (!panel) return;
  try {
    if (document.fullscreenElement === panel) await document.exitFullscreen();
    else if (panel.requestFullscreen) await panel.requestFullscreen();
    else { panel.classList.toggle("is-pseudo-fullscreen"); handleHotelMapFullscreenChange(); }
  } catch (error) {
    panel.classList.toggle("is-pseudo-fullscreen");
    handleHotelMapFullscreenChange();
  }
}

function handleHotelMapFullscreenChange() {
  const panel = $("#hotelMapPanel");
  const button = $("#hotelMapFullscreen");
  if (!panel) return;
  const isFullscreen = document.fullscreenElement === panel || panel.classList.contains("is-pseudo-fullscreen");
  panel.classList.toggle("is-fullscreen", isFullscreen);
  if (button) {
    button.textContent = isFullscreen ? "Salir" : "Pantalla completa";
    button.setAttribute("aria-label", isFullscreen ? "Salir de pantalla completa" : "Ver mapa en pantalla completa");
  }
  window.requestAnimationFrame(() => renderHotelMap());
}

async function toggleHotelTableFullscreen() {
  const panel = $("#hotelTablePanel");
  if (!panel) return;
  try {
    if (document.fullscreenElement === panel) await document.exitFullscreen();
    else if (panel.requestFullscreen) await panel.requestFullscreen();
    else { panel.classList.toggle("is-pseudo-fullscreen"); handleHotelTableFullscreenChange(); }
  } catch (error) {
    panel.classList.toggle("is-pseudo-fullscreen");
    handleHotelTableFullscreenChange();
  }
}

function handleHotelTableFullscreenChange() {
  const panel = $("#hotelTablePanel");
  const button = $("#hotelTableFullscreen");
  if (!panel) return;
  const isFullscreen = document.fullscreenElement === panel || panel.classList.contains("is-pseudo-fullscreen");
  panel.classList.toggle("is-fullscreen", isFullscreen);
  if (button) {
    button.textContent = isFullscreen ? "Salir" : "Pantalla completa";
    button.setAttribute("aria-label", isFullscreen ? "Salir de pantalla completa" : "Ver tabla en pantalla completa");
  }
}

function initHotelControls() {
  const bindSelect = (selector, key) => {
    $(selector)?.addEventListener("change", (event) => {
      state.hotelData.filters[key] = event.target.value;
      renderHotelData();
    });
  };
  $("#hotelSearch")?.addEventListener("input", debounce((event) => {
    state.hotelData.filters.query = event.target.value;
    renderHotelTable();
  }, 150));
  bindSelect("#hotelBoardFilter", "board");
  bindSelect("#hotelRatingFilter", "rating");
  bindSelect("#hotelRiuFilter", "riu");
  bindSelect("#hotelCancelFilter", "cancel");
  $("#hotelTableExport")?.addEventListener("click", exportCsv);
}

function renderAirData() {
  if (!$("#airData")) return;
  renderAirSourceBanner();
  renderAirTabs();
  renderAirFilters();
  renderAirKpis();
  renderAirOverview();
  renderAirTable();
  renderAirMap();
  renderAirCharts();
  renderAirDetail();
}

// Flag demo/mock air data so revenue decisions aren't taken on fictitious signals.
function renderAirSourceBanner() {
  const host = $("#airKpis");
  if (!host || !host.parentNode) return;
  let banner = $("#airSourceBanner");
  // is_live is true for real data (DB extractions or live SerpApi) and false only for mock.
  const isDemo = !state.airData.isLive || state.airData.source === "mock";
  if (!isDemo) {
    if (banner) banner.remove();
    return;
  }
  if (!banner) {
    banner = document.createElement("div");
    banner.id = "airSourceBanner";
    banner.className = "air-source-banner";
    host.parentNode.insertBefore(banner, host);
  }
  const msg = state.airData.warning || "Datos aéreos de demostración — sin captura aérea real conectada.";
  banner.innerHTML = `<span class="pill--demo">DEMO</span>${escapeHtml(msg)}`;
}

function renderAirTabs() {
  if ($("#airData")?.classList.contains("is-visible")) {
    renderViewActions("airData");
  }
  const map = { overview: "airOverview", table: "airTableView", map: "airMapView", charts: "airChartsView", detail: "airDetailView" };
  Object.entries(map).forEach(([tab, id]) => $(`#${id}`)?.classList.toggle("is-visible", state.airData.activeTab === tab));
}

function updateAirFilters() {
  state.airData.filters = {
    query: $("#airSearch")?.value || "",
    market: $("#airMarketFilter")?.value || "",
    origin: $("#airOriginFilter")?.value || "",
    destination: $("#airDestinationFilter")?.value || "",
    airline: $("#airAirlineFilter")?.value || "",
    connection: $("#airConnectionFilter")?.value || "",
    price: $("#airPriceFilter")?.value || "",
    signal: $("#airSignalFilter")?.value || "",
    dateFrom: $("#airDateFrom")?.value || "",
    dateTo: $("#airDateTo")?.value || "",
  };
  state.airData.page = 1;
  renderAirData();
}

function renderAirFilters() {
  const flights = state.airData.flights;
  fillSelect("#airMarketFilter", "Mercado", unique(flights.map((row) => row.market)), state.airData.filters.market);
  fillSelect("#airOriginFilter", "Origen", unique(flights.map((row) => row.origin)), state.airData.filters.origin);
  fillSelect("#airDestinationFilter", "Destino", unique(flights.map((row) => row.destination)), state.airData.filters.destination);
  fillSelect("#airAirlineFilter", "Compañía", unique(flights.flatMap((row) => row.airlines || [])), state.airData.filters.airline);
  fillSelect("#airPriceFilter", "Price level", unique(flights.map((row) => row.price_quality_label)), state.airData.filters.price);
  fillSelect("#airSignalFilter", "Revenue signal", unique(flights.map((row) => row.revenue_signal)), state.airData.filters.signal);
}

function fillSelect(selector, label, values, selected) {
  const element = $(selector);
  if (!element) return;
  const current = selected || element.value || "";
  element.innerHTML = [`<option value="">${escapeHtml(label)}: Todos</option>`, ...values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`)].join("");
  element.value = current;
}

function filteredAirFlights() {
  const filters = state.airData.filters;
  const query = filters.query.trim().toLowerCase();
  return state.airData.flights.filter((row) => {
    const haystack = [row.market, row.origin, row.destination, row.main_airline, ...(row.airlines || []), ...(row.flight_numbers || []), ...(row.aircraft_models || []), row.revenue_signal].join(" ").toLowerCase();
    if (query && !haystack.includes(query)) return false;
    if (filters.market && row.market !== filters.market) return false;
    if (filters.origin && row.origin !== filters.origin) return false;
    if (filters.destination && row.destination !== filters.destination) return false;
    if (filters.airline && !(row.airlines || []).includes(filters.airline)) return false;
    if (filters.price && row.price_quality_label !== filters.price) return false;
    if (filters.signal && row.revenue_signal !== filters.signal) return false;
    if (filters.connection === "direct" && !row.is_direct) return false;
    if (filters.connection === "non_direct" && row.is_direct) return false;
    if (["1 escala", "2 escalas", "3+ escalas"].includes(filters.connection) && row.flight_connection_type !== filters.connection) return false;
    if (filters.dateFrom && (!row.outbound_date || row.outbound_date < filters.dateFrom)) return false;
    if (filters.dateTo && (!row.outbound_date || row.outbound_date > filters.dateTo)) return false;
    return true;
  });
}

function filteredAirRoutes() {
  const routeKeys = new Set(filteredAirFlights().map((row) => row.route_key));
  return state.airData.routes.filter((route) => routeKeys.has(route.route_key));
}

function renderAirKpis() {
  const summary = state.airData.summary || {};
  const dist = summary.price_quality_distribution || {};
  const totalFlights = summary.total_options || 1;
  const baratoPct = Math.round(((dist["Barato"] || 0) / totalFlights) * 100);
  const caroPct = Math.round(((dist["Caro"] || 0) / totalFlights) * 100);
  const gapPct = summary.avg_price_gap_pct;
  const gapLabel = gapPct == null ? "—" : `${gapPct > 0 ? "+" : ""}${number(gapPct, 1)}%`;
  const cards = [
    { label: "Rutas analizadas", value: String(summary.total_routes ?? 0), meta: `${summary.opportunities_count ?? 0} oportunidades · ${summary.risks_count ?? 0} riesgos`, tone: "neutral", tooltip: "Mercados emisores con señal aérea capturada" },
    { label: "% vuelos directos", value: pctDecimal(summary.direct_pct), meta: "Fricción de conexión", tone: "neutral", tooltip: "Porcentaje de opciones directas sobre el total — más directo = menos fricción para el viajero" },
    { label: "Precio mínimo medio", value: currency(summary.avg_lowest_price), meta: gapPct != null ? `vs rango típico: ${gapLabel}` : "Presión de demanda aérea", tone: gapPct == null ? "neutral" : gapPct > 10 ? "down" : gapPct < -10 ? "up" : "neutral", tooltip: "Media del precio más bajo por ruta. Si está por encima del rango típico, los vuelos son caros y puede frenar la demanda hotelera" },
    { label: "Vuelos baratos / caros", value: `${baratoPct}% / ${caroPct}%`, meta: `${dist["Barato"] || 0} baratos · ${dist["Caro"] || 0} caros · ${dist["Normal"] || 0} normales`, tone: "neutral", tooltip: "Distribución de precio por opción de vuelo: Barato = por debajo del mínimo típico, Caro = por encima del máximo típico" },
    { label: "Calidad horaria media", value: number(summary.avg_schedule_quality_score, 0), meta: "Salida, llegada y duración", tone: "neutral", tooltip: "Score 0-100 calculado desde franjas horarias de salida/llegada y duración total del viaje" },
  ];
  $("#airKpis").innerHTML = cards.map((card, i) => renderMetric(card, i)).join("");
}

function renderAirOverview() {
  const routes = filteredAirRoutes();
  $("#airRouteRanking").innerHTML = routes.length
    ? routes.slice(0, 8).map((route) => {
        const gapPct = route.price_gap_pct;
        const gapStr = gapPct == null ? "—" : `${gapPct > 0 ? "+" : ""}${number(gapPct, 1)}%`;
        const gapClass = gapPct == null ? "" : gapPct > 10 ? "delta delta--down" : gapPct < -10 ? "delta delta--up" : "";
        return `<tr>
      <td>${escapeHtml(route.market)}</td>
      <td><button class="air-route-link" data-air-route="${escapeHtml(route.route_key)}">${escapeHtml(route.origin)} → ${escapeHtml(route.destination)}</button></td>
      <td>${currency(route.lowest_price)}</td>
      <td><span class="badge ${airPriceBadge(route.price_quality_label)}">${escapeHtml(route.price_quality_label || "—")}</span></td>
      <td><span class="${gapClass}">${gapStr}</span></td>
      <td>${pctDecimal(route.direct_share)}</td>
      <td class="air-airlines-cell">${escapeHtml(airlinesShort(route.airlines_detected))}</td>
      <td>${renderAirSemaphore(route)}</td>
      <td><strong>${number(route.route_score, 0)}</strong></td>
    </tr>`;
      }).join("")
    : `<tr><td colspan="9">${empty("Sin rutas para los filtros seleccionados.")}</td></tr>`;
  $$("#airRouteRanking [data-air-route]").forEach((button) => button.addEventListener("click", () => selectAirRoute(button.dataset.airRoute)));
  renderAirlineTable($("#airAirlineMiniChart"), filteredAirFlights());
}

function airlinesShort(list, max = 3) {
  const arr = Array.isArray(list) ? list : [];
  if (!arr.length) return "—";
  return arr.length <= max ? arr.join(", ") : `${arr.slice(0, max).join(", ")} +${arr.length - max}`;
}

function renderAirTable() {
  const rows = filteredAirFlights();
  const pageSize = getAirTablePageSize();
  const previousPageSize = Number(state.airData.pageSize || pageSize);
  if (previousPageSize !== pageSize) {
    const firstVisibleIndex = Math.max(0, (state.airData.page - 1) * previousPageSize);
    state.airData.page = Math.floor(firstVisibleIndex / pageSize) + 1;
  }
  state.airData.pageSize = pageSize;
  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
  state.airData.page = Math.min(state.airData.page, totalPages);
  const pageRows = rows.slice((state.airData.page - 1) * pageSize, state.airData.page * pageSize);
  $("#airTableCount").textContent = `Filas: ${rows.length} / ${state.airData.flights.length}`;
  $("#airPageInfo").textContent = `Página ${state.airData.page} / ${totalPages} · ${pageSize} filas/pág.`;
  $("#airFlightRows").innerHTML = pageRows.length
    ? pageRows.map((row) => `<tr>
      <td>${escapeHtml(row.market)}</td><td>${escapeHtml(row.origin || "-")}</td><td>${escapeHtml(row.destination || "-")}</td><td>${row.outbound_date || "-"}</td><td>${formatDaysAhead(row.days_ahead)}</td>
      <td>${escapeHtml(row.main_airline || "-")}</td><td>${escapeHtml((row.flight_numbers || []).join(", "))}</td><td>${escapeHtml((row.aircraft_models || []).join(", "))}</td>
      <td>${row.departure_time || "-"}</td><td>${row.arrival_time || "-"}</td><td><span class="${row.is_direct ? "badge low air-direct-badge" : "badge air-direct-badge"}">${escapeHtml(row.direct_label || "-")}</span></td><td>${row.stops ?? "-"}</td>
      <td>${currency(row.price || row.lowest_price)}</td><td>${renderAirPricePosition(row)}</td><td>${number(row.air_accessibility_index, 2)}</td><td>${formatDuration(row.total_duration_min)}</td>
    </tr>`).join("")
    : `<tr><td colspan="16">${empty("Sin vuelos para los filtros seleccionados.")}</td></tr>`;
}

function isAirTableFullscreen() {
  const panel = $("#airFlightTablePanel");
  return !!panel && (document.fullscreenElement === panel || panel.classList.contains("is-pseudo-fullscreen") || panel.classList.contains("is-fullscreen"));
}

function getAirTablePageSize() {
  if (!isAirTableFullscreen()) return 10;
  const panel = $("#airFlightTablePanel");
  if (!panel) return 10;
  const tableWrap = panel.querySelector(".table-wrap");
  const wrapHeight = tableWrap?.getBoundingClientRect().height || 0;
  const headerHeight = panel.querySelector("thead")?.getBoundingClientRect().height || 30;
  const rowHeights = Array.from(panel.querySelectorAll("#airFlightRows tr"))
    .map((row) => row.getBoundingClientRect().height)
    .filter((height) => height >= 18 && height <= 90)
    .sort((a, b) => a - b);
  const measuredRowHeight = rowHeights.length ? rowHeights[Math.floor(rowHeights.length / 2)] : 32;
  const availableHeight = Math.max(0, wrapHeight - headerHeight - 6);
  const fittedRows = Math.ceil(availableHeight / Math.max(24, measuredRowHeight));
  return Math.max(16, Math.min(100, fittedRows));
}

function formatDaysAhead(value) {
  const days = Number(value);
  if (!Number.isFinite(days)) return "-";
  return `${Math.round(days)} days`;
}

function formatDuration(value) {
  const minutes = Number(value);
  if (!Number.isFinite(minutes) || minutes <= 0) return "-";
  const hours = Math.floor(minutes / 60);
  const rest = Math.round(minutes % 60);
  return hours ? `${hours}h ${String(rest).padStart(2, "0")}m` : `${rest}m`;
}

function renderAirPricePosition(row) {
  const current = Number(row.price || row.lowest_price);
  const lower = Number(row.typical_price_min);
  const average = Number(row.typical_price_avg);
  const upper = Number(row.typical_price_max);
  const values = [current, lower, average, upper].filter(Number.isFinite);
  if (!Number.isFinite(current) || values.length < 2) {
    return `<span class="${airPriceBadge(row.price_quality_label)}">${escapeHtml(row.price_quality_label || "Sin dato")}</span>`;
  }
  const minValue = Number.isFinite(lower) ? lower : Math.min(...values);
  const maxValue = Number.isFinite(upper) ? upper : Math.max(...values);
  const avgValue = Number.isFinite(average) ? average : averageValue(values);
  const spread = Math.max(maxValue - minValue, 1);
  const position = Math.max(0, Math.min(100, ((current - minValue) / spread) * 100));
  const avgPosition = Math.max(0, Math.min(100, ((avgValue - minValue) / spread) * 100));
  const label = row.price_quality_label || "Sin dato";
  return `
    <div class="air-price-position" tabindex="0" style="--price-pos:${position}%; --avg-pos:${avgPosition}%">
      <div class="air-price-position__top">
        <span>${escapeHtml(label)}</span>
        <strong>${currency(current)}</strong>
      </div>
      <div class="air-price-position__track" aria-hidden="true"><i></i><b></b></div>
      <div class="air-price-tooltip" role="tooltip">
        <strong>Posicion del precio</strong>
        <div><span>Limite inferior</span><b>${currency(minValue)}</b></div>
        <div><span>Media</span><b>${currency(avgValue)}</b></div>
        <div><span>Max</span><b>${currency(maxValue)}</b></div>
        <div><span>Precio vuelo</span><b>${currency(current)} · ${number(position, 0)}%</b></div>
      </div>
    </div>`;
}

function renderAirMap() {
  const container = $("#airRouteMap");
  if (!container || state.airData.activeTab !== "map") return;
  renderAirMapControls();
  renderAirMapLegend();
  const routes = filteredAirRoutes();
  const geojson = buildAirRouteGeoJson(routes);
  if (!window.maplibregl || !geojson.features.length) {
    container.innerHTML = empty("Sin rutas con coordenadas disponibles.");
    return;
  }
  const host = ensureMapContainer(container);
  const map = ensureMapInstance(host);
  updateAirRouteMapData(map, host.id, geojson);
  renderAirRouteDrawer(routes.find((route) => route.route_key === state.airData.selectedRouteKey) || routes[0]);
}

// Floating filter overlay shown over the air map in fullscreen (the global filter panel is hidden there).
function renderAirMapControls() {
  const host = $("#airMapControls");
  if (!host) return;
  const flights = state.airData.flights || [];
  const f = state.airData.filters;
  const colorMode = $("#airMapColorMode")?.value || "revenue_signal";
  const opt = (value, label, selected) => `<option value="${escapeHtml(value)}" ${value === selected ? "selected" : ""}>${escapeHtml(label)}</option>`;
  const field = (label, id, optionsHtml) => `<label class="map-controls__field"><span>${escapeHtml(label)}</span><select data-air-map-filter="${id}">${optionsHtml}</select></label>`;
  const markets = unique(flights.map((row) => row.market));
  const prices = unique(flights.map((row) => row.price_quality_label));
  const signals = unique(flights.map((row) => row.revenue_signal));
  const connection = f.connection || "all";
  host.innerHTML = `
    <strong class="map-controls__title">Filtros del mapa</strong>
    ${field("Color", "colorMode", [["revenue_signal", "Revenue signal"], ["price", "Precio"], ["direct_share", "Direct share"], ["schedule_quality_score", "Schedule quality"], ["flight_supply_score", "Flight supply"]].map(([value, label]) => opt(value, label, colorMode)).join(""))}
    ${field("Mercado", "market", opt("", "Todos", f.market) + markets.map((value) => opt(value, value, f.market)).join(""))}
    ${field("Conexión", "connection", [["all", "Todos"], ["direct", "Solo directos"], ["non_direct", "Solo no directos"]].map(([value, label]) => opt(value, label, connection)).join(""))}
    ${field("Nivel precio", "price", opt("", "Todos", f.price) + prices.map((value) => opt(value, value, f.price)).join(""))}
    ${field("Revenue signal", "signal", opt("", "Todos", f.signal) + signals.map((value) => opt(value, value, f.signal)).join(""))}`;
  host.querySelectorAll("[data-air-map-filter]").forEach((element) => {
    element.addEventListener("change", (event) => {
      const key = event.target.dataset.airMapFilter;
      const value = event.target.value;
      if (key === "colorMode") {
        const headerSelect = $("#airMapColorMode");
        if (headerSelect) headerSelect.value = value;
        renderAirMap();
        renderAirMapLegend();
      } else {
        state.airData.filters[key] = value;
        state.airData.page = 1;
        renderAirData();
      }
    });
  });
}

function renderAirMapLegend() {
  const host = $("#airMapLegend");
  if (!host) return;
  const colorMode = $("#airMapColorMode")?.value || "revenue_signal";
  const dot = (color, label) => `<span><i class="map-legend-dot" style="background:${color}"></i>${escapeHtml(label)}</span>`;
  let items;
  if (colorMode === "price") items = dot("#30d158", "Barato") + dot("#64d2ff", "Medio") + dot("#ff453a", "Caro");
  else if (colorMode === "direct_share") items = dot("#30d158", "Mayoría directos") + dot("#ff9f0a", "Algunos") + dot("#ff453a", "Sin directos");
  else if (colorMode === "schedule_quality_score") items = dot("#30d158", "Calidad alta") + dot("#64d2ff", "Media") + dot("#ff453a", "Baja");
  else if (colorMode === "flight_supply_score") items = dot("#30d158", "Oferta alta") + dot("#64d2ff", "Media") + dot("#ff453a", "Baja");
  else items = dot("#30d158", "Oportunidad") + dot("#64d2ff", "Estable") + dot("#ff453a", "Riesgo");
  host.innerHTML = items + dot("#ff9f0a", "Destino") + dot("#64d2ff", "Origen");
}

async function toggleAirMapFullscreen() {
  const panel = $("#airMapPanel");
  if (!panel) return;
  try {
    if (document.fullscreenElement === panel) {
      await document.exitFullscreen();
    } else if (panel.requestFullscreen) {
      await panel.requestFullscreen();
    } else {
      panel.classList.toggle("is-pseudo-fullscreen");
      handleAirMapFullscreenChange();
    }
  } catch (error) {
    panel.classList.toggle("is-pseudo-fullscreen");
    handleAirMapFullscreenChange();
  }
}

function handleAirMapFullscreenChange() {
  const panel = $("#airMapPanel");
  const button = $("#airMapFullscreen");
  if (!panel) return;
  const isFullscreen = document.fullscreenElement === panel || panel.classList.contains("is-pseudo-fullscreen");
  panel.classList.toggle("is-fullscreen", isFullscreen);
  if (button) {
    button.textContent = isFullscreen ? "Salir" : "Pantalla completa";
    button.setAttribute("aria-label", isFullscreen ? "Salir de pantalla completa" : "Ver mapa en pantalla completa");
  }
  window.requestAnimationFrame(() => renderAirMap());
}

function updateAirRouteMapData(map, hostId, geojson) {
  const sourceId = `${sourceIdFor(hostId)}-air-routes`;
  const pointSourceId = `${sourceIdFor(hostId)}-airports`;
  const update = () => {
    if (!map.getSource(sourceId)) map.addSource(sourceId, { type: "geojson", data: geojson });
    // Glow casing behind each route for visibility on the dark basemap.
    if (!map.getLayer(`${sourceId}-casing`)) {
      map.addLayer({ id: `${sourceId}-casing`, type: "line", source: sourceId, layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": ["get", "route_color"], "line-width": ["interpolate", ["linear"], ["get", "num_options"], 1, 4, 4, 8, 8, 12], "line-opacity": 0.16, "line-blur": 4 } });
    }
    if (!map.getLayer(`${sourceId}-line`)) {
      map.addLayer({ id: `${sourceId}-line`, type: "line", source: sourceId, layout: { "line-cap": "round", "line-join": "round" }, paint: { "line-color": ["get", "route_color"], "line-width": ["interpolate", ["linear"], ["get", "num_options"], 1, 1.4, 4, 3, 8, 5], "line-opacity": 0.95 } });
      map.on("click", `${sourceId}-line`, (event) => {
        const routeKey = event.features?.[0]?.properties?.route_key;
        if (!routeKey) return;
        const route = filteredAirRoutes().find((item) => item.route_key === routeKey);
        if (!route) return;
        state.airData.selectedRouteKey = routeKey;
        renderAirRouteDrawer(route);
        showAirRouteMapPopup(map, event.lngLat, route);
      });
      map.on("mouseenter", `${sourceId}-line`, () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", `${sourceId}-line`, () => {
        map.getCanvas().style.cursor = "";
      });
    }
    if (!map.getSource(pointSourceId)) map.addSource(pointSourceId, { type: "geojson", data: buildAirAirportGeoJson(geojson) });
    if (!map.getLayer(`${pointSourceId}-circle`)) {
      map.addLayer({ id: `${pointSourceId}-circle`, type: "circle", source: pointSourceId, paint: {
        "circle-radius": ["case", ["==", ["get", "role"], "dest"], 7, 5],
        "circle-color": ["case", ["==", ["get", "role"], "dest"], "#ff9f0a", "#64d2ff"],
        "circle-stroke-color": "#09090b",
        "circle-stroke-width": 1.5,
      } });
    }
    if (!map.getLayer(`${pointSourceId}-label`)) {
      map.addLayer({ id: `${pointSourceId}-label`, type: "symbol", source: pointSourceId, layout: {
        "text-field": ["get", "code"],
        "text-font": ["Noto Sans Bold"],
        "text-size": 11,
        "text-offset": [0, 1.2],
        "text-anchor": "top",
        "text-allow-overlap": false,
      }, paint: { "text-color": "#e4e4e7", "text-halo-color": "#000000", "text-halo-width": 1.4 } });
    }
    map.getSource(sourceId).setData(geojson);
    map.getSource(pointSourceId).setData(buildAirAirportGeoJson(geojson));
    fitMapToAirRoutes(map, geojson);
  };
  if (map.isStyleLoaded()) update();
  else map.once("load", update);
}

function showAirRouteMapPopup(map, lngLat, route) {
  const flights = filteredAirFlights().filter((flight) => flight.route_key === route.route_key);
  const stats = airRoutePriceStats(route, flights);
  new window.maplibregl.Popup({ closeButton: true, closeOnClick: true, maxWidth: "360px", offset: 18 })
    .setLngLat(lngLat)
    .setHTML(renderAirRouteMapPopup(route, flights, stats))
    .addTo(map);
}

function renderAirRouteMapPopup(route, flights, stats) {
  const operators = route.airlines_detected?.length ? route.airlines_detected : unique(flights.flatMap((flight) => flight.airlines || [flight.main_airline]).filter(Boolean));
  const models = route.aircraft_models_detected?.length ? route.aircraft_models_detected : unique(flights.flatMap((flight) => flight.aircraft_models || []).filter(Boolean));
  return `
    <div class="air-map-popup" role="dialog" aria-label="Detalle ruta ${escapeHtml(route.origin)} a ${escapeHtml(route.destination)}">
      <div class="air-map-popup__top">
        <span>Ruta aérea</span>
        <strong>${escapeHtml(route.origin)} → ${escapeHtml(route.destination)}</strong>
        <small>${escapeHtml(route.market)} · ${escapeHtml(route.revenue_signal || "Sin señal")}</small>
      </div>
      <div class="air-map-popup__prices">
        <div><span>Precio actual</span><strong>${currency(stats.current)}</strong></div>
        <div><span>Precio medio</span><strong>${currency(stats.average)}</strong></div>
        <div><span>Precio bajo</span><strong>${currency(stats.typicalLow)}</strong></div>
        <div><span>Precio alto</span><strong>${currency(stats.typicalHigh)}</strong></div>
      </div>
      <div class="air-map-popup__band" aria-hidden="true">
        <i style="left:${stats.position}%"></i>
      </div>
      <div class="air-map-popup__meta">
        <b>Operadores</b><span>${escapeHtml(operators.join(", ") || "Sin dato")}</span>
        <b>Opciones</b><span>${number(route.num_options, 0)} · ${pctDecimal(route.direct_share)} directos</span>
        <b>Conectividad</b><span>AAI ${number(route.air_accessibility_index, 2)} · Score ${number(route.route_score, 0)}</span>
        <b>Aviones</b><span>${escapeHtml(models.slice(0, 4).join(", ") || "Sin dato")}</span>
      </div>
      <p>${escapeHtml(airInsight(route))}</p>
    </div>`;
}

function airRoutePriceStats(route, flights) {
  const optionPrices = flights.map((flight) => Number(flight.price || flight.lowest_price)).filter(Number.isFinite);
  const typicalMins = flights.map((flight) => Number(flight.typical_price_min)).filter(Number.isFinite);
  const typicalMaxs = flights.map((flight) => Number(flight.typical_price_max)).filter(Number.isFinite);
  const current = Number(route.lowest_price) || Math.min(...optionPrices, 0);
  const average = Number(route.avg_price) || averageValue(optionPrices);
  const typicalAverage = Number(route.typical_price_avg) || average;
  const typicalLow = typicalMins.length ? Math.min(...typicalMins) : Math.min(current, typicalAverage, average);
  const typicalHigh = typicalMaxs.length ? Math.max(...typicalMaxs) : Math.max(current, typicalAverage, average);
  const spread = Math.max(typicalHigh - typicalLow, 1);
  const position = Math.max(0, Math.min(100, ((current - typicalLow) / spread) * 100));
  return { current, average, typicalAverage, typicalLow, typicalHigh, position };
}

function buildAirRouteGeoJson(routes) {
  const colorMode = $("#airMapColorMode")?.value || "revenue_signal";
  return { type: "FeatureCollection", features: routes.map((route) => {
    const origin = state.airData.airports[route.origin];
    const destination = state.airData.airports[route.destination];
    if (!origin || !destination) return null;
    return { type: "Feature", properties: { ...route, route_color: airRouteColor(route, colorMode) }, geometry: { type: "LineString", coordinates: [[origin.lng, origin.lat], [destination.lng, destination.lat]] } };
  }).filter(Boolean) };
}

function buildAirAirportGeoJson(geojson) {
  const seen = new Map();
  geojson.features.forEach((feature) => {
    const coords = feature.geometry.coordinates || [];
    coords.forEach((coordinate, idx) => {
      const key = coordinate.join(",");
      const isDest = idx === coords.length - 1;
      const existing = seen.get(key);
      seen.set(key, {
        coord: coordinate,
        code: existing?.code || airportCodeForCoord(coordinate),
        isDest: existing?.isDest || isDest,
      });
    });
  });
  return {
    type: "FeatureCollection",
    features: Array.from(seen.values()).map((airport) => ({
      type: "Feature",
      properties: { code: airport.code || "", role: airport.isDest ? "dest" : "origin" },
      geometry: { type: "Point", coordinates: airport.coord },
    })),
  };
}

function renderAirCharts() {
  const routes = filteredAirRoutes();
  const flights = filteredAirFlights();
  renderAirCompactRows($("#airMarketComparison"), routes.slice(0, 8));
  renderAirCompactRows($("#airOpportunityRadar"), routes.filter((route) => route.route_risk_level === "Oportunidad").slice(0, 6));
  renderAirCompactRows($("#airRiskRadar"), routes.filter((route) => route.route_risk_level === "Riesgo").slice(0, 6));
  renderAirBars($("#airScheduleChart"), countValues(flights.flatMap((row) => [row.departure_hour_bucket, row.arrival_hour_bucket])).slice(0, 8), "");
  renderAirBars($("#airAircraftChart"), countValues(flights.flatMap((row) => row.aircraft_models || [])).slice(0, 8), "");
  renderAirBars($("#airPriceGapChart"), flights.slice(0, 10).map((row) => [`${row.origin}→${row.destination}`, row.price_gap_pct_vs_typical || 0]), "%");
}

function googleLevelLabel(level) {
  return { low: "Bajo", typical: "Típico", high: "Alto" }[String(level || "").toLowerCase()] || null;
}

// Google Flights price_insights momentum: the route's own ~60-day price trajectory,
// returned whole in a single capture. Rising = destination demand building.
function renderAirPriceMomentum(route) {
  const hist = (Array.isArray(route.price_history) ? route.price_history : [])
    .map((point) => ({ ts: Number(point[0]), price: Number(point[1]) }))
    .filter((point) => Number.isFinite(point.price));
  const level = googleLevelLabel(route.google_price_level);
  const levelCls = String(route.google_price_level || "").toLowerCase();
  const levelBadge = level
    ? `<span class="badge ${levelCls === "low" ? "low" : levelCls === "high" ? "high" : ""}">Demanda Google: ${escapeHtml(level)}</span>`
    : "";

  if (hist.length < 2) {
    return `<div class="evolution-strip"><div class="evolution-strip__header"><strong>Momentum precio aéreo · Google</strong>${levelBadge}</div>${empty("Sin histórico de Google para esta ruta. Disponible tras una nueva captura aérea.")}</div>`;
  }

  const prices = hist.map((p) => p.price);
  const min = Math.min(...prices), max = Math.max(...prices), range = (max - min) || 1;
  const first = prices[0], last = prices[prices.length - 1];
  const momentumPct = first ? ((last - first) / first) * 100 : 0;
  const up = momentumPct > 1, down = momentumPct < -1;
  const color = up ? "var(--bb-amber)" : down ? "var(--bb-cyan)" : "var(--muted)";
  const arrow = up ? "▲" : down ? "▼" : "■";
  const caption = up
    ? "Precios aéreos al alza → demanda al destino creciente: margen para sostener o subir BAR."
    : down
    ? "Precios aéreos a la baja → demanda más blanda: vigilar pricing y pace."
    : "Precios aéreos estables.";
  const W = 600, H = 88, pad = 6;
  const pts = hist
    .map((p, i) => {
      const x = pad + (i / (hist.length - 1)) * (W - pad * 2);
      const y = H - pad - ((p.price - min) / range) * (H - pad * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return `<div class="evolution-strip">
    <div class="evolution-strip__header">
      <strong>Momentum precio aéreo · Google (${hist.length} puntos)</strong>
      <span>${levelBadge} <b style="color:${color}">${arrow} ${Math.abs(momentumPct).toFixed(1)}%</b></span>
    </div>
    <svg class="air-momentum-svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">
      <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <div class="air-momentum-foot"><span>${currency(first)}</span><span>mín ${currency(min)} · máx ${currency(max)}</span><span>${currency(last)}</span></div>
    <p class="air-momentum-caption">${escapeHtml(caption)}</p>
  </div>`;
}

function renderAirHistory(history) {
  if (!history.length) {
    return `<div class="evolution-strip">${empty("Sin histórico guardado para esta ruta. Lanza dos capturas para ver evolución.")}</div>`;
  }
  const values = history.map((item) => item.lowestPrice).filter((value) => value !== null && value !== undefined);
  const minValue = values.length ? Math.min(...values) : 0;
  const maxValue = values.length ? Math.max(...values) : 0;
  return `<div class="evolution-strip">
    <div class="evolution-strip__header"><strong>Evolución precio mínimo</strong><span>${history.length} capturas</span></div>
    <div class="evolution-bars">${history.map((item, index) => {
      const value = item.lowestPrice ?? 0;
      const previous = history[index - 1]?.lowestPrice;
      const tone = previous === undefined || previous === null || value === previous ? "" : value > previous ? "is-up" : "is-down";
      const height = maxValue > minValue ? 22 + ((value - minValue) / (maxValue - minValue)) * 58 : 44;
      return `<div class="evolution-bars__item" title="${escapeHtml(formatDateTime(item.scrapedAt))} · ${escapeHtml(currency(item.lowestPrice))}">
        <span class="${tone}" style="height:${height}px"></span>
        <small>${escapeHtml(currency(item.lowestPrice))}</small>
      </div>`;
    }).join("")}</div>
  </div>`;
}

function renderAirDetail() {
  const route = filteredAirRoutes().find((item) => item.route_key === state.airData.selectedRouteKey) || filteredAirRoutes()[0];
  if (!route) {
    $("#airRouteDetail").innerHTML = empty("Selecciona una ruta para ver detalle.");
    return;
  }
  const flights = filteredAirFlights().filter((row) => row.route_key === route.route_key);
  const history = state.airData.routeHistory[route.route_key] || [];
  $("#airDetailTitle").textContent = `${route.origin} → ${route.destination}`;
  $("#airDetailSubtitle").textContent = `${route.market} · ${route.revenue_signal}`;
  $("#airRouteDetail").innerHTML = `
    <div class="air-detail-kpis">
      ${[["Precio mínimo", currency(route.lowest_price)], ["Precio medio", currency(route.avg_price)], ["AAI", number(route.air_accessibility_index, 2)], ["Opciones", route.num_options], ["% directos", pctDecimal(route.direct_share)], ["Compañías", route.num_airlines], ["Calidad horaria", number(route.avg_schedule_quality_score, 0)]].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(String(value))}</strong></div>`).join("")}
    </div>
    ${renderAirPriceMomentum(route)}
    ${renderAirHistory(history)}
    <article class="insight info"><strong>Insight automático</strong><p>${escapeHtml(airInsight(route))} Si el pickup hotelero está por encima del pace esperado, revisar descuentos activos y considerar subida progresiva de BAR.</p></article>
    <div class="table-wrap"><table><thead><tr><th>Horario</th><th>Compañía</th><th>Vuelo</th><th>Avión</th><th>Directo</th><th>Escalas</th><th>Precio</th><th>Duración</th><th>Calidad</th></tr></thead><tbody>${flights.map((row) => `<tr><td>${row.departure_time || "-"} → ${row.arrival_time || "-"}</td><td>${escapeHtml(row.main_airline || "-")}</td><td>${escapeHtml((row.flight_numbers || []).join(", "))}</td><td>${escapeHtml((row.aircraft_models || []).join(", "))}</td><td><span class="${row.is_direct ? "badge low" : "badge"}">${escapeHtml(row.direct_label)}</span></td><td>${escapeHtml(row.flight_connection_type)}</td><td>${currency(row.price || row.lowest_price)}</td><td>${row.total_duration_min || "-"} min</td><td>${number(row.schedule_quality_score, 0)}</td></tr>`).join("")}</tbody></table></div>`;
}

async function selectAirRoute(routeKey, openDetail = true) {
  state.airData.selectedRouteKey = routeKey;
  if (openDetail) state.airData.activeTab = "detail";
  try {
    await loadAirRouteHistory(routeKey);
  } catch (error) {
    setStatus(readableError(error), "error");
  }
  renderAirData();
}

function renderAirRouteDrawer(route) {
  const drawer = $("#airRouteDrawer");
  if (!drawer) return;
  drawer.innerHTML = route ? `<strong>${route.origin} → ${route.destination}</strong><span>${escapeHtml(route.market)}</span><div class="air-drawer-grid"><b>${currency(route.lowest_price)}</b><b>${number(route.route_score, 0)}</b><small>Precio min</small><small>Route score</small></div><p>${escapeHtml(airInsight(route))}</p><button class="filter-btn" data-air-drawer-detail="${escapeHtml(route.route_key)}">Abrir detalle</button>` : empty("Selecciona una ruta.");
  drawer.querySelector("[data-air-drawer-detail]")?.addEventListener("click", (event) => selectAirRoute(event.currentTarget.dataset.airDrawerDetail));
}

function renderAirCompactRows(container, routes) {
  if (!container) return;
  container.innerHTML = routes.length ? routes.map((route) => `<div class="air-compact-row"><strong>${escapeHtml(route.market)} · ${route.origin}→${route.destination}</strong><span>${currency(route.lowest_price)} · ${pctDecimal(route.direct_share)} directos · score ${number(route.route_score, 0)}</span></div>`).join("") : empty("Sin rutas para esta vista.");
}

function renderAirBars(container, rows, suffix) {
  if (!container) return;
  if (!rows.length) {
    container.innerHTML = empty("Sin datos.");
    return;
  }
  const max = Math.max(...rows.map((row) => Math.abs(Number(row[1]) || 0)), 1);
  container.innerHTML = `<div class="chart-bars chart-bars--compact">${rows.map(([label, value]) => `<div class="chart-bar" style="height:${Math.max(8, (Math.abs(value) / max) * 100)}%"><span>${escapeHtml(String(label))} · ${number(value, suffix ? 1 : 0)}${suffix}</span></div>`).join("")}</div>`;
}

function renderAirlineTable(container, flights) {
  if (!container) return;
  const airlines = new Map();
  flights.forEach((flight) => {
    (flight.airlines || [flight.main_airline]).filter(Boolean).forEach((airline) => {
      const current = airlines.get(airline) || { airline, options: 0, direct: 0, prices: [] };
      current.options += 1;
      if (flight.is_direct) current.direct += 1;
      if (flight.price || flight.lowest_price) current.prices.push(flight.price || flight.lowest_price);
      airlines.set(airline, current);
    });
  });
  const rows = Array.from(airlines.values()).sort((a, b) => b.options - a.options).slice(0, 8);
  container.innerHTML = rows.length
    ? `<table>
        <thead><tr><th>Logo</th><th>Compañía</th><th>Opc.</th><th>Directos</th><th>Precio medio</th></tr></thead>
        <tbody>${rows.map((row) => {
          const avgPrice = row.prices.length ? row.prices.reduce((sum, value) => sum + value, 0) / row.prices.length : null;
          return `<tr>
            <td>${airlineLogo(row.airline)}</td>
            <td><strong>${escapeHtml(row.airline)}</strong></td>
            <td>${row.options}</td>
            <td>${row.direct}</td>
            <td>${currency(avgPrice)}</td>
          </tr>`;
        }).join("")}</tbody>
      </table>`
    : empty("Sin compañías detectadas.");
}

function airlineCode(airline) {
  return {
    "Iberia Express": "I2",
    "Iberia": "IB",
    "Air Europa": "UX",
    "Vueling": "VY",
    "Eurowings": "EW",
    "Condor": "DE",
    "British Airways": "BA",
    "Transavia": "HV",
    "Air France": "AF",
    "Jet2": "LS",
    "Lufthansa": "LH",
    "KLM": "KL",
    "SWISS": "LX",
    "Brussels Airlines": "SN",
    "Austrian": "OS",
    "Austrian Airlines": "OS",
    "TAP Air Portugal": "TP",
    "TAP": "TP",
    "Discover Airlines": "4Y",
    "Edelweiss Air": "WK",
    "Edelweiss": "WK",
    "Binter Canarias": "NT",
    "Binter": "NT",
    "Aer Lingus": "EI",
    "Ryanair": "FR",
    "easyJet": "U2",
    "Norwegian": "DY",
    "Scandinavian Airlines": "SK",
    "SAS": "SK",
    "Finnair": "AY",
    "Wizz Air": "W6",
    "TUI fly": "X3",
    "TUI": "X3",
    "Volotea": "V7",
  }[airline] || String(airline || "?").slice(0, 2).toUpperCase();
}

// Real airline logo from the Google Flights CDN (by IATA code), with graceful
// fallback to the coloured initials if the image fails to load. `logoUrl` lets a
// live SerpApi payload override the derived URL when available.
function airlineLogo(airline, logoUrl) {
  const code = airlineCode(airline);
  const tone = Math.abs(Array.from(String(airline || "")).reduce((sum, char) => sum + char.charCodeAt(0), 0)) % 5;
  const src = logoUrl || `https://www.gstatic.com/flights/airline_logos/70px/${encodeURIComponent(code)}.png`;
  return `<span class="airline-logo airline-logo--${tone}" aria-label="${escapeHtml(airline)}">${escapeHtml(code)}<img class="airline-logo__img" src="${escapeHtml(src)}" alt="" loading="lazy" onerror="this.remove()"></span>`;
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

function renderMetric(card, index = 0) {
  const cls = `metric${index === 0 ? " metric--primary" : ""}`;
  const titleAttr = card.tooltip ? ` title="${escapeHtml(card.tooltip)}"` : "";
  return `<article class="${cls}"${titleAttr}>
    <span>${escapeHtml(card.label)}</span>
    <strong>${escapeHtml(card.value)}</strong>
    ${card.trend != null && card.trend !== "" ? `<small class="${card.tone || "neutral"}">${escapeHtml(card.trend)}</small>` : ""}
    <em>${escapeHtml(card.meta || "")}</em>
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
  const avg = values.reduce((sum, value) => sum + value, 0) / values.length;
  const latest = values[values.length - 1];
  const first = values[0];
  const delta = pctChange(latest, first);
  const range = max - min || 1;
  const width = 640;
  const height = 250;
  const pad = { top: 34, right: 32, bottom: 44, left: 58 };
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
  const barWidth = Math.max(8, Math.min(28, plotWidth / values.length - 6));
  const bars = values
    .map((value, index) => {
      const point = points[index];
      const ratio = (value - min) / range;
      const barHeight = Math.max(4, ratio * (plotHeight * 0.55));
      return `<rect class="trend-volume-bar" x="${point.x - barWidth / 2}" y="${height - pad.bottom - barHeight}" width="${barWidth}" height="${barHeight}" rx="1"></rect>`;
    })
    .join("");

  container.innerHTML = `
    <div class="trend-summary">
      <div><span>Último ADR</span><strong>${currency(latest)}</strong></div>
      <div><span>Media</span><strong>${currency(avg)}</strong></div>
      <div><span>Rango</span><strong>${currency(min)}-${currency(max)}</strong></div>
      <div><span>Movimiento</span><strong class="${badgeClass(delta)}">${pct(delta)}</strong></div>
    </div>
    <svg class="trend-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Evolucion historica del ADR">
      <defs>
        <linearGradient id="trend-area-grad" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="rgba(225, 29, 72, 0.34)"></stop>
          <stop offset="100%" stop-color="rgba(225, 29, 72, 0.02)"></stop>
        </linearGradient>
        <linearGradient id="trend-line-grad" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%" stop-color="#ff9f0a"></stop>
          <stop offset="52%" stop-color="#ff2d55"></stop>
          <stop offset="100%" stop-color="#64d2ff"></stop>
        </linearGradient>
      </defs>
      ${gridLines}
      <line class="trend-average-line" x1="${pad.left}" x2="${width - pad.right}" y1="${pointAt(avg, 0).y}" y2="${pointAt(avg, 0).y}"></line>
      <line class="trend-axis-line" x1="${pad.left}" x2="${width - pad.right}" y1="${height - pad.bottom}" y2="${height - pad.bottom}"></line>
      ${bars}
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
  if (!container) return;
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
    .filter((row) => hasValidCanaryCoordinates(row) && row.pricePerNight !== null && row.pricePerNight !== undefined)
    .map((row) => ({
      hotelName: row.hotelName,
      latitude: Number(row.latitude),
      longitude: Number(row.longitude),
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
  if (!container) return;
  if (!container.offsetWidth || !container.offsetHeight) {
    const view = container.closest(".view");
    if (view?.classList.contains("is-visible")) {
      window.requestAnimationFrame(() => renderHeatmapElement(container, options));
    }
    return;
  }
  const points = options.points || state.heatmap?.points || [];
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
  updateMapData(map, mapContainer.id, featureCollection, options.fit !== false);
  if (overlayRows.length && options.fit !== false) {
    window.setTimeout(() => fitMapToRows(map, overlayRows), 140);
  }
  clearMarkersForMap(mapContainer.id);
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
  const { captureHotels, captureFlights } = state.captureConfig;
  if (!captureHotels && !captureFlights) {
    return { ok: false, message: "Activa al menos un tipo de captura: hoteles o vuelos." };
  }
  if (captureHotels) {
    const v = validateHotelCaptureInputs();
    if (!v.ok) return v;
  }
  if (captureFlights) {
    const v = validateAirCaptureInputs();
    if (!v.ok) return v;
  }
  const hotel = captureHotels ? validateHotelCaptureInputs() : {};
  const air = captureFlights ? validateAirCaptureInputs() : {};
  return { ...hotel, ...air, ok: true };
}

function validateHotelCaptureInputs() {
  const checkIn = state.captureConfig.checkIn;
  const nights = Number(state.captureConfig.nights);
  const weeks = Number(state.captureConfig.weeks);
  const limit = Number(state.captureConfig.limit);
  if (!state.captureConfig.presetIds.length) return { ok: false, step: "hotels", message: "Selecciona al menos una zona hotelera." };
  if (!checkIn) return { ok: false, step: "hotels", message: "Selecciona una fecha de check-in." };
  if (!Number.isInteger(nights) || nights < 1 || nights > 30) return { ok: false, step: "hotels", message: "Noches debe estar entre 1 y 30." };
  if (!Number.isInteger(weeks) || weeks < 1 || weeks > 26) return { ok: false, step: "hotels", message: "Semanas debe estar entre 1 y 26." };
  if (!Number.isInteger(limit) || limit < 1 || limit > 500) return { ok: false, step: "hotels", message: "Hoteles debe estar entre 1 y 500." };
  return { ok: true, step: "hotels", checkIn, nights, weeks, limit };
}

function validateAirCaptureInputs() {
  if (!state.captureConfig.airAreaIds.length) return { ok: false, step: "flights", message: "Selecciona al menos un area para vuelos." };
  const airTripType = state.captureConfig.airTripType === "round_trip" ? "round_trip" : "one_way";
  const airReturnDate = state.captureConfig.airReturnDate || "";
  if (airTripType === "round_trip") {
    if (!airReturnDate) return { ok: false, step: "flights", message: "Selecciona fecha de vuelta para Round trip." };
    if (airReturnDate <= state.captureConfig.checkIn) return { ok: false, step: "flights", message: "La fecha de vuelta debe ser posterior a la salida." };
  }
  if (!["true", "false"].includes(String(state.captureConfig.airDirect))) return { ok: false, step: "flights", message: "Selecciona Vuelo directo: Si o No." };
  return { ok: true, step: "flights", airDirect: state.captureConfig.airDirect === "true", airTripType, airReturnDate };
}

function setCaptureModalStep(step) {
  state.captureModalStep = step === "flights" ? "flights" : "hotels";
  renderCaptureModalStep();
}

function renderCaptureModalStep() {
  const activeStep = state.captureModalStep || "hotels";
  const { captureHotels, captureFlights } = state.captureConfig;
  const onlyHotels = captureHotels && !captureFlights;
  const onlyFlights = !captureHotels && captureFlights;

  $$("[data-capture-step-panel]").forEach((panel) => {
    panel.classList.toggle("is-active", panel.dataset.captureStepPanel === activeStep);
  });
  $$("[data-capture-step-target]").forEach((button) => {
    const targetStep = button.dataset.captureStepTarget;
    button.classList.toggle("is-active", targetStep === activeStep);
    button.classList.toggle("is-complete", targetStep === "hotels" && activeStep === "flights");
    button.classList.toggle("is-disabled",
      (targetStep === "hotels" && !captureHotels) ||
      (targetStep === "flights" && !captureFlights));
  });

  // Atrás: visible solo en step flights y no en modo solo-vuelos
  $("#backCaptureStep")?.classList.toggle("is-hidden", activeStep === "hotels" || onlyFlights);
  // Continuar: visible solo en step hotels y cuando vuelos está activado
  $("#nextCaptureStep")?.classList.toggle("is-hidden", activeStep === "flights" || onlyHotels || onlyFlights);
  // Lanzar: visible cuando estamos en flights, o cuando el tipo es solo hotels, o solo flights
  $("#confirmCaptureModal")?.classList.toggle("is-hidden",
    activeStep === "hotels" && captureFlights && !onlyHotels);

  renderCaptureModalSummary();
}

function updateCaptureTypeCards() {
  $$("[data-capture-type]").forEach((card) => {
    const type = card.dataset.captureType;
    const isActive = type === "hotels" ? state.captureConfig.captureHotels : state.captureConfig.captureFlights;
    card.classList.toggle("is-active", isActive);
    const badge = card.querySelector(".capture-type-card__badge");
    if (badge) badge.textContent = isActive ? "ON" : "OFF";
  });
  // Si solo vuelos está activo, ir directo al step flights
  if (!state.captureConfig.captureHotels && state.captureConfig.captureFlights) {
    state.captureModalStep = "flights";
  } else if (state.captureConfig.captureHotels) {
    state.captureModalStep = "hotels";
  }
  renderCaptureModalStep();
}

async function openCaptureModal() {
  const modal = $("#captureModal");
  if (!modal) return;
  await ensureAirDataBoot().catch((error) => setStatus(readableError(error), "error"));
  const zoneSelect = $("#modalZones");
  if (zoneSelect) {
    zoneSelect.innerHTML = presets.map((preset) => `<option value="${preset.id}" ${state.captureConfig.presetIds.includes(preset.id) ? "selected" : ""}>${escapeHtml(preset.name)}</option>`).join("");
  }
  $("#modalCheckIn").value = state.captureConfig.checkIn;
  $("#modalNights").value = String(state.captureConfig.nights);
  $("#modalWeeks").value = String(state.captureConfig.weeks);
  $("#modalLimit").value = String(state.captureConfig.limit);
  if (!state.captureConfig.airReturnDate) {
    state.captureConfig.airReturnDate = addDays(state.captureConfig.checkIn, Number(state.captureConfig.nights || 6));
  }
  const returnDateInput = $("#modalAirReturnDate");
  if (returnDateInput) returnDateInput.value = state.captureConfig.airReturnDate;
  syncAirAreasFromSelectedZones();
  renderCaptureAirControls();
  updateCaptureTypeCards();
  modal.classList.remove("is-hidden");
  requestAnimationFrame(() => $("#modalZones")?.focus());
}
function closeCaptureModal() {
  const modal = $("#captureModal");
  if (!modal) return;
  modal.classList.add("is-hidden");
}

function applyModalCaptureConfig() {
  const selectedIds = Array.from($("#modalZones")?.selectedOptions || []).map((option) => option.value).filter(Boolean);
  state.captureConfig.presetIds = selectedIds;
  if (selectedIds.length) {
    state.captureConfig.presetId = selectedIds[0];
  }
  state.captureConfig.checkIn = $("#modalCheckIn").value;
  state.captureConfig.nights = Number($("#modalNights").value || state.captureConfig.nights);
  state.captureConfig.weeks = Number($("#modalWeeks").value || state.captureConfig.weeks);
  state.captureConfig.limit = Number($("#modalLimit").value || state.captureConfig.limit);
  state.captureConfig.airAreaIds = selectedValues("#modalAirAreas");
  state.captureConfig.airCountryIds = selectedValues("#modalAirCountries");
  state.captureConfig.airRouteKeys = selectedValues("#modalAirRoutes");
  state.captureConfig.airDirect = $("#modalAirDirect")?.value || "";
  state.captureConfig.airTripType = state.captureConfig.airTripType === "round_trip" ? "round_trip" : "one_way";
  state.captureConfig.airReturnDate = $("#modalAirReturnDate")?.value || state.captureConfig.airReturnDate || "";
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

function syncAirAreasFromSelectedZones() {
  const areaIds = Array.from(new Set(state.captureConfig.presetIds.map((presetId) => presetAirAreaMap[presetId]).filter(Boolean)));
  if (areaIds.length) {
    state.captureConfig.airAreaIds = areaIds;
    reconcileAirRouteSelection();
  }
}

function selectedValues(selector) {
  return Array.from($(selector)?.selectedOptions || []).map((option) => option.value).filter(Boolean);
}

function renderCaptureAirControls() {
  ensureAirCatalog();
  const areaSelect = $("#modalAirAreas");
  const countrySelect = $("#modalAirCountries");
  const routeSelect = $("#modalAirRoutes");
  const directSelect = $("#modalAirDirect");
  if (!areaSelect || !countrySelect || !routeSelect || !directSelect) return;

  const selectedAreas = new Set(state.captureConfig.airAreaIds);
  const availableRoutes = catalogRoutesForSelection({ ignoreCountry: true });
  const availableCountries = unique(availableRoutes.map((route) => route.country));

  areaSelect.innerHTML = state.airCatalog.areas
    .map((area) => `<option value="${escapeHtml(area.id)}" ${selectedAreas.has(area.id) ? "selected" : ""}>${escapeHtml(area.name)} (${escapeHtml(area.destination)})</option>`)
    .join("");

  countrySelect.innerHTML = availableCountries
    .map((country) => `<option value="${escapeHtml(country)}" ${state.captureConfig.airCountryIds.includes(country) ? "selected" : ""}>${escapeHtml(country)}</option>`)
    .join("");

  const routes = catalogRoutesForSelection();
  const grouped = new Map();
  routes.forEach((route) => {
    const group = `${route.areaName} · ${route.country}`;
    if (!grouped.has(group)) grouped.set(group, []);
    grouped.get(group).push(route);
  });
  routeSelect.innerHTML = Array.from(grouped.entries())
    .map(([label, groupRoutes]) => `<optgroup label="${escapeHtml(label)}">${groupRoutes.map((route) => `<option value="${escapeHtml(route.routeKey)}" ${state.captureConfig.airRouteKeys.includes(route.routeKey) ? "selected" : ""}>${escapeHtml(route.label)}</option>`).join("")}</optgroup>`)
    .join("");
  const routeHint = $("#modalAirRouteHint");
  if (routeHint) {
    const selectedCount = state.captureConfig.airRouteKeys.length || routes.length;
    const countryCount = state.captureConfig.airCountryIds.length || availableCountries.length;
    routeHint.textContent = `${selectedCount} rutas disponibles en ${countryCount} paises emisores para las areas elegidas.`;
  }
  directSelect.value = state.captureConfig.airDirect || "";
  const tripType = state.captureConfig.airTripType === "round_trip" ? "round_trip" : "one_way";
  $$("[data-air-trip-type]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.airTripType === tripType);
  });
  const returnDateField = $("#modalAirReturnDateField");
  const returnDateInput = $("#modalAirReturnDate");
  returnDateField?.classList.toggle("is-hidden", tripType !== "round_trip");
  if (returnDateInput) {
    if (!state.captureConfig.airReturnDate) {
      state.captureConfig.airReturnDate = addDays(state.captureConfig.checkIn, Number(state.captureConfig.nights || 6));
    }
    returnDateInput.value = state.captureConfig.airReturnDate;
  }
  $$("[data-air-direct-value]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.airDirectValue === state.captureConfig.airDirect);
  });
  renderCaptureModalSummary(routes);
}

function renderCaptureModalSummary(visibleRoutes = catalogRoutesForSelection()) {
  const target = $("#captureModalSummary");
  if (!target) return;
  const { captureHotels, captureFlights } = state.captureConfig;
  const selectedZones = state.captureConfig.presetIds.length || 0;
  const selectedAreas = state.captureConfig.airAreaIds.length || 0;
  const selectedCountries = state.captureConfig.airCountryIds.length || unique(visibleRoutes.map((route) => route.country)).length;
  const selectedRoutes = state.captureConfig.airRouteKeys.length || visibleRoutes.length;
  const directLabel = state.captureConfig.airDirect === "true" ? "Directos" : state.captureConfig.airDirect === "false" ? "No directos" : "Pendiente";
  const tripLabel = state.captureConfig.airTripType === "round_trip" ? "RT como 2 OW" : "One way";
  const modeLabel = captureHotels && captureFlights ? "Hotel + Vuelo" : captureHotels ? "Solo hoteles" : captureFlights ? "Solo vuelos" : "Ninguno";
  target.innerHTML = [
    ["Modo", modeLabel],
    ["Hoteles", captureHotels ? `${selectedZones} zona${selectedZones === 1 ? "" : "s"}` : "OFF"],
    ["Fotos", `${state.captureConfig.weeks} sem.`],
    ["Destino", captureFlights ? `${selectedAreas} area${selectedAreas === 1 ? "" : "s"}` : "OFF"],
    ["Vuelo", captureFlights ? tripLabel : "OFF"],
    ["Directo", captureFlights ? directLabel : "OFF"],
  ].map(([label, value]) => `<div><span>${escapeHtml(String(label))}</span><strong>${escapeHtml(String(value))}</strong></div>`).join("");
}

function catalogRoutesForSelection({ ignoreCountry = false } = {}) {
  ensureAirCatalog();
  const selectedAreas = new Set(state.captureConfig.airAreaIds);
  const selectedCountries = new Set(ignoreCountry ? [] : state.captureConfig.airCountryIds);
  return (state.airCatalog.routes || []).filter((route) => {
    if (selectedAreas.size && !selectedAreas.has(route.areaId)) return false;
    if (selectedCountries.size && !selectedCountries.has(route.country)) return false;
    return true;
  });
}

function reconcileAirRouteSelection() {
  const validRouteKeys = new Set(catalogRoutesForSelection().map((route) => route.routeKey));
  state.captureConfig.airRouteKeys = state.captureConfig.airRouteKeys.filter((routeKey) => validRouteKeys.has(routeKey));
  const validCountries = new Set(catalogRoutesForSelection({ ignoreCountry: true }).map((route) => route.country));
  state.captureConfig.airCountryIds = state.captureConfig.airCountryIds.filter((country) => validCountries.has(country));
}

function addWeeks(checkIn, weeks) {
  const date = new Date(`${checkIn}T00:00:00`);
  date.setDate(date.getDate() + weeks * 7);
  return toDate(date);
}

function addDays(checkIn, days) {
  const date = new Date(`${checkIn}T00:00:00`);
  date.setDate(date.getDate() + Number(days || 0));
  return toDate(date);
}

function dayDiff(startDate, endDate) {
  const start = new Date(`${startDate}T00:00:00`);
  const end = new Date(`${endDate}T00:00:00`);
  const diff = Math.round((end.getTime() - start.getTime()) / 86400000);
  return Number.isFinite(diff) && diff > 0 ? diff : Number(state.captureConfig.nights || 6);
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
  return `${value > 0 ? "▲ +" : value < 0 ? "▼ " : ""}${Math.abs(value).toFixed(1)}%`;
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

// Coalesce rapid input events so typing doesn't trigger a full re-render per keystroke.
function debounce(fn, ms = 150) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

// Reflect the active sort column + direction in the Explorer headers (↑ / ↓ / ↕).
function updateSortIndicators() {
  document.querySelectorAll("#explorer table th[data-sort]").forEach((th) => {
    const base = th.textContent.replace(/[↕↑↓]\s*$/, "").trim();
    const isActive = th.dataset.sort === state.sortKey;
    const glyph = isActive ? (state.sortAsc ? "↑" : "↓") : "↕";
    th.textContent = `${base} ${glyph}`;
    th.classList.toggle("is-sorted", isActive);
  });
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
  if (mode !== "busy") {
    statusTimer = setTimeout(() => {
      status.classList.remove("is-visible");
    }, mode === "error" ? 6800 : 3800);
  }
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

function hasNumericCoordinates(row) {
  return Number.isFinite(Number(row?.latitude)) && Number.isFinite(Number(row?.longitude));
}

function hasValidGeoCoordinates(row) {
  if (!hasNumericCoordinates(row)) return false;
  const latitude = Number(row.latitude);
  const longitude = Number(row.longitude);
  return latitude >= -90 && latitude <= 90 && longitude >= -180 && longitude <= 180;
}

function hasValidCanaryCoordinates(row) {
  if (!hasValidGeoCoordinates(row)) return false;
  const latitude = Number(row.latitude);
  const longitude = Number(row.longitude);
  return latitude >= 27.5 && latitude <= 29.7 && longitude >= -18.4 && longitude <= -13.0;
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
      "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 5, 0.8, 10, 1.55, 13, 2.15],
      "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 4, 16, 9, 34, 13, 52],
      "heatmap-opacity": 0.72,
      "heatmap-color": [
        "interpolate",
        ["linear"],
        ["heatmap-density"],
        0,
        "rgba(0,0,0,0)",
        0.18,
        "rgba(100,210,255,0.22)",
        0.3,
        "rgba(255,159,10,0.38)",
        0.6,
        "rgba(255,45,85,0.62)",
        1,
        "rgba(255,255,255,0.9)",
      ],
    },
  });

  map.addLayer({
    id: `${sourceId}-points`,
    type: "circle",
    source: sourceId,
    filter: ["==", ["get", "kind"], "pin"],
    paint: {
      "circle-color": "rgba(255, 159, 10, 0.86)",
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 3.5, 12, 5.5],
      "circle-stroke-color": "rgba(8, 8, 10, 0.96)",
      "circle-stroke-width": 1.6,
      "circle-opacity": 0.88,
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

function buildMapFeatureCollection(points, overlayRows = []) {
  const heatFeatures = points
    .filter(hasValidCanaryCoordinates)
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
    .filter(hasValidCanaryCoordinates)
    .map((row) => {
      const ppn = row.pricePerNight ?? (row.price && row.nights ? row.price / row.nights : null);
      return {
        type: "Feature",
        properties: {
          kind: "pin",
          hotelKey: row.hotelKey,
          hotelName: row.hotelName || "Hotel",
          label: currency(ppn),
          price: Number(ppn || 0),
          isRiu: isRiuHotel(row.hotelName),
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
  const points = featureCollection.features.filter((feature) => {
    const coordinates = feature.geometry?.coordinates || [];
    return feature.geometry?.type === "Point" && hasValidCanaryCoordinates({ latitude: coordinates[1], longitude: coordinates[0] });
  });
  if (!points.length) return;
  const bounds = new window.maplibregl.LngLatBounds();
  points.forEach((feature) => bounds.extend(feature.geometry.coordinates));
  map.fitBounds(bounds, { padding: { top: 44, right: 44, bottom: 44, left: 44 }, maxZoom: 13, duration: 420 });
}

// Fit to ALL air-route endpoints (European origins + Canary destinations). The generic
// fitMapToFeatures only keeps Canary points, so passing it the route LineStrings did
// nothing and the map stayed zoomed on Gran Canaria with the routes off-screen.
function fitMapToAirRoutes(map, geojson) {
  const bounds = new window.maplibregl.LngLatBounds();
  let any = false;
  geojson.features.forEach((feature) => {
    (feature.geometry?.coordinates || []).forEach((coordinate) => {
      if (Array.isArray(coordinate) && Number.isFinite(coordinate[0]) && Number.isFinite(coordinate[1])) {
        bounds.extend(coordinate);
        any = true;
      }
    });
  });
  if (!any) return;
  map.resize();
  map.fitBounds(bounds, { padding: { top: 56, right: 56, bottom: 56, left: 56 }, maxZoom: 6.2, duration: 480 });
}

function airportCodeForCoord(coord) {
  const airports = state.airData.airports || {};
  for (const code in airports) {
    const airport = airports[code];
    if (Math.abs(airport.lng - coord[0]) < 1e-3 && Math.abs(airport.lat - coord[1]) < 1e-3) return code;
  }
  return "";
}

function fitMapToRows(map, rows) {
  const points = rows.filter(hasValidCanaryCoordinates);
  if (!points.length) return;
  const bounds = new window.maplibregl.LngLatBounds();
  points.forEach((row) => bounds.extend([Number(row.longitude), Number(row.latitude)]));
  map.resize();
  map.fitBounds(bounds, { padding: { top: 42, right: 42, bottom: 42, left: 42 }, maxZoom: 12.2, duration: 0 });
}

function updateMapData(map, hostId, featureCollection, fit) {
  const sourceId = sourceIdFor(hostId);
  const update = () => {
    ensureMapLayers(map, sourceId);
    const source = map.getSource(sourceId);
    if (source) source.setData(featureCollection);
    map.resize();
    window.requestAnimationFrame(() => {
      map.resize();
      if (fit) fitMapToFeatures(map, featureCollection);
    });
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
    airAreaIds: state.captureConfig.airAreaIds,
    airCountryIds: state.captureConfig.airCountryIds,
    airRouteKeys: state.captureConfig.airRouteKeys,
    airDirect: state.captureConfig.airDirect,
    airTripType: state.captureConfig.airTripType,
    airReturnDate: state.captureConfig.airReturnDate,
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
    if (Array.isArray(parsed.airAreaIds)) state.captureConfig.airAreaIds = parsed.airAreaIds.filter(Boolean);
    if (Array.isArray(parsed.airCountryIds)) state.captureConfig.airCountryIds = parsed.airCountryIds.filter(Boolean);
    if (Array.isArray(parsed.airRouteKeys)) state.captureConfig.airRouteKeys = parsed.airRouteKeys.filter(Boolean);
    if (["true", "false"].includes(String(parsed.airDirect))) state.captureConfig.airDirect = String(parsed.airDirect);
    if (["one_way", "round_trip"].includes(String(parsed.airTripType))) state.captureConfig.airTripType = String(parsed.airTripType);
    if (typeof parsed.airReturnDate === "string") state.captureConfig.airReturnDate = parsed.airReturnDate;
    if (Number.isInteger(parsed.nights) && parsed.nights >= 1 && parsed.nights <= 30) state.captureConfig.nights = parsed.nights;
    if (Number.isInteger(parsed.weeks) && parsed.weeks >= 1 && parsed.weeks <= 26) state.captureConfig.weeks = parsed.weeks;
    if (Number.isInteger(parsed.limit) && parsed.limit >= 1 && parsed.limit <= 500) state.captureConfig.limit = parsed.limit;
  } catch {
    // noop
  }
}

function saveExplorerFilters() {
  localStorage.setItem("revenue-explorer-filters", JSON.stringify({
    query: $("#search")?.value || "",
    ratingMin: $("#filterRating")?.value || "",
    maxPrice: $("#filterMaxPrice")?.value || "",
    onlyRiu: state.filterOnlyRiu,
    criticalGaps: state.filterCriticalGaps,
  }));
}

function loadExplorerFilters() {
  try {
    const raw = localStorage.getItem("revenue-explorer-filters");
    if (!raw) return;
    const parsed = JSON.parse(raw);
    const searchEl = $("#search");
    const ratingEl = $("#filterRating");
    const maxPriceEl = $("#filterMaxPrice");
    if (searchEl && parsed.query) { searchEl.value = parsed.query; state.query = parsed.query; }
    if (ratingEl && parsed.ratingMin) ratingEl.value = parsed.ratingMin;
    if (maxPriceEl && parsed.maxPrice) maxPriceEl.value = parsed.maxPrice;
    if (typeof parsed.onlyRiu === "boolean") {
      state.filterOnlyRiu = parsed.onlyRiu;
      $("#btnFilterRiu")?.classList.toggle("is-active", state.filterOnlyRiu);
    }
    if (typeof parsed.criticalGaps === "boolean") {
      state.filterCriticalGaps = parsed.criticalGaps;
      $("#btnFilterGaps")?.classList.toggle("is-active", state.filterCriticalGaps);
    }
    updateRatingQuickButtons();
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
  if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === "r") {
    event.preventDefault();
    toggleCommandDock();
    return;
  }
  if (["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8"].includes(event.key)) {
    event.preventDefault();
    const viewMap = {
      "F1": "dashboard",
      "F2": "workspace",
      "F3": "scraping",
      "F4": "map",
      "F5": "hotelData",
      "F6": "riu",
      "F7": "revenue",
      "F8": "airData"
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

function toggleCommandDock() {
  const dock = $("#commandDock");
  const input = $("#dockCmdInput");
  if (!dock || !input) return;
  const isOpen = dock.classList.toggle("is-visible");
  dock.setAttribute("aria-hidden", String(!isOpen));
  if (isOpen) {
    input.focus();
    input.select();
    if (!state.ai.active) renderDockSuggestions(input.value || "");
  } else {
    hideDockSuggestions();
  }
}

function hideDockSuggestions() {
  const host = $("#dockSuggest");
  if (host) {
    host.innerHTML = "";
    host.classList.remove("is-visible");
  }
}

function closeCommandDock() {
  const dock = $("#commandDock");
  if (!dock) return;
  dock.classList.remove("is-visible");
  dock.setAttribute("aria-hidden", "true");
  hideDockSuggestions();
}

// Registro de comandos del shortcut (Ctrl+Shift+R). Añadir uno nuevo = añadir
// una entrada aquí: aparece automáticamente en /help y en el autocompletado.
const COMMANDS = [
  // — Vistas —
  { names: ["/dash", "/dashboard"], group: "Vistas", arg: false, desc: "Ir al Dashboard ejecutivo", run: () => goToView("dashboard", "DASHBOARD") },
  { names: ["/riu"], group: "Vistas", arg: false, desc: "Análisis de propiedades RIU", run: () => goToView("riu", "ANÁLISIS RIU") },
  { names: ["/hotel", "/hoteles", "/hotels"], group: "Vistas", arg: false, desc: "Datos hoteleros (KPIs, tabla, mapa)", run: () => goToView("hotelData", "DATOS HOTELEROS") },
  { names: ["/air", "/vuelos", "/flight"], group: "Vistas", arg: false, desc: "Inteligencia aérea Air_Data", run: () => goToView("airData", "AIR_DATA") },
  { names: ["/rev", "/revenue"], group: "Vistas", arg: false, desc: "Revenue Management", run: () => goToView("revenue", "REVENUE") },
  { names: ["/map", "/heatmap"], group: "Vistas", arg: false, desc: "Mapa de calor por ADR", run: () => goToView("map", "MAPA") },
  { names: ["/exp", "/tabla"], group: "Vistas", arg: false, desc: "Explorador con filtros", run: () => goToView("explorer", "EXPLORADOR") },
  { names: ["/work"], group: "Vistas", arg: false, desc: "Área de trabajo modular", run: () => goToView("workspace", "WORKSPACE") },
  { names: ["/scrap", "/capturas"], group: "Vistas", arg: false, desc: "Consola de capturas", run: () => goToView("scraping", "CAPTURAS") },
  // — Acciones —
  { names: ["/run", "/capture", "/captura"], group: "Acciones", arg: false, desc: "Abrir configurador de captura", run: () => { openCaptureModal(); setStatus("Abriendo configurador de captura…", "info"); } },
  { names: ["/refresh", "/reload", "/actualizar"], group: "Acciones", arg: false, desc: "Recargar datos de mercado y vuelos", run: () => refreshAllData() },
  { names: ["/export", "/csv"], group: "Acciones", arg: false, desc: "Exportar CSV de la vista actual", run: () => exportActiveView() },
  { names: ["/settings", "/config", "/ajustes"], group: "Acciones", arg: false, desc: "Abrir configuración", run: () => { openSettingsModal(); setStatus("Abriendo configuración…", "info"); } },
  { names: ["/clear", "/limpiar"], group: "Acciones", arg: false, desc: "Limpiar chat IA o consola", run: () => clearActive() },
  // — Copiloto IA —
  { names: ["/ask", "/ia", "/copilot"], group: "Copiloto IA", arg: true, desc: "Preguntar al copiloto (texto libre)", run: (args) => enterAiMode(args || null) },
  { names: ["/gaps"], group: "Copiloto IA", arg: false, desc: "IA: hoteles con mayor gap vs mercado", run: () => enterAiMode("¿Qué hoteles tienen el mayor gap de precio vs el mercado y qué debería hacer con la tarifa de cada uno?") },
  { names: ["/oportunidades", "/opp"], group: "Copiloto IA", arg: false, desc: "IA: oportunidades de revenue ahora", run: () => enterAiMode("Dame las 3 principales oportunidades de revenue ahora mismo, justificadas con las cifras del snapshot.") },
  { names: ["/pricing", "/tarifa"], group: "Copiloto IA", arg: false, desc: "IA: recomendaciones de pricing RIU", run: () => enterAiMode("Recomiéndame ajustes de pricing concretos para las propiedades RIU según el comp-set y el régimen.") },
  { names: ["/demanda", "/momentum"], group: "Copiloto IA", arg: false, desc: "IA: presión de demanda y momentum aéreo", run: () => enterAiMode("¿Cómo está la presión de demanda del destino y el momentum de los precios aéreos? ¿Qué implica para la tarifa?") },
  // — Ayuda —
  { names: ["/help", "/ayuda", "/?"], group: "Ayuda", arg: false, desc: "Mostrar todos los comandos", run: () => { renderDockSuggestions(""); setStatus("Comandos disponibles listados. Escribe / para filtrar.", "info"); } },
];

function goToView(view, label) {
  showView(view);
  setStatus(`Terminal cambiada a: ${label}`, "ok");
}

function findCommand(word) {
  const token = String(word || "").toLowerCase();
  return COMMANDS.find((command) => command.names.includes(token));
}

function executeCommand(val) {
  const raw = (val || "").trim();
  if (!raw) return;
  const parts = raw.split(/\s+/);
  const word = parts[0].toLowerCase();
  const args = raw.slice(parts[0].length).trim();
  const command = findCommand(word);
  if (!command) {
    setStatus(`Comando no reconocido: ${raw}. Escribe /help`, "error");
    return;
  }
  try {
    command.run(args);
  } catch (error) {
    setStatus(`Error ejecutando ${word}: ${readableError(error)}`, "error");
  }
}

// Exporta la vista activa al CSV adecuado (aéreo o hotelero).
function exportActiveView() {
  if (state.runtime.activeView === "airData") {
    exportAirCsv();
  } else {
    exportCsv();
  }
}

async function refreshAllData() {
  setStatus("Recargando datos de mercado y vuelos…", "busy");
  try {
    await Promise.all([
      loadTargetsForSelection().catch(() => {}),
      (async () => { try { await ensureAirDataBoot(); } catch (_) { await loadAirData().catch(() => {}); } })(),
    ]);
    renderAll();
    if (state.runtime.activeView === "airData") renderAirData();
    setStatus("Datos recargados.", "ok");
  } catch (error) {
    setStatus(`No se pudieron recargar los datos: ${readableError(error)}`, "error");
  }
}

function clearActive() {
  if (state.ai.active) {
    state.ai.messages = [];
    enterAiMode();
    setStatus("Chat del copiloto limpiado.", "ok");
    return;
  }
  const consoleBox = document.getElementById("scrapeConsole");
  if (consoleBox) consoleBox.innerHTML = "";
  setStatus("Consola limpiada.", "ok");
}

// Autocompletado del dock: filtra COMMANDS mientras escribes y permite clic.
function renderDockSuggestions(query) {
  const host = $("#dockSuggest");
  if (!host) return;
  if (state.ai.active) {
    host.innerHTML = "";
    host.classList.remove("is-visible");
    return;
  }
  const q = String(query || "").trim().toLowerCase().replace(/^\//, "");
  const matches = COMMANDS.filter((command) => {
    if (!q) return true;
    return command.names.some((name) => name.replace(/^\//, "").includes(q)) || command.desc.toLowerCase().includes(q);
  });
  if (!matches.length) {
    host.innerHTML = `<div class="cmd-suggest__empty">Sin comandos para “${escapeHtml(query)}”</div>`;
    host.classList.add("is-visible");
    return;
  }
  host.innerHTML = matches
    .map(
      (command) => `
      <button type="button" class="cmd-suggest__row" data-cmd="${command.names[0]}">
        <span class="cmd-suggest__cmd">${command.names[0]}${command.arg ? " <em>…</em>" : ""}</span>
        <span class="cmd-suggest__desc">${escapeHtml(command.desc)}</span>
        <span class="cmd-suggest__group">${escapeHtml(command.group)}</span>
      </button>`,
    )
    .join("");
  host.classList.add("is-visible");
}

// ---------------------------------------------------------------------------
// Copiloto IA de revenue (/ask) — chat sobre el snapshot del mercado activo
// ---------------------------------------------------------------------------
function enterAiMode(initialQuestion) {
  state.ai.active = true;
  const dock = $("#commandDock");
  const cmdBar = dock?.querySelector(".cmd-bar--dock");
  const chat = $("#aiChat");
  if (dock) {
    dock.classList.add("is-visible", "is-ai");
    dock.setAttribute("aria-hidden", "false");
  }
  if (cmdBar) cmdBar.style.display = "none";
  if (chat) chat.hidden = false;
  hideDockSuggestions();
  if (!state.ai.messages.length) {
    state.ai.messages.push({
      role: "assistant",
      content: "Hola 👋 Soy tu copiloto de revenue. Tengo el snapshot del mercado activo (hoteles y vuelos). Pregúntame por pricing, gaps vs mercado, presión de demanda, oportunidades o el momentum aéreo.",
    });
  }
  renderAiChat();
  window.requestAnimationFrame(() => $("#aiChatInput")?.focus());
  if (initialQuestion) sendAiMessage(initialQuestion);
}

function exitAiMode() {
  state.ai.active = false;
  const dock = $("#commandDock");
  const cmdBar = dock?.querySelector(".cmd-bar--dock");
  const chat = $("#aiChat");
  if (chat) chat.hidden = true;
  if (cmdBar) cmdBar.style.display = "";
  if (dock) {
    dock.classList.remove("is-visible", "is-ai");
    dock.setAttribute("aria-hidden", "true");
  }
}

async function sendAiMessage(text) {
  const clean = (text || "").trim();
  if (!clean || state.ai.pending) return;
  state.ai.messages.push({ role: "user", content: clean });
  state.ai.pending = true;
  renderAiChat();
  // El snapshot aéreo se calienta en segundo plano; nos aseguramos de que esté
  // listo antes de construir el contexto para que el copiloto "vea" los vuelos.
  try {
    await ensureAirDataBoot();
  } catch (error) {
    console.warn("Air data no disponible para el copiloto:", error);
  }
  try {
    const payload = {
      messages: state.ai.messages.filter((message) => message.role === "user" || message.role === "assistant"),
      context: buildAiContext(),
    };
    const data = await api("/api/ai/chat", { method: "POST", body: JSON.stringify(payload) });
    state.ai.messages.push({ role: "assistant", content: data.reply || "(sin respuesta)" });
  } catch (error) {
    state.ai.messages.push({ role: "assistant", content: `⚠️ ${readableError(error)}`, error: true });
  } finally {
    state.ai.pending = false;
    renderAiChat();
  }
}

function renderAiChat() {
  const host = $("#aiChatMessages");
  if (!host) return;
  const bubbles = state.ai.messages.map((message) => {
    const cls = message.role === "user" ? "ai-msg ai-msg--user" : `ai-msg ai-msg--ai${message.error ? " ai-msg--error" : ""}`;
    return `<div class="${cls}">${formatAiText(message.content)}</div>`;
  });
  if (state.ai.pending) {
    bubbles.push(`<div class="ai-msg ai-msg--ai ai-msg--pending"><span class="ai-typing"><i></i><i></i><i></i></span></div>`);
  }
  host.innerHTML = bubbles.join("");
  host.scrollTop = host.scrollHeight;
}

function formatAiText(text) {
  let html = escapeHtml(String(text || ""));
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/^\s*[-*]\s+(.+)$/gm, "<li>$1</li>");
  html = html.replace(/((?:<li>.*?<\/li>\s*)+)/gs, "<ul>$1</ul>");
  html = html.replace(/\n/g, "<br>");
  return html;
}

function buildAiContext() {
  const rows = state.rows || [];
  const summary = state.photoDetail?.summary || {};
  const metrics = state.metrics || {};
  const median = metrics.market?.medianPricePerNight ?? summary.medianPricePerNight ?? null;
  const round1 = (value) => (typeof value === "number" ? Math.round(value * 10) / 10 : value);
  // El servidor trunca el snapshot (ventana de contexto pequeña). Limitamos la
  // lista de hoteles para dejar sitio garantizado a vuelos y métricas.
  const list = rows.slice(0, 18).map((row) => ({
    nombre: row.hotelName,
    riu: isRiuHotel(row.hotelName),
    adrNoche: row.pricePerNight,
    adrPersona: row.pricePerPersonPerNight,
    rating: row.rating,
    resenas: row.reviewCount,
    regimen: row.board,
    cancelacionGratis: row.freeCancellation === true,
    gapVsMercadoPct: (row.pricePerNight != null && median) ? round1(((row.pricePerNight - median) / median) * 100) : null,
  }));
  const airRoutes = state.airData?.routes || [];
  const air = (state.airData?.summary || airRoutes.length)
    ? {
        resumen: state.airData?.summary || null,
        fuente: state.airData?.isLive ? "datos en vivo (SerpApi)" : "datos de demostración",
        rutas: airRoutes.slice(0, 12).map((route) => ({
          mercado: route.market,
          ruta: `${route.origin}-${route.destination}`,
          precioMin: route.lowest_price,
          precioMedio: route.avg_price,
          gapPrecioPct: round1(route.price_gap_pct),
          nivelPrecio: route.price_quality_label,
          nivelGoogle: route.google_price_level,
          pctDirectos: route.direct_share != null ? round1(route.direct_share * 100) : null,
          numAerolineas: route.num_airlines,
          calidadHorariaScore: route.avg_schedule_quality_score,
          ofertaVuelosScore: route.flight_supply_score,
          tension: airSemaphore(route).label,
          senalRevenue: route.revenue_signal,
        })),
      }
    : null;
  return {
    mercado: (typeof activePresets === "function" ? activePresets().map((preset) => preset.name).join(", ") : "") || "Mercado activo",
    capturadoEn: state.latest?.snapshot?.scrapedAt || null,
    // Orden deliberado: vuelos y agregados primero; la lista larga de hoteles al
    // final, que es lo que se recorta si el snapshot supera el límite del modelo.
    vuelos: air,
    hoteles: {
      total: rows.length,
      adrMedioNoche: summary.avgPricePerNight,
      adrMedioPersona: summary.avgPricePerPersonNight,
      medianaNoche: median,
      rateShoppingIndex: metrics.rateShoppingIndex,
      indicadoresDemanda: metrics.demandIndicators,
      distribucionTiers: metrics.priceTierDistribution,
      correlacionRatingPrecio: metrics.ratingPriceCorrelation,
      lista: list,
    },
  };
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

function airInsight(route) {
  if (!route) return "Sin señal aérea disponible.";
  const signal = String(route.revenue_signal || "");
  const gapPct = route.price_gap_pct;
  const gapStr = gapPct != null ? ` (precio medio ${gapPct > 0 ? "+" : ""}${number(gapPct, 1)}% vs rango típico)` : "";
  if (signal === "Oportunidad pricing") {
    return `${route.origin} → ${route.destination} tiene vuelos baratos y mayoría directos${gapStr}. Oportunidad de subida de tarifa si el pickup hotelero acompaña.`;
  }
  if (signal === "Oportunidad marketing limitada") {
    return `${route.origin} → ${route.destination} tiene vuelos baratos${gapStr} pero poca conectividad directa. Invertir en marketing para convertir el interés en reserva.`;
  }
  if (signal === "Riesgo de demanda") {
    return `${route.origin} → ${route.destination} con vuelos caros${gapStr}. La fricción aérea puede frenar la demanda hotelera. Vigilar pickup antes de subir BAR.`;
  }
  if (signal === "Mercado con fricción") {
    return `${route.origin} → ${route.destination}: precios normales pero pocas opciones directas. La conectividad limitada puede reducir la conversión desde este mercado.`;
  }
  if ((route.avg_schedule_quality_score || 0) >= 75 && (route.num_airlines || 0) <= 1) {
    return `${route.origin} → ${route.destination} con buena calidad horaria pero dependencia de un único operador. Vigilar elasticidad ante cambios de frecuencia.`;
  }
  return `${route.origin} → ${route.destination} mercado estable${gapStr}. Mantener seguimiento de precio aéreo y pickup antes de mover BAR.`;
}

function airBadgeClass(signal) {
  if (String(signal).includes("Oportunidad")) return "badge low";
  if (String(signal).includes("Riesgo")) return "badge high";
  return "badge";
}

function renderAirSemaphore(route) {
  const signal = airSemaphore(route);
  return `<span class="air-semaphore air-semaphore--${signal.tone}" title="${escapeHtml(signal.label)}" aria-label="${escapeHtml(signal.label)}"><i></i></span>`;
}

function airSemaphore(route) {
  const priceLabel = String(route?.price_quality_label || "");
  const revenue = String(route?.revenue_signal || "");
  if (priceLabel === "Barato" || revenue.includes("Oportunidad")) return { tone: "green", label: revenue || "Buen Precio" };
  if (priceLabel === "Caro" || revenue.includes("Riesgo")) return { tone: "red", label: revenue || "Precio alto" };
  if (revenue === "Mercado con fricción") return { tone: "yellow", label: "Mercado con fricción" };
  return { tone: "yellow", label: "En la media" };
}

function airPriceBadge(label) {
  if (label === "Barato") return "badge low";
  if (label === "Caro") return "badge high";
  return "badge";
}

function airRouteColor(route, mode) {
  if (mode === "price") return (route.lowest_price || 0) > 260 ? "#ff453a" : (route.lowest_price || 0) < 160 ? "#30d158" : "#64d2ff";
  if (mode === "direct_share") return (route.direct_share || 0) >= 0.5 ? "#30d158" : (route.direct_share || 0) > 0 ? "#ff9f0a" : "#ff453a";
  if (mode === "schedule_quality_score") return (route.avg_schedule_quality_score || 0) >= 75 ? "#30d158" : (route.avg_schedule_quality_score || 0) >= 60 ? "#64d2ff" : "#ff453a";
  if (mode === "flight_supply_score") return (route.flight_supply_score || 0) >= 65 ? "#30d158" : (route.flight_supply_score || 0) >= 35 ? "#64d2ff" : "#ff453a";
  if (String(route.revenue_signal).includes("Oportunidad")) return "#30d158";
  if (String(route.revenue_signal).includes("Riesgo")) return "#ff453a";
  return "#64d2ff";
}

function averageValue(values) {
  const validValues = values.map(Number).filter(Number.isFinite);
  if (!validValues.length) return 0;
  return validValues.reduce((sum, value) => sum + value, 0) / validValues.length;
}

function unique(values) {
  return Array.from(new Set(values.filter(Boolean))).sort((a, b) => String(a).localeCompare(String(b)));
}

function countValues(values) {
  const counts = new Map();
  values.filter(Boolean).forEach((value) => counts.set(value, (counts.get(value) || 0) + 1));
  return Array.from(counts.entries()).sort((a, b) => b[1] - a[1]);
}

function groupMin(rows, labelKey, valueKey) {
  const groups = new Map();
  rows.forEach((row) => {
    const label = row[labelKey] ?? "-";
    const value = Number(row[valueKey] || 0);
    groups.set(label, Math.min(groups.get(label) || value, value));
  });
  return Array.from(groups.entries()).sort((a, b) => Number(a[0]) - Number(b[0]));
}

function number(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return new Intl.NumberFormat("es-ES", { maximumFractionDigits: digits, minimumFractionDigits: digits > 0 ? digits : 0 }).format(Number(value));
}

function pctDecimal(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return `${Math.round(Number(value) * 100)}%`;
}

function exportAirCsv() {
  const rows = filteredAirFlights();
  if (!rows.length) {
    setStatus("No hay vuelos Air_Data para exportar.", "error");
    return;
  }
  const header = ["market", "origin", "destination", "outbound_date", "return_date", "days_ahead", "main_airline", "flight_numbers", "aircraft_models", "departure_time", "arrival_time", "direct_label", "flight_connection_type", "stops", "price", "price_quality_label", "air_accessibility_index", "schedule_quality_score", "revenue_signal"];
  const csv = [header, ...rows.map((row) => header.map((key) => Array.isArray(row[key]) ? row[key].join(" | ") : row[key] ?? ""))]
    .map((line) => line.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(","))
    .join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `air-data-${Date.now()}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

async function loadHotelPriceHistory(hotelKey) {
  if (!hotelKey) return [];
  const query = new URLSearchParams({ hotelKey, limit: "24" });
  if (state.activeTargetId) query.set("targetId", String(state.activeTargetId));
  const payload = await api(`/api/hotels/price-history?${query.toString()}`);
  state.hotelHistory[hotelKey] = Array.isArray(payload.history) ? payload.history : [];
  return state.hotelHistory[hotelKey];
}

function renderHotelHistory(history) {
  if (!history?.length) return empty("Sin histórico de precio para este hotel.");
  const values = history.map((row) => row.pricePerNight).filter((price) => price !== null && price !== undefined);
  const minValue = values.length ? Math.min(...values) : 0;
  const maxValue = values.length ? Math.max(...values) : 0;
  return `<div class="evolution-bars evolution-bars--hotel">${history.map((item, index) => {
    const value = item.pricePerNight ?? 0;
    const previous = history[index - 1]?.pricePerNight;
    const tone = previous === undefined || previous === null || value === previous ? "" : value > previous ? "is-up" : "is-down";
    const height = maxValue > minValue ? 18 + ((value - minValue) / (maxValue - minValue)) * 52 : 38;
    return `<div class="evolution-bars__item" title="${escapeHtml(formatDateTime(item.scrapedAt))} · ${escapeHtml(currency(item.pricePerNight))}">
      <span class="${tone}" style="height:${height}px"></span>
      <small>${escapeHtml(currency(item.pricePerNight))}</small>
    </div>`;
  }).join("")}</div>`;
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

    <div class="map-drawer__section">
      <span>Evolución precio/noche</span>
      <div id="hotelPriceHistory">${renderHotelHistory(state.hotelHistory[hotel.hotelKey])}</div>
    </div>
  `;
  
  drawer.classList.add("is-visible");
  loadHotelPriceHistory(hotel.hotelKey)
    .then((history) => {
      const target = document.getElementById("hotelPriceHistory");
      if (target) target.innerHTML = renderHotelHistory(history);
    })
    .catch((error) => setStatus(readableError(error), "error"));
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
  const prices = rows
    .filter(hasValidCanaryCoordinates)
    .map((row) => row.pricePerNight ?? (row.price && row.nights ? row.price / row.nights : null))
    .filter((price) => Number.isFinite(Number(price)) && Number(price) > 0)
    .map(Number);
  const avgPrice = prices.length ? prices.reduce((sum, p) => sum + p, 0) / prices.length : 150;
  
  rows.forEach(row => {
    if (!hasValidCanaryCoordinates(row)) return;
    
    const ppn = row.pricePerNight ?? (row.price && row.nights ? row.price / row.nights : null);
    if (!ppn) return;
    
    const el = document.createElement("div");
    el.className = "maplibre-marker-price";
    el.setAttribute("role", "button");
    el.setAttribute("tabindex", "0");
    el.setAttribute("aria-label", `${row.hotelName || "Hotel"} · ${currency(ppn)} por noche`);
    el.title = `${row.hotelName || "Hotel"} · ${currency(ppn)} por noche`;
    const dot = document.createElement("span");
    dot.className = "maplibre-marker-price__dot";
    dot.setAttribute("aria-hidden", "true");
    const badge = document.createElement("div");
    badge.className = "maplibre-marker-price__badge";
    
    const isRiu = String(row.hotelName || "").toLowerCase().includes("riu");
    if (isRiu) {
      el.classList.add("riu");
      badge.textContent = `★ €${Math.round(ppn)}`;
    } else {
      badge.textContent = `€${Math.round(ppn)}`;
      if (ppn < avgPrice * 0.85) {
        el.classList.add("low");
      } else if (ppn > avgPrice * 1.15) {
        el.classList.add("high");
      } else {
        el.classList.add("mid");
      }
    }
    el.appendChild(dot);
    el.appendChild(badge);
    
    el.addEventListener("click", (e) => {
      e.stopPropagation();
      openMapDrawerForHotel(row);
    });
    el.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      openMapDrawerForHotel(row);
    });
    
    const marker = new window.maplibregl.Marker({ element: el, anchor: "center", offset: [0, 0] })
      .setLngLat([Number(row.longitude), Number(row.latitude)])
      .addTo(map);
      
    list.push(marker);
  });
  
  activeMarkers.set(mapId, list);
}

async function renderRevenuePanel() {
  if (!$("#revenue")?.classList.contains("is-visible")) return;
  const targetId = state.activeTargetId;
  const setText = (sel, val) => { const el = $(sel); if (el) el.textContent = val; };
  if (!targetId) {
    $("#revenueOpportunitiesRows").innerHTML = `<tr><td colspan="5">${empty("Selecciona un mercado para ver análisis de revenue.")}</td></tr>`;
    $("#pickupAnalysisStack").innerHTML = empty("Sin datos.");
    $("#stabilityIndexRows").innerHTML = `<tr><td colspan="5">${empty("Sin datos.")}</td></tr>`;
    ["#revOppsCount", "#revPickup", "#revVol", "#revCons"].forEach((sel) => setText(sel, "—"));
    return;
  }

  try {
    const [opps, pickup, demand, stability] = await Promise.all([
      api(`/api/analytics/revenue-opportunities?targetId=${targetId}`),
      api(`/api/analytics/pickup?targetId=${targetId}`),
      api(`/api/analytics/demand-curve?targetId=${targetId}`),
      api(`/api/analytics/competitive-stability?targetId=${targetId}`)
    ]);

    const oppRows = opps.opportunities || [];
    const pickupList = pickup.pickup || [];
    const stabList = stability.stability || [];

    // KPIs — computed from real analytics data (no fabricated values)
    const up = pickupList.filter((p) => (p.pickupPct ?? 0) > 0).length;
    const down = pickupList.filter((p) => (p.pickupPct ?? 0) < 0).length;
    const avgVol = stabList.length ? stabList.reduce((s, r) => s + (r.stddevPricePerNight || 0), 0) / stabList.length : null;
    const avgCons = stabList.length ? stabList.reduce((s, r) => s + (r.consistencyScore || 0), 0) / stabList.length : null;
    setText("#revOppsCount", String(oppRows.length));
    setText("#revPickup", pickupList.length ? `${up}↑ / ${down}↓` : "—");
    setText("#revVol", avgVol != null ? currency(avgVol) : "—");
    setText("#revCons", avgCons != null ? number(avgCons, 0) : "—");

    // 1. Opportunities — model: hotelName, type, title, message, severity, score, currentAdr, marketAdr
    const oppsTable = $("#revenueOpportunitiesRows");
    if (oppsTable) {
      oppsTable.innerHTML = oppRows.length
        ? oppRows.map((row) => {
            const name = row.hotelName || "Mercado";
            const isRiu = String(name).toLowerCase().includes("riu");
            const gapPct = (row.currentAdr != null && row.marketAdr) ? ((row.currentAdr - row.marketAdr) / row.marketAdr) * 100 : null;
            const gapCls = gapPct == null ? "neutral" : gapPct >= 0 ? "high" : "low";
            const sevCls = row.severity === "critical" ? "high" : row.severity === "warning" ? "neutral" : "low";
            return `<tr class="${isRiu ? 'riu-row' : ''}">
              <td><strong>${isRiu ? '<span class="riu-tag">RIU</span>' : ''}${escapeHtml(name)}</strong></td>
              <td><span class="badge ${sevCls}">${escapeHtml(row.title || row.type || "—")}</span></td>
              <td>${gapPct == null ? "—" : `<span class="badge ${gapCls}">${pct(gapPct)}</span>`}</td>
              <td><strong>${number(row.score ?? 0, 0)}</strong></td>
              <td>${escapeHtml(row.message || "")}</td>
            </tr>`;
          }).join("")
        : `<tr><td colspan="5">${empty("No hay oportunidades de tarifa detectadas en este mercado.")}</td></tr>`;
    }

    // 2. Pickup — model: hotelName, checkIn, pickupAbsolute (Δ€), pickupPct
    const pickupStack = $("#pickupAnalysisStack");
    if (pickupStack) {
      pickupStack.innerHTML = pickupList.length
        ? pickupList.map((item) => {
            const pctVal = item.pickupPct ?? 0;
            const tone = pctVal > 0 ? "warning" : "info";
            return `<article class="insight ${tone}">
              <strong>${escapeHtml(item.hotelName || "Hotel")}</strong>
              <p>Check-in: ${item.checkIn || "-"} · Δ tarifa: <strong>${currency(item.pickupAbsolute)}</strong> (${pct(pctVal)} vs ant.)</p>
            </article>`;
          }).join("")
        : empty("Sin pickup reciente (requiere ≥2 capturas del mismo mercado).");
    }

    // 3. Competitive stability — model: hotelName, avgPricePerNight, stddevPricePerNight, positioningLabel, consistencyScore (0–100)
    const stabTable = $("#stabilityIndexRows");
    if (stabTable) {
      stabTable.innerHTML = stabList.length
        ? stabList.map((row) => {
            const isRiu = String(row.hotelName).toLowerCase().includes("riu");
            const posCls = /premium/i.test(row.positioningLabel || "") ? "high" : /descuento/i.test(row.positioningLabel || "") ? "low" : "neutral";
            return `<tr class="${isRiu ? 'riu-row' : ''}">
              <td><strong>${isRiu ? '<span class="riu-tag">RIU</span>' : ''}${escapeHtml(row.hotelName)}</strong></td>
              <td>${currency(row.avgPricePerNight)}</td>
              <td>± ${currency(row.stddevPricePerNight)}</td>
              <td><span class="badge ${posCls}">${escapeHtml(row.positioningLabel || "—")}</span></td>
              <td><strong>${number(row.consistencyScore ?? 0, 0)}</strong></td>
            </tr>`;
          }).join("")
        : `<tr><td colspan="5">${empty("Sin datos de estabilidad (requiere ≥2 capturas del mismo mercado).")}</td></tr>`;
    }

    // 4. Demand curve
    renderDemandCurveChart(demand.demandCurve || []);

  } catch (error) {
    setStatus("Error cargando panel de Revenue: " + readableError(error), "error");
  }
}

function renderDemandCurveChart(data) {
  const canvas = document.getElementById("demandCurveCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  // Simple Canvas line drawing for demand curve to keep it high-performance and dependency-free
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  canvas.width = width;
  canvas.height = height;

  ctx.clearRect(0, 0, width, height);

  if (!data || !data.length) {
    ctx.fillStyle = "rgba(255, 255, 255, 0.3)";
    ctx.font = "12px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Sin datos de curva de demanda históricos", width / 2, height / 2);
    return;
  }

  // Draw grid
  ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
  ctx.lineWidth = 1;
  for (let i = 1; i < 4; i++) {
    const y = (height / 4) * i;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }

  // Draw line — Canvas 2D cannot resolve CSS vars, use the literal amber.
  const AMBER = "#ff9f0a";
  const prices = data.map(d => d.avgAdr || 0);
  const minP = Math.min(...prices);
  const maxP = Math.max(...prices);
  const range = (maxP - minP) || 1;
  const denom = data.length > 1 ? data.length - 1 : 1;

  ctx.beginPath();
  ctx.strokeStyle = AMBER;
  ctx.lineWidth = 3;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  data.forEach((d, idx) => {
    const x = (width / denom) * idx;
    const y = height - 20 - ((d.avgAdr - minP) / range) * (height - 40);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Draw dots
  data.forEach((d, idx) => {
    const x = (width / denom) * idx;
    const y = height - 20 - ((d.avgAdr - minP) / range) * (height - 40);
    ctx.beginPath();
    ctx.fillStyle = AMBER;
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();

    // label first and last
    if (idx === 0 || idx === data.length - 1) {
      ctx.fillStyle = "#fff";
      ctx.font = "9px monospace";
      ctx.fillText(currency(d.avgAdr), x - 15, y - 8);
    }
  });
}

