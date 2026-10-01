/* ============================================================================
   Atlas · Rate Intelligence — lógica de interfaz (vanilla JS, sin dependencias)
   Consume los endpoints reales /api/* del backend Flask.
   La CSP prohíbe scripts inline: todo el comportamiento vive aquí.
   ============================================================================ */
'use strict';

/* ------------------------------------------------------------------ utils */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const NBSP = ' ';
function nEs(x, dec = 0) {
  if (x === null || x === undefined || Number.isNaN(Number(x))) return '—';
  return Number(x).toLocaleString('es-ES', { minimumFractionDigits: dec, maximumFractionDigits: dec });
}
const money = (value, currency) => value == null ? '—' : `${nEs(value)} ${esc(currency || 'moneda desconocida')}`;
const eur = (x, dec = 0) => (x === null || x === undefined ? '—' : `${nEs(x, dec)}${NBSP}€`);
function signPct(x, dec = 1) {
  if (x === null || x === undefined || Number.isNaN(Number(x))) return '—';
  const v = Number(x);
  const s = v > 0 ? '+' : v < 0 ? '−' : '';
  return `${s}${nEs(Math.abs(v), dec)}%`;
}
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
function normalizeText(value) { return String(value ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase(); }

function hotelComparisonSignature(row) {
  const normalise = (value) => value == null ? '' : String(value).trim().toLowerCase();
  const fields = [normalise(row.hotelKey), normalise(row.checkIn), normalise(row.checkOut),
    row.nights, row.pax, normalise(row.roomType), normalise(row.board), normalise(row.currency),
    row.freeCancellation == null ? null : Boolean(row.freeCancellation)];
  const nights = (Date.parse(row.checkOut) - Date.parse(row.checkIn)) / 86400000;
  const price = row.pricePerNight ?? (row.price == null ? NaN : row.price / nights);
  if (fields.some((value) => value == null || value === '') || !Number.isFinite(nights) ||
      nights <= 0 || nights !== row.nights || row.pax <= 0 || !Number.isFinite(price) || price <= 0) return null;
  return JSON.stringify(fields);
}

function uniqueHotelProducts(rows) {
  const products = new Map(), duplicates = new Set();
  for (const row of rows) {
    const key = hotelComparisonSignature(row);
    if (key == null) continue;
    if (products.has(key)) duplicates.add(key);
    products.set(key, row);
  }
  for (const key of duplicates) products.delete(key);
  return products;
}

async function api(path, opts) {
  const requestOpts = Object.assign({}, opts);
  if (!(requestOpts.body instanceof FormData)) requestOpts.headers = Object.assign({ 'Content-Type': 'application/json' }, requestOpts.headers || {});
  const res = await fetch(path, requestOpts);
  let body = null;
  try { body = await res.json(); } catch (_) { /* noop */ }
  if (!res.ok) {
    const msg = (body && body.error) || `Error ${res.status}`;
    const err = new Error(msg); err.status = res.status; err.body = body; throw err;
  }
  return body;
}

function median(arr) {
  if (!arr.length) return 0;
  const s = [...arr].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}
function percentileVal(arr, p) {
  if (!arr.length) return 0;
  const s = [...arr].sort((a, b) => a - b);
  const idx = (p / 100) * (s.length - 1);
  const lo = Math.floor(idx), hi = Math.ceil(idx);
  return s[lo] + (s[hi] - s[lo]) * (idx - lo);
}

/* count-up on [data-count] integers */
function runCounters(root) {
  const nodes = $$('[data-count]', root).map((n) => ({ n, target: Number(n.getAttribute('data-count')) }));
  if (!nodes.length) return;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce) { nodes.forEach(({ n, target }) => (n.textContent = nEs(target))); return; }
  nodes.forEach(({ n }) => (n.textContent = '0'));
  const t0 = performance.now(), dur = 900;
  const step = (t) => {
    const k = Math.min(1, (t - t0) / dur);
    const e = 1 - Math.pow(1 - k, 3);
    nodes.forEach(({ n, target }) => (n.textContent = nEs(Math.round(target * e))));
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/* --------------------------------------------------------------- charts */

/* Línea simple (tendencia) */
function lineSVG(points, opts = {}) {
  const vals = points.map((p) => p.v).filter((v) => v > 0);
  if (vals.length < 2) return emptyChart(150);
  const min = Math.min(...vals), max = Math.max(...vals);
  const W = 400, H = 150, x0 = 40, x1 = 392, y0 = 20, y1 = 122;
  const sx = (i) => x0 + (i / (points.length - 1)) * (x1 - x0);
  const sy = (v) => y0 + (max > min ? (1 - (v - min) / (max - min)) : 0.5) * (y1 - y0);
  let d = '';
  points.forEach((p, i) => { d += `${i ? 'L' : 'M'} ${sx(i).toFixed(1)} ${sy(p.v).toFixed(1)} `; });
  const last = points[points.length - 1];
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" height="${H}" class="svg-block">
    <g stroke="var(--line-soft)" stroke-width="1"><line x1="${x0}" y1="${y0}" x2="${x1}" y2="${y0}"></line><line x1="${x0}" y1="71" x2="${x1}" y2="71"></line><line x1="${x0}" y1="${y1}" x2="${x1}" y2="${y1}"></line></g>
    <g font-family="'Space Mono',monospace" font-size="9" fill="var(--fainter)"><text x="${x0 - 6}" y="23" text-anchor="end">${nEs(max)}</text><text x="${x0 - 6}" y="${y1 + 3}" text-anchor="end">${nEs(min)}</text></g>
    <path d="${d.trim()}" fill="none" stroke="var(--ac)" stroke-width="2.2" stroke-linecap="round" stroke-dasharray="1400" style="animation:atDraw 1200ms cubic-bezier(.22,1,.36,1) 200ms both;"></path>
    <g style="animation:atPop 380ms cubic-bezier(.22,1,.36,1) 1100ms both; transform-origin:center;"><circle cx="${sx(points.length - 1).toFixed(1)}" cy="${sy(last.v).toFixed(1)}" r="4" fill="var(--ac)"></circle></g>
  </svg>`;
}

function emptyChart(h) {
  return `<div class="empty" style="height:${h}px; display:flex; align-items:center; justify-content:center;">Sin datos suficientes para dibujar este gráfico.</div>`;
}

/* >>> hoja-de-mercado:logica — funciones puras (sin DOM ni State), probadas en tests/hotel-sheet.test.cjs */
const SHEET_VIEWS = [
  { id: 'market', label: 'Mercado', test: () => true },
  { id: 'high', label: 'Tarifa alta', hint: '≥ +30 % vs mediana', test: (h) => h.vsMedian != null && h.vsMedian >= 30 },
  { id: 'flexible', label: 'Cancelación flexible', test: (h) => h.cancel === true },
  { id: 'scarcity', label: 'Escasez', test: (h) => h.scarcity },
  { id: 'unstable', label: 'Menos estables', hint: 'estabilidad < 90', test: (h) => h.stab != null && h.stab < 90 },
];
const SHEET_CHIPS = [
  { id: 'adults', label: 'Adults only', test: (h) => h.adultsOnly },
  { id: 'moved', label: 'Con movimiento', test: (h) => h.delta != null && h.delta !== 0 },
  { id: 'new', label: 'Nuevos', test: (h) => h.isNew },
];
const SHEET_GROUPS = [
  { id: 'none', label: 'Sin agrupar' }, { id: 'chain', label: 'Cadena' }, { id: 'zone', label: 'Zona' },
  { id: 'segment', label: 'Segmento' }, { id: 'tier', label: 'Tramo de precio' },
];
const SHEET_SORT_KEYS = ['name', 'adr', 'pers', 'vs', 'delta', 'stab', 'nota', 'reviews', 'cancel', 'avail'];
const SHEET_TIER_ORDER = ['high', 'mid', 'low', 'none'];

/* Cupo a este precio: devuelve el texto y el tono (bad | warn | plain | none). */
function hotelStockInfo(row) {
  if (row.observationStatus === 'parse_error') return { text: 'Precio no interpretable', tone: 'bad' };
  if (row.observationStatus === 'closed' || row.closed) return { text: 'Hotel cerrado', tone: 'plain' };
  if (row.soldOut) return { text: 'Sin disponibilidad', tone: 'bad' };
  if (row.observationStatus === 'unknown' && row.price == null) return { text: 'No confirmada', tone: 'none' };
  const n = row.unitsLeft;
  if (n == null) return { text: '—', tone: 'none' };
  if (n <= 0) return { text: 'Sin disponibilidad', tone: 'bad' };
  if (n === 1) return { text: 'Queda 1', tone: 'bad' };
  return { text: `Quedan ${n}`, tone: 'warn' }; // Booking solo publica «quedan N» cuando el cupo es escaso
}

/* Etiqueta canónica de zona: las variantes sin acento o con otras mayúsculas se unen en la más frecuente. */
function hotelZoneLabels(rows) {
  const variants = new Map();
  rows.forEach((row) => {
    const label = String(row.city || row.popularDistrict || row.displayLocation || '').trim();
    if (!label) return;
    const key = normalizeText(label);
    if (!variants.has(key)) variants.set(key, new Map());
    variants.get(key).set(label, (variants.get(key).get(label) || 0) + 1);
  });
  const labels = new Map();
  variants.forEach((counts, key) => {
    const best = [...counts.entries()].sort((a, b) => b[1] - a[1] || Number(/[^\u0000-\u007f]/.test(b[0])) - Number(/[^\u0000-\u007f]/.test(a[0])) || a[0].localeCompare(b[0], 'es'))[0][0];
    labels.set(key, best);
  });
  return labels;
}

function hotelSheetModel(rows, metrics, stabilityRows) {
  rows = rows || [];
  const prices = rows.map((r) => Number(r.pricePerNight)).filter((p) => p > 0);
  const marketMedian = metrics && metrics.market && Number(metrics.market.medianPricePerNight) > 0 ? Number(metrics.market.medianPricePerNight) : median(prices);
  const rsi = (metrics && metrics.rateShoppingIndex) || {};
  const p25 = Number(rsi.bottomQuartileThreshold) > 0 ? Number(rsi.bottomQuartileThreshold) : percentileVal(prices, 25);
  const p75 = Number(rsi.topQuartileThreshold) > 0 ? Number(rsi.topQuartileThreshold) : percentileVal(prices, 75);
  const changeByKey = new Map(((metrics && metrics.competitiveSet) || []).filter((h) => h.priceChangePct != null).map((h) => [h.hotelKey, Number(h.priceChangePct)]));
  const newKeys = new Set(((metrics && metrics.newEntrants) || []).map((h) => h.hotelKey));
  const stabilityByKey = new Map();
  (stabilityRows || []).forEach((entry) => {
    const score = Math.round(Number(entry.consistencyScore)); // se muestra entero: la clasificación usa el mismo valor que ve el usuario
    if (!Number.isFinite(score)) return;
    const current = stabilityByKey.get(entry.hotelKey);
    if (!current || Number(entry.observations || 0) > Number(current.observations || 0)) stabilityByKey.set(entry.hotelKey, { score, observations: entry.observations });
  });
  const zoneLabels = hotelZoneLabels(rows);
  const hotels = rows.map((r, i) => {
    const adr = Number(r.pricePerNight) > 0 ? Number(r.pricePerNight) : null;
    const zoneKey = normalizeText(r.city || r.popularDistrict || r.displayLocation || '');
    const zone = zoneLabels.get(zoneKey) || '';
    const units = r.unitsLeft == null ? null : Number(r.unitsLeft);
    const stability = stabilityByKey.get(r.hotelKey);
    const delta = changeByKey.has(r.hotelKey) ? changeByKey.get(r.hotelKey) : null;
    const stock = hotelStockInfo(r);
    return {
      idx: i, key: r.hotelKey, name: r.hotelName || '', chain: r.chain || null, adultsOnly: Boolean(r.adultsOnly),
      zone, zoneKey, adr, pers: Number(r.pricePerPersonPerNight) > 0 ? Number(r.pricePerPersonPerNight) : null,
      vsMedian: adr != null && marketMedian > 0 ? (adr / marketMedian - 1) * 100 : null,
      delta, isNew: newKeys.has(r.hotelKey), prevAdr: adr != null && delta != null ? adr / (1 + delta / 100) : null,
      stab: stability ? stability.score : null, stabObs: stability ? stability.observations : null,
      nota: r.rating == null ? null : Number(r.rating), reviews: r.reviewCount == null ? null : Number(r.reviewCount),
      cancel: r.freeCancellation === true ? true : r.freeCancellation === false ? false : null,
      units, soldOut: Boolean(r.soldOut), stock, scarcity: Boolean(r.soldOut) || (units != null && units > 0),
      tier: adr == null ? 'none' : adr >= p75 ? 'high' : adr < p25 ? 'low' : 'mid',
      rank: 0, row: r,
      search: normalizeText([r.hotelName, r.chain, zone].filter(Boolean).join(' ')),
    };
  });
  [...hotels].sort((a, b) => (b.adr ?? -1) - (a.adr ?? -1)).forEach((h, i) => { h.rank = i + 1; });
  return { hotels, median: marketMedian, p25, p75, minAdr: prices.length ? Math.min(...prices) : null, maxAdr: prices.length ? Math.max(...prices) : null, zoneLabels };
}

function hotelSheetFilter(model, query) {
  const view = SHEET_VIEWS.find((v) => v.id === query.view) || SHEET_VIEWS[0];
  const chips = (query.chips || []).map((id) => SHEET_CHIPS.find((c) => c.id === id)).filter(Boolean);
  const needle = normalizeText(String(query.search || '')).trim();
  return model.hotels.filter((h) => view.test(h) && chips.every((c) => c.test(h)) && (!needle || h.search.includes(needle)));
}

function hotelSheetSortValue(h, key) {
  switch (key) {
    case 'name': return h.name;
    case 'adr': return h.adr;
    case 'pers': return h.pers;
    case 'vs': return h.vsMedian;
    case 'delta': return h.delta;
    case 'stab': return h.stab;
    case 'nota': return h.nota;
    case 'reviews': return h.reviews;
    case 'cancel': return h.cancel == null ? null : Number(h.cancel);
    case 'avail': return h.soldOut ? 0 : h.units; // menos cupo primero en ascendente; sin dato siempre al final
    default: return h.adr;
  }
}

/* Los valores vacíos van siempre al final, sea cual sea el sentido; el empate se resuelve por ADR y nombre. */
function hotelSheetSort(list, sort) {
  const key = SHEET_SORT_KEYS.includes(sort && sort.key) ? sort.key : 'adr';
  const dir = sort && sort.dir === 1 ? 1 : -1;
  return [...list].sort((a, b) => {
    const x = hotelSheetSortValue(a, key), y = hotelSheetSortValue(b, key);
    if (x == null && y != null) return 1;
    if (y == null && x != null) return -1;
    if (x != null && y != null && x !== y) return (typeof x === 'string' ? x.localeCompare(y, 'es', { sensitivity: 'base' }) : x - y) * dir;
    return (b.adr ?? -1) - (a.adr ?? -1) || a.name.localeCompare(b.name, 'es', { sensitivity: 'base' });
  });
}

function hotelSheetTierLabel(id, model) {
  if (id === 'high') return `Alto · más de ${eur(model.p75)}`;
  if (id === 'low') return `Bajo · menos de ${eur(model.p25)}`;
  if (id === 'mid') return `Central · ${nEs(model.p25)}–${eur(model.p75)}`;
  return 'Sin precio';
}

/* Agrupa una lista ya filtrada y ordenada. Devuelve null cuando no se agrupa. */
function hotelSheetGroups(list, group, model) {
  if (!group || group === 'none') return null;
  const buckets = new Map();
  const place = (id, label, last, h) => {
    if (!buckets.has(id)) buckets.set(id, { id, label, last, hotels: [] });
    buckets.get(id).hotels.push(h);
  };
  list.forEach((h) => {
    if (group === 'chain') h.chain ? place(`c:${h.chain}`, h.chain, false, h) : place('c:', 'Sin cadena reconocida', true, h);
    else if (group === 'zone') h.zone ? place(`z:${h.zoneKey}`, h.zone, false, h) : place('z:', 'Sin zona', true, h);
    else if (group === 'segment') h.adultsOnly ? place('s:adults', 'Adults only', false, h) : place('s:other', 'Familiar y mixto', false, h);
    else if (group === 'tier') place(`t:${h.tier}`, hotelSheetTierLabel(h.tier, model), false, h);
  });
  const groups = [...buckets.values()].map((g) => ({ ...g, median: median(g.hotels.map((h) => h.adr).filter((v) => v != null)) }));
  if (group === 'tier') return groups.sort((a, b) => SHEET_TIER_ORDER.indexOf(a.id.slice(2)) - SHEET_TIER_ORDER.indexOf(b.id.slice(2)));
  return groups.sort((a, b) => Number(a.last) - Number(b.last) || b.hotels.length - a.hotels.length || a.label.localeCompare(b.label, 'es', { sensitivity: 'base' }));
}

/* CSV para hojas de cálculo en español: separador «;», BOM UTF-8, decimales con coma y texto citado. */
function hotelSheetCsv(list) {
  const safe = (value) => { const text = String(value ?? ''); return /^[=+\-@\t\r]/.test(text) ? `'${text}` : text; };
  const quote = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`;
  const num = (value, decimals) => (value == null || !Number.isFinite(Number(value)) ? '' : Number(value).toFixed(decimals).replace('.', ','));
  const head = ['Hotel', 'Cadena', 'Zona', 'ADR hab (€)', 'ADR pers (€)', 'Δ foto (%)', 'vs mediana (%)', 'Estabilidad', 'Nota', 'Reseñas', 'Cancelación gratis', 'Disponibilidad'];
  const lines = list.map((h) => [
    safe(h.name), safe(h.chain || ''), safe(h.zone), num(h.adr, 2), num(h.pers, 2), num(h.delta, 1), num(h.vsMedian, 1), num(h.stab, 0), num(h.nota, 1),
    h.reviews == null ? '' : String(h.reviews), h.cancel === true ? 'Sí' : h.cancel === false ? 'No' : '', h.stock.tone === 'none' ? '' : h.stock.text,
  ]);
  return `﻿${[head, ...lines].map((cells) => cells.map(quote).join(';')).join('\r\n')}`;
}
/* <<< hoja-de-mercado:logica */

/* >>> panel-bi:logica — funciones puras del panel de análisis (sin DOM ni State), probadas en tests/hotel-bi.test.cjs */
const BI_HORIZONS = [14, 30, 60, 90];
const BI_TARGET = { min: 25, max: 90, step: 5, initial: 60 };
const BI_MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];
const BI_WEEKDAYS = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'];
const BI_MAP_COLORS = { low: '#1f7a52', mid: '#c98a1e', high: '#b94f50', closed: '#8b91a3' };
const BI_CLOSURE_WINDOW = 14; // «Cierres»: dos o más fechas cerradas en los próximos 14 días

/* Cuantil con interpolación lineal (el mismo método que el backend). */
function biQuantile(values, q) {
  const data = (values || []).filter((v) => v != null && Number.isFinite(Number(v))).map(Number).sort((a, b) => a - b);
  if (!data.length) return null;
  const pos = (data.length - 1) * q, lo = Math.floor(pos), hi = Math.ceil(pos);
  return data[lo] + (data[hi] - data[lo]) * (pos - lo);
}

function biDate(iso) { const [y, m, d] = String(iso).slice(0, 10).split('-').map(Number); return new Date(Date.UTC(y, m - 1, d)); }
function biDayLabel(iso) { const s = String(iso || ''); return s.length >= 10 ? `${s.slice(8, 10)}/${s.slice(5, 7)}` : '—'; }
function biDayLong(iso) { return iso ? `${BI_WEEKDAYS[biDate(iso).getUTCDay()]} ${biDayLabel(iso)}` : '—'; }
function biDaysBetween(fromIso, toIso) { return Math.round((biDate(toIso) - biDate(fromIso)) / 86400000); }
function biSigned(value, decimals = 1) {
  if (value == null || !Number.isFinite(Number(value))) return '—';
  const v = Number(value);
  return `${v > 0 ? '+' : v < 0 ? '−' : ''}${nEs(Math.abs(v), decimals)}`;
}

/* Value score (README §3B): clamp(0, 100, round(50 + (nota − medianaNota) × 22 − (precio / mediana − 1) × 60)). */
function biValueScore(nota, price, dayMedian, medianNota) {
  if (nota == null || medianNota == null || !(price > 0) || !(dayMedian > 0)) return null;
  return Math.max(0, Math.min(100, Math.round(50 + (Number(nota) - Number(medianNota)) * 22 - (Number(price) / Number(dayMedian) - 1) * 60)));
}

/* Celda de calor: alfa proporcional a la desviación frente a la mediana del día, máximo 0,6. */
function biHeat(price, dayMedian) {
  if (!(price > 0) || !(dayMedian > 0)) return null;
  const r = price / dayMedian - 1;
  if (Math.abs(r) < 0.05) return { bg: 'var(--line-soft)', r };
  const a = Math.min(0.6, 0.14 + Math.abs(r) * 0.9).toFixed(2);
  return { bg: r < 0 ? `rgba(31,122,82,${a})` : `rgba(185,79,80,${a})`, r };
}

/* Semáforo del mapa de precios: ≤ −15 % verde, en la mediana ámbar, ≥ +15 % rojo; cerrado gris. */
function biMapTone(price, dayMedian) {
  if (!(price > 0) || !(dayMedian > 0)) return 'closed';
  const r = price / dayMedian;
  return r <= 0.85 ? 'low' : r < 1.15 ? 'mid' : 'high';
}

function biPinSize(reviews) { return Math.round(Math.min(24, 10 + Math.sqrt(Math.max(0, Number(reviews) || 0)) / 5)); }
function biDotSize(reviews) { return Math.round(Math.min(22, 8 + Math.sqrt(Math.max(0, Number(reviews) || 0)) / 5)); }

/* Cabecera del calendario: con ≤ 30 días el número de día; con más, el mes el día 1 (y en la primera
   columna) y el número de los lunes salvo que caigan a 2 días o menos de un cambio de mes. */
function biCalendarHead(dates) {
  const H = dates.length;
  return dates.map((iso, i) => {
    const d = biDate(iso);
    const day = d.getUTCDate();
    const first = day === 1 || i === 0;
    if (H <= 30) return { text: String(day), month: first };
    const near = [-2, -1, 1, 2].some((k) => i + k >= 0 && i + k < H && biDate(dates[i + k]).getUTCDate() === 1);
    if (first) return { text: BI_MONTHS[d.getUTCMonth()].toUpperCase(), month: true };
    if (d.getUTCDay() === 1 && !near) return { text: String(day), month: false };
    return { text: '', month: false };
  });
}

/* Puesto de un hotel en una fecha: 1 = el más caro, como en el prototipo. */
function biRankAt(hotels, key, index) {
  const priced = hotels.filter((h) => h.prices[index] != null).sort((a, b) => b.prices[index] - a.prices[index]);
  const position = priced.findIndex((h) => h.key === key);
  return position < 0 ? null : { rank: position + 1, of: priced.length };
}

/* Tarifa sugerida (README §3B): suma de seis componentes en euros sobre la mediana del día. */
function biRecommendation({ openPrices, dayMedian, targetPct, valueScore, closed, low, scopeSize, deltas, leadDays }) {
  if (!(dayMedian > 0) || !openPrices.length) return null;
  const M = dayMedian;
  const Pt = biQuantile(openPrices, targetPct / 100);
  const vs = valueScore == null ? 50 : valueScore;
  const closedShare = (closed + low * 0.5) / Math.max(1, scopeSize);
  const movement = deltas.reduce((sum, d) => sum + (Number(d) || 0), 0) / Math.max(1, scopeSize) / 100;
  const leadFactor = leadDays < 21 ? 0.03 : leadDays > 60 ? -0.02 : 0;
  const parts = [
    { id: 'median', value: M, base: true, n: openPrices.length },
    { id: 'target', value: Pt - M, pct: targetPct, price: Pt },
    { id: 'value', value: ((vs - 50) / 50) * 0.05 * M, score: vs },
    { id: 'scarcity', value: Math.min(0.08, closedShare * 0.35) * M, closed, low },
    { id: 'movement', value: movement * M, movement: movement * 100 },
    { id: 'lead', value: leadFactor * M, lead: leadDays },
  ];
  return { parts, suggested: Math.round(parts.reduce((sum, p) => sum + p.value, 0)) };
}

/* Semanas del horizonte con la proporción de celdas cerradas y con cupo bajo. Solo cuentan las
   celdas observadas (abiertas, cupo bajo o cerradas): una semana sin captura queda sin dato. */
function biWeeks(dates, hotels) {
  const weeks = [];
  for (let start = 0; start < dates.length; start += 7) {
    let closed = 0, low = 0, total = 0;
    for (let i = start; i < Math.min(dates.length, start + 7); i++) {
      hotels.forEach((h) => {
        const s = h.status[i];
        if (s === 'closed') { closed++; total++; } else if (s === 'low') { low++; total++; } else if (s === 'ok') total++;
      });
    }
    weeks.push({ start: dates[start], closed, low, total });
  }
  return weeks;
}

/* Alertas de competidores ordenadas por relevancia (peso del prototipo). */
function biAlerts(hotels) {
  const list = [];
  hotels.forEach((h) => {
    if (h.isNew) list.push({ type: 'mov', tag: 'Nuevo', tone: 'ac', key: h.key, name: h.name, text: `Entra en el set con ${eur(h.adr)}`, value: eur(h.adr), weight: 50 });
    else if (h.delta != null && h.delta <= -3) list.push({ type: 'mov', tag: 'Bajada', tone: 'bad', key: h.key, name: h.name, text: `${eur(h.prevAdr)} → ${eur(h.adr)}`, value: `${biSigned(h.delta)} %`, weight: 80 + Math.abs(h.delta) });
    else if (h.delta != null && h.delta >= 5) list.push({ type: 'mov', tag: 'Subida', tone: 'good', key: h.key, name: h.name, text: `${eur(h.prevAdr)} → ${eur(h.adr)}`, value: `${biSigned(h.delta)} %`, weight: 60 + h.delta });
    if (h.latestUnits === 1) list.push({ type: 'disp', tag: 'Queda 1', tone: 'bad', key: h.key, name: h.name, text: 'Última unidad en la estancia capturada', value: eur(h.adr), weight: 70 });
    const closures = h.status.slice(0, BI_CLOSURE_WINDOW).filter((s) => s === 'closed').length;
    if (closures >= 2) list.push({ type: 'disp', tag: 'Cierres', tone: 'warn', key: h.key, name: h.name, text: `${closures} fechas cerradas en los próximos ${BI_CLOSURE_WINDOW} días`, value: `${closures} d`, weight: 40 + closures });
  });
  return list.sort((a, b) => b.weight - a.weight);
}
/* <<< panel-bi:logica */

/* ------------------------------------------------- preferencias de interfaz */
const PREFS = { theme: 'atlas.theme', density: 'atlas.density', sidebar: 'atlas.sidebar', view: 'atlas.view' };
const THEMES = ['claro', 'oscuro'];
const DENSITIES = ['compacta', 'equilibrada', 'espaciosa'];
const STALE_DATA_DAYS = 7; // un ciclo de captura semanal: a partir de ahí los datos se marcan como antiguos
const TOAST_MS = 3600;

function readPref(key, allowed, fallback) {
  try { const value = localStorage.getItem(key); return allowed.includes(value) ? value : fallback; } catch (_) { return fallback; }
}
function writePref(key, value) {
  try { localStorage.setItem(key, value); } catch (_) { /* las preferencias son opcionales */ }
}

/* --------------------------------------------------------------- estado */
const State = {
  view: 'dashboard',
  theme: 'claro',
  density: 'equilibrada',
  sidebarCollapsed: false,
  palette: { open: false, query: '', index: 0, items: [] },
  captureJob: null,          // { id, pct, targetId } mientras hay una captura en curso
  captureDialogParams: null, // parámetros mostrados en el diálogo de confirmación
  freshCaptureTargetId: null, // mercado que acaba de capturarse desde esta sesión
  lastExtractionAt: null,
  copilotPrompt: null,       // pregunta pendiente al saltar al Copilot desde otra vista
  overlayReturnFocus: null,
  copilotMode: 'auto',
  copilotHistoryOpen: (() => {
    try { const saved = localStorage.getItem('atlas:copilot:history-open'); return saved == null ? window.innerWidth >= 1440 : saved === '1'; } catch (_) { return window.innerWidth >= 1440; }
  })(),
  copilotSessionQuery: '',
  copilotSending: false,
  copilotSendingBySession: {},
  copilotActiveJobs: {},
  copilotPanel: null,
  copilotPanelFocusOrigin: null,
  copilotLastResult: null,
  copilotAttachments: [],
  targets: [],
  targetId: null,
  metrics: {},   // cache por targetId
  snapshots: {}, // cache por targetId
  demandCurves: {}, // cache por targetId
  hotelStability: {}, // cache por targetId
  photoHistories: {}, // cache por targetId
  captureHistories: {}, // cache por targetId; una extracción puede reunir varios cortes semanales
  photoDetails: {},
  dataPromises: {}, // peticiones compartidas para evitar duplicados concurrentes
  captureComparisonOpen: false,
  hotelPriceHistories: {},
  hotelPriceHistoryPromises: {},
  selectedPhotoId: null,
  captureHotelSearch: '',
  dashboardMap: null,
  dashboardMapMarkers: [],
  dashboardMapResizeObserver: null,
  dashboard: {                  // Dashboard: señales, ventana del mapa y su gráfica
    allSignals: false, sel: null, chart: 'hist', cmp: false, ptHover: null,
    model: null, photos: [], signals: [], previousSnapshotId: null, returnFocus: null,
  },
  biMap: null,
  flightMap: null,
  workspaceDraft: null,
  workspaceDraftTargetId: null,
  workspaceDirty: false,
  workspaceSaveError: '',
  workspaceHotelSelections: {},
  workspaceRevisions: {},
  workspaceSemanticData: {},
  copilotWorkspaceContext: null,
  mapLoader: null,
  hotelView: 'market',          // vista guardada de la hoja de mercado
  hotelChips: [],               // filtros combinables (Adults only, Con movimiento, Nuevos)
  hotelQueryTargetId: null,
  hotelSearch: '',
  hotelSort: { key: 'adr', dir: -1 },
  hotelGroup: 'none',
  hotelVariant: 'A',            // A: tabla; B: tabla + panel de detalle
  hotelExpanded: {},            // hotelKey → fila de tarifas por habitación desplegada
  hotelSelectedKey: null,       // hotel seleccionado en la variante B
  hotelPinnedKey: null,         // hotel fijado para comparar (variante B)
  hotelTab: 'bi',               // pestaña de Hoteles: panel de análisis (por defecto) u hoja de mercado
  bi: null,                     // panel de análisis: filtros, fecha activa, hotel propio y datos del calendario
  hotelSheet: null,             // modelo calculado de la hoja activa
  hotelRateDetails: {},
  hotelRateDetailPromises: {},
  reputation: {
    hotelKey: null,
    tab: 'profile',
    catalog: [],
    selectedKeys: new Set(),
    query: '',
    captureSettings: {google_maps: false, google_hotels: true, booking: true, maxReviews: '1000', unboundedReviews: false, budgetUsd: '', unitCostUsd: '', maxDecisions: '24'},
    reviewRequestId: 0,
    profile: null,
    reviews: null,
    reviewPage: 0,
    reviewFilters: { source: '', language: '', rating: '', topic: '', dateFrom: '', dateTo: '', query: '' },
    comparison: [],
    activeJobId: null,
    activeJobKind: null,
    job: null,
    noteReviewId: null,
    pendingEvidenceId: null,
  },
  air: null,
  airRuns: null,
  airComparison: null,
  flight: null,        // Vuelos: pestaña, ruta seleccionada, modo del mapa y desplegable de captura
  flightModel: null,
  flightMarkers: [],
  airOperations: {     // tabla «Operación aérea»: filtros, orden y página (paginada en el servidor)
    page: 1, query: '', segment: '', origin: '', airline: '', connection: '', sort: 'date-asc', requestId: 0, fullscreen: false,
  },
  sessions: [],
  activeSession: null,
  authRequired: false,
  authenticated: false,
  authBusy: false,
};

const VIEWS = ['dashboard', 'hotels', 'reputation', 'flights', 'copilot', 'workspace', 'captures'];
const LABELS = { dashboard: 'Dashboard', hotels: 'Hoteles', reputation: 'Reputación', flights: 'Vuelos', copilot: 'Copilot', workspace: 'Espacio de trabajo', captures: 'Capturas' };
function mount(view) { return $(`#view-${view}`); }
function activeTarget() { return State.targets.find((t) => t.id === State.targetId) || null; }

/* --------------------------------------------------------------- router */
function setView(view) {
  if (!VIEWS.includes(view)) view = 'dashboard';
  if (view !== 'flights' && State.airOperations.fullscreen) {
    State.airOperations.fullscreen = false;
    document.body.classList.remove('air-operations-fullscreen');
  }
  State.view = view;
  document.body.dataset.view = view;
  $('#crumbView').textContent = LABELS[view];
  $$('.view').forEach((s) => s.classList.toggle('is-visible', s.id === `view-${view}`));
  $$('.nav__item').forEach((b) => {
    const active = b.dataset.view === view;
    b.classList.toggle('is-active', active);
    if (active) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current');
  });
  writePref(PREFS.view, view);
  window.scrollTo(0, 0);
  const reputationQuery = view === 'reputation' && State.reputation.hotelKey
    ? `?hotelKey=${encodeURIComponent(State.reputation.hotelKey)}` : '';
  try { history.replaceState({ view }, '', `#${view}${reputationQuery}`); } catch (_) { /* noop */ }
  renderView(view);
}

async function renderView(view) {
  const fn = {
    dashboard: renderDashboard, hotels: renderHotels, flights: renderFlights,
    reputation: renderHotelReputation,
    copilot: renderCopilot, workspace: renderWorkspace, captures: renderCaptures,
  }[view];
  if (fn) await fn();
}

function skeleton(host, kind) {
  if (kind === 'dashboard') {
    host.innerHTML = `<div class="page sk-page" aria-busy="true"><div class="sk sk--title"></div><div class="grid grid--4">
      ${'<div class="sk" style="height:104px;"></div>'.repeat(4)}
    </div><div class="sk" style="height:520px;"></div></div>`;
  } else {
    host.innerHTML = `<div class="page sk-page" aria-busy="true"><div class="sk sk--title"></div><div class="sk" style="height:120px;"></div><div class="sk" style="height:320px;"></div></div>`;
  }
}

function renderNoActiveTarget(host, title, subtitle) {
  host.innerHTML = `<div class="page">${pageHead(title, subtitle, '')}<article class="card card--pad empty-state" aria-live="polite">
    <div class="card__kicker">Mercado activo</div>
    <h2>Configura un mercado para empezar</h2>
    <p>No hay ningún mercado disponible en esta base de datos. Cuando exista un mercado, aquí aparecerán sus capturas, métricas y comparativas.</p>
  </article></div>`;
}

/* datos con caché */
function cachedApi(cache, key, requestKey, path, force = false) {
  if (!force && Object.prototype.hasOwnProperty.call(cache, key)) return Promise.resolve(cache[key]);
  if (State.dataPromises[requestKey]) return State.dataPromises[requestKey];
  const promise = api(path)
    .then((payload) => {
      cache[key] = payload;
      return payload;
    })
    .finally(() => { delete State.dataPromises[requestKey]; });
  State.dataPromises[requestKey] = promise;
  return promise;
}

async function getMetrics(targetId, force) {
  return cachedApi(State.metrics, targetId, `metrics:${targetId}`, `/api/dashboard/metrics?targetId=${targetId}`, force);
}
async function getSnapshot(targetId, force) {
  return cachedApi(State.snapshots, targetId, `snapshot:${targetId}`, `/api/snapshots/latest?targetId=${targetId}`, force);
}
async function getDemandCurve(targetId, force = false) {
  return cachedApi(State.demandCurves, targetId, `demand:${targetId}`, `/api/analytics/demand-curve?targetId=${targetId}`, force);
}
async function getHotelStability(targetId, force = false) {
  return cachedApi(State.hotelStability, targetId, `stability:${targetId}`, `/api/analytics/competitive-stability?targetId=${targetId}&snapshots=10`, force);
}
async function getPhotoHistory(targetId, force = false) {
  return cachedApi(State.photoHistories, targetId, `photo-history:${targetId}`, `/api/photos/history?targetId=${targetId}&limit=40`, force);
}
async function getCaptureHistory(targetId, force = false) {
  return cachedApi(State.captureHistories, targetId, `capture-history:${targetId}`, `/api/captures/history?targetId=${targetId}&limit=40`, force);
}
async function getPhotoDetail(snapshotId, force = false) {
  return cachedApi(State.photoDetails, snapshotId, `photo-detail:${snapshotId}`, `/api/photos/${snapshotId}`, force);
}
async function getHotelPriceHistory(targetId, hotelKey, force = false) {
  if (!State.hotelPriceHistories[targetId]) State.hotelPriceHistories[targetId] = {};
  const cache = State.hotelPriceHistories[targetId];
  if (!force && cache[hotelKey]) return cache[hotelKey];
  const promiseKey = `${targetId}:${hotelKey}`;
  if (State.hotelPriceHistoryPromises[promiseKey]) return State.hotelPriceHistoryPromises[promiseKey];
  const promise = api(`/api/hotels/price-history?targetId=${targetId}&limit=100&hotelKey=${encodeURIComponent(hotelKey)}`)
    .then((payload) => {
      cache[hotelKey] = payload.history || [];
      return cache[hotelKey];
    })
    .finally(() => { delete State.hotelPriceHistoryPromises[promiseKey]; });
  State.hotelPriceHistoryPromises[promiseKey] = promise;
  return promise;
}

function adrHistorySVG(photos) {
  const rows = (photos || []).filter((photo) => photo.scrapedAt && Number(photo.avgPricePerNight)).map((photo) => ({
    date: new Date(photo.scrapedAt), avg: Number(photo.avgPricePerNight), capturedRows: photo.capturedRows || 0,
  })).filter((row) => !Number.isNaN(row.date.getTime())).sort((a, b) => a.date - b.date);
  rows.forEach((row, index) => { row.index = index + 1; });
  if (rows.length < 2) return emptyChart(230);
  const values = rows.map((row) => row.avg).filter((value) => Number.isFinite(value));
  const min = Math.floor(Math.min(...values) / 10) * 10;
  const max = Math.ceil(Math.max(...values) / 10) * 10;
  const W = 820, H = 238, x0 = 58, x1 = 798, y0 = 20, y1 = 180;
  const sx = (index) => x0 + (index / (rows.length - 1)) * (x1 - x0);
  const sy = (value) => y0 + (1 - (value - min) / (max - min || 1)) * (y1 - y0);
  const line = rows.map((row, index) => `${index ? 'L' : 'M'} ${sx(index).toFixed(1)} ${sy(row.avg).toFixed(1)}`).join(' ');
  const points = rows.map((row, index) => {
    const label = row.date.toLocaleDateString('es-ES', { day: '2-digit', month: 'short', timeZone: 'UTC' }).replace('.', '');
    const time = row.date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' });
    return `<circle cx="${sx(index).toFixed(1)}" cy="${sy(row.avg).toFixed(1)}" r="4.5" fill="var(--ac)"><title>Captura ${row.index} · ${label} ${time}: ADR medio ${eur(row.avg)} · ${row.capturedRows} hoteles</title></circle><text x="${sx(index).toFixed(1)}" y="207" text-anchor="middle">${row.index}</text>`;
  }).join('');
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" height="238" class="svg-block" role="img" aria-label="Evolución temporal del ADR por captura"><g stroke="var(--line-soft)" stroke-width="1"><line x1="${x0}" y1="${y0}" x2="${x1}" y2="${y0}"></line><line x1="${x0}" y1="${(y0 + y1) / 2}" x2="${x1}" y2="${(y0 + y1) / 2}"></line><line x1="${x0}" y1="${y1}" x2="${x1}" y2="${y1}"></line></g><g font-family="'Space Mono',monospace" font-size="9" fill="var(--fainter)"><text x="${x0 - 8}" y="${y0 + 3}" text-anchor="end">${eur(max)}</text><text x="${x0 - 8}" y="${y1 + 3}" text-anchor="end">${eur(min)}</text></g><path d="${line}" fill="none" stroke="var(--ac)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"></path><g>${points}</g></svg><div class="legend dashboard-history-legend"><span><i style="width:12px;height:2px;border-radius:0;background:var(--ac);"></i>ADR medio por captura · eje X = número de captura</span></div>`;
}

/* --------------------------------------------------------- head helpers */
function pageHead(title, subtitle, actionsHTML, stampHTML) {
  return `<div class="page-head">
    <div><h1>${esc(title)}</h1><p>${subtitle}</p></div>
    ${stampHTML ? `<div class="stamp">${stampHTML}</div>` : actionsHTML ? `<div class="actions">${actionsHTML}</div>` : ''}
  </div>`;
}
function fmtStamp(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
function boardTag(board) {
  return `<span class="tag">${esc(board || '—')}</span>`;
}
function availChip(row) {
  if (row.observationStatus === 'parse_error') return '<span class="chip chip--bad">Precio no interpretable</span>';
  if (row.observationStatus === 'closed') return '<span class="chip chip--neutral">Hotel cerrado</span>';
  if (row.observationStatus === 'unknown' && row.price == null) return '<span class="dim">Disponibilidad no confirmada</span>';
  if (row.soldOut) return '<span class="chip chip--bad">Sin disponibilidad</span>';
  const n = row.unitsLeft;
  if (n === null || n === undefined) return '<span class="dim">—</span>';
  if (n <= 1) return `<span class="chip chip--bad">Queda ${n}</span>`;
  if (n <= 3) return `<span class="chip chip--warn">Quedan ${n}</span>`;
  return `<span class="chip chip--good">Quedan ${n}</span>`;
}

/* =============================================================== MAPAS */
const MAP_STYLES = {
  claro: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
  oscuro: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
};
const MAP_LOAD_TIMEOUT_MS = 6000; // pasado este tiempo sin MapLibre se muestra el fondo rayado con el aviso
const MAP_FAILED_TEXT = 'mapa · MapLibre + CARTO';

function atlasMapStyle() { return MAP_STYLES[State.theme] || MAP_STYLES.claro; }

/* Cambia el mapa base de todos los mapas vivos. Los mapas con capas propias (rutas aéreas)
   las vuelven a añadir en su manejador `_atlasRestyle` cuando el estilo nuevo termina de cargar. */
function restyleMaps() {
  [State.dashboardMap, State.biMap, State.flightMap].filter(Boolean).forEach((map) => {
    try {
      map.setStyle(atlasMapStyle(), { diff: false });
      if (typeof map._atlasRestyle === 'function') map.once('style.load', map._atlasRestyle);
    } catch (_) { /* un mapa que se está destruyendo no bloquea el cambio de tema */ }
  });
}

function loadMapLibre() {
  if (window.maplibregl) return Promise.resolve(window.maplibregl);
  if (State.mapLoader) return State.mapLoader;
  State.mapLoader = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    const fail = () => { window.clearTimeout(timer); State.mapLoader = null; script.remove(); reject(new Error(MAP_FAILED_TEXT)); };
    const timer = window.setTimeout(fail, MAP_LOAD_TIMEOUT_MS);
    script.src = 'https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js';
    script.onload = () => { window.clearTimeout(timer); if (window.maplibregl) resolve(window.maplibregl); else fail(); };
    script.onerror = fail;
    document.head.appendChild(script);
  });
  return State.mapLoader;
}

/* Marca un marco de mapa como no disponible: fondo rayado y el aviso del README. */
function mapFrameStatus(frame, text) {
  if (!frame) return;
  frame.querySelector('.map-frame__status')?.remove();
  if (text == null) return;
  frame.insertAdjacentHTML('beforeend', `<div class="map-frame__status" role="status">${esc(text)}</div>`);
}

/* Crea un mapa CARTO con los controles del prototipo. Si el estilo no llega en ~6 s, avisa. */
function createAtlasMap(container, options) {
  const ml = window.maplibregl;
  const map = new ml.Map({ container, style: atlasMapStyle(), attributionControl: { compact: true }, ...options });
  map.scrollZoom.disable();
  map.addControl(new ml.NavigationControl({ showCompass: false }), 'top-left');
  const frame = container.closest('.map-frame');
  const timer = window.setTimeout(() => { if (!map._removed && !map.isStyleLoaded()) mapFrameStatus(frame, MAP_FAILED_TEXT); }, MAP_LOAD_TIMEOUT_MS);
  map.once('load', () => { window.clearTimeout(timer); mapFrameStatus(frame, null); });
  // Un listener propio sustituye al console.error por defecto de MapLibre: las peticiones canceladas al
  // destruir o recrear el mapa no son errores; si falla el estilo antes de cargar, se muestra el aviso.
  map.on('error', (event) => {
    if (event?.error?.name === 'AbortError') return;
    if (!map.isStyleLoaded()) mapFrameStatus(frame, MAP_FAILED_TEXT);
  });
  map.on('remove', () => { window.clearTimeout(timer); });
  return map;
}

/* Marcador sin `position` inline en su raíz: el contenido va en un hijo con position:relative (clase .map-pin). */
function mapPinElement(innerHTML) {
  const root = document.createElement('div');
  const pin = document.createElement('div');
  pin.className = 'map-pin';
  pin.innerHTML = innerHTML;
  root.appendChild(pin);
  return root;
}

function validLngLat(row) {
  const lat = Number(row?.latitude), lng = Number(row?.longitude);
  if (row?.latitude == null || row?.longitude == null || String(row.latitude).trim() === '' || String(row.longitude).trim() === '') return null;
  return Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180 ? [lng, lat] : null;
}

/* =============================================================== DASHBOARD */
const DASH_SIGNALS_SHOWN = 3;
const DASH_MAP_HEIGHT = 600;
const DASH_POPOVER_MAX = 680;
const DASH_OUTLIERS = 11;
const DASH_PRICE_TYPES = ['price_leader', 'protect_rate', 'aggressive_pricing', 'premium_opportunity'];
const DASH_SIGNAL_ICON = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M12 3v3M12 18v3M3 12h3M18 12h3M6 6l2 2M16 16l2 2M6 18l2-2M16 8l2-2"></path></svg>';

/* Señales del backend (insights) en el orden del prototipo: primero las que requieren atención. */
function dashboardSignalModel(insights, hotels) {
  const rank = { critical: 0, warning: 1, info: 2 };
  const names = new Set((hotels || []).map((h) => h.name));
  return (insights || []).slice().sort((a, b) => (rank[a.severity] ?? 3) - (rank[b.severity] ?? 3)).map((s) => {
    const attention = s.severity === 'critical' || s.severity === 'warning';
    const value = s.value != null && DASH_PRICE_TYPES.includes(s.type) ? eur(s.value)
      : s.changePct != null ? pctTxt(s.changePct, 1)
      : s.value != null ? nEs(s.value) : '';
    return { attention, level: attention ? 'Atención' : 'Lectura', value, title: s.title || 'Señal de mercado', text: s.message || '', hotel: s.hotelName && names.has(s.hotelName) ? s.hotelName : null };
  });
}

function dashboardSignalsHTML(signals) {
  const attention = signals.filter((s) => s.attention).length;
  const reading = signals.length - attention;
  const all = State.dashboard.allSignals;
  const shown = signals.slice(0, all ? signals.length : DASH_SIGNALS_SHOWN);
  const count = signals.length ? `${attention} ${attention === 1 ? 'requiere' : 'requieren'} atención · ${reading} de lectura` : 'Sin señales con la foto actual';
  const toggle = signals.length > DASH_SIGNALS_SHOWN
    ? `<button type="button" class="dash-signals__toggle" data-dash-signals aria-expanded="${all}" aria-controls="dashSignalsGrid">${all ? 'Ver menos' : `Ver las ${signals.length} señales`}</button>` : '';
  const cards = shown.map((s, i) => `<article class="dash-signal" style="animation-delay:${i * 60}ms">
      <div class="dash-signal__top"><span class="dash-signal__level${s.attention ? ' is-attention' : ''}">${s.level}</span>${s.value ? `<strong>${esc(s.value)}</strong>` : ''}</div>
      <strong class="dash-signal__title">${esc(s.title)}</strong>
      <p>${esc(s.text)}</p>
      <div class="dash-signal__actions">${s.hotel ? `<button type="button" class="dash-signal__open" data-dash-hotel="${esc(s.hotel)}">Ver hotel</button>` : ''}<button type="button" class="dash-signal__ask" data-dash-ask="${esc(`${s.title}: ${s.text} ¿Qué hago?`)}">Preguntar al Copilot →</button></div>
    </article>`).join('');
  return `<section class="dash-signals" id="dashSignals" aria-labelledby="dashSignalsTitle">
    <div class="dash-signals__head"><div class="dash-signals__title"><span class="dash-signals__icon">${DASH_SIGNAL_ICON}</span><strong id="dashSignalsTitle">Señales de hoy</strong><span class="dash-signals__count">${count}</span></div>${toggle}</div>
    ${signals.length ? `<div class="dash-signals__grid" id="dashSignalsGrid">${cards}</div>` : '<p class="dash-signals__empty">No hay señales calculadas con la captura actual.</p>'}
  </section>`;
}

/* Fotos del mercado ordenadas de la más antigua a la más reciente, solo con ADR válido. */
function dashboardPhotos(history) {
  return (history?.photos || []).filter((p) => p.scrapedAt && Number(p.avgPricePerNight) > 0 && Number.isFinite(Date.parse(p.scrapedAt)))
    .slice().sort((a, b) => Date.parse(a.scrapedAt) - Date.parse(b.scrapedAt) || Number(a.id) - Number(b.id));
}

function dashboardRange(values, padRatio, minPad) {
  const lo = Math.min(...values), hi = Math.max(...values);
  const pad = Math.max(minPad, (hi - lo) * padRatio);
  return { lo: lo - pad, hi: hi + pad };
}

function dashboardAdrCardHTML(medianAdr, photos) {
  let spark = '<div class="dash-spark__empty">Se necesitan dos fotos para la evolución</div>';
  if (photos.length >= 2) {
    const values = photos.map((p) => Number(p.avgPricePerNight));
    const { lo, hi } = dashboardRange(values, 0.25, 8);
    const pts = values.map((v, i) => `${((i / (values.length - 1)) * 300).toFixed(1)},${(90 - ((v - lo) / (hi - lo)) * 80).toFixed(1)}`).join(' ');
    spark = `<svg viewBox="0 0 300 90" preserveAspectRatio="none" role="img" aria-label="ADR medio de las ${photos.length} fotos del mercado"><polyline points="0,90 ${pts} 300,90" fill="var(--accent-soft)" stroke="none"></polyline><polyline points="${pts}" fill="none" stroke="var(--ac)" stroke-width="2" vector-effect="non-scaling-stroke" stroke-linejoin="round"></polyline></svg>`;
  }
  const axis = photos.length ? `<div class="dash-axis"><span>foto #${photos[0].id}</span><span>${photos.length} ${photos.length === 1 ? 'foto' : 'fotos'}</span><span>#${photos.at(-1).id}</span></div>` : '';
  return `<article class="dash-card dash-card--adr">
    <span class="card__kicker">ADR mediano</span>
    <div class="dash-big"><strong>${medianAdr > 0 ? nEs(medianAdr) : '—'}</strong><span>€</span></div>
    <span class="dash-foot">Tarifa pública · habitación/noche</span>
    <div class="dash-spark">${spark}</div>
    ${axis}
  </article>`;
}

function dashboardSwarmHTML(model) {
  const hotels = model.hotels.filter((h) => h.adr != null).sort((a, b) => a.adr - b.adr);
  const head = `<div class="dash-card__head"><div><span class="card__kicker">Dispersión del set</span><h2>Dónde compite el mercado</h2></div>
    <div class="dash-legend"><span><i class="is-mid"></i>&lt;${nEs(model.p25)} €</span><span><i class="is-lo"></i>${nEs(model.p25)}–${nEs(model.p75)} €</span><span><i class="is-ac"></i>&gt;${nEs(model.p75)} €</span></div></div>`;
  if (hotels.length < 2 || !(model.maxAdr > model.minAdr)) return `<article class="dash-card dash-card--swarm">${head}<div class="empty">Se necesitan al menos dos hoteles con tarifa.</div></article>`;
  const x = (v) => ((v - model.minAdr) / (model.maxAdr - model.minAdr)) * 100;
  const placed = [];
  let levels = 0;
  const dots = hotels.map((h, i) => {
    const pos = x(h.adr);
    let level = 0;
    while (placed.some((p) => p.level === level && Math.abs(p.pos - pos) < 1.9)) level++;
    placed.push({ pos, level });
    levels = Math.max(levels, level);
    const tone = h.adr > model.p75 ? 'ac' : h.adr >= model.p25 ? 'lo' : 'mid';
    return `<button type="button" class="dash-swarm__dot is-${tone}" style="left:${pos.toFixed(2)}%;bottom:${26 + level * 17}px;animation-delay:${i * 18}ms" data-dash-hotel="${esc(h.name)}" data-dash-tip="${esc(h.name)}" data-dash-tip-adr="${esc(eur(h.adr))}" aria-label="${esc(`${h.name} · ${eur(h.adr)}`)}"></button>`;
  }).join('');
  return `<article class="dash-card dash-card--swarm">${head}
    <div class="dash-swarm" style="min-height:${Math.max(150, 60 + levels * 17)}px">
      <div class="dash-swarm__band" style="left:${x(model.p25).toFixed(2)}%;width:${(x(model.p75) - x(model.p25)).toFixed(2)}%"></div>
      <div class="dash-swarm__med" style="left:${x(model.median).toFixed(2)}%"></div>
      <span class="dash-swarm__medlabel" style="left:${x(model.median).toFixed(2)}%">mediana ${eur(model.median)}</span>
      ${dots}
      <div class="dash-swarm__axis"><span>${eur(model.minAdr)}</span><span>${eur(model.maxAdr)}</span></div>
      <div class="dash-swarm__tip" id="dashSwarmTip" hidden></div>
    </div>
  </article>`;
}

function dashboardOutliersHTML(model) {
  const list = model.hotels.filter((h) => h.vsMedian != null).sort((a, b) => Math.abs(b.vsMedian) - Math.abs(a.vsMedian)).slice(0, DASH_OUTLIERS);
  const rows = list.map((h) => {
    const w = Math.min(50, (Math.abs(h.vsMedian) / 150) * 50);
    const left = h.vsMedian >= 0 ? 50 : 50 - w;
    return `<button type="button" class="dash-outlier" data-dash-hotel="${esc(h.name)}"><span class="dash-outlier__name">${esc(h.name)}</span><span class="dash-outlier__adr">${eur(h.adr)}</span><span class="dash-outlier__bar"><span class="dash-outlier__track"><i class="${h.vsMedian >= 0 ? 'is-up' : 'is-down'}" style="left:${left.toFixed(2)}%;width:${w.toFixed(2)}%"></i></span><span class="dash-outlier__vs">${pctTxt(h.vsMedian, 0)}</span></span></button>`;
  }).join('');
  return `<article class="dash-card dash-card--outliers"><span class="card__kicker">Fuera del centro</span><h2>Mayor distancia a la mediana</h2>
    <div class="dash-outliers">${rows || '<div class="empty">Sin tarifas comparables.</div>'}</div></article>`;
}

/* Semana (lunes) de una fecha ISO, para el resumen semanal del histórico. */
function dashboardWeekStart(iso) {
  const d = new Date(iso);
  const day = (d.getDay() + 6) % 7;
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() - day);
}

function dashboardHistoryHTML(photos) {
  const head = (stats) => `<div class="dash-card__head"><div><span class="card__kicker">Histórico de capturas</span><h2>ADR medio por foto</h2></div>${stats}</div>`;
  if (photos.length < 2) return `<article class="dash-card dash-card--history">${head('')}<div class="empty">Se necesitan dos fotos para representar la evolución del ADR.</div></article>`;
  const weeks = new Map();
  photos.forEach((p) => {
    const start = dashboardWeekStart(p.scrapedAt);
    const key = start.getTime();
    if (!weeks.has(key)) weeks.set(key, { start, values: [] });
    weeks.get(key).values.push(Number(p.avgPricePerNight));
  });
  const lastWeeks = [...weeks.values()].sort((a, b) => a.start - b.start).slice(-2).map((w) => ({ label: `Sem. ${w.start.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' }).replace('.', '')}`, value: w.values.reduce((s, v) => s + v, 0) / w.values.length }));
  const change = lastWeeks.length === 2 && lastWeeks[0].value ? ((lastWeeks[1].value / lastWeeks[0].value) - 1) * 100 : null;
  const stats = `<div class="dash-history__stats">${lastWeeks.map((w) => `<span>${esc(w.label)} <b>${eur(w.value)}</b></span>`).join('')}${change == null ? '' : `<span class="dash-history__delta ${change > 0 ? 'pos' : change < 0 ? 'neg' : ''}">${pctTxt(change, 1)}</span>`}</div>`;
  const values = photos.map((p) => Number(p.avgPricePerNight));
  const { lo: rawLo, hi: rawHi } = dashboardRange(values, 0.1, 5);
  const lo = Math.floor(rawLo / 10) * 10, hi = Math.ceil(rawHi / 10) * 10;
  const n = photos.length;
  const px = (i) => 50 + i * (640 / (n - 1));
  const py = (v) => 140 - ((v - lo) / (hi - lo)) * 120;
  const line = photos.map((p, i) => `${px(i).toFixed(1)},${py(Number(p.avgPricePerNight)).toFixed(1)}`).join(' ');
  const every = n > 14 ? 2 : 1;
  const points = photos.map((p, i) => {
    const date = new Date(p.scrapedAt).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' });
    const label = i % every === 0 || i === n - 1 ? `<text x="${px(i).toFixed(1)}" y="162" text-anchor="middle">#${p.id}</text>` : '';
    return `<circle cx="${px(i).toFixed(1)}" cy="${py(Number(p.avgPricePerNight)).toFixed(1)}" r="4" fill="var(--card)" stroke="var(--ac)" stroke-width="2"><title>Foto #${p.id} · ${date} · ${eur(p.avgPricePerNight)}</title></circle>${label}`;
  }).join('');
  return `<article class="dash-card dash-card--history">${head(stats)}
    <svg class="dash-history__chart" viewBox="0 0 700 170" role="img" aria-label="ADR medio por foto"><line x1="0" x2="700" y1="20" y2="20" stroke="var(--line)"></line><line x1="0" x2="700" y1="140" y2="140" stroke="var(--line)"></line><g class="dash-svg-text"><text x="0" y="14">${eur(hi)}</text><text x="0" y="134">${eur(lo)}</text></g><polyline points="${line}" fill="none" stroke="var(--ac)" stroke-width="2" stroke-linejoin="round"></polyline><g class="dash-svg-text">${points}</g></svg>
  </article>`;
}

/* Curva de entrada: ADR medio de las observaciones agrupadas por días hasta la estancia. */
function dashboardCurveHTML(points) {
  const rows = (points || []).filter((p) => Number.isFinite(Number(p.daysUntilCheckIn)) && Number(p.avgAdr) > 0);
  const windows = [
    ['≤ 21 días', (d) => d <= 21], ['22–42 días', (d) => d >= 22 && d <= 42], ['> 42 días', (d) => d > 42],
  ].map(([label, test]) => {
    const values = rows.filter((p) => test(Number(p.daysUntilCheckIn))).map((p) => Number(p.avgAdr));
    return values.length ? { label, value: values.reduce((s, v) => s + v, 0) / values.length, points: values.length } : null;
  }).filter(Boolean);
  const head = '<div><span class="card__kicker">Curva de entrada</span><h2>ADR según días hasta la estancia</h2></div>';
  if (!windows.length) return `<article class="dash-card dash-card--curve">${head}<div class="empty">No hay observaciones suficientes por horizonte de entrada.</div><span class="dash-curve__note">Observaciones agregadas por horizonte; no es una previsión.</span></article>`;
  const values = windows.map((w) => w.value);
  const min = Math.min(...values), max = Math.max(...values);
  const lo = min * 0.9, hi = max * 1.02;
  const bars = windows.map((w) => {
    const width = hi > lo ? ((w.value - lo) / (hi - lo)) * 100 : 60;
    return `<div class="dash-curve__row"><span>${w.label}</span><div class="dash-curve__track"><i class="${windows.length > 1 && w.value === min ? 'is-low' : ''}" style="width:${width.toFixed(1)}%"></i></div><strong title="${w.points} ${w.points === 1 ? 'punto' : 'puntos'}">${eur(w.value)}</strong></div>`;
  }).join('');
  return `<article class="dash-card dash-card--curve">${head}${bars}<span class="dash-curve__note">Observaciones agregadas por horizonte; no es una previsión.</span></article>`;
}

async function renderDashboard() {
  const host = mount('dashboard');
  const request = {};
  host._dashboardRequest = request;
  const targetId = State.targetId;
  const t = activeTarget();
  destroyDashboardMap();
  skeleton(host, 'dashboard');
  if (!Number.isInteger(State.targetId)) { renderNoActiveTarget(host, 'Lectura de mercado', 'Panel principal'); return; }
  let d, s, history, demand;
  try { [d, s, history, demand] = await Promise.all([getMetrics(targetId), getSnapshot(targetId), getPhotoHistory(targetId), getDemandCurve(targetId).catch(() => ({ demandCurve: [] }))]); }
  catch (e) { if (host._dashboardRequest === request && State.targetId === targetId) host.innerHTML = `<div class="page">${pageHead('Lectura de mercado', 'Panel principal', '')}<div class="inline-error">No se pudieron cargar las métricas: ${esc(e.message)}</div></div>`; return; }
  if (host._dashboardRequest !== request || State.targetId !== targetId || State.view !== 'dashboard') return;
  if (d.currencyPolicy?.status === 'blocked') { host.innerHTML = `<div class="page"><div class="inline-error">${esc(d.currencyPolicy.reason)}</div></div>`; return; }

  const rows = s.latest?.rows || [];
  const snapshot = s.latest?.snapshot || d.latestSnapshot || {};
  const model = hotelSheetModel(rows, d, []);
  const priced = model.hotels.filter((h) => h.adr != null);
  const photos = dashboardPhotos(history);
  const mv = d.movement || {};
  State.dashboard.model = model;
  State.dashboard.photos = photos;
  State.dashboard.previousSnapshotId = mv.previousSnapshotId ?? null;
  State.dashboard.signals = dashboardSignalModel(d.insights, model.hotels);
  const at = snapshot.scrapedAt || null;
  const fresh = dataAgeDays(at) === 0 && State.freshCaptureTargetId === targetId;
  const moveValue = mv.isComparable ? Number(mv.avgPricePerNightChangePct) : null;
  const pricedPct = rows.length ? (priced.length / rows.length) * 100 : 0;

  host.innerHTML = `<div class="page dash">
    <div class="page-head"><div><h1>Lectura de mercado</h1><p>${esc(t ? t.name : 'Mercado')} · ${nEs(rows.length)} hoteles observados${snapshot.id ? ` · foto #${snapshot.id}` : ''}</p></div>
      <div class="page-head__meta"><span>Extracción ${esc(fmtStamp(at))}</span>${fresh ? '' : '<button type="button" class="btn page-head__btn" data-dash-refresh>Actualizar datos</button>'}</div></div>
    ${dashboardSignalsHTML(State.dashboard.signals)}
    <div class="dash-grid">
      ${dashboardAdrCardHTML(model.median, photos)}
      <article class="dash-card dash-card--count"><span class="card__kicker">Hoteles con tarifa</span><div class="dash-mid"><strong>${nEs(priced.length)}</strong><span>/ ${nEs(rows.length)}</span></div><div class="dash-meter"><i style="width:${pricedPct.toFixed(1)}%"></i></div><span class="dash-foot">${rows.length ? `${nEs(pricedPct, 0)} % con precio observable` : 'Sin hoteles observados'}</span></article>
      ${dashboardSwarmHTML(model)}
      <article class="dash-card dash-card--move"><span class="card__kicker">Movimiento ADR</span><strong class="dash-move${moveValue > 0 ? ' is-up' : moveValue < 0 ? ' is-down' : ''}">${moveValue == null ? '—' : pctTxt(moveValue, 1)}</strong><span class="dash-foot">${mv.isComparable ? `${nEs(mv.changedHotels)} hoteles movidos · <span class="pos">▲${nEs(mv.priceIncreases)}</span> <span class="neg">▼${nEs(mv.priceDrops)}</span>` : 'Sin comparativa con la foto anterior'}</span></article>
      <article class="dash-card dash-card--map">
        <div class="dash-card__head"><div><span class="card__kicker">Mapa hotelero</span><h2>Precio por ubicación</h2></div><div class="dash-legend"><span><i class="is-low"></i>bajo</span><span><i class="is-mid-tier"></i>medio</span><span><i class="is-high"></i>alto</span></div></div>
        <div class="map-frame dash-map" id="dashMapFrame"><div class="map-frame__canvas" id="dashMap" aria-label="Mapa de hoteles del mercado activo"></div><div class="dash-pop-layer" id="dashPopLayer"></div></div>
      </article>
      ${dashboardOutliersHTML(model)}
      ${dashboardHistoryHTML(photos)}
      ${dashboardCurveHTML(demand.demandCurve || [])}
    </div>
  </div>`;
  void renderDashboardHotelMap(model);
}

function destroyDashboardMap() {
  if (State.dashboardMapResizeObserver) { State.dashboardMapResizeObserver.disconnect(); State.dashboardMapResizeObserver = null; }
  State.dashboardMapMarkers.forEach((marker) => marker.remove());
  State.dashboardMapMarkers = [];
  if (State.dashboardMap) { State.dashboardMap.remove(); State.dashboardMap = null; }
  State.dashboard.sel = null;
  State.dashboard.ptHover = null;
}

async function renderDashboardHotelMap(model) {
  const frame = $('#dashMapFrame');
  const container = $('#dashMap');
  if (!frame || !container) return;
  const request = {};
  frame._mapRequest = request;
  const points = model.hotels.filter((h) => h.adr != null && validLngLat(h.row));
  if (!points.length) { mapFrameStatus(frame, 'No hay hoteles con tarifa y coordenadas válidas en esta foto.'); return; }
  try { await loadMapLibre(); } catch (_) { if (frame.isConnected && frame._mapRequest === request) mapFrameStatus(frame, MAP_FAILED_TEXT); return; }
  if (!frame.isConnected || frame._mapRequest !== request || State.view !== 'dashboard') return;
  destroyDashboardMap();
  const ml = window.maplibregl;
  let map;
  try { map = createAtlasMap(container, { center: [-15.655, 27.782], zoom: 10.7 }); }
  catch (_) { mapFrameStatus(frame, MAP_FAILED_TEXT); return; }
  State.dashboardMap = map;
  const bounds = new ml.LngLatBounds();
  points.forEach((h) => {
    const lngLat = validLngLat(h.row);
    bounds.extend(lngLat);
    const el = mapPinElement(`<button type="button" class="map-pin__dot map-pin__dot--${h.tier === 'none' ? 'mid' : h.tier}" data-dash-pin="${esc(h.key)}" aria-label="${esc(`${h.name} · ${eur(h.adr)}. Abrir inspector de tarifa`)}" aria-haspopup="dialog"></button>`);
    State.dashboardMapMarkers.push(new ml.Marker({ element: el }).setLngLat(lngLat).addTo(map));
  });
  // El prototipo centra el sur de Gran Canaria a zoom 10.7; si el set es más amplio se encuadra sin pasar de ese zoom.
  map.fitBounds(bounds, { padding: 48, maxZoom: 10.7, duration: 0 });
  map.on('move', () => positionDashboardPopover());
  if (typeof ResizeObserver !== 'undefined') {
    State.dashboardMapResizeObserver = new ResizeObserver(() => { if (State.dashboardMap === map) { map.resize(); positionDashboardPopover(); } });
    State.dashboardMapResizeObserver.observe(frame);
  }
}

/* ---- ventana del mapa (inspector de tarifa) */
function dashboardHotel(key) { return State.dashboard.model?.hotels.find((h) => h.key === key) || null; }

/* Serie «por extracción»: mediana del hotel en cada foto del mercado, alineada con las fotos. */
function dashboardHistSeries(history, photos) {
  const bySnapshot = new Map();
  (history || []).forEach((entry) => {
    const value = Number(entry.pricePerNight);
    if (entry.snapshotId == null || !(value > 0)) return;
    if (!bySnapshot.has(Number(entry.snapshotId))) bySnapshot.set(Number(entry.snapshotId), []);
    bySnapshot.get(Number(entry.snapshotId)).push(value);
  });
  return photos.map((p) => ({
    label: `#${p.id}`, date: new Date(p.scrapedAt).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' }),
    value: bySnapshot.has(Number(p.id)) ? median(bySnapshot.get(Number(p.id))) : null, set: Number(p.avgPricePerNight),
  }));
}

/* Serie «por fecha de entrada»: última extracción frente a la anterior. Una extracción reúne
   las fotos tomadas con menos de 20 minutos de separación (un barrido de varias fechas). */
function dashboardDateSeries(history) {
  const valid = (history || []).filter((e) => e.snapshotId != null && e.checkIn && Number(e.pricePerNight) > 0 && Number.isFinite(Date.parse(e.scrapedAt)))
    .slice().sort((a, b) => Date.parse(a.scrapedAt) - Date.parse(b.scrapedAt));
  const batches = [];
  valid.forEach((entry) => {
    const at = Date.parse(entry.scrapedAt);
    let batch = batches.at(-1);
    if (!batch || at - batch.lastAt > 20 * 60 * 1000) { batch = { entries: [], lastAt: at, ids: [] }; batches.push(batch); }
    batch.entries.push(entry);
    batch.lastAt = at;
    if (!batch.ids.includes(Number(entry.snapshotId))) batch.ids.push(Number(entry.snapshotId));
  });
  if (!batches.length) return null;
  const byDate = (batch) => {
    const map = new Map();
    (batch?.entries || []).forEach((e) => { if (!map.has(e.checkIn)) map.set(e.checkIn, []); map.get(e.checkIn).push(Number(e.pricePerNight)); });
    return new Map([...map.entries()].map(([k, v]) => [k, median(v)]));
  };
  const current = byDate(batches.at(-1));
  const previous = batches.length > 1 ? byDate(batches.at(-2)) : new Map();
  const dates = [...new Set([...current.keys(), ...previous.keys()])].sort();
  const label = (batch) => { const ids = batch.ids; return ids.length === 1 ? `#${ids[0]}` : `#${ids[0]}–#${ids.at(-1)}`; };
  return {
    points: dates.map((date) => ({ label: `${date.slice(8, 10)}/${date.slice(5, 7)}`, value: current.get(date) ?? null, prev: previous.get(date) ?? null })),
    currentLabel: label(batches.at(-1)), previousLabel: batches.length > 1 ? label(batches.at(-2)) : null,
  };
}

function dashboardPopoverChartHTML(h) {
  const st = State.dashboard;
  const history = State.hotelPriceHistories[State.targetId]?.[h.key];
  if (!history) return '<div class="dash-pop__loading"><i></i>Cargando evolución por extracción…</div>';
  let s1, s2 = null, labels, leg1, leg2 = '', dashed = st.chart === 'hist', readout;
  if (st.chart === 'hist') {
    const series = dashboardHistSeries(history, st.photos);
    s1 = series.map((p) => p.value);
    if (st.cmp) s2 = series.map((p) => p.set);
    labels = series.map((p) => p.label);
    leg1 = 'ADR del hotel por extracción'; leg2 = 'Media del set';
    const i = st.ptHover;
    readout = i != null && s1[i] != null ? `Foto ${labels[i]} · ${series[i].date} · ${eur(s1[i])}${st.cmp ? ` · set ${eur(series[i].set)}` : ''}` : null;
  } else {
    const series = dashboardDateSeries(history);
    if (!series) return '<div class="dash-pop__empty">Sin fechas de entrada observadas para este hotel.</div>';
    s1 = series.points.map((p) => p.value);
    s2 = series.previousLabel ? series.points.map((p) => p.prev) : null;
    labels = series.points.map((p) => p.label);
    leg1 = `Última captura · ${series.currentLabel}`; leg2 = series.previousLabel ? `Captura anterior · ${series.previousLabel}` : '';
    const i = st.ptHover;
    readout = i != null && s1[i] != null ? `Entrada ${labels[i]} · ${eur(s1[i])}${s2 && s2[i] != null ? ` · antes ${eur(s2[i])}` : ''}` : null;
  }
  const vals = [...s1, ...(s2 || [])].filter((v) => v != null);
  if (!vals.length) return '<div class="dash-pop__empty">Este hotel no tiene tarifas en las fotos disponibles.</div>';
  let lo = Math.min(...vals), hi = Math.max(...vals);
  const pad = Math.max(6, (hi - lo) * 0.12); lo -= pad; hi += pad;
  const n = s1.length;
  const X = (i) => (n === 1 ? 215 : 34 + i * (362 / (n - 1)));
  const Y = (v) => 140 - ((v - lo) / (hi - lo)) * 128;
  const line = (arr) => arr.map((v, i) => (v == null ? null : `${X(i).toFixed(1)},${Y(v).toFixed(1)}`)).filter(Boolean).join(' ');
  const idx = s1.map((v, i) => (v == null ? null : i)).filter((i) => i != null);
  const l1 = line(s1);
  const area = idx.length > 1 ? `${X(idx[0]).toFixed(1)},140 ${l1} ${X(idx.at(-1)).toFixed(1)},140` : '';
  const xl = labels.map((t, i) => ({ t, i })).filter(({ i }) => n <= 8 || i % 2 === 1 || i === n - 1)
    .map(({ t, i }) => `<text x="${X(i).toFixed(1)}" y="160" text-anchor="middle">${esc(t)}</text>`).join('');
  const pts = s1.map((v, i) => (v == null ? '' : `<circle cx="${X(i).toFixed(1)}" cy="${Y(v).toFixed(1)}" r="${st.ptHover === i ? 5.5 : 3.5}" class="dash-pop__pt${st.ptHover === i ? ' is-on' : ''}" data-dash-pt="${i}"></circle>`)).join('');
  const c2 = dashed ? 'var(--faint)' : 'var(--warn-ink)';
  const fallback = h.isNew ? 'Nuevo en el set: solo aparece en la última extracción' : 'Pasa el cursor por los puntos';
  return `<div class="dash-pop__readout" aria-live="polite">${esc(readout || fallback)}</div>
    <svg viewBox="0 0 400 170" role="img" aria-label="${esc(leg1)}"><line x1="34" x2="396" y1="12" y2="12" stroke="var(--line)"></line><line x1="34" x2="396" y1="76" y2="76" stroke="var(--line)"></line><line x1="34" x2="396" y1="140" y2="140" stroke="var(--line)"></line>
      <g class="dash-svg-text dash-svg-text--sm"><text x="28" y="15" text-anchor="end">${eur(hi)}</text><text x="28" y="143" text-anchor="end">${eur(lo)}</text>${xl}</g>
      ${s2 ? `<polyline points="${line(s2)}" fill="none" stroke="${c2}" stroke-width="1.6" stroke-dasharray="${dashed ? '4 4' : '0'}" stroke-linejoin="round"></polyline>` : ''}
      ${area ? `<polyline points="${area}" fill="var(--accent-soft)" stroke="none" opacity=".7"></polyline>` : ''}
      <polyline points="${l1}" fill="none" stroke="var(--ac)" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"></polyline>${pts}</svg>
    <div class="dash-pop__legend"><span><i style="background:var(--ac)"></i>${esc(leg1)}</span>${s2 ? `<span><i style="background:${c2}"></i>${esc(leg2)}</span>` : ''}</div>`;
}

function dashboardPopoverFacts(h) {
  const cached = State.hotelRateDetails[State.targetId]?.[h.key] || null;
  const rates = cached && cached.rows ? cached.rows : [];
  const genius = !rates.length ? null : rates.some((rate) => rate.genius === true) ? true : rates.every((rate) => rate.genius === false) ? false : null;
  const row = h.row;
  return [
    ['Nota', h.nota == null ? '—' : `${nEs(h.nota, 1)}${h.reviews == null ? '' : ` · ${nEs(h.reviews)} reseñas`}`, ''],
    ['Régimen', row.board || '—', ''],
    ['Habitación', row.roomType || '—', ''],
    ['Cancelación', h.cancel === true ? 'Gratis' : h.cancel === false ? 'No gratuita' : '—', h.cancel === true ? 'pos' : ''],
    ['Disponibilidad', h.stock.tone === 'none' ? 'Observable' : h.stock.text, h.stock.tone === 'warn' || h.stock.tone === 'bad' ? 'warn' : ''],
    ['Genius', genius === true ? 'Participa' : genius === false ? 'No participa' : '—', genius === true ? 'ac' : ''],
    ['Distancia playa', row.beachDistance || '—', ''],
  ];
}

function dashboardPopoverHTML(h) {
  const st = State.dashboard;
  const priced = st.model.hotels.filter((x) => x.adr != null).length;
  const sub = [h.chain, h.zone, h.adultsOnly ? 'Adults only' : ''].filter(Boolean).join(' · ');
  const prevId = st.previousSnapshotId;
  const delta = h.isNew ? ['Nuevo en el set', 'ac']
    : h.delta == null ? ['Sin comparativa con la foto anterior', 'dim']
    : h.delta === 0 ? [`Sin cambio vs foto #${prevId}`, 'dim']
    : [`${h.delta > 0 ? '▲' : '▼'} ${nEs(Math.abs(h.delta), 1)} % vs foto #${prevId} (${eur(h.prevAdr)})`, h.delta > 0 ? 'pos' : 'neg'];
  const modes = [['hist', 'Por extracción'], ['dates', 'Por fecha de entrada']].map(([id, label]) => `<button type="button" class="${st.chart === id ? 'is-active' : ''}" data-dash-chart="${id}" aria-pressed="${st.chart === id}">${label}</button>`).join('');
  return `<div class="dash-pop__head"><div class="dash-pop__title"><span class="dash-pop__kicker">Inspector de tarifa · puesto ${h.rank} de ${priced}</span><h3 id="dashPopTitle">${esc(h.name)}</h3>${sub ? `<span class="dash-pop__sub">${esc(sub)}</span>` : ''}</div><button type="button" class="icon-x" data-dash-close aria-label="Cerrar inspector">×</button></div>
    <div class="dash-pop__body">
      <div class="dash-pop__chart"><div class="dash-pop__modes"><div class="seg seg--sm" role="group" aria-label="Modo de la gráfica">${modes}</div>${st.chart === 'hist' ? `<button type="button" class="dash-pop__cmp" data-dash-cmp aria-pressed="${st.cmp}"><i aria-hidden="true"></i>Media del set</button>` : ''}</div><div id="dashPopChart">${dashboardPopoverChartHTML(h)}</div></div>
      <div class="dash-pop__side"><div class="dash-pop__adr"><span class="dash-pop__kicker">ADR hab/noche</span><div class="dash-pop__adrrow"><strong>${eur(h.adr)}</strong>${h.vsMedian == null ? '' : `<span class="dash-pop__vs${h.vsMedian >= 0 ? ' is-up' : ''}">${pctTxt(h.vsMedian, 0)} vs mediana</span>`}</div><span class="dash-pop__delta ${delta[1]}">${esc(delta[0])}</span></div>
        <dl class="dash-pop__facts" id="dashPopFacts">${dashboardPopoverFacts(h).map(([k, v, tone]) => `<div><dt>${esc(k)}</dt><dd class="${tone}" title="${esc(v)}">${esc(v)}</dd></div>`).join('')}</dl></div>
    </div>
    <div class="dash-pop__foot"><button type="button" class="btn btn--primary" data-dash-hotel="${esc(h.name)}">Ver en la hoja de mercado</button><button type="button" class="btn" data-dash-ask="${esc(`¿Cómo ha evolucionado el precio de ${h.name}?`)}">Preguntar al Copilot</button></div>`;
}

function paintDashboardPopover(part) {
  const h = dashboardHotel(State.dashboard.sel);
  const pop = $('#dashPop');
  if (!h || !pop) return;
  if (part === 'chart') { const chart = $('#dashPopChart', pop); if (chart) chart.innerHTML = dashboardPopoverChartHTML(h); positionDashboardPopover(); return; }
  if (part === 'facts') {
    const facts = $('#dashPopFacts', pop);
    if (facts) facts.innerHTML = dashboardPopoverFacts(h).map(([k, v, tone]) => `<div><dt>${esc(k)}</dt><dd class="${tone}" title="${esc(v)}">${esc(v)}</dd></div>`).join('');
    return;
  }
  pop.innerHTML = dashboardPopoverHTML(h);
}

function openDashboardPopover(key) {
  const h = dashboardHotel(key);
  const layer = $('#dashPopLayer');
  if (!h || !layer || !State.dashboardMap) return;
  const st = State.dashboard;
  if (st.sel !== key) st.ptHover = null;
  if (!st.sel) st.returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  st.sel = key;
  $$('[data-dash-pin]').forEach((pin) => pin.classList.toggle('is-selected', pin.dataset.dashPin === key));
  layer.innerHTML = `<span class="dash-pop-ring" id="dashPopRing"></span><svg class="dash-pop-link" aria-hidden="true"><line id="dashPopLine" stroke="var(--ac)" stroke-width="1.5" stroke-dasharray="3 3"></line><circle id="dashPopAnchor" r="3" fill="var(--ac)"></circle></svg><div class="dash-pop" id="dashPop" role="dialog" aria-labelledby="dashPopTitle"></div>`;
  paintDashboardPopover();
  positionDashboardPopover(true);
  $('#dashPop [data-dash-close]')?.focus({ preventScroll: true });
  const targetId = State.targetId;
  getHotelPriceHistory(targetId, key).then(() => { if (State.dashboard.sel === key && State.targetId === targetId) paintDashboardPopover('chart'); })
    .catch((error) => { const chart = $('#dashPopChart'); if (chart && State.dashboard.sel === key) chart.innerHTML = `<div class="dash-pop__empty">No se pudo cargar la evolución: ${esc(error.message)}</div>`; });
  void ensureHotelRateDetails(key).then(() => { if (State.dashboard.sel === key && State.targetId === targetId) paintDashboardPopover('facts'); });
}

function closeDashboardPopover() {
  const st = State.dashboard;
  if (!st.sel) return false;
  st.sel = null;
  st.ptHover = null;
  const layer = $('#dashPopLayer');
  if (layer) layer.innerHTML = '';
  $$('[data-dash-pin].is-selected').forEach((pin) => pin.classList.remove('is-selected'));
  const origin = st.returnFocus;
  st.returnFocus = null;
  if (origin instanceof HTMLElement && origin.isConnected) origin.focus({ preventScroll: true });
  return true;
}

/* Coloca la ventana junto al punto (a la derecha o, si no cabe, a la izquierda) y la línea que los une.
   Al abrirla, si no cabe a ningún lado, desplaza el mapa para que la ventana no tape el punto. */
function positionDashboardPopover(reveal = false) {
  const st = State.dashboard;
  const map = State.dashboardMap;
  const frame = $('#dashMapFrame');
  const pop = $('#dashPop');
  const h = dashboardHotel(st.sel);
  if (!map || !frame || !pop || !h) return;
  const p = map.project(validLngLat(h.row));
  const W = frame.clientWidth, H = frame.clientHeight || DASH_MAP_HEIGHT;
  const cw = Math.min(DASH_POPOVER_MAX, W - 66); // deja sitio al punto y a la línea junto a la ventana
  pop.classList.toggle('is-narrow', cw < 560);
  pop.style.width = `${cw}px`;
  const chh = pop.offsetHeight || (cw < 560 ? 580 : 450);
  const right = p.x + 30 + cw <= W - 12;
  if (reveal && !right && p.x - 30 - cw < 12) {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    map.easeTo({ center: map.unproject([W / 2 + p.x - 24, H / 2]), duration: reduce ? 0 : 320, essential: true });
  }
  const left = Math.max(12, right ? p.x + 30 : p.x - 30 - cw);
  const top = Math.max(12, Math.min(H - chh - 12, p.y - 150));
  const ax = right ? left : left + cw;
  const ay = Math.max(top + 24, Math.min(top + chh - 24, p.y));
  pop.style.left = `${left}px`;
  pop.style.top = `${top}px`;
  pop.style.transformOrigin = `${(p.x - left).toFixed(0)}px ${(p.y - top).toFixed(0)}px`;
  const ring = $('#dashPopRing');
  if (ring) { ring.style.left = `${p.x}px`; ring.style.top = `${p.y}px`; }
  const lineEl = $('#dashPopLine');
  if (lineEl) { lineEl.setAttribute('x1', p.x); lineEl.setAttribute('y1', p.y); lineEl.setAttribute('x2', ax); lineEl.setAttribute('y2', ay); }
  const anchor = $('#dashPopAnchor');
  if (anchor) { anchor.setAttribute('cx', ax); anchor.setAttribute('cy', ay); }
}

function showDashboardSwarmTip(dot) {
  const tip = $('#dashSwarmTip');
  if (!tip) return;
  if (!dot) { tip.hidden = true; return; }
  tip.innerHTML = `<b>${esc(dot.dataset.dashTip)}</b> · ${esc(dot.dataset.dashTipAdr)}`;
  tip.style.left = dot.style.left;
  tip.style.bottom = dot.style.bottom;
  tip.hidden = false;
}

function handleDashboardClick(e) {
  const target = e.target instanceof Element ? e.target : null;
  if (!target || !target.closest('#view-dashboard')) return false;
  if (target.closest('[data-dash-signals]')) {
    State.dashboard.allSignals = !State.dashboard.allSignals;
    const section = $('#dashSignals');
    if (section) { section.outerHTML = dashboardSignalsHTML(State.dashboard.signals); $('#dashSignals [data-dash-signals]')?.focus(); }
    return true;
  }
  const pin = target.closest('[data-dash-pin]');
  if (pin) { e.stopPropagation(); openDashboardPopover(pin.dataset.dashPin); return true; }
  if (target.closest('[data-dash-close]')) { closeDashboardPopover(); return true; }
  const mode = target.closest('[data-dash-chart]');
  if (mode) { State.dashboard.chart = mode.dataset.dashChart === 'dates' ? 'dates' : 'hist'; State.dashboard.ptHover = null; paintDashboardPopover(); positionDashboardPopover(); $(`#dashPop [data-dash-chart="${State.dashboard.chart}"]`)?.focus(); return true; }
  if (target.closest('[data-dash-cmp]')) { State.dashboard.cmp = !State.dashboard.cmp; paintDashboardPopover(); $('#dashPop [data-dash-cmp]')?.focus(); return true; }
  const hotel = target.closest('[data-dash-hotel]');
  if (hotel) { openHotelInHotels(hotel.dataset.dashHotel); return true; }
  const ask = target.closest('[data-dash-ask]');
  if (ask) { askCopilot(ask.dataset.dashAsk); return true; }
  if (target.closest('[data-dash-refresh]')) { void openCaptureDialog(); return true; }
  return false;
}

function handleDashboardOver(e) {
  const target = e.target instanceof Element ? e.target : null;
  if (!target || State.view !== 'dashboard') return;
  const tip = $('#dashSwarmTip');
  if (target.closest('.dash-swarm')) showDashboardSwarmTip(target.closest('.dash-swarm__dot'));
  else if (tip && !tip.hidden) tip.hidden = true;
  const pt = target.closest('[data-dash-pt]');
  if (pt && Number(pt.dataset.dashPt) !== State.dashboard.ptHover) { State.dashboard.ptHover = Number(pt.dataset.dashPt); paintDashboardPopover('chart'); }
}

function rateNights(checkIn, checkOut) {
  if (!checkIn || !checkOut) return null;
  const start = Date.parse(`${checkIn}T00:00:00Z`);
  const end = Date.parse(`${checkOut}T00:00:00Z`);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return null;
  return Math.round((end - start) / 86400000);
}

function compactBoardLabel(board) {
  if (!board) return 'No informado';
  const value = String(board).toLowerCase();
  if (value.includes('todo incluido')) return 'Todo incluido';
  if (value.includes('desayuno') && value.includes('cena')) return 'Media pensión';
  if (value.includes('desayuno')) return 'Desayuno';
  if (value.includes('solo alojamiento') || value.includes('solo habitación') || value.includes('room only')) return 'Solo alojamiento';
  return String(board);
}

/* ================================================================= HOTELES */
/* ================================================= HOTELES · HOJA DE MERCADO */
const HOTEL_QUERY_KEY = 'atlas.hotels.query.v2';
const HOTEL_VARIANT_KEY = 'atlas.hotels.variant';
const HOTEL_TAB_KEY = 'atlas.hotelTab';
const HOTEL_DENSITY_ICONS = {
  compacta: '<path d="M5 6h14M5 10h14M5 14h14M5 18h14"/>',
  equilibrada: '<path d="M5 7h14M5 12h14M5 17h14"/>',
  espaciosa: '<path d="M5 8h14M5 16h14"/>',
};

function defaultHotelSort() { return { key: 'adr', dir: -1 }; }

function restoreHotelQuery(targetId) {
  State.hotelVariant = readPref(HOTEL_VARIANT_KEY, ['A', 'B'], 'A');
  State.hotelTab = readPref(HOTEL_TAB_KEY, ['sheet', 'bi'], 'bi');
  if (State.hotelQueryTargetId === targetId) return;
  let saved = {};
  try {
    const parsed = JSON.parse(localStorage.getItem(`${HOTEL_QUERY_KEY}.${targetId}`) || 'null');
    if (parsed && typeof parsed === 'object') saved = parsed;
  } catch (_) { /* una preferencia local dañada no bloquea la consulta */ }
  State.hotelQueryTargetId = targetId;
  State.hotelView = SHEET_VIEWS.some((v) => v.id === saved.view) ? saved.view : 'market';
  State.hotelChips = Array.isArray(saved.chips) ? saved.chips.filter((id) => SHEET_CHIPS.some((c) => c.id === id)) : [];
  State.hotelSearch = typeof saved.search === 'string' ? saved.search.slice(0, 160) : '';
  const key = saved.sort && SHEET_SORT_KEYS.includes(saved.sort.key) ? saved.sort.key : 'adr';
  State.hotelSort = { key, dir: saved.sort && saved.sort.dir === 1 ? 1 : -1 };
  State.hotelGroup = SHEET_GROUPS.some((g) => g.id === saved.group) ? saved.group : 'none';
  State.hotelExpanded = {};
  State.hotelSelectedKey = null;
  State.hotelPinnedKey = null;
}

function persistHotelQuery() {
  if (!State.targetId) return;
  try {
    localStorage.setItem(`${HOTEL_QUERY_KEY}.${State.targetId}`, JSON.stringify({
      view: State.hotelView, chips: State.hotelChips, search: State.hotelSearch, sort: State.hotelSort, group: State.hotelGroup,
    }));
  } catch (_) { /* la consulta sigue funcionando aunque no haya almacenamiento local */ }
}

function pctTxt(value, decimals = 0) {
  if (value == null || !Number.isFinite(Number(value))) return '—';
  const v = Number(value);
  return `${v > 0 ? '+' : v < 0 ? '−' : ''}${nEs(Math.abs(v), decimals)}${NBSP}%`;
}

function hotelSheetHotel(key) {
  return State.hotelSheet ? State.hotelSheet.model.hotels.find((h) => h.key === key) || null : null;
}

/* columnas por variante: A (tabla completa) y B (tabla más estrecha + panel lateral) */
function hotelSheetColumns(variant) {
  const wide = variant !== 'B';
  return [
    { id: 'rank', label: '#', width: 64, sticky: 0 },
    { id: 'name', label: 'Hotel', width: null, sticky: 64, sort: 'name', align: 'left' },
    { id: 'adr', label: 'ADR/hab', width: wide ? 100 : 96, sort: 'adr', align: 'right' },
    ...(wide ? [{ id: 'pers', label: 'ADR/pers', width: 96, sort: 'pers', align: 'right' }] : []),
    { id: 'vs', label: 'vs mediana', width: wide ? 190 : 170, sort: 'vs', align: 'left' },
    { id: 'delta', label: 'Δ foto', width: wide ? 100 : 96, sort: 'delta', align: 'right' },
    { id: 'stab', label: 'Estab.', width: wide ? 80 : 76, sort: 'stab', align: 'right' },
    { id: 'nota', label: 'Nota', width: wide ? 70 : 64, sort: 'nota', align: 'right' },
    ...(wide ? [{ id: 'reviews', label: 'Reseñas', width: 90, sort: 'reviews', align: 'right' }] : []),
    { id: 'cancel', label: 'Cancel.', width: wide ? 90 : 84, sort: 'cancel', align: 'left' },
    { id: 'avail', label: 'Disponib.', width: wide ? 120 : 112, sort: 'avail', align: 'right' },
  ];
}

function hotelSheetColgroupHTML(variant) {
  return hotelSheetColumns(variant).map((c) => `<col${c.width ? ` style="width:${c.width}px"` : ''}>`).join('');
}

function hotelSheetHeadHTML(variant) {
  const sort = State.hotelSort;
  const columns = hotelSheetColumns(variant);
  return `<tr>${columns.map((c) => {
    const active = c.sort && sort.key === c.sort;
    const stickyClass = c.sticky != null ? ` hsheet__sticky hsheet__sticky--${c.id}` : '';
    const align = c.align === 'right' ? ' is-right' : '';
    const ariaSort = c.sort ? ` aria-sort="${active ? (sort.dir === 1 ? 'ascending' : 'descending') : 'none'}"` : '';
    const body = c.sort
      ? `<button type="button" class="hsheet__sort${active ? ' is-active' : ''}" data-sheet-sort="${c.sort}" title="Ordenar por ${esc(c.label)}">${esc(c.label)}${active ? `<span class="hsheet__arrow" aria-hidden="true">${sort.dir === 1 ? '↑' : '↓'}</span>` : ''}</button>`
      : `<span class="hsheet__nosort">${esc(c.label)}</span>`;
    return `<th scope="col"${ariaSort} class="${align}${stickyClass}">${body}</th>`;
  }).join('')}</tr>`;
}

function hotelSheetRowHTML(h, variant) {
  const open = Boolean(State.hotelExpanded[h.key]);
  const selected = variant === 'B' && State.hotelSelectedKey === h.key;
  const pinned = variant === 'B' && State.hotelPinnedKey === h.key;
  const wide = variant !== 'B';
  const w = h.vsMedian == null ? 0 : Math.min(50, Math.abs(h.vsMedian) / 150 * 50);
  const positive = (h.vsMedian || 0) >= 0;
  const stabTone = h.stab == null ? '' : h.stab >= 95 ? 'good' : h.stab < 85 ? 'warn' : 'plain';
  const deltaTone = h.isNew ? 'new' : h.delta == null ? 'none' : h.delta > 0 ? 'up' : h.delta < 0 ? 'down' : 'flat';
  const deltaText = h.isNew ? 'Nuevo' : h.delta == null ? '—' : h.delta === 0 ? `0,0${NBSP}%` : `${h.delta > 0 ? '▲' : '▼'} ${nEs(Math.abs(h.delta), 1)}${NBSP}%`;
  const big = h.delta != null && Math.abs(h.delta) >= 8 ? ' is-big' : '';
  const sub = [pinned ? 'Fijado para comparar' : '', h.chain, h.zone, h.adultsOnly ? 'Adults only' : ''].filter(Boolean).join(' · ');
  const stock = h.stock;
  const index = h.idx;
  return `<tr class="hrow${open ? ' is-open' : ''}${selected ? ' is-selected' : ''}${pinned ? ' is-pinned' : ''}" data-sheet-row="${esc(h.key)}"${variant === 'B' ? ` tabindex="0"${selected ? ' aria-current="true"' : ''}` : ''}>
    <td class="hsheet__sticky hsheet__sticky--rank"><button type="button" class="hrow__chev" data-sheet-toggle="${esc(h.key)}" aria-expanded="${open}" aria-controls="hdetail-${index}" aria-label="Tarifas por habitación de ${esc(h.name)}" title="Tipos de habitación"><svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor" aria-hidden="true"><path d="M9 6l7 6-7 6z"/></svg></button><span class="hrow__rank">${h.rank}</span></td>
    <td class="hsheet__sticky hsheet__sticky--name"><span class="hrow__name">${esc(h.name)}</span>${sub ? `<span class="hrow__sub">${esc(sub)}</span>` : ''}</td>
    <td class="num hrow__adr">${eur(h.adr)}</td>
    ${wide ? `<td class="num hrow__pers">${eur(h.pers)}</td>` : ''}
    <td><div class="vsbar"><div class="vsbar__track"><i class="vsbar__mid"></i>${h.vsMedian == null ? '' : `<i class="vsbar__fill ${positive ? 'is-up' : 'is-down'}" style="left:${positive ? 50 : 50 - w}%;width:${w}%"></i>`}</div><span class="vsbar__val${positive ? '' : ' is-down'}">${pctTxt(h.vsMedian, 0)}</span></div></td>
    <td class="num"><span class="hdelta hdelta--${deltaTone}${big}">${deltaText}</span></td>
    <td class="num">${h.stab == null ? '<span class="dim">—</span>' : `<span class="hstab hstab--${stabTone}" title="${esc(`${nEs(h.stabObs)} observaciones`)}">${nEs(h.stab, 0)}</span>`}</td>
    <td class="num">${h.nota == null ? '<span class="dim">—</span>' : nEs(h.nota, 1)}</td>
    ${wide ? `<td class="num dim">${h.reviews == null ? '—' : nEs(h.reviews)}</td>` : ''}
    <td>${h.cancel === true ? '<span class="pos">Gratis</span>' : h.cancel === false ? '<span class="dim">No</span>' : '<span class="dim">—</span>'}</td>
    <td class="num">${stock.tone === 'none' ? '<span class="dim">—</span>' : `<span class="hstock hstock--${stock.tone}">${esc(stock.text)}</span>`}</td>
  </tr>${open ? `<tr class="hdetail" id="hdetail-${index}"><td colspan="${hotelSheetColumns(variant).length}"><div class="hdetail__box" data-sheet-rooms-panel="${esc(h.key)}">${hotelRoomsPanelHTML(h, State.hotelRateDetails[State.targetId]?.[h.key] || null)}</div></td></tr>` : ''}`;
}

function hotelSheetBodyHTML(list, groups, variant) {
  const colspan = hotelSheetColumns(variant).length;
  const pinned = variant === 'B' && State.hotelPinnedKey ? hotelSheetHotel(State.hotelPinnedKey) : null;
  const top = pinned ? hotelSheetRowHTML(pinned, variant) : '';
  const rest = (rows) => (pinned ? rows.filter((h) => h.key !== pinned.key) : rows);
  if (!groups) return top + rest(list).map((h) => hotelSheetRowHTML(h, variant)).join('');
  return top + groups.map((g) => ({ ...g, hotels: rest(g.hotels) })).filter((g) => g.hotels.length).map((g) => `<tr class="hgroup"><td colspan="${colspan}"><div class="hgroup__box"><strong>${esc(g.label)}</strong><span>${g.hotels.length} ${g.hotels.length === 1 ? 'hotel' : 'hoteles'} · mediana ${eur(g.median || null)}</span></div></td></tr>${g.hotels.map((h) => hotelSheetRowHTML(h, variant)).join('')}`).join('');
}

/* tarifas por habitación: panel desplegable de la fila (ambas variantes) */
function hotelRateGroups(rows) {
  const groups = new Map();
  rows.slice().sort((a, b) => String(a.roomType || '').localeCompare(String(b.roomType || ''), 'es', { sensitivity: 'base' }) || Number(a.maxOccupancy || 0) - Number(b.maxOccupancy || 0) || Number(a.priceFinal ?? Infinity) - Number(b.priceFinal ?? Infinity)).forEach((rate) => {
    const key = `${rate.roomType || ''}::${rate.maxOccupancy ?? ''}`;
    if (!groups.has(key)) groups.set(key, { roomType: rate.roomType, maxOccupancy: rate.maxOccupancy, rates: [] });
    groups.get(key).rates.push(rate);
  });
  return [...groups.values()];
}

function rateNightly(rate) {
  const total = rate.priceFinal == null ? null : Number(rate.priceFinal);
  const nights = rateNights(rate.checkIn, rate.checkOut);
  return Number.isFinite(total) && nights ? total / nights : null;
}

function hotelRoomsPanelHTML(h, cached) {
  const retry = `<button type="button" class="btn btn--sm" data-hotel-load-rates="${esc(h.key)}">Reintentar</button>`;
  if (!cached || cached.status === 'loading') return '<div class="hdetail__state"><i class="hdetail__spin" aria-hidden="true"></i>Comprobando tarifas capturadas…</div>';
  if (cached.status === 'error') return `<div class="hdetail__state"><span class="neg">${esc(cached.message || 'No se pudo cargar el desglose.')}</span>${retry}</div>`;
  if (!cached.rows || !cached.rows.length) return `<div class="hdetail__state"><span>No hay tarifas de detalle capturadas para este hotel.</span>${retry}</div>`;
  const rows = cached.rows;
  const groups = hotelRateGroups(rows);
  const first = rows[0];
  const nights = rateNights(first.checkIn, first.checkOut);
  const freeCount = rows.filter((rate) => rate.freeCancellation === true).length;
  const genius = rows.some((rate) => rate.genius === true);
  const independent = cached.provenance && cached.provenance.scope === 'independent_latest_detail';
  const ddmm = (iso) => { const [, m, d] = String(iso || '').split('-'); return d && m ? `${d}/${m}` : '—'; };
  const stay = first.checkIn && first.checkOut ? `${ddmm(first.checkIn)} → ${ddmm(first.checkOut)}${nights ? ` · ${nights} noches` : ''}${first.adults ? ` · ${first.adults} adultos` : ''}` : 'No informada';
  const body = groups.map((g) => `<tbody><tr class="hrooms__group"><th colspan="7" scope="rowgroup"><strong>${esc(g.roomType || 'Habitación sin identificar')}</strong><span>${g.rates.length} ${g.rates.length === 1 ? 'tarifa' : 'tarifas'}${g.maxOccupancy != null ? ` · máx. ${nEs(g.maxOccupancy)} personas` : ''}</span></th></tr>${g.rates.map((rate) => {
    const total = rate.priceFinal == null ? null : Number(rate.priceFinal);
    const original = rate.priceOriginal == null ? null : Number(rate.priceOriginal);
    const nightly = rateNightly(rate);
    const discount = Number.isFinite(original) && Number.isFinite(total) && original > total;
    const stock = rate.unitsLeft == null ? { text: 'Sin aviso', tone: 'none' } : hotelStockInfo({ unitsLeft: rate.unitsLeft });
    const free = rate.freeCancellation === true;
    return `<tr>
      <td>${esc(rate.board ? compactBoardLabel(rate.board) : 'Sin informar')}</td>
      <td>${rate.maxOccupancy == null ? '<span class="dim">Sin informar</span>' : `<span class="mono">${nEs(rate.maxOccupancy)}</span> ${Number(rate.maxOccupancy) === 1 ? 'persona' : 'personas'}`}</td>
      <td><span class="${free ? 'pos' : rate.freeCancellation === false ? '' : 'dim'} hrooms__cancel">${free ? 'Gratuita' : rate.freeCancellation === false ? 'No gratuita' : 'Sin informar'}</span>${rate.cancellationText || rate.prepaymentText ? `<small>${[rate.cancellationText, rate.prepaymentText].filter(Boolean).map(esc).join(' · ')}</small>` : ''}</td>
      <td>${stock.tone === 'none' ? '<span class="dim">Sin aviso</span>' : `<span class="hstock hstock--${stock.tone}">${esc(stock.text)}</span>`}</td>
      <td>${rate.program ? `<span class="hrooms__prog">${esc(rate.program)}</span>` : '<span class="dim">Sin programa</span>'}${discount ? `<small class="pos">−${nEs(Math.round((original - total) / original * 100))}${NBSP}% · ahorro ${eur(original - total)}</small>` : ''}</td>
      <td class="num"><strong>${Number.isFinite(total) ? eur(total) : 'Sin informar'}</strong>${discount ? `<s>${eur(original)}</s>` : ''}</td>
      <td class="num hrooms__night${nightly != null && h.adr != null && Math.abs(nightly - h.adr) < 0.5 ? ' is-sheet' : ''}">${nightly == null ? '—' : eur(nightly)}</td>
    </tr>`;
  }).join('')}</tbody>`).join('');
  return `<div class="hdetail__head">
      <div><strong>Tarifas por habitación</strong><span class="mono">${groups.length} ${groups.length === 1 ? 'tipo' : 'tipos'} de habitación · ${rows.length} ${rows.length === 1 ? 'tarifa' : 'tarifas'}</span></div>
      <div class="hdetail__ctx">
        <span><b>Estancia</b> ${esc(stay)}</span>
        <span><b>Cancelación gratuita</b> ${freeCount} de ${rows.length} ${rows.length === 1 ? 'tarifa' : 'tarifas'}</span>
        ${genius ? '<span class="chip hdetail__genius">Participa en Genius</span>' : ''}
        <button type="button" class="btn btn--xs" data-sheet-ask="${esc(h.key)}">Preguntar al Copilot</button>
      </div>
    </div>
    <div class="hrooms__wrap"><table class="hrooms"><caption class="sr-only">Tarifas de ${esc(h.name)} por habitación, régimen y condiciones</caption><colgroup><col class="hrooms__c1"><col class="hrooms__c2"><col class="hrooms__c3"><col class="hrooms__c4"><col class="hrooms__c5"><col class="hrooms__c6"><col class="hrooms__c7"></colgroup><thead><tr><th scope="col">Régimen</th><th scope="col" title="Capacidad máxima informada de la habitación, no la ocupación de la búsqueda">Ocupación máx.</th><th scope="col">Cancelación · pago</th><th scope="col">Cupo</th><th scope="col">Programa / descuento</th><th scope="col" class="r">Total estancia</th><th scope="col" class="r">Por noche</th></tr></thead>${body}</table></div>
    <p class="hdetail__foot">Capturado el ${esc(fmtStamp(first.capturedAt))}${independent ? ' · captura independiente, no vinculada a la oferta de la hoja: fecha, estancia y ocupación pueden diferir' : ''} · Genius es una señal de participación del hotel; solo se muestra como descuento cuando la oferta lo declara.</p>`;
}

function paintHotelRooms(key) {
  const h = hotelSheetHotel(key);
  if (!h) return;
  const cached = State.hotelRateDetails[State.targetId]?.[key] || null;
  $$(`[data-sheet-rooms-panel="${CSS.escape(key)}"]`).forEach((el) => { el.innerHTML = hotelRoomsPanelHTML(h, cached); });
  if (State.hotelVariant === 'B' && State.hotelSelectedKey === key) paintHotelAside();
}

async function ensureHotelRateDetails(key) {
  const targetId = State.targetId;
  if (!State.hotelRateDetails[targetId]) State.hotelRateDetails[targetId] = {};
  const cache = State.hotelRateDetails[targetId];
  const cached = cache[key];
  if (cached && cached.status !== 'loading' && cached.status !== 'error') { paintHotelRooms(key); return; }
  if (State.hotelRateDetailPromises[`${targetId}:${key}`]) return State.hotelRateDetailPromises[`${targetId}:${key}`];
  cache[key] = { status: 'loading' };
  paintHotelRooms(key);
  const latest = State.snapshots[targetId]?.latest;
  // la evidencia vinculada solo existe para hoteles de la última foto; el resto usa su detalle independiente
  const snapshotId = latest?.rows?.some((row) => row.hotelKey === key) ? latest.snapshot?.id : null;
  const promise = api(`/api/hotels/rate-details?targetId=${targetId}&hotelKey=${encodeURIComponent(key)}${snapshotId ? `&snapshotId=${snapshotId}` : ''}`)
    .then((payload) => { cache[key] = { status: payload.rows?.length ? 'loaded' : 'empty', rows: payload.rows || [], provenance: payload.provenance }; })
    .catch((error) => { cache[key] = { status: 'error', message: error.message }; })
    .finally(() => { delete State.hotelRateDetailPromises[`${targetId}:${key}`]; if (targetId === State.targetId) paintHotelRooms(key); });
  State.hotelRateDetailPromises[`${targetId}:${key}`] = promise;
  return promise;
}

/* panel lateral de la variante B */
function hotelAsideHTML(h) {
  const sheet = State.hotelSheet;
  if (!h) return '<div class="haside__empty"><strong>Selecciona un hotel</strong><span>Verás su posición en el set y el cambio entre fotos.</span></div>';
  const model = sheet.model;
  const cached = State.hotelRateDetails[State.targetId]?.[h.key] || null;
  const rates = cached && cached.rows ? cached.rows : [];
  const genius = !rates.length ? null : rates.some((rate) => rate.genius === true) ? true : rates.every((rate) => rate.genius === false) ? false : null;
  const span = (model.maxAdr != null && model.minAdr != null && model.maxAdr > model.minAdr) ? model.maxAdr - model.minAdr : null;
  const pos = (v) => (span ? Math.max(0, Math.min(100, ((v - model.minAdr) / span) * 100)) : 50);
  const strip = model.hotels.filter((x) => x.adr != null).map((x) => `<i class="haside__dot${x.key === h.key ? ' is-me' : ''}" style="left:${pos(x.adr)}%" title="${esc(`${x.name} · ${eur(x.adr)}`)}"></i>`).join('');
  const nightsText = h.row.nights ? `Total ${h.row.nights} noches` : 'Total estancia';
  const facts = [
    ['ADR/pers', eur(h.pers), ''], [nightsText, eur(h.row.price), ''], ['Estabilidad', h.stab == null ? '—' : `${nEs(h.stab, 0)}/100`, ''],
    ['Nota', h.nota == null ? '—' : `${nEs(h.nota, 1)}${h.reviews == null ? '' : ` · ${nEs(h.reviews)} reseñas`}`, ''],
    ['Cancelación', h.cancel === true ? 'Gratis' : h.cancel === false ? 'Sin cancelación' : '—', h.cancel === true ? 'pos' : ''],
    ['Disponibilidad', h.stock.tone === 'none' ? 'Sin aviso' : h.stock.text, h.stock.tone === 'warn' || h.stock.tone === 'bad' ? 'warn' : ''],
    ['Genius', genius === true ? 'Genius' : genius === false ? 'No participa' : '—', genius === true ? 'ac' : ''],
    ['Distancia playa', h.row.beachDistance || '—', ''],
  ];
  const roomGroups = hotelRateGroups(rates).map((g) => {
    const nightly = g.rates.map(rateNightly).filter((v) => v != null);
    const units = g.rates.map((rate) => rate.unitsLeft).filter((v) => v != null && v > 0);
    const program = g.rates.find((rate) => rate.program);
    const tag = units.length ? (Math.min(...units) === 1 ? 'Queda 1' : `Quedan ${Math.min(...units)}`) : program ? (/genius/i.test(program.program) ? 'Genius' : 'Oferta') : 'Disponible';
    const tone = units.length ? 'warn' : program ? 'ac' : 'plain';
    return `<div class="haside__room"><span class="haside__roomname"><span>${esc(g.roomType || 'Habitación sin identificar')}</span><small>${g.maxOccupancy != null ? `máx. ${nEs(g.maxOccupancy)} pers. · ` : ''}${g.rates.length} ${g.rates.length === 1 ? 'tarifa' : 'tarifas'}</small></span><span class="hstock hstock--${tone}">${esc(tag)}</span><strong class="mono">${nightly.length ? `desde ${eur(Math.min(...nightly))}` : '—'}</strong></div>`;
  }).join('');
  const roomsBody = !cached || cached.status === 'loading' ? '<p class="haside__note">Comprobando tarifas capturadas…</p>'
    : cached.status === 'error' ? `<p class="haside__note neg">${esc(cached.message || 'No se pudo cargar el desglose.')}</p>`
    : roomGroups || '<p class="haside__note">No hay tarifas de detalle capturadas para este hotel.</p>';
  const vsBadge = h.vsMedian == null ? '' : `<span class="chip haside__vs${h.vsMedian >= 0 ? ' is-up' : ''}">${pctTxt(h.vsMedian, 0)} vs mediana</span>`;
  const sub = [h.chain, h.zone, h.adultsOnly ? 'Adults only' : ''].filter(Boolean).join(' · ');
  return `<div class="haside__head"><div class="haside__kicker"><span>Posición ${h.rank} de ${model.hotels.length}</span>${vsBadge}</div><h2>${esc(h.name)}</h2>${sub ? `<span class="haside__sub">${esc(sub)}</span>` : ''}</div>
    <div class="haside__price"><div><span class="kpi__label">ADR hab/noche</span><strong>${h.adr == null ? '—' : nEs(h.adr)}<span>${NBSP}€</span></strong></div><div class="haside__prev">${h.prevAdr == null ? '' : `<span>antes ${eur(h.prevAdr)}</span>`}<span class="${h.isNew ? 'ac' : h.delta > 0 ? 'pos' : h.delta < 0 ? 'neg' : ''}">${h.isNew ? 'Nuevo en el set' : h.delta == null ? 'Sin comparativa' : pctTxt(h.delta, 1)}</span></div></div>
    <div class="haside__strip"><span class="kpi__label">Lugar en el set</span><div class="haside__track"><i class="haside__line"></i>${strip}${span ? `<i class="haside__med" style="left:${pos(model.median)}%"></i>` : ''}</div><div class="haside__scale"><span>${eur(model.minAdr)}</span><span>mediana ${eur(model.median)}</span><span>${eur(model.maxAdr)}</span></div></div>
    <dl class="haside__facts">${facts.map(([k, v, tone]) => `<div><dt>${esc(k)}</dt><dd class="${tone}">${esc(v)}</dd></div>`).join('')}</dl>
    <div class="haside__rooms"><div class="haside__roomshead"><span class="kpi__label">Tipos de habitación</span><button type="button" class="link-button haside__link" data-sheet-rooms="${esc(h.key)}">Ver tarifas</button></div>${roomsBody}</div>
    <div class="haside__actions"><button type="button" class="btn btn--primary haside__ask" data-sheet-ask="${esc(h.key)}">Preguntar al Copilot</button><button type="button" class="btn haside__pin" data-sheet-pin="${esc(h.key)}" aria-pressed="${State.hotelPinnedKey === h.key}">Fijar para comparar</button></div>`;
}

function paintHotelAside() {
  const aside = $('#hotelAside');
  if (!aside) return;
  aside.innerHTML = hotelAsideHTML(hotelSheetHotel(State.hotelSelectedKey));
}

/* barra de herramientas */
function hotelToolbarHTML(model) {
  const views = SHEET_VIEWS.map((v) => {
    const count = model.hotels.filter(v.test).length;
    const active = State.hotelView === v.id;
    return `<button type="button" class="${active ? 'is-active' : ''}" data-sheet-view="${v.id}" aria-pressed="${active}"${v.hint ? ` title="${esc(v.hint)}"` : ''}>${esc(v.label)}<b>${count}</b></button>`;
  }).join('');
  const chips = SHEET_CHIPS.map((c) => {
    const on = State.hotelChips.includes(c.id);
    return `<button type="button" class="pill${on ? ' is-active' : ''}" data-sheet-chip="${c.id}" aria-pressed="${on}">${esc(c.label)}<b>${model.hotels.filter(c.test).length}</b></button>`;
  }).join('');
  const densities = ['compacta', 'equilibrada', 'espaciosa'].map((d) => {
    const on = State.density === d;
    return `<button type="button" class="${on ? 'is-active' : ''}" data-sheet-density="${d}" aria-pressed="${on}" aria-label="Densidad ${d}" title="Densidad ${d}"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">${HOTEL_DENSITY_ICONS[d]}</svg></button>`;
  }).join('');
  return { views, chips, densities };
}

/* Selector del control enfocado: la barra, las cabeceras y las filas se reconstruyen al repintar y el foco no debe perderse. */
function hotelFocusSelector(el) {
  if (!(el instanceof HTMLElement)) return null;
  for (const [prop, attr] of [['sheetView', 'data-sheet-view'], ['sheetChip', 'data-sheet-chip'], ['sheetDensity', 'data-sheet-density'], ['sheetSort', 'data-sheet-sort'], ['sheetToggle', 'data-sheet-toggle'], ['sheetVariant', 'data-sheet-variant'], ['sheetRow', 'data-sheet-row']]) {
    if (el.dataset[prop] !== undefined) return `${el.tagName.toLowerCase()}[${attr}="${CSS.escape(el.dataset[prop])}"]`;
  }
  return null;
}

function paintHotelSheet({ focusKey = null } = {}) {
  const sheet = State.hotelSheet;
  if (!sheet || !$('#hotelTable')) return;
  const keepFocus = hotelFocusSelector(document.activeElement);
  const { model } = sheet;
  const variant = State.hotelVariant;
  const list = hotelSheetSort(hotelSheetFilter(model, { view: State.hotelView, chips: State.hotelChips, search: State.hotelSearch }), State.hotelSort);
  sheet.list = list;
  if (variant === 'B' && !list.some((h) => h.key === State.hotelSelectedKey)) State.hotelSelectedKey = list[0] ? list[0].key : null;
  const tools = hotelToolbarHTML(model);
  $('#hotelViews').innerHTML = tools.views;
  $('#hotelChips').innerHTML = tools.chips;
  $('#hotelDensity').innerHTML = tools.densities;
  $('#hotelColgroup').innerHTML = hotelSheetColgroupHTML(variant);
  $('#hotelTableHead').innerHTML = hotelSheetHeadHTML(variant);
  $('#hotelSheetBody').innerHTML = hotelSheetBodyHTML(list, hotelSheetGroups(list, State.hotelGroup, model), variant);
  $('#hotelEmpty').hidden = list.length > 0;
  $('#hotelSearchClear').hidden = !State.hotelSearch;
  $('#exportHotels').disabled = list.length === 0;
  const med = list.length === model.hotels.length ? model.median : median(list.map((h) => h.adr).filter((v) => v != null));
  $('#hotelFootLeft').textContent = `${list.length} de ${model.hotels.length} hoteles · mediana ${eur(med || null)}`;
  $$('[data-sheet-variant]').forEach((b) => { const on = b.dataset.sheetVariant === variant; b.classList.toggle('is-active', on); b.setAttribute('aria-pressed', String(on)); });
  const group = $('#hotelGroup'); if (group) group.value = State.hotelGroup;
  if (variant === 'B') {
    paintHotelAside();
    if (State.hotelSelectedKey && !State.hotelRateDetails[State.targetId]?.[State.hotelSelectedKey]) void ensureHotelRateDetails(State.hotelSelectedKey);
  }
  persistHotelQuery();
  if (focusKey) $(`[data-sheet-toggle="${CSS.escape(focusKey)}"]`)?.focus();
  else if (keepFocus) $(keepFocus)?.focus({ preventScroll: true });
  const table = $('#hotelTable');
  if (table && !sheet.painted) { sheet.painted = true; table.classList.add('is-entering'); setTimeout(() => table.classList.remove('is-entering'), 900); }
}

function hotelSheetKpisHTML(model, metrics, snapshot) {
  const hotels = model.hotels;
  const rows = hotels.map((h) => h.row);
  const priced = hotels.filter((h) => h.adr != null);
  const adr = priced.length ? priced.reduce((sum, h) => sum + h.adr, 0) / priced.length : null;
  const persValues = hotels.filter((h) => h.pers != null);
  const pers = persValues.length ? persValues.reduce((sum, h) => sum + h.pers, 0) / persValues.length : null;
  const allInc = rows.filter((r) => (r.board || '').toLowerCase().includes('todo')).length;
  const rated = hotels.filter((h) => h.nota != null);
  const rating = rated.length ? rated.reduce((sum, h) => sum + h.nota, 0) / rated.length : null;
  const reviews = hotels.reduce((sum, h) => sum + (h.reviews || 0), 0);
  const freeCancel = hotels.filter((h) => h.cancel === true).length;
  const scarce = hotels.filter((h) => h.scarcity).length;
  const soldOut = hotels.filter((h) => h.soldOut).length;
  const pct = (n) => (hotels.length ? Math.round((n / hotels.length) * 100) : 0);
  const mv = metrics && metrics.movement;
  const comparable = mv && mv.isComparable;
  const cells = [
    { label: 'En mercado', value: nEs(hotels.length), unit: '', foot: 'con régimen detectado' },
    { label: 'ADR hab/noche', value: nEs(adr, 0), unit: '€', foot: `mediana ${eur(model.median)} · pers. ${eur(pers)}` },
    { label: 'Todo incluido', value: String(pct(allInc)), unit: '%', foot: `${allInc}/${hotels.length} hoteles` },
    { label: 'Rating medio', value: rating == null ? '—' : nEs(rating, 1), unit: '', foot: `${nEs(reviews)} reseñas` },
    { label: 'Cancel. gratis', value: String(pct(freeCancel)), unit: '%', foot: `${freeCancel}/${hotels.length} la ofrecen` },
    { label: 'Con escasez', value: String(scarce), unit: '', foot: `${soldOut} sold-out` },
    { label: 'Movimiento', aria: comparable ? `${mv.priceIncreases} subidas y ${mv.priceDrops} bajadas` : '', value: comparable ? `▲${mv.priceIncreases} ▼${mv.priceDrops}` : '—', unit: '', foot: comparable ? `entre foto #${mv.previousSnapshotId} y #${snapshot.id}` : 'Sin comparativa disponible' },
  ];
  return cells.map((c) => `<div class="kpi-strip__cell"><span class="kpi-strip__label">${esc(c.label)}</span><div class="kpi-strip__value"><strong${c.aria ? ` aria-label="${esc(c.aria)}"` : ''}>${esc(c.value)}</strong>${c.unit ? `<span>${c.unit}</span>` : ''}</div><span class="kpi-strip__foot" title="${esc(c.foot)}">${esc(c.foot)}</span></div>`).join('');
}

async function renderHotels() {
  const host = mount('hotels');
  if (!Number.isInteger(State.targetId)) {
    renderNoActiveTarget(host, 'Hoteles', 'Tarifas y condiciones del set competitivo.');
    return;
  }
  const targetId = State.targetId;
  restoreHotelQuery(targetId);
  destroyBiMap();
  skeleton(host, 'list');
  let s, m, stabilityPayload;
  try { [s, m, stabilityPayload] = await Promise.all([getSnapshot(targetId), getMetrics(targetId), getHotelStability(targetId)]); }
  catch (e) { host.innerHTML = `<div class="page">${pageHead('Hoteles', 'Mercado activo', '')}<div class="inline-error">No se pudieron cargar los hoteles: ${esc(e.message)}</div></div>`; return; }
  if (targetId !== State.targetId || State.view !== 'hotels') return;
  if (m.currencyPolicy?.status === 'blocked') { host.innerHTML = `<div class="page"><div class="inline-error">${esc(m.currencyPolicy.reason)}</div></div>`; return; }

  const model = hotelSheetModel(s.latest.rows || [], m, stabilityPayload.stability || []);
  State.hotelSheet = { model, snapshot: s.latest.snapshot, metrics: m, list: [] };
  const target = activeTarget();
  const variant = State.hotelVariant;
  const tools = hotelToolbarHTML(model);
  const aside = variant === 'B' ? '<aside class="haside" id="hotelAside" aria-label="Detalle del hotel seleccionado" aria-live="polite"></aside>' : '';

  const isSheet = State.hotelTab === 'sheet';
  const tabs = [['sheet', 'Hoja de mercado', `${model.hotels.length} hoteles`], ['bi', 'Panel de análisis', 'BI · rate shopping']];
  const biPanel = '<div id="biHost"></div>';
  host.innerHTML = `<div class="page hsheet-page">
    <div class="page-head">
      <div><h1>Hoteles</h1><p>Tarifas y condiciones del set competitivo · ${esc(target ? target.name : 'Mercado activo')}</p></div>
      ${isSheet ? `<div class="actions">
        <div class="variant-switch" role="group" aria-label="Variante de la hoja">
          <span>Variante</span>
          <div class="seg"><button type="button" data-sheet-variant="A" aria-pressed="${variant === 'A'}" class="${variant === 'A' ? 'is-active' : ''}">A · Tabla</button><button type="button" data-sheet-variant="B" aria-pressed="${variant === 'B'}" class="${variant === 'B' ? 'is-active' : ''}">B · Tabla + detalle</button></div>
        </div>
        <button type="button" class="btn btn--icon-text" id="exportHotels"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M12 4v11m0 0-4-4m4 4 4-4M5 19h14"/></svg>Exportar CSV</button>
      </div>` : ''}
    </div>
    <div class="htabs" role="tablist" aria-label="Secciones de hoteles">${tabs.map(([id, label, hint]) => `<button type="button" role="tab" class="htabs__tab${State.hotelTab === id ? ' is-active' : ''}" id="hotelTab-${id}" data-hotel-tab="${id}" aria-selected="${State.hotelTab === id}" aria-controls="hotelTabPanel" tabindex="${State.hotelTab === id ? 0 : -1}">${esc(label)}<span>${esc(hint)}</span></button>`).join('')}</div>
    <div class="htabpanel" id="hotelTabPanel" role="tabpanel" aria-labelledby="hotelTab-${State.hotelTab}">
    ${isSheet ? `    <section class="kpi-strip" aria-label="Resumen del set competitivo">${hotelSheetKpisHTML(model, m, s.latest.snapshot)}</section>
    <div class="hsheet-layout${variant === 'B' ? ' has-aside' : ''}">
      <div class="hsheet card">
        <div class="hsheet__bar">
          <div class="seg" id="hotelViews" role="group" aria-label="Vistas guardadas">${tools.views}</div>
          <i class="hsheet__bar-sep" aria-hidden="true"></i>
          <div class="hsheet__chips" id="hotelChips" role="group" aria-label="Filtros combinables">${tools.chips}</div>
          <span class="hsheet__spacer"></span>
          <label class="hsheet__search"><svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="m20 20-4-4"/></svg><input type="search" id="hotelSearch" value="${esc(State.hotelSearch)}" placeholder="Hotel, cadena o zona" aria-label="Buscar hoteles por nombre, cadena o zona" autocomplete="off" /><button type="button" id="hotelSearchClear" aria-label="Borrar búsqueda"${State.hotelSearch ? '' : ' hidden'}>×</button></label>
          <label class="hsheet__group"><span>Agrupar</span><select id="hotelGroup" aria-label="Agrupar hoteles">${SHEET_GROUPS.map((g) => `<option value="${g.id}"${State.hotelGroup === g.id ? ' selected' : ''}>${esc(g.label)}</option>`).join('')}</select></label>
          <div class="seg seg--icons" id="hotelDensity" role="group" aria-label="Densidad de filas">${tools.densities}</div>
        </div>
        <div class="hsheet__scroll" id="hotelScroll" tabindex="0" role="region" aria-label="Hoja de mercado: desplazamiento horizontal y vertical">
          <table class="hsheet__table" id="hotelTable" data-variant="${variant}">
            <caption class="sr-only">Hoteles del set competitivo con tarifa, posición frente a la mediana, variación entre fotos, estabilidad, nota, cancelación y disponibilidad</caption>
            <colgroup id="hotelColgroup"></colgroup>
            <thead id="hotelTableHead"></thead>
            <tbody id="hotelSheetBody"></tbody>
          </table>
          <div class="hsheet__empty" id="hotelEmpty" hidden>
            <i aria-hidden="true"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="6.5"/><path d="m20 20-4-4"/></svg></i>
            <strong>Ningún hotel coincide</strong><span>Prueba con otro nombre o quita algún filtro.</span>
            <button type="button" class="btn" data-sheet-reset>Restablecer filtros</button>
          </div>
        </div>
        <div class="hsheet__foot"><span id="hotelFootLeft"></span><span>Booking · GraphQL · foto #${s.latest.snapshot.id} · ${esc(fmtStamp(s.latest.snapshot.scrapedAt))}</span></div>
      </div>
      ${aside}
    </div>
` : biPanel}
    </div>
  </div>`;
  if (!isSheet) { void renderHotelsBI($('#biHost'), model, m); return; }
  paintHotelSheet();
}

/* ---- eventos de la hoja (delegados desde wireEvents) ---- */
function toggleHotelExpand(key) {
  State.hotelExpanded[key] = !State.hotelExpanded[key];
  paintHotelSheet({ focusKey: key });
  if (State.hotelExpanded[key]) void ensureHotelRateDetails(key);
}

function activateHotelRow(key) {
  if (State.hotelVariant === 'B') {
    if (State.hotelSelectedKey === key) return;
    State.hotelSelectedKey = key;
    paintHotelSheet();
  } else toggleHotelExpand(key);
}

function setHotelSort(key) {
  if (!SHEET_SORT_KEYS.includes(key)) return;
  State.hotelSort = State.hotelSort.key === key ? { key, dir: State.hotelSort.dir * -1 } : { key, dir: key === 'name' || key === 'avail' ? 1 : -1 };
  paintHotelSheet();
}

function resetHotelQuery() {
  State.hotelView = 'market'; State.hotelChips = []; State.hotelSearch = ''; State.hotelGroup = 'none'; State.hotelSort = defaultHotelSort();
  const input = $('#hotelSearch'); if (input) input.value = '';
  paintHotelSheet();
}

function setHotelVariant(variant) {
  if (!['A', 'B'].includes(variant) || variant === State.hotelVariant) return;
  State.hotelVariant = variant;
  writePref(HOTEL_VARIANT_KEY, variant);
  renderHotels();
}

function exportHotels() {
  const list = State.hotelSheet && State.hotelSheet.list;
  if (!list || !list.length) return;
  const blob = new Blob([hotelSheetCsv(list)], { type: 'text/csv;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `atlas-hoteles-${State.targetId}.csv`;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  toast(`CSV exportado · ${list.length} ${list.length === 1 ? 'hotel' : 'hoteles'}`, 'ok');
}

function setHotelTab(tab) {
  if (!['sheet', 'bi'].includes(tab)) return;
  State.hotelTab = tab;
  writePref(HOTEL_TAB_KEY, tab);
  renderHotels().then(() => $(`#hotelTab-${tab}`)?.focus());
}

function handleHotelSheetClick(e) {
  const t = e.target instanceof Element ? e.target : null;
  if (!t || !t.closest('.hsheet-page')) return false;
  const tab = t.closest('[data-hotel-tab]');
  if (tab) { if (tab.dataset.hotelTab !== State.hotelTab) setHotelTab(tab.dataset.hotelTab); return true; }
  const view = t.closest('[data-sheet-view]');
  if (view) { State.hotelView = view.dataset.sheetView; paintHotelSheet(); return true; }
  const chip = t.closest('[data-sheet-chip]');
  if (chip) { const id = chip.dataset.sheetChip; State.hotelChips = State.hotelChips.includes(id) ? State.hotelChips.filter((x) => x !== id) : [...State.hotelChips, id]; paintHotelSheet(); return true; }
  const sort = t.closest('[data-sheet-sort]');
  if (sort) { setHotelSort(sort.dataset.sheetSort); return true; }
  const density = t.closest('[data-sheet-density]');
  if (density) { applyDensity(density.dataset.sheetDensity); paintHotelSheet(); return true; }
  const variant = t.closest('[data-sheet-variant]');
  if (variant) { setHotelVariant(variant.dataset.sheetVariant); return true; }
  const toggle = t.closest('[data-sheet-toggle]');
  if (toggle) { toggleHotelExpand(toggle.dataset.sheetToggle); return true; }
  const rooms = t.closest('[data-sheet-rooms]');
  if (rooms) {
    const key = rooms.dataset.sheetRooms;
    State.hotelExpanded[key] = true;
    paintHotelSheet({ focusKey: key });
    void ensureHotelRateDetails(key);
    $(`[data-sheet-row="${CSS.escape(key)}"]`)?.scrollIntoView({ block: 'nearest' });
    return true;
  }
  const pin = t.closest('[data-sheet-pin]');
  if (pin) {
    const h = hotelSheetHotel(pin.dataset.sheetPin);
    if (!h) return true;
    const pinning = State.hotelPinnedKey !== h.key;
    State.hotelPinnedKey = pinning ? h.key : null;
    paintHotelSheet();
    $('[data-sheet-pin]')?.focus();
    toast(pinning ? `${h.name} fijado para comparar` : `${h.name} ya no está fijado`, pinning ? 'ok' : 'info');
    return true;
  }
  const ask = t.closest('[data-sheet-ask]');
  if (ask) { const h = hotelSheetHotel(ask.dataset.sheetAsk); if (h) askCopilot(`¿Cómo se posiciona ${h.name} frente al set?`); return true; }
  const load = t.closest('[data-hotel-load-rates]');
  if (load) { const key = load.dataset.hotelLoadRates; const cache = State.hotelRateDetails[State.targetId]; if (cache) delete cache[key]; void ensureHotelRateDetails(key); return true; }
  if (t.closest('#hotelSearchClear')) { State.hotelSearch = ''; const input = $('#hotelSearch'); if (input) { input.value = ''; input.focus(); } paintHotelSheet(); return true; }
  if (t.closest('[data-sheet-reset]')) { resetHotelQuery(); return true; }
  if (t.closest('#exportHotels')) { exportHotels(); return true; }
  const row = t.closest('tr[data-sheet-row]');
  if (row && !t.closest('button, a, input, select, label')) { activateHotelRow(row.dataset.sheetRow); return true; }
  return false;
}

function handleHotelSheetKey(e) {
  if (!(e.target instanceof Element)) return false;
  const tab = e.target.closest('[role="tab"][data-hotel-tab]');
  if (tab && ['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) {
    e.preventDefault();
    const order = ['sheet', 'bi'];
    const next = e.key === 'Home' ? 'sheet' : e.key === 'End' ? 'bi' : order[(order.indexOf(tab.dataset.hotelTab) + 1) % 2];
    setHotelTab(next);
    return true;
  }
  const row = e.target.closest('tr[data-sheet-row]');
  if (!row || e.target !== row) return false;
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); activateHotelRow(row.dataset.sheetRow); return true; }
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    // en la variante B las filas son seleccionables: las flechas las recorren sin tabular por todas
    const rows = $$('tr[data-sheet-row][tabindex]');
    const next = rows[rows.indexOf(row) + (e.key === 'ArrowDown' ? 1 : -1)];
    if (next) { e.preventDefault(); next.focus(); next.scrollIntoView({ block: 'nearest' }); return true; }
  }
  return false;
}

/* Abre Hoteles con un hotel buscado (ticker, paleta, señales). */
function openHotelInHotels(name) {
  State.hotelQueryTargetId = State.targetId; // evita que se restaure la consulta guardada encima de la búsqueda
  State.hotelTab = 'sheet'; // al llegar con un hotel buscado se abre la hoja
  writePref(HOTEL_TAB_KEY, 'sheet');
  State.hotelView = 'market';
  State.hotelChips = [];
  State.hotelGroup = 'none';
  State.hotelSearch = String(name || '');
  persistHotelQuery();
  setView('hotels');
}

/* ======================================================= HOTELES · PANEL DE ANÁLISIS */
function biOwnKey(targetId = State.targetId) { return `atlas.ownHotel.${targetId}`; }

function biReset(targetId) {
  const own = (() => { try { return localStorage.getItem(biOwnKey(targetId)) || ''; } catch (_) { return ''; } })();
  State.bi = {
    targetId, own, horizon: 90, board: 'all', fam: 'all', zone: null, seg: null, chain: null, focus: null,
    boxMode: 'zone', alertTab: 'all', target: BI_TARGET.initial, data: null, sheet: null, metrics: null,
    markers: {}, fitKey: null, drawer: null, error: null,
  };
}

async function loadBiData(force = false) {
  const st = State.bi;
  const key = `${st.targetId}|${st.board}|${st.fam}`;
  if (!force && st.data && st.dataKey === key) return st.data;
  const params = new URLSearchParams({ targetId: String(st.targetId), from: localIsoDate(), days: '90', board: st.board, roomFamily: st.fam });
  const data = await api(`/api/hotels/rate-calendar?${params}`);
  if (State.bi !== st) return null;
  st.data = data;
  st.dataKey = key;
  return data;
}

/* Modelo calculado del panel para el horizonte, los filtros cruzados y la fecha activa. */
function biModel() {
  const st = State.bi, data = st.data;
  const H = st.horizon;
  const dates = data.dates.slice(0, H);
  const coverage = data.coverage.dates.slice(0, H);
  const sheetByKey = new Map((st.sheet?.hotels || []).map((h) => [h.key, h]));
  const all = data.hotels.map((h) => {
    const s = sheetByKey.get(h.key);
    return {
      ...h, prices: h.prices.slice(0, H), status: h.status.slice(0, H), units: h.units.slice(0, H),
      segment: h.adultsOnly ? 'Adults only' : 'Familiar y mixto', nota: h.rating == null ? null : Number(h.rating),
      delta: s ? s.delta : null, isNew: s ? s.isNew : false, prevAdr: s ? s.prevAdr : null, adr: s ? s.adr : null,
      latestUnits: s ? s.units : null, beach: s ? s.row.beachDistance : null,
    };
  });
  const inScope = (h) => (!st.zone || h.zone === st.zone) && (!st.seg || h.segment === st.seg) && (!st.chain || h.chain === st.chain);
  const hs = all.filter(inScope);
  const dayMeds = [], dayQ1 = [], dayQ3 = [];
  for (let i = 0; i < H; i++) {
    const ps = hs.map((h) => h.prices[i]).filter((v) => v != null);
    dayMeds.push(biQuantile(ps, 0.5)); dayQ1.push(biQuantile(ps, 0.25)); dayQ3.push(biQuantile(ps, 0.75));
  }
  const captured = coverage.map((c, i) => (c ? i : null)).filter((i) => i != null);
  const latestIdx = data.latestCheckIn ? dates.indexOf(data.latestCheckIn) : -1;
  const defaultFi = latestIdx >= 0 && coverage[latestIdx] ? latestIdx : captured.length ? captured[0] : 0;
  const chosen = st.focus ? dates.indexOf(st.focus) : -1;
  const fi = chosen >= 0 ? chosen : defaultFi;
  const fMed = dayMeds[fi];
  const open = hs.filter((h) => h.prices[fi] != null).map((h) => ({ h, p: h.prices[fi] }));
  const notes = hs.map((h) => h.nota).filter((v) => v != null);
  const own = all.find((h) => h.key === st.own) || null;
  return {
    H, dates, coverage, all, hs, dayMeds, dayQ1, dayQ3, captured, fi, defaultFi, fMed, open,
    closedToday: hs.filter((h) => h.status[fi] === 'closed').length,
    lowToday: hs.filter((h) => h.status[fi] === 'low').length,
    mNota: biQuantile(notes, 0.5), own, ownP: own ? own.prices[fi] : null,
    vscore: (h, price) => biValueScore(h.nota, price, fMed, biQuantile(notes, 0.5)),
  };
}

function biFocusLabel(m) { return biDayLong(m.dates[m.fi]); }

function biFiltersHTML(m) {
  const st = State.bi, data = st.data;
  const options = [...data.hotels].sort((a, b) => String(a.name).localeCompare(String(b.name), 'es')).map((h) => `<option value="${esc(h.key)}"${h.key === st.own ? ' selected' : ''}>${esc(h.name)}</option>`).join('');
  const horizons = BI_HORIZONS.map((n) => `<button type="button" class="${st.horizon === n ? 'is-active' : ''}" data-bi-horizon="${n}" aria-pressed="${st.horizon === n}">${n} días</button>`).join('');
  const boards = (data.facets?.boards || []).map((b) => `<option value="${esc(b)}"${st.board === b ? ' selected' : ''}>${esc(b)}</option>`).join('');
  const fams = (data.facets?.roomFamilies || []).map((f) => `<option value="${esc(f)}"${st.fam === f ? ' selected' : ''}>${esc(f)}</option>`).join('');
  return `<label class="bi-field bi-field--own"><span>Hotel propio</span><select id="biOwn" class="bi-select${st.own ? ' is-set' : ''}" aria-label="Hotel propio"><option value=""${st.own ? '' : ' selected'}>Ninguno · vista de mercado</option>${options}</select></label>
    <div class="bi-field"><span>Fechas de entrada</span><div class="seg seg--sm bi-horizons" role="group" aria-label="Horizonte de fechas de entrada">${horizons}</div></div>
    <label class="bi-field"><span>Régimen</span><select id="biBoard" class="bi-select" aria-label="Régimen"><option value="all"${st.board === 'all' ? ' selected' : ''}>Todos los regímenes</option>${boards}</select></label>
    <label class="bi-field"><span>Tipo de habitación</span><select id="biFam" class="bi-select" aria-label="Tipo de habitación"><option value="all"${st.fam === 'all' ? ' selected' : ''}>Todas las habitaciones</option>${fams}</select></label>
    <span class="bi-filters__spacer"></span>
    <div class="bi-chips" id="biChips">${biChipsHTML(m)}</div>`;
}

function biChipsHTML(m) {
  const st = State.bi;
  const chips = [];
  if (st.zone) chips.push(['zone', `Zona: ${st.zone}`]);
  if (st.seg) chips.push(['seg', st.seg]);
  if (st.chain) chips.push(['chain', `Cadena: ${st.chain}`]);
  if (m.fi !== m.defaultFi) chips.push(['focus', `Entrada ${biDayLabel(m.dates[m.fi])}`]);
  return `${chips.map(([kind, label]) => `<button type="button" class="bi-chip" data-bi-clear="${kind}" aria-label="Quitar filtro ${esc(label)}">${esc(label)}<span aria-hidden="true">×</span></button>`).join('')}${chips.length ? '<button type="button" class="bi-clear" data-bi-clear="all">Limpiar</button>' : ''}<span class="bi-scope">${m.hs.length} de ${m.all.length} hoteles</span>`;
}

function biKpisHTML(m) {
  const st = State.bi, mv = st.metrics?.movement || {};
  const up = m.hs.filter((h) => h.delta > 0).length, down = m.hs.filter((h) => h.delta < 0).length;
  const latestId = st.metrics?.latestSnapshot?.id;
  const movement = { label: 'Movimiento del set', value: `▲${up} ▼${down}`, foot: mv.isComparable && mv.previousSnapshotId ? `foto #${mv.previousSnapshotId} → #${latestId}` : 'sin foto comparable' };
  const noCapture = !m.coverage[m.fi];
  const day = biDayLabel(m.dates[m.fi]);
  let cells;
  if (m.own) {
    const rank = biRankAt(m.hs, m.own.key, m.fi);
    const status = m.own.status[m.fi];
    const vs = m.vscore(m.own, m.ownP);
    cells = [
      { label: `Tu tarifa · ${day}`, value: m.ownP != null ? nEs(m.ownP) : status === 'closed' ? 'Cerrado' : '—', unit: m.ownP != null ? '€' : '', foot: rank ? `puesto ${rank.rank} de ${rank.of}` : noCapture ? 'sin captura ese día' : 'sin disponibilidad', tone: 'ac' },
      { label: 'Índice de precio', value: m.ownP != null && m.fMed ? nEs((m.ownP / m.fMed) * 100) : '—', foot: 'mediana del set = 100' },
      { label: 'Mediana del set', value: m.fMed ? nEs(m.fMed) : '—', unit: m.fMed ? '€' : '', foot: noCapture ? 'sin captura ese día' : `${m.open.length} hoteles con tarifa` },
      { label: 'Value score', value: vs ?? '—', unit: vs == null ? '' : '/100', foot: m.own.nota != null && m.mNota != null ? `nota ${nEs(m.own.nota, 1)} vs mediana ${nEs(m.mNota, 1)}` : 'sin nota publicada' },
      { label: 'Competidores cerrados', value: noCapture ? '—' : nEs(m.closedToday), foot: noCapture ? 'sin captura ese día' : `${m.lowToday} con cupo bajo ese día` },
      movement,
    ];
  } else {
    const meds = m.dayMeds.filter((v) => v != null);
    cells = [
      { label: `Mediana · ${day}`, value: m.fMed ? nEs(m.fMed) : '—', unit: m.fMed ? '€' : '', foot: m.fMed ? `P25 ${eur(m.dayQ1[m.fi])} · P75 ${eur(m.dayQ3[m.fi])}` : 'sin captura ese día' },
      { label: 'Dispersión', value: m.dayQ1[m.fi] > 0 ? nEs((m.dayQ3[m.fi] / m.dayQ1[m.fi] - 1) * 100) : '—', unit: m.dayQ1[m.fi] > 0 ? '%' : '', foot: 'P75 sobre P25' },
      { label: 'Hoteles en el alcance', value: nEs(m.hs.length), foot: noCapture ? 'sin captura ese día' : `${m.open.length} con tarifa ese día` },
      { label: 'Cerrados ese día', value: noCapture ? '—' : nEs(m.closedToday), foot: noCapture ? 'sin captura ese día' : `${m.lowToday} con cupo bajo` },
      { label: `Mediana ${m.H} días`, value: meds.length ? nEs(biQuantile(meds, 0.5)) : '—', unit: meds.length ? '€' : '', foot: meds.length ? `rango ${eur(Math.min(...meds))}–${eur(Math.max(...meds))}` : 'sin capturas en el horizonte' },
      movement,
    ];
  }
  return cells.map((k) => `<div class="kpi-strip__cell"><span class="kpi-strip__label">${esc(k.label)}</span><div class="kpi-strip__value"><strong class="${k.tone === 'ac' ? 'ac' : ''}">${esc(String(k.value))}</strong>${k.unit ? `<span>${esc(k.unit)}</span>` : ''}</div><span class="kpi-strip__foot">${esc(k.foot)}</span></div>`).join('');
}

function biZonesHTML(m) {
  const st = State.bi;
  const names = [...new Set(m.all.map((h) => h.zone).filter(Boolean))];
  const zones = names.map((z) => {
    const zs = m.all.filter((h) => h.zone === z && (!st.seg || h.segment === st.seg) && (!st.chain || h.chain === st.chain));
    const ps = zs.map((h) => h.prices[m.fi]).filter((v) => v != null);
    const med = biQuantile(ps, 0.5);
    return { z, n: zs.length, med, tone: med == null || !m.fMed ? 'none' : biMapTone(med, m.fMed) };
  }).filter((z) => z.n).sort((a, b) => (b.med ?? -1) - (a.med ?? -1));
  if (!zones.length) return '';
  return `<div class="bi-zones__head"><span>Zona</span><span>Htl · mediana</span></div>${zones.map((z) => `<button type="button" class="bi-zone${st.zone === z.z ? ' is-active' : ''}" data-bi-zone="${esc(z.z)}" aria-pressed="${st.zone === z.z}"><span class="bi-zone__name"><i class="tone-${z.tone}"></i><span>${esc(z.z)}</span></span><span class="bi-zone__meta">${z.n} · <b>${z.med == null ? '—' : eur(z.med)}</b></span></button>`).join('')}`;
}

function biRecoHTML(m) {
  const st = State.bi, own = m.own;
  const day = biDayLabel(m.dates[m.fi]);
  const capture = m.coverage[m.fi];
  const age = capture ? dataAgeDays(capture.scrapedAt) : null;
  const reco = biRecommendation({
    openPrices: m.open.map((x) => x.p), dayMedian: m.fMed, targetPct: st.target, valueScore: m.vscore(own, m.ownP),
    closed: m.closedToday, low: m.lowToday, scopeSize: m.hs.length, deltas: m.hs.map((h) => h.delta), leadDays: biDaysBetween(localIsoDate(), m.dates[m.fi]),
  });
  const head = `<div class="bi-reco__kicker"><span class="card__kicker">Tarifa sugerida · entrada ${esc(biFocusLabel(m))}</span>${reco ? `<span class="chip chip--warn" title="${esc(`${m.open.length} hoteles con tarifa · datos de hace ${age ?? '—'} días`)}">Confianza ${m.open.length < 6 ? 'baja' : (age > 14 || m.open.length < 15) ? 'media-baja' : 'media'}</span>` : ''}</div><div class="bi-reco__name">${esc(own.name)}</div>`;
  if (!reco) return `<div class="bi-card bi-reco"><div class="bi-reco__top">${head}</div><div class="bi-reco__empty">${capture ? 'Ningún hotel del alcance tiene tarifa en esta fecha.' : 'Sin captura para esta fecha de entrada. Elige una fecha capturada en el calendario.'}</div></div>`;
  const cur = m.ownP;
  const diff = cur ? (reco.suggested / cur - 1) * 100 : null;
  const label = {
    median: () => ['Mediana del set', `${reco.parts[0].n} hoteles con tarifa el ${day}`],
    target: (p) => [`Posición objetivo P${p.pct}`, `precio del percentil ${p.pct}: ${eur(p.price)}`],
    value: (p) => [`Value score ${p.score}`, p.score >= 50 ? 'tu nota permite cobrar más' : 'nota por debajo del set'],
    scarcity: (p) => ['Escasez de la competencia', `${p.closed} cerrados · ${p.low} con cupo bajo`],
    movement: (p) => ['Movimiento reciente del set', `media ${biSigned(p.movement)} % entre fotos`],
    lead: (p) => [`Antelación ${p.lead} días`, p.lead < 21 ? 'entrada cercana: margen al alza' : p.lead > 60 ? 'entrada lejana: prudencia' : 'ventana central'],
  };
  const maxAbs = Math.max(...reco.parts.filter((p) => !p.base).map((p) => Math.abs(p.value)), 1);
  const rows = reco.parts.map((p) => {
    const [k, why] = label[p.id](p);
    if (p.base) return `<div class="bi-part"><span class="bi-part__label"><span>${esc(k)}</span><small>${esc(why)}</small></span><span class="bi-part__bar"><i class="bi-part__axis"></i></span><strong class="bi-part__value is-base">${eur(p.value)}</strong></div>`;
    const w = (Math.abs(p.value) / maxAbs) * 50;
    const tone = p.value >= 0 ? 'pos' : 'neg';
    return `<div class="bi-part"><span class="bi-part__label"><span>${esc(k)}</span><small>${esc(why)}</small></span><span class="bi-part__bar"><i class="bi-part__axis"></i><i class="bi-part__fill is-${tone}" style="left:${p.value >= 0 ? 50 : 50 - w}%;width:${w.toFixed(1)}%"></i></span><strong class="bi-part__value ${tone}">${p.value >= 0 ? '+' : '−'}${nEs(Math.abs(Math.round(p.value)))} €</strong></div>`;
  }).join('');
  st.recoText = `Explica la tarifa sugerida de ${reco.suggested} € para ${own.name} el ${day}. Componentes: ${reco.parts.map((p) => `${label[p.id](p)[0]} ${Math.round(p.value)} €`).join('; ')}`;
  st.recoValue = reco.suggested;
  return `<div class="bi-card bi-reco">
    <div class="bi-reco__top">${head}
      <div class="bi-reco__values"><div><span class="bi-reco__lab">Sugerida</span><strong class="bi-reco__sug">${nEs(reco.suggested)}<span> €</span></strong></div>
      <div class="bi-reco__cur"><span class="bi-reco__lab">Actual ${cur != null ? eur(cur) : `— (${m.own.status[m.fi] === 'closed' ? 'cerrado' : 'sin captura'})`}</span>${diff == null ? '' : `<span class="bi-reco__diff ${diff >= 0 ? 'pos' : 'neg'}">${biSigned(diff)} %</span>`}</div></div>
    </div>
    <div class="bi-reco__parts">${rows}</div>
    <div class="bi-reco__foot">
      <div class="bi-reco__target"><label for="biTarget">Posición objetivo en el set</label><strong>P${st.target}</strong></div>
      <input type="range" id="biTarget" min="${BI_TARGET.min}" max="${BI_TARGET.max}" step="${BI_TARGET.step}" value="${st.target}" aria-label="Percentil objetivo">
      <div class="bi-reco__actions"><button type="button" class="btn btn--primary" data-bi-copy>Copiar tarifa</button><button type="button" class="btn" data-bi-ask-reco>Explicar con Copilot</button></div>
      <span class="bi-reco__note">Basada en precios públicos de hace ${age ?? '—'} ${age === 1 ? 'día' : 'días'}. No incluye ocupación, pickup ni restricciones propias.</span>
    </div>
  </div>`;
}

function biDayHTML(m) {
  const st = State.bi;
  const sorted = [...m.open].sort((a, b) => a.p - b.p);
  const options = [...st.data.hotels].sort((a, b) => String(a.name).localeCompare(String(b.name), 'es')).map((h) => `<option value="${esc(h.key)}">${esc(h.name)}</option>`).join('');
  const invite = `<div class="bi-card bi-invite"><strong>Tarifa sugerida</strong><span>Elige tu hotel arriba y verás la tarifa recomendada para cada fecha, desglosada en mediana, posición objetivo, valor, escasez, movimiento y antelación.</span><select id="biOwnInvite" class="bi-select is-invite" aria-label="Elegir hotel propio"><option value="">Elegir hotel propio…</option>${options}</select></div>`;
  if (!sorted.length) {
    return `<div class="bi-card bi-day"><span class="card__kicker">Mercado · entrada ${esc(biFocusLabel(m))}</span><div class="bi-day__big"><strong>—</strong><span>€ mediana</span></div><p class="bi-day__empty">${m.coverage[m.fi] ? 'Ningún hotel del alcance tiene tarifa en esta fecha.' : 'Sin captura para esta fecha de entrada.'}</p></div>${invite}`;
  }
  const min = sorted[0].p, max = sorted.at(-1).p;
  const X = (v) => (max > min ? ((v - min) / (max - min)) * 100 : 50);
  const best = [...m.open].map((x) => ({ ...x, vs: m.vscore(x.h, x.p) })).filter((x) => x.vs != null).sort((a, b) => b.vs - a.vs)[0];
  const short = (name) => String(name).split(' - ')[0];
  const facts = [
    ['Más barato', `${short(sorted[0].h.name)} · ${eur(sorted[0].p)}`, sorted[0].h.key],
    ['Más caro', `${short(sorted.at(-1).h.name)} · ${eur(sorted.at(-1).p)}`, sorted.at(-1).h.key],
    ['Mejor value score', best ? `${short(best.h.name)} · ${best.vs}` : '—', best ? best.h.key : null],
  ].map(([k, v, key]) => key ? `<button type="button" class="bi-fact" data-bi-open="${esc(key)}"><span>${esc(k)}</span><b>${esc(v)}</b></button>` : `<div class="bi-fact"><span>${esc(k)}</span><b>${esc(v)}</b></div>`).join('');
  return `<div class="bi-card bi-day"><span class="card__kicker">Mercado · entrada ${esc(biFocusLabel(m))}</span>
    <div class="bi-day__big"><strong>${nEs(m.fMed)}</strong><span>€ mediana</span></div>
    <div class="bi-box" aria-hidden="true"><i class="bi-box__line"></i><i class="bi-box__iqr" style="left:${X(m.dayQ1[m.fi]).toFixed(1)}%;width:${(X(m.dayQ3[m.fi]) - X(m.dayQ1[m.fi])).toFixed(1)}%"></i><i class="bi-box__med" style="left:${X(m.fMed).toFixed(1)}%"></i></div>
    <div class="bi-box__scale"><span>${eur(min)}</span><span>P25 ${eur(m.dayQ1[m.fi])} · P75 ${eur(m.dayQ3[m.fi])}</span><span>${eur(max)}</span></div>
    <div class="bi-facts">${facts}<div class="bi-fact"><span>Cerrados</span><b>${m.closedToday} hoteles · ${m.lowToday} con cupo bajo</b></div></div>
  </div>${invite}`;
}

function biCalendarHTML(m) {
  const st = State.bi;
  const H = m.H;
  const cols = `270px repeat(${H}, minmax(0, 1fr))`;
  const showText = H <= 30;
  const head = biCalendarHead(m.dates).map((c, i) => `<span class="${i === m.fi ? 'is-focus' : c.month ? 'is-month' : ''}${m.coverage[i] ? '' : ' is-empty'}">${c.text}</span>`).join('');
  const meds = m.dayMeds.filter((v) => v != null);
  const mMax = meds.length ? Math.max(...meds) : 1, mMin = meds.length ? Math.min(...meds) : 0;
  const medRow = m.dayMeds.map((v, i) => (v == null ? `<span class="bi-cal__med" data-d="${i}"></span>`
    : `<span class="bi-cal__med" data-d="${i}" role="button" tabindex="0" aria-label="${esc(`Entrada ${biDayLong(m.dates[i])} · mediana ${eur(v)}`)}" aria-pressed="${i === m.fi}"><i style="height:${(30 + ((v - mMin) / Math.max(1, mMax - mMin)) * 70).toFixed(0)}%"></i></span>`)).join('');
  let rankRow = '';
  if (m.own) {
    rankRow = `<div class="bi-cal__row bi-cal__rank" style="grid-template-columns:${cols}"><span class="bi-cal__label is-own">Rank del hotel propio</span>${m.dates.map((_, i) => {
      const r = biRankAt(m.hs, m.own.key, i);
      const s = m.own.status[i];
      if (r) { const pct = (r.rank - 1) / Math.max(1, r.of - 1); return `<span data-d="${i}" class="${pct < 0.34 ? 'is-top' : pct < 0.67 ? 'is-mid' : 'is-low'}">${showText ? r.rank : ''}</span>`; }
      return s === 'closed' ? `<span data-d="${i}" class="is-closed">${showText ? '×' : ''}</span>` : `<span data-d="${i}" class="is-none"></span>`;
    }).join('')}</div>`;
  }
  const rows = [...m.hs].sort((a, b) => (b.key === st.own) - (a.key === st.own) || (b.prices[m.fi] ?? -1) - (a.prices[m.fi] ?? -1) || String(a.name).localeCompare(String(b.name), 'es'));
  const body = rows.map((h, ri) => {
    const cells = m.dates.map((_, i) => {
      const s = h.status[i], p = h.prices[i];
      if (p != null) {
        const heat = biHeat(p, m.dayMeds[i]);
        return `<span data-h="${esc(h.key)}" data-d="${i}" class="bi-cell${s === 'low' ? ' is-low' : ''}${heat && Math.abs(heat.r) > 0.45 ? ' is-strong' : ''}" style="background:${heat ? heat.bg : 'var(--line-soft)'}">${showText ? nEs(p) : ''}</span>`;
      }
      if (s === 'closed') return `<span data-h="${esc(h.key)}" data-d="${i}" class="bi-cell is-closed"></span>`;
      return `<span data-h="${esc(h.key)}" data-d="${i}" class="bi-cell is-empty"></span>`;
    }).join('');
    const isOwn = h.key === st.own;
    return `<div class="bi-cal__row${isOwn ? ' is-own' : ''}" style="grid-template-columns:${cols}"><button type="button" class="bi-cal__name" data-bi-open="${esc(h.key)}"><span class="bi-cal__pos">${ri + 1}</span><span>${esc(h.name)}</span></button>${cells}</div>`;
  }).join('');
  const captured = m.captured.length;
  return `<div class="bi-card__head bi-cal__head"><div class="bi-card__title"><span class="card__kicker">Rate calendar · entradas ${biDayLabel(m.dates[0])} – ${biDayLabel(m.dates.at(-1))}</span><h2>Tarifa por hotel y fecha de entrada</h2></div>
      <div class="bi-cal__aside"><span class="bi-cal__readout" id="biCalReadout" aria-live="polite">Pasa el cursor por el calendario</span>
      <div class="bi-legend"><span class="bi-legend__scale" aria-hidden="true"><i style="background:rgba(31,122,82,.55)"></i><i style="background:rgba(31,122,82,.22)"></i><i style="background:var(--line-soft)"></i><i style="background:rgba(185,79,80,.22)"></i><i style="background:rgba(185,79,80,.55)"></i></span><span>vs mediana del día</span><i class="bi-legend__closed" aria-hidden="true"></i><span>cerrado</span><i class="bi-legend__low" aria-hidden="true"></i><span>cupo bajo</span><i class="bi-legend__empty" aria-hidden="true"></i><span>sin captura</span></div></div></div>
    <div class="bi-cal__body">
      <div class="bi-cal__grid" id="biCalGrid">
        <div class="bi-cal__row bi-cal__days" style="grid-template-columns:${cols}"><span></span>${head}</div>
        <div class="bi-cal__row bi-cal__medrow" style="grid-template-columns:${cols}"><span class="bi-cal__label">Mediana del set</span>${medRow}</div>
        ${rankRow}
        <div class="bi-cal__rows">${body || '<div class="bi-cal__nohotels">Ningún hotel tiene tarifas con estos filtros. Prueba otro régimen o tipo de habitación.</div>'}</div>
        <div class="bi-cal__focus" style="left:calc(270px + 1px + (100% - 271px) * ${(m.fi / H).toFixed(5)});width:calc((100% - 271px) / ${H})" aria-hidden="true"></div>
      </div>
      <div class="bi-cal__foot"><span>Pulsa una fecha para recalcular mapa, KPIs, distribución y tarifa sugerida. Pulsa un hotel para abrir su ficha.</span><span class="mono">entrada ${biDayLabel(m.dates[m.fi])} seleccionada · ${m.open.length} con tarifa · ${m.closedToday} cerrados · ${captured} ${captured === 1 ? 'fecha capturada' : 'fechas capturadas'} de ${H}</span></div>
    </div>`;
}

function biCalendarReadout(m, key, d) {
  if (d == null || Number.isNaN(d)) return 'Pasa el cursor por el calendario';
  const iso = m.dates[d];
  if (!key) {
    if (!m.coverage[d]) return `${biDayLong(iso)} · sin captura`;
    return `${biDayLong(iso)} · mediana ${eur(m.dayMeds[d])} · P25–P75 ${eur(m.dayQ1[d])}–${eur(m.dayQ3[d])}`;
  }
  const h = m.all.find((x) => x.key === key);
  if (!h) return '';
  const p = h.prices[d], s = h.status[d];
  const short = String(h.name).split(' - ')[0];
  if (p != null) return `${short} · ${biDayLong(iso)} · ${eur(p)} · ${biSigned((p / m.dayMeds[d] - 1) * 100, 0)} % vs mediana (${eur(m.dayMeds[d])})${s === 'low' ? ' · cupo bajo' : ''}`;
  const why = { closed: 'cerrado', unknown: 'no aparece en una captura parcial', nomatch: 'sin tarifa con estos filtros' }[s] || 'sin captura';
  return `${short} · ${biDayLong(iso)} · ${why}`;
}

/* Gráfica de líneas con huecos: une solo los puntos con dato y dibuja cada punto. */
function biPolyline(points) { return points.filter(Boolean).map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' '); }
function biBand(top, bottom) {
  const valid = top.map((p, i) => (p && bottom[i] ? i : null)).filter((i) => i != null);
  if (valid.length < 2) return '';
  return [...valid.map((i) => top[i]), ...valid.map((i) => bottom[i]).reverse()].map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
}

function biIndexHTML(m) {
  const st = State.bi, H = m.H;
  const X = (i) => 40 + i * (760 / Math.max(1, H - 1));
  let kicker, title, summary, line, band, refY = null, yl, leg1, leg2, dots;
  if (m.own) {
    const vals = m.dayMeds.map((med, i) => (m.own.prices[i] != null && med ? (m.own.prices[i] / med) * 100 : null));
    const b1 = m.dayQ1.map((v, i) => (v != null && m.dayMeds[i] ? (v / m.dayMeds[i]) * 100 : null));
    const b3 = m.dayQ3.map((v, i) => (v != null && m.dayMeds[i] ? (v / m.dayMeds[i]) * 100 : null));
    const pool = [...vals, ...b1, ...b3, 100].filter((v) => v != null);
    const lo = Math.min(...pool) - 5, hi = Math.max(...pool) + 5;
    const Y = (v) => 180 - ((v - lo) / (hi - lo)) * 170;
    const pts = vals.map((v, i) => (v == null ? null : [X(i), Y(v)]));
    const avg = vals.filter((v) => v != null);
    const closedDays = m.own.status.filter((s) => s === 'closed').length;
    kicker = `Índice de precio (ARI) · ${H} días`; title = `${String(m.own.name).split(' - ')[0]} frente al set`;
    summary = avg.length ? `media ${nEs(avg.reduce((a, v) => a + v, 0) / avg.length)} · ${closedDays} ${closedDays === 1 ? 'día' : 'días'} cerrado` : 'sin tarifa del hotel en el horizonte';
    line = biPolyline(pts); dots = pts; band = biBand(b3.map((v, i) => (v == null ? null : [X(i), Y(v)])), b1.map((v, i) => (v == null ? null : [X(i), Y(v)])));
    refY = Y(100); yl = [nEs(hi), nEs((hi + lo) / 2), nEs(lo)]; leg1 = 'Índice del hotel (100 = mediana)'; leg2 = 'Banda P25–P75 del set';
  } else {
    const pool = [...m.dayQ1, ...m.dayQ3].filter((v) => v != null);
    const lo = (pool.length ? Math.min(...pool) : 0) - 10, hi = (pool.length ? Math.max(...pool) : 100) + 10;
    const Y = (v) => 180 - ((v - lo) / (hi - lo)) * 170;
    const meds = m.dayMeds.filter((v) => v != null);
    kicker = `Índice de precio del mercado · ${H} días`; title = 'Mediana y banda central por fecha';
    summary = meds.length ? `mín ${eur(Math.min(...meds))} · máx ${eur(Math.max(...meds))}` : 'sin capturas en el horizonte';
    const pts = m.dayMeds.map((v, i) => (v == null ? null : [X(i), Y(v)]));
    line = biPolyline(pts); dots = pts; band = biBand(m.dayQ3.map((v, i) => (v == null ? null : [X(i), Y(v)])), m.dayQ1.map((v, i) => (v == null ? null : [X(i), Y(v)])));
    yl = [eur(hi), eur((hi + lo) / 2), eur(lo)]; leg1 = 'Mediana del set'; leg2 = 'P25–P75';
  }
  const xl = m.dates.map((iso, i) => ({ iso, i })).filter(({ iso, i }) => i === 0 || biDate(iso).getUTCDate() === 1 || (H <= 30 && i % 7 === 0)).map(({ iso, i }) => `<text x="${X(i).toFixed(1)}" y="202" text-anchor="middle">${biDayLabel(iso)}</text>`).join('');
  const circles = dots.map((p) => (p ? `<circle cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="3" fill="var(--card)" stroke="var(--ac)" stroke-width="2"></circle>` : '')).join('');
  return `<div class="bi-card__head"><div class="bi-card__title"><span class="card__kicker">${esc(kicker)}</span><h2>${esc(title)}</h2></div><span class="bi-card__summary">${esc(summary)}</span></div>
    <svg class="bi-chart" viewBox="0 0 800 210" role="img" aria-label="${esc(title)}"><line x1="40" x2="800" y1="10" y2="10" stroke="var(--line)"></line><line x1="40" x2="800" y1="95" y2="95" stroke="var(--line)"></line><line x1="40" x2="800" y1="180" y2="180" stroke="var(--line)"></line>
      <g class="bi-svg-text"><text x="34" y="13" text-anchor="end">${yl[0]}</text><text x="34" y="98" text-anchor="end">${yl[1]}</text><text x="34" y="183" text-anchor="end">${yl[2]}</text>${xl}</g>
      ${band ? `<polygon points="${band}" fill="var(--accent-soft)" opacity=".9"></polygon>` : ''}
      ${refY != null ? `<line x1="40" x2="800" y1="${refY.toFixed(1)}" y2="${refY.toFixed(1)}" stroke="var(--ink)" stroke-dasharray="4 4" opacity=".5"></line>` : ''}
      ${line ? `<polyline points="${line}" fill="none" stroke="var(--ac)" stroke-width="2.2" stroke-linejoin="round"></polyline>` : ''}${circles}
      <line x1="${X(m.fi).toFixed(1)}" x2="${X(m.fi).toFixed(1)}" y1="6" y2="184" stroke="var(--ac)" stroke-width="1" opacity=".6"></line></svg>
    <div class="bi-legend bi-legend--chart"><span><i class="is-line"></i>${esc(leg1)}</span><span><i class="is-band"></i>${esc(leg2)}</span></div>`;
}

function biEvolutionHTML(m) {
  const st = State.bi;
  const caps = st.data.extractions || [];
  const head = (summary) => `<div class="bi-card__head"><div class="bi-card__title"><span class="card__kicker">Evolución por extracción</span><h2>Cómo se ha movido la tarifa del set</h2></div><span class="bi-card__summary">${esc(summary)}</span></div>`;
  const keys = new Set(m.hs.map((h) => h.key));
  const stats = caps.map((e) => {
    const ps = Object.entries(e.prices || {}).filter(([k]) => keys.has(k)).map(([, v]) => v);
    return { e, med: biQuantile(ps, 0.5), q1: biQuantile(ps, 0.25), q3: biQuantile(ps, 0.75), own: m.own ? e.prices?.[m.own.key] ?? null : null };
  });
  const valid = stats.filter((s) => s.med != null);
  if (valid.length < 2) return `${head('se necesitan dos fotos')}<div class="empty">Se necesitan dos fotos con tarifas del alcance para dibujar la evolución.</div>`;
  const pool = [...stats.flatMap((s) => [s.q1, s.q3]), ...stats.map((s) => s.own)].filter((v) => v != null);
  const lo = Math.min(...pool) - 10, hi = Math.max(...pool) + 10;
  const X = (k) => 40 + k * (760 / Math.max(1, caps.length - 1));
  const Y = (v) => 180 - ((v - lo) / (hi - lo)) * 170;
  const medPts = stats.map((s, k) => (s.med == null ? null : [X(k), Y(s.med)]));
  const ownPts = stats.map((s, k) => (s.own == null ? null : [X(k), Y(s.own)]));
  const band = biBand(stats.map((s, k) => (s.q3 == null ? null : [X(k), Y(s.q3)])), stats.map((s, k) => (s.q1 == null ? null : [X(k), Y(s.q1)])));
  const first = valid[0].med, last = valid.at(-1).med;
  const points = [
    ...stats.map((s, k) => (s.med == null ? '' : `<circle cx="${X(k).toFixed(1)}" cy="${Y(s.med).toFixed(1)}" r="3.5" fill="var(--card)" stroke="var(--mid)" stroke-width="2"><title>Foto #${s.e.snapshotId} · entrada ${biDayLabel(s.e.checkIn)} · mediana ${eur(s.med)}</title></circle>`)),
    ...stats.map((s, k) => (s.own == null ? '' : `<circle cx="${X(k).toFixed(1)}" cy="${Y(s.own).toFixed(1)}" r="3.5" fill="var(--card)" stroke="var(--ac)" stroke-width="2"><title>Foto #${s.e.snapshotId} · ${eur(s.own)}</title></circle>`)),
  ].join('');
  const xl = caps.map((e, k) => `<text x="${X(k).toFixed(1)}" y="202" text-anchor="middle">#${e.snapshotId}</text>`).join('');
  return `${head(`mediana ${eur(first)} → ${eur(last)} · ${biSigned((last / first - 1) * 100)} %`)}
    <svg class="bi-chart" viewBox="0 0 800 210" role="img" aria-label="Mediana del set por foto"><line x1="40" x2="800" y1="10" y2="10" stroke="var(--line)"></line><line x1="40" x2="800" y1="180" y2="180" stroke="var(--line)"></line>
      <g class="bi-svg-text"><text x="34" y="13" text-anchor="end">${eur(hi)}</text><text x="34" y="183" text-anchor="end">${eur(lo)}</text>${xl}</g>
      ${band ? `<polygon points="${band}" fill="var(--accent-soft)" opacity=".9"></polygon>` : ''}
      <polyline points="${biPolyline(medPts)}" fill="none" stroke="var(--mid)" stroke-width="2" stroke-linejoin="round"></polyline>
      ${m.own ? `<polyline points="${biPolyline(ownPts)}" fill="none" stroke="var(--ac)" stroke-width="2.4" stroke-linejoin="round"></polyline>` : ''}${points}</svg>
    <div class="bi-legend bi-legend--chart"><span><i class="is-mid"></i>Mediana del set</span><span><i class="is-band"></i>P25–P75</span>${m.own ? '<span><i class="is-line"></i>Hotel propio</span>' : ''}</div>`;
}

function biGroupKey(mode, h) { return mode === 'zone' ? h.zone : mode === 'segment' ? h.segment : h.chain; }

function biBoxesHTML(m) {
  const st = State.bi;
  const modes = [['zone', 'Zona'], ['segment', 'Segmento'], ['chain', 'Cadena']].map(([id, label]) => `<button type="button" class="${st.boxMode === id ? 'is-active' : ''}" data-bi-box-mode="${id}" aria-pressed="${st.boxMode === id}">${label}</button>`).join('');
  const groups = new Map();
  m.open.forEach(({ h, p }) => { const g = biGroupKey(st.boxMode, h); if (!g) return; if (!groups.has(g)) groups.set(g, []); groups.get(g).push(p); });
  const all = m.open.map((x) => x.p);
  const bmin = all.length ? Math.min(...all) : 0, bmax = all.length ? Math.max(...all) : 1;
  const BX = (v) => ((v - bmin) / Math.max(1, bmax - bmin)) * 100;
  const active = st.boxMode === 'zone' ? st.zone : st.boxMode === 'segment' ? st.seg : st.chain;
  const rows = [...groups.entries()].filter(([, a]) => st.boxMode !== 'chain' || a.length > 1).map(([g, a]) => {
    const mn = Math.min(...a), mx = Math.max(...a), q1 = biQuantile(a, 0.25), q3 = biQuantile(a, 0.75), md = biQuantile(a, 0.5);
    const ownHere = m.own && m.ownP != null && biGroupKey(st.boxMode, m.own) === g;
    return { g, n: a.length, md, html: `<button type="button" class="bi-group${active === g ? ' is-active' : ''}" data-bi-group="${esc(g)}" aria-pressed="${active === g}"><span class="bi-group__name">${esc(g)} <small>${a.length}</small></span><span class="bi-group__plot"><i class="bi-group__whisker" style="left:${BX(mn).toFixed(1)}%;width:${(BX(mx) - BX(mn)).toFixed(1)}%"></i><i class="bi-group__iqr" style="left:${BX(q1).toFixed(1)}%;width:${Math.max(0.8, BX(q3) - BX(q1)).toFixed(1)}%"></i><i class="bi-group__med" style="left:${BX(md).toFixed(1)}%"></i>${ownHere ? `<i class="bi-group__own" style="left:${BX(m.ownP).toFixed(1)}%" title="Tu hotel · ${eur(m.ownP)}"></i>` : ''}</span><span class="bi-group__value">${eur(md)}</span></button>` };
  }).sort((a, b) => b.md - a.md).map((r) => r.html).join('');
  return `<div class="bi-card__head"><div class="bi-card__title"><span class="card__kicker">Distribución · entrada ${esc(biFocusLabel(m))}</span><h2>Rango de precios por grupo</h2></div><div class="seg seg--sm" role="group" aria-label="Agrupar por">${modes}</div></div>
    <div class="bi-groups">${rows || `<div class="empty">${m.open.length ? 'No hay grupos con dos o más hoteles.' : 'Sin tarifas en esta fecha.'}</div>`}</div>`;
}

function biScatterHTML(m) {
  const st = State.bi;
  const pts = m.open.filter(({ h }) => h.nota != null);
  const head = `<div class="bi-card__head"><div class="bi-card__title"><span class="card__kicker">Reputación vs precio · value score</span><h2>Quién ofrece más por su precio</h2></div><span class="bi-card__summary" id="biScatterReadout">tamaño = reseñas · pulsa para abrir ficha</span></div>`;
  if (pts.length < 2 || !m.fMed || m.mNota == null) return `${head}<div class="empty">Se necesitan al menos dos hoteles con tarifa y nota en esta fecha.</div>`;
  const xs = pts.map((x) => x.p), ys = pts.map((x) => x.h.nota);
  const xlo = Math.min(...xs, 100) * 0.92, xhi = Math.max(...xs, 200) * 1.04;
  const ylo = Math.min(...ys, 7.5) - 0.15, yhi = Math.max(...ys, 9) + 0.1;
  const SX = (v) => ((v - xlo) / (xhi - xlo)) * 100, SY = (v) => ((v - ylo) / (yhi - ylo)) * 100;
  const dots = pts.map(({ h, p }) => {
    const own = h.key === st.own, vs = m.vscore(h, p), size = biDotSize(h.reviews);
    const tone = own ? 'own' : vs >= 60 ? 'good' : vs <= 40 ? 'bad' : 'mid';
    const readout = `${String(h.name).split(' - ')[0]} · ${eur(p)} · nota ${nEs(h.nota, 1)} · value ${vs}`;
    return `<button type="button" class="bi-dot is-${tone}" style="left:${SX(p).toFixed(2)}%;bottom:${SY(h.nota).toFixed(2)}%;width:${size}px;height:${size}px" data-bi-open="${esc(h.key)}" data-bi-readout="${esc(readout)}" aria-label="${esc(readout)}"></button>`;
  }).join('');
  return `${head}<div class="bi-scatter"><div class="bi-scatter__plot">
      <i class="bi-scatter__good" style="width:${SX(m.fMed).toFixed(2)}%;height:${(100 - SY(m.mNota)).toFixed(2)}%"></i>
      <i class="bi-scatter__vx" style="left:${SX(m.fMed).toFixed(2)}%"></i><i class="bi-scatter__hy" style="top:${(100 - SY(m.mNota)).toFixed(2)}%"></i>
      <span class="bi-q bi-q--tl">Valor alto</span><span class="bi-q bi-q--tr">Premium justificado</span><span class="bi-q bi-q--bl">Económico</span><span class="bi-q bi-q--br">Caro para su nota</span>
      ${dots}</div>
    <span class="bi-scatter__ymax">${nEs(yhi, 1)}</span><span class="bi-scatter__ymin">${nEs(ylo, 1)}</span>
    <div class="bi-scatter__x"><span>${eur(xlo)}</span><span>precio por noche · nota Booking</span><span>${eur(xhi)}</span></div></div>`;
}

function biAlertsHTML(m) {
  const st = State.bi, mv = st.metrics?.movement || {};
  const list = biAlerts(m.hs);
  const tabs = [['all', 'Todas'], ['mov', 'Precio'], ['disp', 'Disponibilidad']].map(([id, label]) => `<button type="button" class="${st.alertTab === id ? 'is-active' : ''}" data-bi-alert-tab="${id}" aria-pressed="${st.alertTab === id}">${label}<b>${list.filter((a) => id === 'all' || a.type === id).length}</b></button>`).join('');
  const shown = list.filter((a) => st.alertTab === 'all' || a.type === st.alertTab);
  const title = mv.isComparable && mv.previousSnapshotId ? `Movimientos entre la foto #${mv.previousSnapshotId} y la #${st.metrics.latestSnapshot?.id}` : 'Movimientos de la última foto';
  return `<div class="bi-card__head"><div class="bi-card__title"><span class="card__kicker">Alertas de competidores</span><h2>${esc(title)}</h2></div><div class="seg seg--sm" role="group" aria-label="Tipo de alerta">${tabs}</div></div>
    <div class="bi-alerts">${shown.map((a) => `<button type="button" class="bi-alert" data-bi-open="${esc(a.key)}"><span class="bi-alert__tag is-${a.tone}">${esc(a.tag)}</span><span class="bi-alert__body"><b>${esc(a.name)}</b><small>${esc(a.text)}</small></span><strong class="is-${a.tone}">${esc(a.value)}</strong></button>`).join('') || '<div class="empty">Sin alertas con los filtros actuales.</div>'}</div>`;
}

function biAvailabilityHTML(m) {
  const weeks = biWeeks(m.dates, m.hs);
  const bars = weeks.map((w) => {
    if (!w.total) return `<div class="bi-week is-empty" title="Semana del ${biDayLabel(w.start)} · sin captura"><span>—</span><div></div><div></div></div>`;
    const pc = w.closed / w.total, pl = w.low / w.total;
    return `<div class="bi-week" title="Semana del ${biDayLabel(w.start)} · ${nEs(pc * 100)} % cerrado · ${nEs(pl * 100)} % cupo bajo"><span>${nEs((pc + pl) * 100)} %</span><div class="bi-week__low" style="height:${Math.min(100, pl * 300).toFixed(1)}%"></div><div class="bi-week__closed" style="height:${Math.min(100, pc * 300).toFixed(1)}%"></div></div>`;
  }).join('');
  const labels = weeks.map((w) => `<span>${biDayLabel(w.start)}</span>`).join('');
  const closers = m.hs.map((h) => ({ h, c: h.status.filter((s) => s === 'closed').length, l: h.status.filter((s) => s === 'low').length }))
    .filter((x) => x.c + x.l > 0).sort((a, b) => (b.c * 2 + b.l) - (a.c * 2 + a.l)).slice(0, 6)
    .map((x) => { const s = x.h.status[m.fi]; const now = s === 'closed' ? 'cerrado' : s === 'low' ? 'cupo bajo' : s === 'ok' ? 'abierto' : 'sin dato'; return `<button type="button" class="bi-closer" data-bi-open="${esc(x.h.key)}"><span>${esc(x.h.name)}</span><span class="neg">${x.c} d</span><span class="warn">${x.l} d</span><span>${now}</span></button>`; }).join('');
  return `<div class="bi-card__head"><div class="bi-card__title"><span class="card__kicker">Disponibilidad y cierres · entradas ${biDayLabel(m.dates[0])} – ${biDayLabel(m.dates.at(-1))}</span><h2>Presión de ocupación en el set</h2></div><div class="bi-legend"><span><i class="bi-sw is-closed"></i>cerrado</span><span><i class="bi-sw is-low"></i>cupo bajo</span></div></div>
    <div class="bi-weeks">${bars}</div><div class="bi-weeks__labels">${labels}</div>
    <div class="bi-closers"><div class="bi-closer bi-closer--head"><span>Hotel</span><span>Cerrado</span><span>Cupo bajo</span><span>Hoy</span></div>${closers || '<div class="empty">Sin cierres ni cupo bajo en las fechas capturadas.</div>'}</div>`;
}

/* ---- pintado */
function paintBi() {
  const st = State.bi;
  const root = $('#biRoot');
  if (!root || !st.data) return;
  const m = biModel();
  st.model = m;
  $('#biChips').innerHTML = biChipsHTML(m);
  $('#biKpis').innerHTML = biKpisHTML(m);
  $('#biMapKicker').textContent = `Mapa de precios · entrada ${biFocusLabel(m)}`;
  $('#biZones').innerHTML = biZonesHTML(m);
  $('#biSide').innerHTML = m.own ? biRecoHTML(m) : biDayHTML(m);
  $('#biCal').innerHTML = biCalendarHTML(m);
  $('#biIndex').innerHTML = biIndexHTML(m);
  $('#biEvo').innerHTML = biEvolutionHTML(m);
  $('#biBoxes').innerHTML = biBoxesHTML(m);
  $('#biScatter').innerHTML = biScatterHTML(m);
  $('#biAlerts').innerHTML = biAlertsHTML(m);
  $('#biAvail').innerHTML = biAvailabilityHTML(m);
  syncBiMarkers(m);
  if (st.drawer) paintBiDrawer();
}

async function renderHotelsBI(panel, sheetModel, metrics) {
  const targetId = State.targetId;
  if (!State.bi || State.bi.targetId !== targetId) biReset(targetId);
  const st = State.bi;
  st.sheet = sheetModel;
  st.metrics = metrics;
  destroyBiMap();
  panel.innerHTML = '<div class="bi" aria-busy="true"><div class="sk" style="height:62px"></div><div class="sk" style="height:84px"></div><div class="sk" style="height:560px"></div></div>';
  try { await loadBiData(); }
  catch (e) { if (panel.isConnected) panel.innerHTML = `<div class="inline-error">No se pudo cargar el panel de análisis: ${esc(e.message)}</div>`; return; }
  if (!panel.isConnected || State.bi !== st || State.hotelTab !== 'bi' || State.targetId !== targetId) return;
  const m = biModel();
  panel.innerHTML = `<div class="bi" id="biRoot">
    <div class="bi-filters" id="biFilters">${biFiltersHTML(m)}</div>
    <section class="kpi-strip kpi-strip--bi" id="biKpis" aria-label="Indicadores del set en la fecha activa"></section>
    <div class="bi-flow">
      <div class="bi-card bi-map-card"><div class="bi-card__head bi-map-card__head"><div class="bi-card__title"><span class="card__kicker" id="biMapKicker"></span><h2>Dónde está caro y dónde barato</h2></div>
        <div class="bi-legend"><span><i class="bi-sw is-dot tone-low"></i>−15 % o menos</span><span><i class="bi-sw is-dot tone-mid"></i>en la mediana</span><span><i class="bi-sw is-dot tone-high"></i>+15 % o más</span><span>· tamaño = reseñas</span></div></div>
        <div class="map-frame bi-map" id="biMapFrame"><div class="map-frame__canvas" id="biMap" aria-label="Mapa de precios del set en la fecha activa"></div><div class="bi-zones" id="biZones" role="group" aria-label="Filtrar por zona"></div></div></div>
      <div class="bi-side" id="biSide"></div>
      <section class="bi-card bi-cal" id="biCal" aria-label="Calendario de tarifas"></section>
      <section class="bi-card bi-chart-card" id="biIndex"></section>
      <section class="bi-card bi-chart-card" id="biEvo"></section>
      <section class="bi-card bi-boxes" id="biBoxes"></section>
      <section class="bi-card bi-scatter-card" id="biScatter"></section>
      <section class="bi-card bi-alerts-card" id="biAlerts"></section>
      <section class="bi-card bi-avail" id="biAvail"></section>
    </div>
  </div>`;
  paintBi();
  void renderBiMap();
}

/* ---- mapa de precios */
function destroyBiMap() {
  const st = State.bi;
  if (st) Object.values(st.markers || {}).forEach((item) => item.marker.remove());
  if (st) { st.markers = {}; st.fitKey = null; }
  if (State.biMap) { State.biMap.remove(); State.biMap = null; }
}

async function renderBiMap() {
  const st = State.bi;
  const frame = $('#biMapFrame'), container = $('#biMap');
  if (!frame || !container || !st?.data) return;
  const request = {};
  frame._mapRequest = request;
  const points = st.data.hotels.filter((h) => validLngLat({ latitude: h.lat, longitude: h.lng }));
  if (!points.length) { mapFrameStatus(frame, 'No hay hoteles con coordenadas en el alcance.'); return; }
  try { await loadMapLibre(); } catch (_) { if (frame.isConnected) mapFrameStatus(frame, MAP_FAILED_TEXT); return; }
  if (!frame.isConnected || frame._mapRequest !== request || State.bi !== st) return;
  destroyBiMap();
  let map;
  try { map = createAtlasMap(container, { center: [-15.66, 27.782], zoom: 10.8 }); }
  catch (_) { mapFrameStatus(frame, MAP_FAILED_TEXT); return; }
  State.biMap = map;
  const ml = window.maplibregl;
  points.forEach((h) => {
    const root = mapPinElement(`<button type="button" class="bi-pin" data-bi-open="${esc(h.key)}" aria-label="${esc(h.name)}"></button><span class="bi-pin__label"></span>`);
    const marker = new ml.Marker({ element: root }).setLngLat(validLngLat({ latitude: h.lat, longitude: h.lng })).addTo(map);
    st.markers[h.key] = { marker, root, pin: root.querySelector('.bi-pin'), label: root.querySelector('.bi-pin__label') };
  });
  if (st.model) syncBiMarkers(st.model);
}

function syncBiMarkers(m) {
  const st = State.bi;
  if (!State.biMap || !st.markers) return;
  const visible = new Set(m.hs.map((h) => h.key));
  m.all.forEach((h) => {
    const item = st.markers[h.key];
    if (!item) return;
    const price = h.prices[m.fi];
    const own = h.key === st.own;
    const size = biPinSize(h.reviews);
    item.root.hidden = !visible.has(h.key);
    item.pin.style.width = `${size}px`;
    item.pin.style.height = `${size}px`;
    item.pin.style.background = BI_MAP_COLORS[price != null && m.fMed ? biMapTone(price, m.fMed) : 'closed'];
    item.pin.classList.toggle('is-closed', price == null);
    item.pin.classList.toggle('is-own', own);
    item.label.classList.toggle('is-own', own);
    item.label.textContent = own ? `Tu hotel · ${price != null ? eur(price) : 'cerrado'}` : `${String(h.name).split(' - ')[0]} · ${price != null ? eur(price) : 'cerrado'}`;
    item.pin.setAttribute('aria-label', `${h.name} · ${price != null ? eur(price) : h.status[m.fi] === 'closed' ? 'cerrado' : 'sin tarifa'}. Abrir ficha`);
    item.root.style.zIndex = own ? '3' : '';
  });
  const fitKey = `${st.zone || ''}|${st.seg || ''}|${st.chain || ''}`;
  if (st.fitKey !== fitKey) {
    const first = st.fitKey == null;
    st.fitKey = fitKey;
    const coords = m.hs.map((h) => validLngLat({ latitude: h.lat, longitude: h.lng })).filter(Boolean);
    if (coords.length) {
      const bounds = coords.reduce((b, c) => b.extend(c), new window.maplibregl.LngLatBounds(coords[0], coords[0]));
      const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      State.biMap.fitBounds(bounds, { padding: { top: 60, bottom: 40, left: 60, right: 290 }, maxZoom: 13.5, duration: first || reduce ? 0 : 700 });
    }
  }
}

/* ---- ficha lateral */
function biDrawerHTML(m, key) {
  const st = State.bi;
  const h = m.all.find((x) => x.key === key);
  if (!h) return '';
  const price = h.prices[m.fi];
  const rank = biRankAt(m.hs, h.key, m.fi);
  const vs = m.vscore(h, price);
  const cached = State.hotelRateDetails[State.targetId]?.[key] || null;
  const rates = cached && cached.rows ? cached.rows : [];
  const genius = !rates.length ? null : rates.some((r) => r.genius === true) ? 'Participa' : rates.every((r) => r.genius === false) ? 'No' : null;
  const sub = [h.chain, h.zone, h.adultsOnly ? 'Adults only' : '', h.beach ? `playa a ${h.beach}` : ''].filter(Boolean).join(' · ');
  const status = h.status[m.fi];
  const kpis = [
    [`Tarifa ${biDayLabel(m.dates[m.fi])}`, price != null ? eur(price) : status === 'closed' ? 'Cerrado' : '—', 'ac'],
    ['Índice', price != null && m.fMed ? nEs((price / m.fMed) * 100) : '—', ''],
    ['Value score', vs ?? '—', ''],
    ['Nota', h.nota != null ? `${nEs(h.nota, 1)}${h.reviews != null ? ` · ${nEs(h.reviews)}` : ''}` : '—', ''],
    ['Δ foto', h.isNew ? 'Nuevo' : h.delta != null ? `${biSigned(h.delta)} %` : '—', h.delta > 0 ? 'pos' : h.delta < 0 ? 'neg' : ''],
    ['Genius', genius || '—', ''],
  ].map(([k, v, tone]) => `<div><span>${esc(k)}</span><strong class="${tone}">${esc(String(v))}</strong></div>`).join('');
  const caps = st.data.extractions || [];
  const series = caps.map((e) => e.prices?.[key] ?? null);
  const setSeries = caps.map((e) => e.median);
  const pool = [...series, ...setSeries].filter((v) => v != null);
  let chart = '<div class="bi-drawer__empty">Sin tarifas del hotel en las fotos disponibles.</div>';
  if (pool.length && series.filter((v) => v != null).length >= 1) {
    const lo = Math.min(...pool) - 10, hi = Math.max(...pool) + 10;
    const DX = (k) => (caps.length > 1 ? k * (440 / (caps.length - 1)) : 220), DY = (v) => 100 - ((v - lo) / (hi - lo)) * 90;
    const line = biPolyline(series.map((v, k) => (v == null ? null : [DX(k), DY(v)])));
    const setLine = biPolyline(setSeries.map((v, k) => (v == null ? null : [DX(k), DY(v)])));
    const dots = series.map((v, k) => (v == null ? '' : `<circle cx="${DX(k).toFixed(1)}" cy="${DY(v).toFixed(1)}" r="2.5" fill="var(--ac)"><title>Foto #${caps[k].snapshotId} · ${eur(v)}</title></circle>`)).join('');
    chart = `<svg class="bi-drawer__chart" viewBox="0 0 440 120" role="img" aria-label="Tarifa del hotel por extracción"><line x1="0" x2="440" y1="10" y2="10" stroke="var(--line)"></line><line x1="0" x2="440" y1="100" y2="100" stroke="var(--line)"></line><polyline points="${setLine}" fill="none" stroke="var(--faint)" stroke-width="1.5" stroke-dasharray="4 4"></polyline><polyline points="${line}" fill="none" stroke="var(--ac)" stroke-width="2.2" stroke-linejoin="round"></polyline>${dots}<g class="bi-svg-text"><text x="0" y="118">#${caps[0]?.snapshotId ?? ''}</text><text x="440" y="118" text-anchor="end">#${caps.at(-1)?.snapshotId ?? ''}</text></g></svg><div class="bi-drawer__legend"><span>— hotel</span><span>- - mediana del set</span></div>`;
  }
  const cal = m.dates.map((iso, i) => {
    const p = h.prices[i], s = h.status[i];
    const heat = p != null ? biHeat(p, m.dayMeds[i]) : null;
    const cls = p != null ? '' : s === 'closed' ? ' is-closed' : ' is-empty';
    return `<span class="bi-mini${cls}${s === 'low' ? ' is-low' : ''}${i === m.fi ? ' is-focus' : ''}" style="${heat ? `background:${heat.bg}` : ''}" title="${esc(`${biDayLong(iso)} · ${p != null ? eur(p) : s === 'closed' ? 'cerrado' : 'sin captura'}`)}"></span>`;
  }).join('');
  const rooms = !cached || cached.status === 'loading' ? '<p class="bi-drawer__empty">Comprobando tarifas capturadas…</p>'
    : cached.status === 'error' ? `<p class="bi-drawer__empty neg">${esc(cached.message || 'No se pudo cargar el desglose.')}</p>`
    : hotelRateGroups(rates).map((g) => {
      const nightly = g.rates.map(rateNightly).filter((v) => v != null);
      const units = g.rates.map((r) => r.unitsLeft).filter((v) => v != null && v > 0);
      const program = g.rates.find((r) => r.program);
      const tag = units.length ? (Math.min(...units) === 1 ? 'Queda 1' : `Quedan ${Math.min(...units)}`) : program ? (/genius/i.test(program.program) ? 'Genius' : 'Oferta') : 'Disponible';
      const tone = units.length ? 'warn' : program ? 'ac' : 'plain';
      return `<div class="bi-room"><span class="bi-room__name"><span>${esc(g.roomType || 'Habitación sin identificar')}</span><small>${g.maxOccupancy != null ? `máx. ${nEs(g.maxOccupancy)} pers. · ` : ''}${g.rates.length} ${g.rates.length === 1 ? 'tarifa' : 'tarifas'}</small></span><span class="hstock hstock--${tone}">${esc(tag)}</span><strong class="mono">${nightly.length ? `desde ${eur(Math.min(...nightly))}` : '—'}</strong></div>`;
    }).join('') || '<p class="bi-drawer__empty">No hay tarifas de detalle capturadas para este hotel.</p>';
  const isOwn = st.own === key;
  return `<div class="bi-drawer__head"><div><span class="card__kicker">Ficha · puesto ${rank ? rank.rank : '—'} de ${rank ? rank.of : m.hs.length}</span><h2 id="sidePanelTitle">${esc(h.name)}</h2>${sub ? `<span class="bi-drawer__sub">${esc(sub)}</span>` : ''}</div><button type="button" class="icon-x icon-x--lg" data-side-close aria-label="Cerrar ficha">×</button></div>
    <div class="bi-drawer__body">
      <div class="bi-drawer__kpis">${kpis}</div>
      <section class="bi-drawer__section"><span class="card__kicker">Tarifa por extracción</span>${chart}</section>
      <section class="bi-drawer__section"><span class="card__kicker">Calendario · entradas ${biDayLabel(m.dates[0])} – ${biDayLabel(m.dates.at(-1))}</span><div class="bi-minical">${cal}</div></section>
      <section class="bi-drawer__section bi-drawer__rooms"><span class="card__kicker">Habitaciones y tarifas</span>${rooms}</section>
    </div>
    <div class="bi-drawer__foot"><button type="button" class="btn btn--primary" data-bi-set-own="${esc(key)}"${isOwn ? ' disabled' : ''}>${isOwn ? 'Es tu hotel propio' : 'Fijar como hotel propio'}</button><button type="button" class="btn" data-bi-sheet="${esc(h.name)}">Ver en hoja de mercado</button></div>`;
}

function paintBiDrawer() {
  const st = State.bi;
  const body = $('#sidePanelBody');
  if (!st?.drawer || !body || $('#sidePanel').dataset.kind !== 'bi' || !st.model) return;
  const keepFocus = document.activeElement?.matches?.('#sidePanelBody [data-side-close]');
  body.innerHTML = biDrawerHTML(st.model, st.drawer);
  if (keepFocus) $('[data-side-close]', body)?.focus();
}

function openBiDrawer(key) {
  const st = State.bi;
  if (!st?.model) return;
  st.drawer = key;
  openSidePanel('bi', 'side-panel--bi');
  paintBiDrawer();
  $('#sidePanelBody [data-side-close]')?.focus();
  const targetId = State.targetId;
  void ensureHotelRateDetails(key).then(() => { if (State.bi === st && st.drawer === key && State.targetId === targetId) paintBiDrawer(); });
}

function setBiOwn(key) {
  const st = State.bi;
  st.own = key || '';
  try { if (st.own) localStorage.setItem(biOwnKey(), st.own); else localStorage.removeItem(biOwnKey()); } catch (_) { /* preferencia opcional */ }
  const select = $('#biOwn');
  if (select) { select.value = st.own; select.classList.toggle('is-set', Boolean(st.own)); }
  paintBi();
}

async function setBiDataFilter(kind, value) {
  const st = State.bi;
  st[kind] = value;
  const root = $('#biRoot');
  root?.setAttribute('aria-busy', 'true');
  try { await loadBiData(); } catch (e) { toast(`No se pudo recalcular: ${e.message}`, 'warn'); }
  root?.removeAttribute('aria-busy');
  if (State.bi !== st || !$('#biRoot')) return;
  $('#biFilters').innerHTML = biFiltersHTML(biModel());
  $(`#${kind === 'board' ? 'biBoard' : 'biFam'}`)?.focus();
  destroyBiMap();
  paintBi();
  void renderBiMap();
}

function handleBiClick(e) {
  const t = e.target instanceof Element ? e.target : null;
  const st = State.bi;
  if (!t || !st || !(t.closest('#biRoot') || t.closest('#sidePanel[data-kind="bi"]'))) return false;
  const open = t.closest('[data-bi-open]');
  if (open) { openBiDrawer(open.dataset.biOpen); return true; }
  const horizon = t.closest('[data-bi-horizon]');
  if (horizon) { st.horizon = Number(horizon.dataset.biHorizon); if (st.focus && st.data.dates.indexOf(st.focus) >= st.horizon) st.focus = null; $$('[data-bi-horizon]').forEach((b) => { const on = Number(b.dataset.biHorizon) === st.horizon; b.classList.toggle('is-active', on); b.setAttribute('aria-pressed', String(on)); }); paintBi(); return true; }
  const zone = t.closest('[data-bi-zone]');
  if (zone) { st.zone = st.zone === zone.dataset.biZone ? null : zone.dataset.biZone; paintBi(); return true; }
  const group = t.closest('[data-bi-group]');
  if (group) { const g = group.dataset.biGroup; const k = st.boxMode === 'zone' ? 'zone' : st.boxMode === 'segment' ? 'seg' : 'chain'; st[k] = st[k] === g ? null : g; paintBi(); return true; }
  const clear = t.closest('[data-bi-clear]');
  if (clear) { const k = clear.dataset.biClear; if (k === 'all') Object.assign(st, { zone: null, seg: null, chain: null, focus: null }); else st[k] = null; paintBi(); $('#biChips button, #biOwn')?.focus(); return true; }
  const mode = t.closest('[data-bi-box-mode]');
  if (mode) { st.boxMode = mode.dataset.biBoxMode; $('#biBoxes').innerHTML = biBoxesHTML(st.model); $(`[data-bi-box-mode="${st.boxMode}"]`)?.focus(); return true; }
  const tab = t.closest('[data-bi-alert-tab]');
  if (tab) { st.alertTab = tab.dataset.biAlertTab; $('#biAlerts').innerHTML = biAlertsHTML(st.model); $(`[data-bi-alert-tab="${st.alertTab}"]`)?.focus(); return true; }
  const day = t.closest('#biCalGrid [data-d]');
  if (day) { st.focus = st.model.dates[Number(day.dataset.d)] || null; if (st.focus === st.model.dates[st.model.defaultFi]) st.focus = null; paintBi(); return true; }
  if (t.closest('[data-bi-copy]')) {
    const value = st.recoValue;
    navigator.clipboard?.writeText(String(value)).catch(() => {});
    toast(`Tarifa sugerida ${nEs(value)} € copiada · ${biDayLabel(st.model.dates[st.model.fi])}`, 'ok');
    return true;
  }
  if (t.closest('[data-bi-ask-reco]')) { askCopilot(st.recoText); return true; }
  const setOwn = t.closest('[data-bi-set-own]');
  if (setOwn) { const h = st.model.all.find((x) => x.key === setOwn.dataset.biSetOwn); closeSidePanel(); setBiOwn(setOwn.dataset.biSetOwn); if (h) toast(`${h.name} fijado como hotel propio`, 'ok'); return true; }
  const sheet = t.closest('[data-bi-sheet]');
  if (sheet) { closeSidePanel({ restoreFocus: false }); openHotelInHotels(sheet.dataset.biSheet); return true; }
  return false;
}

function handleBiOver(e) {
  const t = e.target instanceof Element ? e.target : null;
  const st = State.bi;
  if (!t || !st?.model || State.hotelTab !== 'bi') return;
  const readout = $('#biCalReadout');
  if (readout) {
    const cell = t.closest('#biCalGrid [data-d]');
    const key = cell ? `${cell.dataset.h || ''}:${cell.dataset.d}` : null;
    if (key !== st.hoverKey) { st.hoverKey = key; readout.textContent = cell ? biCalendarReadout(st.model, cell.dataset.h || null, Number(cell.dataset.d)) : 'Pasa el cursor por el calendario'; }
  }
  const scatter = $('#biScatterReadout');
  if (scatter) {
    const dot = t.closest('.bi-dot');
    const text = dot ? dot.dataset.biReadout : 'tamaño = reseñas · pulsa para abrir ficha';
    if (scatter.textContent !== text) scatter.textContent = text;
  }
}

function handleBiChange(e) {
  const t = e.target;
  if (!(t instanceof Element) || !State.bi) return false;
  if (t.id === 'biOwn' || t.id === 'biOwnInvite') { setBiOwn(t.value); if (t.id === 'biOwnInvite') $('#biOwn')?.focus(); return true; }
  if (t.id === 'biBoard') { void setBiDataFilter('board', t.value || 'all'); return true; }
  if (t.id === 'biFam') { void setBiDataFilter('fam', t.value || 'all'); return true; }
  return false;
}

function handleBiInput(e) {
  if (!(e.target instanceof Element) || e.target.id !== 'biTarget' || !State.bi?.model) return false;
  State.bi.target = Number(e.target.value);
  const side = $('#biSide');
  if (side) { side.innerHTML = biRecoHTML(State.bi.model); $('#biTarget')?.focus(); }
  return true;
}

/* ---- panel lateral genérico (ficha BI, configuración de Reputación) */
function openSidePanel(kind, modifier) {
  const overlay = $('#sidePanel');
  if (!overlay) return;
  overlay.dataset.kind = kind;
  $('#sidePanelBody').className = `side-panel ${modifier || ''}`.trim();
  openOverlay('sidePanel', '[data-side-close]');
}

function closeSidePanel(options) {
  const overlay = $('#sidePanel');
  if (!overlay || overlay.hidden) return false;
  const kind = overlay.dataset.kind;
  if (kind === 'bi' && State.bi) State.bi.drawer = null;
  closeOverlay('sidePanel', options);
  $('#sidePanelBody').innerHTML = '';
  overlay.dataset.kind = '';
  return true;
}

function kpiSm(label, count, unit, foot) {
  return `<article class="kpi kpi--sm"><div class="kpi__label">${esc(label)}</div><div><strong data-count="${count}">0</strong>${unit ? `<span class="kpi__unit">${unit}</span>` : ''}</div><div class="kpi__foot">${foot}</div></article>`;
}
function kpiSmRaw(label, value, unit, foot) {
  return `<article class="kpi kpi--sm"><div class="kpi__label">${esc(label)}</div><div><strong>${value}</strong>${unit ? `<span class="kpi__unit">${unit}</span>` : ''}</div><div class="kpi__foot">${foot}</div></article>`;
}

function captureComparisonStats(currentDetail, previousDetail) {
  const currentRows = (currentDetail?.rows || []).filter((row) => Number.isFinite(Number(row.pricePerNight)));
  const previousRows = (previousDetail?.rows || []).filter((row) => Number.isFinite(Number(row.pricePerNight)));
  const previousBySignature = uniqueHotelProducts(previousRows);
  const currentUnique = uniqueHotelProducts(currentRows);
  const currentSignatures = new Set(currentUnique.keys());
  const comparable = [...currentUnique.values()].filter((row) => previousBySignature.has(hotelComparisonSignature(row)));
  const onlyCurrent = currentRows.filter((row) => !previousBySignature.has(hotelComparisonSignature(row)));
  const onlyPrevious = previousRows.filter((row) => !currentSignatures.has(hotelComparisonSignature(row)));
  const average = (items) => items.length ? items.reduce((sum, item) => sum + Number(item.pricePerNight), 0) / items.length : null;
  const oneCurrency = new Set(comparable.map((row) => row.currency)).size === 1;
  const avgCurrent = oneCurrency ? average(comparable) : null;
  const avgPrevious = oneCurrency ? average(comparable.map((row) => previousBySignature.get(hotelComparisonSignature(row)))) : null;
  const avgChange = avgCurrent != null && avgPrevious ? ((avgCurrent - avgPrevious) / avgPrevious) * 100 : null;
  return { currentRows, previousRows, comparable, onlyCurrent, onlyPrevious, previousBySignature, avgCurrent, avgPrevious, avgChange };
}

function captureComparisonHTML(currentDetail, previousDetail, currentPhoto, previousPhoto) {
  const { comparable, onlyCurrent, onlyPrevious, previousBySignature, avgCurrent, avgChange } = captureComparisonStats(currentDetail, previousDetail);
  const changed = comparable.map((row) => {
    const previous = previousBySignature.get(hotelComparisonSignature(row));
    const currentAdr = Number(row.pricePerNight), previousAdr = Number(previous.pricePerNight);
    const delta = currentAdr - previousAdr;
    const pct = previousAdr ? (delta / previousAdr) * 100 : null;
    return { row, previous, currentAdr, previousAdr, delta, pct };
  }).sort((a, b) => Math.abs(b.pct || 0) - Math.abs(a.pct || 0)).slice(0, 12);
  const movementRows = changed.map((item) => {
    const tone = item.delta > .01 ? 'up' : item.delta < -.01 ? 'down' : 'flat';
    const signedEur = `${item.delta > .01 ? '+' : item.delta < -.01 ? '−' : ''}${eur(Math.abs(item.delta))}`;
    return `<tr><td class="name">${esc(item.row.hotelName)}</td><td class="num dim">${eur(item.previousAdr)}</td><td class="num">${eur(item.currentAdr)}</td><td class="num capture-change capture-change--${tone}">${signedEur}</td><td class="num capture-change capture-change--${tone}">${signPct(item.pct)}</td><td>${boardTag(item.row.board)}</td></tr>`;
  }).join('');
  const deltaTone = avgChange != null && avgChange > .5 ? 'up' : avgChange != null && avgChange < -.5 ? 'down' : 'flat';
  return `<article class="card table-card mb12" id="captureComparison"><div class="table-card__head capture-comparison__head"><div><div class="card__kicker" style="margin-bottom:5px;">Comparación de fotos</div><strong style="font-size:15px;">Foto #${currentPhoto.id} frente a foto #${previousPhoto.id}</strong><span class="capture-comparison__stamp">${fmtStamp(currentPhoto.scrapedAt)} vs. ${fmtStamp(previousPhoto.scrapedAt)} · Emparejamiento por hotel, estancia, habitación, régimen y condiciones</span></div><button type="button" class="btn btn--quiet" data-capture-compare-close>Cerrar comparación</button></div><div class="capture-comparison-summary"><div><span>Filas equivalentes</span><strong>${avgCurrent == null ? '—' : eur(avgCurrent)}</strong><small>${comparable.length} con el mismo producto</small></div><div><span>Δ ADR comparable</span><strong class="capture-change capture-change--${deltaTone}">${signPct(avgChange)}</strong><small>solo filas equivalentes</small></div><div><span>Producto actual</span><strong>${onlyCurrent.length}</strong><small>sin equivalente anterior</small></div><div><span>Producto anterior</span><strong>${onlyPrevious.length}</strong><small>sin equivalente actual</small></div></div><div class="table-scroll"><table class="t" style="min-width:760px;"><caption class="sr-only">Mayores variaciones de ADR entre las dos capturas seleccionadas</caption><thead><tr><th>Hotel</th><th class="r">ADR anterior</th><th class="r">ADR actual</th><th class="r">Δ €</th><th class="r">Δ ADR</th><th>Régimen</th></tr></thead><tbody>${movementRows || '<tr><td colspan="6" class="empty">No hay filas con el mismo hotel, estancia y producto en ambas capturas.</td></tr>'}</tbody></table></div></article>`;
}

/* ================================================================== VUELOS */
let airOperationsSearchTimer = null;
let airPlanTimer = null;
const FLIGHT_TABS = ['overview', 'routes', 'operations'];
const FLIGHT_TAB_KEY = 'atlas.flightTab';
const AIR_PAGE_SIZE = 50;
const AIR_LPA = { code: 'LPA', lat: 27.9319, lng: -15.3866 };
const AIR_TIER_COLORS = ['#1f7a52', '#c98a1e', '#b94f50'];
const AIR_OPS_COLUMNS = [
  // [etiqueta, clave de ordenación del servidor, alineación, ancho]
  ['Mercado', null, 'l', 150], ['Origen', 'origin', 'l', 170], ['Destino', null, 'l', 110], ['Fecha', 'date', 'l', 100],
  ['Aerolínea', null, 'l', 170], ['Vuelo', null, 'l', 150], ['Avión', null, 'l', 150], ['Clase', null, 'l', 80],
  ['Salida', null, 'r', 72], ['Llegada', null, 'r', 72], ['Conexión', null, 'l', 130], ['Duración', 'duration', 'r', 88],
  ['Precio', 'price', 'r', 84], ['Posición en ruta', null, 'l', 150], ['AAI', 'aai', 'r', 64], ['Vuelta', null, 'l', 84], ['Captura', null, 'l', 130],
];

function airDate(value) {
  if (!value) return '—';
  const date = new Date(`${value}T12:00:00Z`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' });
}
function airShortDate(value) { const s = String(value || ''); return s.length >= 10 ? `${s.slice(8, 10)}/${s.slice(5, 7)}` : '—'; }
function durationLabel(minutes) {
  const value = Number(minutes);
  if (!Number.isFinite(value) || value < 0) return '—';
  return `${Math.floor(value / 60)}h ${String(Math.round(value % 60)).padStart(2, '0')}m`;
}
function airlineCode(airline) {
  return {
    'Iberia Express': 'I2', Iberia: 'IB', 'Air Europa': 'UX', Vueling: 'VY', Eurowings: 'EW', Condor: 'DE',
    'British Airways': 'BA', Transavia: 'HV', 'Air France': 'AF', Jet2: 'LS', Lufthansa: 'LH', KLM: 'KL', SWISS: 'LX',
    'Brussels Airlines': 'SN', Austrian: 'OS', 'Austrian Airlines': 'OS', 'Tap Air Portugal': 'TP', 'TAP Air Portugal': 'TP', TAP: 'TP',
    'Discover Airlines': '4Y', 'Edelweiss Air': 'WK', Edelweiss: 'WK', 'Binter Canarias': 'NT', Binter: 'NT',
    'Aer Lingus': 'EI', Ryanair: 'FR', easyJet: 'U2', Norwegian: 'DY', 'Scandinavian Airlines': 'SK', SAS: 'SK',
    Finnair: 'AY', 'Wizz Air': 'W6', 'TUI fly': 'X3', TUI: 'X3', 'TUI fly Netherlands': 'OR', Volotea: 'V7',
  }[airline] || String(airline || '?').slice(0, 2).toUpperCase();
}
const AIR_MARKET_BY_IATA = {
  MAD: ['Español', 'España'], BCN: ['Español', 'España'],
  DUS: ['Alemán', 'Alemania'], FRA: ['Alemán', 'Alemania'], MUC: ['Alemán', 'Alemania'],
  LHR: ['Británico', 'Reino Unido'], LGW: ['Británico', 'Reino Unido'], MAN: ['Británico', 'Reino Unido'], BHX: ['Británico', 'Reino Unido'],
  AMS: ['Neerlandés', 'Países Bajos'], CDG: ['Francés', 'Francia'], DUB: ['Irlandés', 'Irlanda'],
  BRU: ['Belga', 'Bélgica'], ZRH: ['Suizo', 'Suiza'], MXP: ['Italiano', 'Italia'],
  LIS: ['Portugués', 'Portugal'], OPO: ['Portugués', 'Portugal'], ARN: ['Sueco', 'Suecia'], CPH: ['Danés', 'Dinamarca'],
};
function airMarketFromIata(row) {
  const code = [row.origin, row.destination].map((value) => String(value || '').toUpperCase()).find((value) => AIR_MARKET_BY_IATA[value]);
  const mapped = code ? AIR_MARKET_BY_IATA[code] : null;
  return mapped ? { segment: mapped[0], country: mapped[1] } : { segment: 'Internacional', country: '' };
}
function airSegment(row) { return row.market_segment || airMarketFromIata(row).segment; }

function airCaptureStartDate() {
  const date = new Date();
  date.setHours(12, 0, 0, 0);
  return date.toISOString().slice(0, 10);
}

function restoreFlightState() {
  if (State.flight) return State.flight;
  State.flight = { tab: readPref(FLIGHT_TAB_KEY, FLIGHT_TABS, 'overview'), focus: null, mapMode: 'options', planOpen: false, firstDate: airCaptureStartDate(), budget: 500, estimate: null, barHover: null };
  return State.flight;
}

/* Modelo del resumen aéreo a partir de la foto aérea vigente y la comparación con la anterior. */
function flightModel(data, comparison) {
  const flights = data.flights || [];
  const airports = data.airports || {};
  const deltas = new Map();
  (comparison?.points || []).forEach((p) => { if (p.comparable && p.changePct != null) { if (!deltas.has(p.origin)) deltas.set(p.origin, []); deltas.get(p.origin).push(Number(p.changePct)); } });
  const routes = (data.routes || []).map((r) => {
    const fs = flights.filter((f) => f.origin === r.origin);
    const prices = fs.map((f) => Number(f.price)).filter((v) => v > 0);
    const durs = fs.map((f) => Number(f.total_duration_min)).filter((v) => v > 0);
    const ap = airports[r.origin] || {};
    const d = deltas.get(r.origin);
    return {
      code: r.origin, key: r.route_key, city: r.market || ap.city || r.origin, airport: ap.name || r.origin, country: r.market_country || ap.country || '',
      lat: ap.lat, lng: ap.lng, segment: r.market_segment || airMarketFromIata(r).segment,
      options: Number(r.num_options || fs.length), airlines: r.airlines_detected || [], minP: Number(r.lowest_price) || (prices.length ? Math.min(...prices) : null),
      avgP: Number(r.avg_price) || (prices.length ? prices.reduce((a, b) => a + b, 0) / prices.length : null), maxP: prices.length ? Math.max(...prices) : null,
      directPct: Math.round(Number(r.direct_share || 0) * 100), durAvg: durs.length ? durs.reduce((a, b) => a + b, 0) / durs.length : null,
      delta: d && d.length ? d.reduce((a, b) => a + b, 0) / d.length : null, flights: fs,
    };
  }).filter((r) => r.avgP != null);
  const sortedAvg = routes.map((r) => r.avgP).sort((a, b) => a - b);
  const q1 = sortedAvg[Math.floor(sortedAvg.length / 3)], q2 = sortedAvg[Math.floor((sortedAvg.length * 2) / 3)];
  routes.forEach((r) => { r.tier = r.avgP < q1 ? 0 : r.avgP < q2 ? 1 : 2; });
  const comparable = (comparison?.points || []).filter((p) => p.comparable && p.changePct != null);
  return {
    flights, routes, airports, capture: data.capture || {}, summary: data.summary || {},
    variation: comparable.length ? comparable.reduce((a, p) => a + Number(p.changePct), 0) / comparable.length : null,
    comparableRoutes: comparable.length,
  };
}

function flightHeaderHTML(model) {
  const st = State.flight;
  const segments = new Set(model.routes.map((r) => r.segment)).size;
  const direct = model.routes.filter((r) => r.directPct > 0).length;
  const at = model.capture.capturedAt;
  const plan = st.planOpen ? flightPlanHTML(model) : '';
  return `<div class="page-head"><div><h1>Vuelos</h1><p>Conectividad aérea hacia Gran Canaria · ${direct} ${direct === 1 ? 'ruta directa' : 'rutas directas'} desde ${segments} ${segments === 1 ? 'mercado emisor' : 'mercados emisores'}</p></div>
    <div class="page-head__meta fl-head"><span>Foto aérea ${esc(fmtStamp(at))} · ${nEs(model.flights.length)} opciones</span><button type="button" class="btn btn--primary page-head__btn" data-fl-plan aria-expanded="${st.planOpen}" aria-controls="flPlan">Nueva captura aérea</button>${plan}</div></div>
    <div class="htabs" role="tablist" aria-label="Vistas de vuelos">${[['overview', 'Resumen', ''], ['routes', 'Rutas', model.routes.length], ['operations', 'Operación aérea', model.flights.length]].map(([id, label, count]) => `<button type="button" role="tab" class="htabs__tab${st.tab === id ? ' is-active' : ''}" id="flTab-${id}" data-flight-tab="${id}" aria-selected="${st.tab === id}" aria-controls="flPanel" tabindex="${st.tab === id ? 0 : -1}">${label}${count === '' ? '' : `<span>${nEs(count)}</span>`}</button>`).join('')}</div>`;
}

function flightPlanHTML(model) {
  const st = State.flight, est = st.estimate;
  const ok = est && est.withinBudget && est.serpapiConfigured !== false;
  const estText = !est ? '<span>Calculando consultas…</span><strong>—</strong>'
    : est.error ? `<span>${esc(est.error)}</span><strong>—</strong>`
    : `<span>${nEs(est.dateCount)} fechas × ${nEs(est.routes)} rutas${est.serpapiConfigured === false ? ' · falta SERPAPI_API_KEY' : ''}</span><strong>${nEs(est.queries)} consultas</strong>`;
  return `<div class="fl-plan" id="flPlan" role="dialog" aria-label="Preparar una foto de conectividad">
    <div><strong>Preparar una foto de conectividad</strong><p>SerpAPI · 1 adulto · turista · solo ida. 14 fechas diarias y después una semanal hasta 90 días.</p></div>
    <div class="fl-plan__fields"><label><span>Primera salida</span><input type="date" id="airCaptureStart" value="${esc(st.firstDate)}"></label><label><span>Presupuesto de consultas</span><input type="number" id="airCaptureBudget" min="1" max="5000" step="1" value="${esc(st.budget)}"></label></div>
    <div class="fl-plan__est${est && !est.error ? (ok ? ' is-ok' : ' is-bad') : ''}" id="airCaptureEstimate" role="status">${estText}</div>
    <button type="button" class="btn btn--primary fl-plan__go" data-air-capture-start${ok ? '' : ' disabled'}>Iniciar captura</button>
  </div>`;
}

function flightKpisHTML(model) {
  const fl = model.flights;
  const prices = fl.map((f) => Number(f.price)).filter((v) => v > 0);
  const dates = new Set(fl.map((f) => f.outbound_date).filter(Boolean)).size;
  const direct = fl.filter((f) => f.is_direct).length;
  const airlines = new Set(fl.map((f) => f.main_airline).filter(Boolean)).size;
  const durs = fl.map((f) => Number(f.total_duration_min)).filter((v) => v > 0);
  const access = model.routes.length ? model.routes.reduce((a, r) => a + r.minP, 0) / model.routes.length : null;
  const v = model.variation;
  const cells = [
    ['Rutas activas', nEs(model.routes.length), '', `${new Set(model.routes.map((r) => r.segment)).size} mercados emisores`],
    ['Opciones', nEs(fl.length), '', `${dates} ${dates === 1 ? 'fecha' : 'fechas'} de salida`],
    ['Precio de acceso', access == null ? '—' : nEs(access), access == null ? '' : '€', 'mínimo medio por ruta'],
    ['Precio medio', prices.length ? nEs(prices.reduce((a, b) => a + b, 0) / prices.length) : '—', prices.length ? '€' : '', '1 adulto · solo ida'],
    ['Variación', v == null ? '—' : biSigned(v), v == null ? '' : '%', v == null ? 'sin foto aérea comparable' : `vs foto anterior · ${model.comparableRoutes} rutas`, v == null ? '' : v > 0 ? 'neg' : v < 0 ? 'pos' : ''],
    ['Directos', fl.length ? nEs((direct / fl.length) * 100) : '—', fl.length ? '%' : '', `${fl.length - direct} opciones con escala`],
    ['Aerolíneas', nEs(airlines), '', durs.length ? `duración media ${durationLabel(durs.reduce((a, b) => a + b, 0) / durs.length)}` : 'sin duración publicada'],
  ];
  return cells.map(([label, value, unit, foot, tone]) => `<div class="kpi-strip__cell"><span class="kpi-strip__label">${label}</span><div class="kpi-strip__value"><strong>${value}</strong>${unit ? `<span>${unit}</span>` : ''}</div><span class="kpi-strip__foot${tone ? ` ${tone}` : ''}">${esc(foot)}</span></div>`).join('');
}

function flightRouteCardHTML(model, r) {
  if (!r) return '<div class="empty">Sin rutas en la foto aérea.</div>';
  const st = State.flight;
  const options = model.routes.map((x) => `<option value="${esc(x.code)}"${x.code === r.code ? ' selected' : ''}>${esc(x.code)} · ${esc(x.city)}</option>`).join('');
  const facts = [['Mínimo', eur(r.minP), 'ac'], ['Medio', eur(r.avgP), ''], ['Máximo', eur(r.maxP), ''], ['Opciones', nEs(r.options), ''], ['Directos', `${r.directPct} %`, ''], ['Duración', durationLabel(r.durAvg), '']]
    .map(([k, v, tone]) => `<div><span>${k}</span><strong class="${tone}">${v}</strong></div>`).join('');
  const dates = [...new Set(r.flights.map((f) => f.outbound_date).filter(Boolean))].sort();
  const byDate = dates.map((d) => ({ d, v: Math.min(...r.flights.filter((f) => f.outbound_date === d).map((f) => Number(f.price)).filter((v) => v > 0)) }));
  const bmax = Math.max(...byDate.map((b) => b.v), 1), bmin = Math.min(...byDate.map((b) => b.v));
  const bars = byDate.map((b) => `<i class="${b.v === bmin ? 'is-min' : ''}" style="height:${((b.v / bmax) * 100).toFixed(1)}%" title="${esc(`${airShortDate(b.d)} · ${eur(b.v)}`)}" data-fl-bar="${esc(`${airShortDate(b.d)} · ${eur(b.v)}`)}"></i>`).join('');
  const axis = dates.length ? `<span>${airShortDate(dates[0])}</span>${dates.length > 2 ? `<span>${airShortDate(dates[Math.floor(dates.length / 2)])}</span>` : ''}${dates.length > 1 ? `<span>${airShortDate(dates.at(-1))}</span>` : ''}` : '';
  const airlines = [...new Set(r.flights.map((f) => f.main_airline).filter(Boolean))].map((name) => {
    const fs = r.flights.filter((f) => f.main_airline === name);
    return { name, aircraft: (fs[0].aircraft_models || [])[0] || '', n: fs.length, min: Math.min(...fs.map((f) => Number(f.price))) };
  }).sort((a, b) => a.min - b.min).map((a) => `<div class="fl-airline"><span class="fl-iata">${esc(airlineCode(a.name))}</span><span class="fl-airline__name">${esc(a.name)}${a.aircraft ? ` <small>· ${esc(a.aircraft)}</small>` : ''}</span><span class="fl-airline__n">${a.n} opc.</span><strong>${eur(a.min)}</strong></div>`).join('');
  return `<div class="fl-route__head"><div class="fl-route__top"><span class="card__kicker">Ruta seleccionada</span><select id="flRouteSelect" class="fl-route__select" aria-label="Ruta seleccionada">${options}</select></div><h2>${esc(r.code)} → LPA</h2><span>${esc(r.airport)}${r.country ? ` · ${esc(r.country)}` : ''}</span></div>
    <div class="fl-route__facts">${facts}</div>
    <div class="fl-route__bars"><div class="fl-route__barshead"><span class="card__kicker">Mínimo por fecha de salida</span><span id="flBarReadout">${dates.length > 1 ? 'más barato en verde' : `${dates.length} fecha capturada`}</span></div><div class="fl-bars">${bars}</div><div class="fl-bars__axis">${axis}</div></div>
    <div class="fl-route__airlines"><span class="card__kicker">Aerolíneas</span>${airlines || '<span class="dim">Sin aerolíneas</span>'}</div>
    <div class="fl-route__foot"><button type="button" class="btn" data-fl-ops="${esc(r.code)}">Ver ${nEs(r.options)} vuelos</button><button type="button" class="btn fl-ask" data-fl-ask="${esc(`¿Cómo evoluciona el precio de ${r.code} → LPA?`)}">Preguntar al Copilot</button></div>`;
}

function flightHeatHTML(model, focus) {
  const start = model.capture.capturedAt ? new Date(model.capture.capturedAt) : new Date();
  const weeks = Array.from({ length: 13 }, (_, w) => { const d = new Date(start.getFullYear(), start.getMonth(), start.getDate() + w * 7); return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`; });
  const rows = model.routes.map((r) => {
    const cells = Array.from({ length: 13 }, (_, w) => {
      const ws = r.flights.filter((f) => Number(f.days_ahead) >= 0 && Math.floor(Math.max(0, Number(f.days_ahead) - 1) / 7) === w).map((f) => Number(f.price)).filter((v) => v > 0);
      if (!ws.length) return '<span class="fl-heat__cell is-empty" title="Sin datos">—</span>';
      const v = Math.min(...ws), idx = v / r.avgP - 1, a = Math.min(0.6, Math.abs(idx) * 1.6);
      const bg = Math.abs(idx) < 0.04 ? 'var(--line-soft)' : idx < 0 ? `rgba(31,122,82,${a.toFixed(2)})` : `rgba(185,79,80,${a.toFixed(2)})`;
      return `<span class="fl-heat__cell${a > 0.4 ? ' is-strong' : ''}${r.code === focus ? ' is-focus' : ''}" style="background:${bg}" title="${esc(`${r.code} · semana del ${weeks[w]} · ${eur(v)} (${biSigned(idx * 100)} % vs media)`)}">${nEs(v)}</span>`;
    }).join('');
    return `<button type="button" class="fl-heat__route${r.code === focus ? ' is-focus' : ''}" data-fl-route="${esc(r.code)}">${esc(r.code)} <small>${esc(r.city)}</small></button>${cells}`;
  }).join('');
  return `<div class="dash-card__head"><div><span class="card__kicker">Mapa de calor</span><h2>Precio mínimo por ruta y semana de salida</h2></div><div class="fl-heat__legend"><span>bajo su media</span><span class="bi-legend__scale" aria-hidden="true"><i style="background:rgba(31,122,82,.55)"></i><i style="background:rgba(31,122,82,.2)"></i><i style="background:var(--line-soft)"></i><i style="background:rgba(185,79,80,.2)"></i><i style="background:rgba(185,79,80,.55)"></i></span><span>sobre su media</span></div></div>
    <div class="fl-heat"><span></span>${weeks.map((w) => `<span class="fl-heat__week">${w}</span>`).join('')}${rows}</div>`;
}

function flightLeadHTML(model) {
  const buckets = [['≤ 14 días', 0, 14], ['15–30 días', 15, 30], ['31–60 días', 31, 60], ['61–90 días', 61, 90]].map(([label, a, b]) => {
    const vs = model.flights.filter((f) => Number(f.days_ahead) >= a && Number(f.days_ahead) <= b && f.air_accessibility_index != null).map((f) => Number(f.air_accessibility_index));
    if (!vs.length) return `<div class="fl-lead"><span>${label}</span><div class="fl-lead__track"><i class="fl-lead__axis"></i></div><strong class="dim">—</strong></div>`;
    const idx = vs.reduce((x, v) => x + v, 0) / vs.length - 1, w = Math.min(50, (Math.abs(idx) / 0.2) * 50);
    return `<div class="fl-lead" title="${vs.length} opciones"><span>${label}</span><div class="fl-lead__track"><i class="fl-lead__axis"></i><i class="fl-lead__fill ${idx >= 0 ? 'is-up' : 'is-down'}" style="left:${idx >= 0 ? 50 : 50 - w}%;width:${w.toFixed(1)}%"></i></div><strong class="${idx >= 0 ? 'neg' : 'pos'}">${biSigned(idx * 100)} %</strong></div>`;
  }).join('');
  return `<div><span class="card__kicker">Curva de antelación</span><h2>Precio según días hasta la salida</h2></div>${buckets}<span class="dash-curve__note">Índice AAI (precio / precio típico de la ruta) por tramo de antelación. Agrega las ${model.routes.length} rutas.</span>`;
}

function flightShareHTML(model) {
  const names = [...new Set(model.flights.map((f) => f.main_airline).filter(Boolean))];
  const share = names.map((n) => { const fs = model.flights.filter((f) => f.main_airline === n); return { n, count: fs.length, min: Math.min(...fs.map((f) => Number(f.price))) }; }).sort((a, b) => b.count - a.count).slice(0, 8);
  const max = share[0]?.count || 1;
  return `<span class="card__kicker">Cuota de oferta</span><h2>Aerolíneas</h2>${share.map((s) => `<div class="fl-share"><span>${esc(s.n)}</span><div class="fl-share__track"><i style="width:${((s.count / max) * 100).toFixed(1)}%"></i></div><span class="mono">${nEs((s.count / model.flights.length) * 100, 1)}%</span><span class="mono dim">${eur(s.min)}</span></div>`).join('') || '<div class="empty">Sin aerolíneas.</div>'}`;
}

function flightMarketsHTML(model) {
  const names = [...new Set(model.routes.map((r) => r.segment))];
  const segs = names.map((n) => { const rs = model.routes.filter((r) => r.segment === n), fs = model.flights.filter((f) => airSegment(f) === n); return { n, routes: rs.length, opts: fs.length, min: Math.min(...fs.map((f) => Number(f.price))) }; }).sort((a, b) => b.opts - a.opts);
  const max = segs[0]?.opts || 1;
  return `<span class="card__kicker">Origen de la demanda</span><h2>Mercados emisores</h2><div class="fl-mkt fl-mkt--head"><span>Mercado</span><span>Rutas</span><span>Opc.</span><span>Desde</span></div>${segs.map((s) => `<div class="fl-mkt"><span class="fl-mkt__name"><i style="width:${Math.max(8, (s.opts / max) * 36).toFixed(0)}px"></i><span>${esc(s.n)}</span></span><span>${s.routes}</span><span>${s.opts}</span><strong>${eur(s.min)}</strong></div>`).join('')}`;
}

function flightSignalsHTML(model) {
  const rs = model.routes;
  if (!rs.length) return '<span class="card__kicker">Lectura automática</span><h2>Señales aéreas</h2><div class="empty">Sin rutas.</div>';
  const avgNet = rs.reduce((a, r) => a + r.avgP, 0) / rs.length;
  const byAvg = [...rs].sort((a, b) => b.avgP - a.avgP)[0];
  const cheapest = [...rs].sort((a, b) => a.minP - b.minP)[0];
  const spread = [...rs].sort((a, b) => (b.maxP - b.minP) - (a.maxP - a.minP))[0];
  const lowDirect = [...rs].sort((a, b) => a.directPct - b.directPct)[0];
  const via = (lowDirect.flights.find((f) => !f.is_direct)?.layover_airports || [])[0];
  const moved = [...rs].filter((r) => r.delta != null).sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))[0];
  const signals = [
    [eur(byAvg.avgP), `Ruta más cara: ${byAvg.code}`, `${byAvg.city}: ${nEs(byAvg.avgP / avgNet, 1)}× el precio medio de la red.`, 'neg', byAvg.code],
    [eur(cheapest.minP), `Acceso más barato: ${cheapest.code}`, `Mínimo observado desde ${cheapest.city}.`, 'pos', cheapest.code],
    [`+${eur(spread.maxP - spread.minP)}`, `Mayor amplitud: ${spread.code}`, 'Diferencia entre mínimo y máximo en la ruta.', '', spread.code],
    [`${lowDirect.directPct} %`, `Menos directos: ${lowDirect.code}`, lowDirect.directPct === 100 ? 'Toda la oferta observada es directa.' : `Parte de la oferta conecta vía ${via || 'otro aeropuerto'}.`, 'warn', lowDirect.code],
    moved ? [`${biSigned(moved.delta)} %`, `Mayor cambio: ${moved.code}`, 'Variación del precio frente a la foto aérea anterior.', moved.delta > 0 ? 'neg' : 'pos', moved.code] : null,
  ].filter(Boolean);
  return `<span class="card__kicker">Lectura automática</span><h2>Señales aéreas</h2>${signals.map(([v, title, text, tone, code]) => `<button type="button" class="fl-signal" data-fl-route="${esc(code)}"><span class="fl-signal__v ${tone}">${esc(v)}</span><span><strong>${esc(title)}</strong><span>${esc(text)}</span></span></button>`).join('')}`;
}

function flightOverviewHTML(model) {
  const st = State.flight;
  const focus = model.routes.find((r) => r.code === st.focus) || model.routes[0] || null;
  st.focus = focus ? focus.code : null;
  const legend = { options: 'Número de opciones observadas', airlines: 'Número de aerolíneas', price: 'Más gruesa = más barata' }[st.mapMode];
  return `<section class="kpi-strip kpi-strip--bi kpi-strip--fl" aria-label="Resumen de conectividad">${flightKpisHTML(model)}</section>
    <div class="dash-grid">
      <article class="dash-card dash-card--map fl-map-card"><div class="dash-card__head"><div><span class="card__kicker">Red de rutas</span><h2>Conectividad hacia LPA</h2></div>
        <div class="fl-map__tools"><div class="seg seg--sm" role="group" aria-label="Grosor de línea">${[['options', 'Oferta'], ['airlines', 'Aerolíneas'], ['price', 'Precio']].map(([id, label]) => `<button type="button" class="${st.mapMode === id ? 'is-active' : ''}" data-fl-mode="${id}" aria-pressed="${st.mapMode === id}">${label}</button>`).join('')}</div>
        <div class="dash-legend"><span><i class="fl-line tone-low"></i>bajo</span><span><i class="fl-line tone-mid"></i>medio</span><span><i class="fl-line tone-high"></i>alto</span></div></div></div>
        <div class="map-frame fl-map" id="flMapFrame"><div class="map-frame__canvas" id="flMap" aria-label="Mapa de rutas hacia Gran Canaria"></div><div class="fl-map__legend"><span class="card__kicker">Grosor de línea</span><span id="flMapLegend">${legend}</span></div></div></article>
      <article class="dash-card fl-route" id="flRoute">${flightRouteCardHTML(model, focus)}</article>
      <article class="dash-card fl-heat-card" id="flHeat">${flightHeatHTML(model, st.focus)}</article>
      <article class="dash-card fl-lead-card">${flightLeadHTML(model)}</article>
      <article class="dash-card fl-small">${flightShareHTML(model)}</article>
      <article class="dash-card fl-small">${flightMarketsHTML(model)}</article>
      <article class="dash-card fl-small">${flightSignalsHTML(model)}</article>
    </div>`;
}

function flightRoutesHTML(model) {
  const rs = [...model.routes].sort((a, b) => b.avgP - a.avgP);
  if (!rs.length) return '<article class="card card--pad"><div class="empty">Sin rutas en la foto aérea.</div></article>';
  const lo = Math.floor(Math.min(...rs.map((r) => r.minP)) / 50) * 50, hi = Math.ceil(Math.max(...rs.map((r) => r.maxP)) / 50) * 50;
  const X = (v) => ((v - lo) / Math.max(1, hi - lo)) * 100;
  const ticks = Array.from({ length: 5 }, (_, i) => lo + ((hi - lo) * i) / 4);
  const rows = rs.map((r) => `<button type="button" class="fl-range" data-fl-route-open="${esc(r.code)}"><span class="fl-range__name"><strong>${esc(r.code)} → LPA</strong><small>${esc(r.city)}</small></span>
    <span class="fl-range__plot"><i class="fl-range__axis"></i><i class="fl-range__span" style="left:${X(r.minP).toFixed(1)}%;width:${(X(r.maxP) - X(r.minP)).toFixed(1)}%"></i><i class="fl-range__min" style="left:${X(r.minP).toFixed(1)}%"></i><i class="fl-range__avg" style="left:${X(r.avgP).toFixed(1)}%"></i><i class="fl-range__max" style="left:${X(r.maxP).toFixed(1)}%"></i></span>
    <span class="mono">${nEs(r.minP)} · ${nEs(r.avgP)} · ${nEs(r.maxP)} €</span><span class="mono dim">${r.directPct} %</span><span class="mono ${r.delta > 0 ? 'neg' : r.delta < 0 ? 'pos' : 'dim'}">${r.delta == null ? '—' : `${biSigned(r.delta)} %`}</span></button>`).join('');
  return `<article class="card card--pad fl-ranges"><div class="dash-card__head"><div><span class="card__kicker">Precio de entrada vs. medio vs. máximo</span><h2>Amplitud de tarifa por ruta</h2></div><div class="dash-legend"><span><i class="fl-key fl-key--min"></i>mínimo</span><span><i class="fl-key fl-key--avg"></i>medio</span><span><i class="fl-key fl-key--max"></i>máximo</span></div></div>
    <div class="fl-range fl-range--head"><span>Ruta</span><span></span><span>Mín · medio · máx</span><span>Directos</span><span>Δ foto</span></div>${rows}
    <div class="fl-ranges__axis"><span></span><span class="fl-ranges__ticks">${ticks.map((t) => `<span>${eur(t)}</span>`).join('')}</span><span></span><span></span><span></span></div>
    <p class="fl-note">Ofertas observadas, no billetes vendidos.</p></article>`;
}

/* ---- operación aérea (tabla profesional, paginada en el servidor) */
function airOperationParams(extra = {}) {
  const q = State.airOperations;
  const params = new URLSearchParams({ page: String(q.page), pageSize: String(AIR_PAGE_SIZE), sort: q.sort, ...extra });
  [['query', 'query'], ['segment', 'segment'], ['origin', 'origin'], ['airline', 'airline'], ['connection', 'connection']].forEach(([key, param]) => { if (q[key]) params.set(param, q[key]); });
  return params.toString();
}

function persistAirOperationsQuery() {
  try {
    const q = State.airOperations;
    localStorage.setItem('atlas.air-operations.query.v3', JSON.stringify({ query: q.query, segment: q.segment, origin: q.origin, airline: q.airline, connection: q.connection, sort: q.sort }));
  } catch (_) { /* la consulta sigue operativa sin almacenamiento local */ }
}

const AIR_SORTS = ['price-asc', 'price-desc', 'duration-asc', 'duration-desc', 'aai-asc', 'aai-desc', 'date-asc', 'date-desc', 'origin-asc', 'origin-desc'];
function restoreAirOperationsQuery() {
  const q = State.airOperations;
  if (q.restored) return;
  q.restored = true;
  try {
    const stored = JSON.parse(localStorage.getItem('atlas.air-operations.query.v3') || 'null');
    if (!stored || typeof stored !== 'object') return;
    ['query', 'segment', 'origin', 'airline'].forEach((key) => { q[key] = typeof stored[key] === 'string' ? stored[key].slice(0, 120) : ''; });
    q.connection = ['', 'direct', 'non_direct'].includes(stored.connection) ? stored.connection : '';
    q.sort = AIR_SORTS.includes(stored.sort) ? stored.sort : q.sort;
  } catch (_) { /* una preferencia local dañada no bloquea la vista */ }
}

function airPositionCell(row) {
  const min = Number(row.typical_price_min), max = Number(row.typical_price_max), price = Number(row.price ?? row.lowest_price);
  const label = row.price_quality_label;
  const text = label === 'Barato' ? 'barato para la ruta' : label === 'Caro' ? 'caro para la ruta' : label === 'Normal' ? 'en la media' : 'sin rango típico';
  const tone = label === 'Barato' ? 'pos' : label === 'Caro' ? 'neg' : 'dim';
  if (!Number.isFinite(min) || !Number.isFinite(max) || !Number.isFinite(price) || max <= min) return `<div class="fl-pos"><div class="fl-pos__bar"><i></i><i></i><i></i></div><span class="fl-pos__label ${tone}">${text}</span></div>`;
  // los tramos son: por debajo del típico, dentro y por encima; el marcador se sitúa en el tercio que le toca
  const point = price < min ? Math.max(2, (price / min) * 33.3) : price > max ? Math.min(98, 66.7 + ((price - max) / max) * 33.3) : 33.3 + ((price - min) / (max - min)) * 33.4;
  return `<div class="fl-pos" title="${esc(`Rango típico ${eur(min)}–${eur(max)} · observado ${eur(price)}`)}"><div class="fl-pos__bar"><i></i><i></i><i></i><em style="left:${point.toFixed(1)}%"></em></div><span class="fl-pos__label ${tone}">${text}</span></div>`;
}

function airOperationRow(row) {
  const segment = airSegment(row);
  const stops = Number(row.num_layovers || row.stops || 0);
  const via = (row.layover_airports || [])[0];
  const conn = row.is_direct ? '<span class="chip chip--good">Directo</span>' : `<span class="chip chip--warn">${stops || 1} escala${stops > 1 ? 's' : ''}${via ? ` · ${esc(via)}` : ''}</span>`;
  const aai = row.air_accessibility_index == null ? null : Number(row.air_accessibility_index);
  const airline = row.main_airline || (row.airlines || []).join(' · ') || '—';
  return `<tr>
    <th scope="row" class="fops__sticky"><strong>${esc(segment)}</strong><small>${esc(row.market || '—')}</small></th>
    <td><strong class="mono">${esc(row.origin || '—')}</strong><small>${esc(row.departure_airport_name || '')}</small></td>
    <td><strong class="mono">${esc(row.destination || '—')}</strong><small>${esc(row.arrival_airport_name || 'Gran Canaria')}</small></td>
    <td class="mono nowrap">${esc(airShortDate(row.outbound_date))}${row.days_ahead == null ? '' : ` <small class="inline">${nEs(row.days_ahead)}d</small>`}</td>
    <td><span class="fl-airline__cell"><span class="fl-iata">${esc(airlineCode(airline))}</span><span class="ellipsis">${esc(airline)}</span></span></td>
    <td class="mono muted ellipsis" title="${esc((row.flight_numbers || []).join(' · '))}">${esc((row.flight_numbers || []).join(' · ') || '—')}</td>
    <td class="muted ellipsis" title="${esc((row.aircraft_models || []).join(' · '))}">${esc((row.aircraft_models || []).join(' · ') || '—')}</td>
    <td class="muted">${esc((row.travel_classes || []).map((c) => (c === 'Economy' ? 'Turista' : c)).join(' · ') || '—')}</td>
    <td class="mono r">${esc(row.departure_time || '—')}</td>
    <td class="mono r">${esc(row.arrival_time || '—')}</td>
    <td title="${esc(row.is_direct ? 'Sin escala' : `Escala en ${(row.layover_airports || []).join(', ') || 'aeropuerto no informado'}`)}">${conn}</td>
    <td class="mono r muted">${durationLabel(row.total_duration_min)}</td>
    <td class="mono r fops__price">${eur(row.price ?? row.lowest_price)}</td>
    <td>${airPositionCell(row)}</td>
    <td class="mono r ${aai == null ? 'dim' : aai < 0.9 ? 'pos' : aai > 1.1 ? 'neg' : ''}" title="Precio observado dividido por el promedio típico de la ruta">${aai == null ? '—' : nEs(aai, 2)}</td>
    <td class="dim">${row.return_date ? esc(airShortDate(row.return_date)) : 'Solo ida'}</td>
    <td class="mono dim nowrap">${esc(fmtStamp(row.capture_run_at || row.search_datetime))}</td>
  </tr>`;
}

async function flightOperationsHTML(model) {
  const q = State.airOperations;
  restoreAirOperationsQuery();
  const data = await api(`/api/air-data/options?${airOperationParams()}`);
  const total = Number(data.total || 0);
  const pages = Math.max(1, Math.ceil(total / AIR_PAGE_SIZE));
  if (q.page > pages) { q.page = pages; return flightOperationsHTML(model); }
  const from = total ? (q.page - 1) * AIR_PAGE_SIZE + 1 : 0, to = Math.min(total, q.page * AIR_PAGE_SIZE);
  const facets = data.facets || {};
  const segments = [...new Set(model.flights.map(airSegment))].sort((a, b) => a.localeCompare(b, 'es'));
  const select = (key, label, values, placeholder, labelOf = (v) => v) => `<label class="fops__filter"><span>${label}</span><select data-air-operation-filter="${key}">${[['', placeholder], ...values.map((v) => [v, labelOf(v)])].map(([v, l]) => `<option value="${esc(v)}"${q[key] === v ? ' selected' : ''}>${esc(l)}</option>`).join('')}</select></label>`;
  const sortKey = q.sort.replace(/-(asc|desc)$/, ''), sortDir = q.sort.endsWith('desc') ? 'desc' : 'asc';
  const heads = AIR_OPS_COLUMNS.map(([label, key, align], i) => {
    const active = key && sortKey === key;
    const inner = `${label}${active ? `<span aria-hidden="true">${sortDir === 'asc' ? '↑' : '↓'}</span>` : ''}`;
    return `<th scope="col" class="${align === 'r' ? 'r' : ''}${i === 0 ? ' fops__sticky' : ''}"${active ? ` aria-sort="${sortDir === 'asc' ? 'ascending' : 'descending'}"` : ''}>${key ? `<button type="button" data-air-sort="${key}" class="${active ? 'is-active' : ''}">${inner}</button>` : `<span>${label}</span>`}</th>`;
  }).join('');
  const body = (data.rows || []).map(airOperationRow).join('');
  const filtered = ['query', 'segment', 'origin', 'airline', 'connection'].some((k) => q[k]);
  return `<article class="fops${q.fullscreen ? ' is-fullscreen' : ''}" id="airOperationsCard">
    <div class="fops__head"><div><strong>Operación aérea</strong><span>${nEs(total)} de ${nEs(model.flights.length)} opciones</span></div>
      <div class="fops__tools"><button type="button" class="btn btn--sm" data-air-export>Exportar CSV</button><button type="button" class="btn btn--sm" data-air-operations-fullscreen aria-pressed="${q.fullscreen}">${q.fullscreen ? 'Salir de pantalla completa' : 'Pantalla completa'}</button></div></div>
    <div class="fops__filters" role="group" aria-label="Filtros de opciones aéreas">
      <label class="fops__filter fops__filter--search"><span>Buscar</span><input type="search" id="airOperationsSearch" value="${esc(q.query)}" placeholder="Aerolínea, vuelo, avión o aeropuerto" autocomplete="off"></label>
      ${select('segment', 'Mercado', segments, 'Todos')}
      ${select('origin', 'Ruta', model.routes.map((r) => r.code), 'Todas', (v) => `${v} → LPA`)}
      ${select('airline', 'Aerolínea', facets.airlines || [], 'Todas')}
      <label class="fops__filter"><span>Conexión</span><select data-air-operation-filter="connection"><option value=""${!q.connection ? ' selected' : ''}>Todas</option><option value="direct"${q.connection === 'direct' ? ' selected' : ''}>Solo directos</option><option value="non_direct"${q.connection === 'non_direct' ? ' selected' : ''}>Con escala</option></select></label>
      <button type="button" class="fops__reset" data-air-operation-reset${filtered || q.sort !== 'date-asc' ? '' : ' disabled'}>Restablecer</button>
    </div>
    <div class="fops__scroll" tabindex="0" role="region" aria-label="Opciones de vuelo: desplazamiento horizontal y vertical">
      <table class="fops__table" id="airOperationsTable"><caption class="sr-only">Opciones de vuelo capturadas, con conexión, precio, posición frente al rango típico, índice de accesibilidad y duración</caption>
        <colgroup>${AIR_OPS_COLUMNS.map((c) => `<col style="width:${c[3]}px">`).join('')}</colgroup>
        <thead><tr>${heads}</tr></thead><tbody>${body}</tbody></table>
      ${body ? '' : '<div class="fops__empty"><strong>Ninguna opción coincide</strong><span>Cambia los filtros o restablécelos.</span></div>'}
    </div>
    <div class="fops__pager"><span>${total ? `${from}–${to} de ${nEs(total)} · página ${q.page}/${pages}` : '0 resultados'}</span><div><button type="button" class="btn btn--xs" data-air-operation-page="prev"${q.page <= 1 ? ' disabled' : ''}>← Anterior</button><button type="button" class="btn btn--xs" data-air-operation-page="next"${q.page >= pages ? ' disabled' : ''}>Siguiente →</button></div></div>
  </article>`;
}

async function exportAirOperations() {
  const rows = [];
  for (let page = 1; page <= 50; page++) {
    const data = await api(`/api/air-data/options?${airOperationParams({ page: String(page), pageSize: '200' })}`);
    rows.push(...(data.rows || []));
    if (rows.length >= Number(data.total || 0) || !(data.rows || []).length) break;
  }
  const safe = (value) => { const text = String(value ?? ''); return /^[=+\-@\t\r]/.test(text) ? `'${text}` : text; };
  const head = ['Mercado', 'Ciudad', 'Origen', 'Destino', 'Fecha', 'Días', 'Aerolínea', 'Vuelo', 'Avión', 'Clase', 'Salida', 'Llegada', 'Conexión', 'Duración (min)', 'Precio (€)', 'Posición', 'AAI', 'Vuelta', 'Captura'];
  const lines = rows.map((r) => [airSegment(r), r.market, r.origin, r.destination, r.outbound_date, r.days_ahead, r.main_airline, (r.flight_numbers || []).join(' · '), (r.aircraft_models || []).join(' · '), (r.travel_classes || []).join(' · '), r.departure_time, r.arrival_time,
    r.is_direct ? 'Directo' : `${r.num_layovers || 1} escala ${(r.layover_airports || []).join(' ')}`.trim(), r.total_duration_min, r.price == null ? '' : String(r.price).replace('.', ','), r.price_quality_label, r.air_accessibility_index == null ? '' : String(r.air_accessibility_index).replace('.', ','), r.return_date || '', r.capture_run_at || r.search_datetime || '']
    .map((v) => `"${safe(v).replace(/"/g, '""')}"`).join(';'));
  const blob = new Blob([`﻿${[head.join(';'), ...lines].join('\r\n')}`], { type: 'text/csv;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'operacion-aerea.csv';
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  toast(`CSV exportado · ${rows.length} opciones`, 'ok');
}

function toggleAirOperationsFullscreen(force) {
  const next = typeof force === 'boolean' ? force : !State.airOperations.fullscreen;
  State.airOperations.fullscreen = next;
  document.body.classList.toggle('air-operations-fullscreen', next);
  const card = $('#airOperationsCard');
  if (card) card.classList.toggle('is-fullscreen', next);
  const button = $('[data-air-operations-fullscreen]');
  if (button) { button.setAttribute('aria-pressed', String(next)); button.textContent = next ? 'Salir de pantalla completa' : 'Pantalla completa'; button.focus(); }
}

async function paintAirOperations({ focusSearch = false } = {}) {
  const panel = $('#flPanel');
  if (!panel || !State.flightModel) return;
  const requestId = ++State.airOperations.requestId;
  try {
    const html = await flightOperationsHTML(State.flightModel);
    if (requestId !== State.airOperations.requestId || !panel.isConnected) return;
    panel.innerHTML = `${State.airOperations.fullscreen ? '<div class="fops__backdrop" data-air-operations-fullscreen></div>' : ''}${html}`;
    persistAirOperationsQuery();
    if (focusSearch) { const input = $('#airOperationsSearch'); input?.focus(); input?.setSelectionRange(input.value.length, input.value.length); }
  } catch (e) { if (panel.isConnected) panel.innerHTML = `<div class="inline-error">No se pudieron cargar las opciones aéreas: ${esc(e.message)}</div>`; }
}

function updateAirOperationsQuery(key, value, focusSearch = false) {
  const q = State.airOperations;
  q[key] = value;
  q.page = 1;
  void paintAirOperations({ focusSearch });
}

function resetAirOperationsQuery() {
  Object.assign(State.airOperations, { page: 1, query: '', segment: '', origin: '', airline: '', connection: '', sort: 'date-asc' });
  void paintAirOperations({ focusSearch: true });
}

function setAirSort(key) {
  const q = State.airOperations;
  const [current, dir] = [q.sort.replace(/-(asc|desc)$/, ''), q.sort.endsWith('desc') ? 'desc' : 'asc'];
  q.sort = `${key}-${current === key && dir === 'asc' ? 'desc' : 'asc'}`;
  q.page = 1;
  void paintAirOperations().then(() => $(`[data-air-sort="${key}"]`)?.focus());
}

/* ---- captura aérea (desplegable de la cabecera) */
async function estimateAirCapture() {
  const st = State.flight;
  const requestId = (st.estimateRequest = (st.estimateRequest || 0) + 1);
  st.estimate = null;
  repaintFlightPlan();
  try {
    const estimate = await api('/api/air-data/capture/estimate', {
      method: 'POST',
      body: JSON.stringify({ areaIds: ['gran-canaria'], routeKeys: [], countryIds: [], direct: true, outboundDate: st.firstDate, dailyDays: 14, weeklyUntilDays: 90, maxQueries: Number(st.budget) || 0 }),
    });
    if (requestId !== st.estimateRequest) return;
    st.estimate = estimate;
  } catch (error) {
    if (requestId !== st.estimateRequest) return;
    st.estimate = { error: error.message };
  }
  repaintFlightPlan();
}

function repaintFlightPlan() {
  const plan = $('#flPlan');
  if (!plan || !State.flightModel) return;
  const focusId = document.activeElement && plan.contains(document.activeElement) ? document.activeElement.id : null;
  plan.outerHTML = flightPlanHTML(State.flightModel);
  if (focusId) $(`#${focusId}`)?.focus();
}

async function startAirCapture() {
  const st = State.flight, estimate = st.estimate;
  if (!estimate || !estimate.withinBudget) return;
  const button = $('[data-air-capture-start]');
  if (button) button.disabled = true;
  try {
    const response = await api('/api/jobs/air-capture', {
      method: 'POST',
      body: JSON.stringify({ areaIds: ['gran-canaria'], routeKeys: [], countryIds: [], direct: true, outboundDate: st.firstDate, dailyDays: 14, weeklyUntilDays: 90, maxQueries: Number(st.budget) || 0 }),
    });
    st.planOpen = false;
    st.estimate = null;
    $('#flPlan')?.remove();
    $('[data-fl-plan]')?.setAttribute('aria-expanded', 'false');
    toast(`Captura aérea en cola · ${nEs(estimate.queries)} consultas${response.job?.id ? ` · trabajo ${response.job.id}` : ''}`, 'ok');
  } catch (error) {
    toast(`No se pudo iniciar la captura: ${error.message}`, 'warn');
    if (button) button.disabled = false;
  }
}

/* ---- mapa de rutas */
function flightArc(a, b) {
  const pts = [];
  const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, dx = b[0] - a[0], dy = b[1] - a[1];
  const cx = mx - dy * 0.22, cy = my + dx * 0.22;
  for (let i = 0; i <= 24; i++) {
    const t = i / 24;
    pts.push([(1 - t) * (1 - t) * a[0] + 2 * (1 - t) * t * cx + t * t * b[0], (1 - t) * (1 - t) * a[1] + 2 * (1 - t) * t * cy + t * t * b[1]]);
  }
  return pts;
}

function flightWidthExpr() {
  const st = State.flight;
  const v = st.mapMode === 'options' ? ['get', 'opts'] : st.mapMode === 'airlines' ? ['*', ['get', 'air'], 22] : ['/', 40000, ['get', 'price']];
  return ['case', ['==', ['get', 'code'], st.focus || ''], ['+', 2.5, ['/', v, 14]], ['+', 1, ['/', v, 22]]];
}

function paintFlightMap() {
  const map = State.flightMap;
  if (!map) return;
  if (map.getLayer && map.getLayer('fl-routes')) {
    map.setPaintProperty('fl-routes', 'line-width', flightWidthExpr());
    map.setPaintProperty('fl-routes', 'line-opacity', ['case', ['==', ['get', 'code'], State.flight.focus || ''], 1, 0.5]);
  }
  $$('[data-fl-label]').forEach((el) => el.classList.toggle('is-focus', el.dataset.flLabel === State.flight.focus));
}

async function renderFlightMap(model) {
  const frame = $('#flMapFrame'), container = $('#flMap');
  if (!frame || !container) return;
  const routes = model.routes.filter((r) => Number.isFinite(r.lat) && Number.isFinite(r.lng));
  if (!routes.length) { mapFrameStatus(frame, 'No hay aeropuertos con coordenadas en la foto aérea.'); return; }
  try { await loadMapLibre(); } catch (_) { if (frame.isConnected) mapFrameStatus(frame, MAP_FAILED_TEXT); return; }
  if (!frame.isConnected || State.view !== 'flights') return;
  destroyFlightMap();
  let map;
  try { map = createAtlasMap(container, { center: [-1.5, 43], zoom: 3.05 }); } catch (_) { mapFrameStatus(frame, MAP_FAILED_TEXT); return; }
  State.flightMap = map;
  const ml = window.maplibregl;
  const geo = { type: 'FeatureCollection', features: routes.map((r) => ({ type: 'Feature', properties: { code: r.code, color: AIR_TIER_COLORS[r.tier], opts: r.options, air: r.airlines.length, price: r.avgP }, geometry: { type: 'LineString', coordinates: flightArc([r.lng, r.lat], [AIR_LPA.lng, AIR_LPA.lat]) } })) };
  const addLayers = () => {
    if (map.getSource('fl-routes')) return;
    map.addSource('fl-routes', { type: 'geojson', data: geo });
    map.addLayer({ id: 'fl-routes', type: 'line', source: 'fl-routes', layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': ['get', 'color'], 'line-width': flightWidthExpr(), 'line-opacity': 0.6 } });
    paintFlightMap();
  };
  map._atlasRestyle = addLayers;
  map.once('style.load', addLayers);
  map.on('click', 'fl-routes', (e) => { const code = e.features?.[0]?.properties?.code; if (code) setFlightFocus(code); });
  map.on('mouseenter', 'fl-routes', () => { map.getCanvas().style.cursor = 'pointer'; });
  map.on('mouseleave', 'fl-routes', () => { map.getCanvas().style.cursor = ''; });
  routes.forEach((r) => {
    const label = mapPinElement(`<button type="button" class="fl-label" data-fl-label="${esc(r.code)}" data-fl-route="${esc(r.code)}" aria-label="${esc(`${r.code} → LPA · desde ${eur(r.minP)}`)}">${esc(r.code)} · ${eur(r.minP)}</button>`);
    State.flightMarkers.push(new ml.Marker({ element: label, anchor: 'bottom', offset: [0, -4] }).setLngLat([r.lng, r.lat]).addTo(map));
    const dot = mapPinElement(`<span class="fl-dot" style="background:${AIR_TIER_COLORS[r.tier]}"></span>`);
    State.flightMarkers.push(new ml.Marker({ element: dot }).setLngLat([r.lng, r.lat]).addTo(map));
  });
  const hub = mapPinElement('<span class="fl-hub"><i></i><b>LPA</b></span>');
  State.flightMarkers.push(new ml.Marker({ element: hub, anchor: 'left', offset: [-7, 0] }).setLngLat([AIR_LPA.lng, AIR_LPA.lat]).addTo(map));
  paintFlightMap();
}

function destroyFlightMap() {
  (State.flightMarkers || []).forEach((m) => m.remove());
  State.flightMarkers = [];
  if (State.flightMap) { State.flightMap.remove(); State.flightMap = null; }
}

function setFlightFocus(code) {
  const st = State.flight, model = State.flightModel;
  if (!model || !model.routes.some((r) => r.code === code)) return;
  st.focus = code;
  const card = $('#flRoute');
  if (card) card.innerHTML = flightRouteCardHTML(model, model.routes.find((r) => r.code === code));
  const heat = $('#flHeat');
  if (heat) heat.innerHTML = flightHeatHTML(model, code);
  paintFlightMap();
}

async function renderFlights() {
  const host = mount('flights');
  const st = restoreFlightState();
  destroyFlightMap();
  if (st.tab !== 'operations' && State.airOperations.fullscreen) toggleAirOperationsFullscreen(false);
  skeleton(host, 'list');
  let data, comparison;
  try {
    [data, comparison] = await Promise.all([
      State.air || api('/api/air-data?direction=arrival'),
      State.airComparison || api('/api/air-data/comparison?direction=arrival').catch(() => ({ points: [] })),
    ]);
    State.air = data; State.airComparison = comparison;
  } catch (e) { host.innerHTML = `<div class="page">${pageHead('Vuelos', 'Conectividad aérea hacia Gran Canaria', '')}<div class="inline-error">No se pudo cargar la conectividad aérea: ${esc(e.message)}</div></div>`; return; }
  if (State.view !== 'flights') return;
  const model = flightModel(data, comparison);
  State.flightModel = model;
  host.innerHTML = `<div class="page fl">${flightHeaderHTML(model)}<div id="flPanel" role="tabpanel" aria-labelledby="flTab-${st.tab}" class="fl-panel"></div></div>`;
  const panel = $('#flPanel');
  if (st.tab === 'overview') { panel.innerHTML = flightOverviewHTML(model); void renderFlightMap(model); }
  else if (st.tab === 'routes') panel.innerHTML = flightRoutesHTML(model);
  else await paintAirOperations();
  if (st.planOpen) void estimateAirCapture();
}

function setFlightTab(tab) {
  if (!FLIGHT_TABS.includes(tab)) return;
  State.flight.tab = tab;
  writePref(FLIGHT_TAB_KEY, tab);
  void renderFlights().then(() => $(`#flTab-${tab}`)?.focus());
}

function handleFlightClick(e) {
  const t = e.target instanceof Element ? e.target : null;
  if (!t || !State.flight || !t.closest('#view-flights')) {
    if (State.flight?.planOpen && t && !t.closest('#flPlan') && !t.closest('[data-fl-plan]') && $('#flPlan')) { State.flight.planOpen = false; $('#flPlan').remove(); $('[data-fl-plan]')?.setAttribute('aria-expanded', 'false'); }
    return false;
  }
  const st = State.flight;
  if (st.planOpen && !t.closest('#flPlan') && !t.closest('[data-fl-plan]')) { st.planOpen = false; $('#flPlan')?.remove(); $('[data-fl-plan]')?.setAttribute('aria-expanded', 'false'); }
  const tab = t.closest('[data-flight-tab]');
  if (tab) { if (tab.dataset.flightTab !== st.tab) setFlightTab(tab.dataset.flightTab); return true; }
  if (t.closest('[data-fl-plan]')) {
    st.planOpen = !st.planOpen;
    $('[data-fl-plan]').setAttribute('aria-expanded', String(st.planOpen));
    if (st.planOpen) { $('.fl-head').insertAdjacentHTML('beforeend', flightPlanHTML(State.flightModel)); $('#airCaptureStart')?.focus(); void estimateAirCapture(); } else $('#flPlan')?.remove();
    return true;
  }
  if (t.closest('[data-air-capture-start]')) { void startAirCapture(); return true; }
  const mode = t.closest('[data-fl-mode]');
  if (mode) {
    st.mapMode = mode.dataset.flMode;
    $$('[data-fl-mode]').forEach((b) => { const on = b.dataset.flMode === st.mapMode; b.classList.toggle('is-active', on); b.setAttribute('aria-pressed', String(on)); });
    $('#flMapLegend').textContent = { options: 'Número de opciones observadas', airlines: 'Número de aerolíneas', price: 'Más gruesa = más barata' }[st.mapMode];
    paintFlightMap();
    return true;
  }
  const route = t.closest('[data-fl-route]');
  if (route) { setFlightFocus(route.dataset.flRoute); return true; }
  const routeOpen = t.closest('[data-fl-route-open]');
  if (routeOpen) { st.focus = routeOpen.dataset.flRouteOpen; setFlightTab('overview'); return true; }
  const ops = t.closest('[data-fl-ops]');
  if (ops) { Object.assign(State.airOperations, { page: 1, query: '', segment: '', airline: '', connection: '', origin: ops.dataset.flOps }); setFlightTab('operations'); return true; }
  const ask = t.closest('[data-fl-ask]');
  if (ask) { askCopilot(ask.dataset.flAsk); return true; }
  const sort = t.closest('[data-air-sort]');
  if (sort) { setAirSort(sort.dataset.airSort); return true; }
  const page = t.closest('[data-air-operation-page]');
  if (page) { State.airOperations.page = Math.max(1, State.airOperations.page + (page.dataset.airOperationPage === 'next' ? 1 : -1)); void paintAirOperations(); return true; }
  if (t.closest('[data-air-operation-reset]')) { resetAirOperationsQuery(); return true; }
  if (t.closest('[data-air-operations-fullscreen]')) { toggleAirOperationsFullscreen(); void paintAirOperations(); return true; }
  if (t.closest('[data-air-export]')) { void exportAirOperations(); return true; }
  return false;
}

function handleFlightInput(e) {
  const t = e.target;
  if (!(t instanceof Element) || !State.flight) return false;
  if (t.id === 'airOperationsSearch') {
    clearTimeout(airOperationsSearchTimer);
    const value = t.value.slice(0, 120);
    airOperationsSearchTimer = setTimeout(() => updateAirOperationsQuery('query', value, true), 220);
    return true;
  }
  if (t.id === 'airCaptureStart' || t.id === 'airCaptureBudget') {
    if (t.id === 'airCaptureStart') State.flight.firstDate = t.value; else State.flight.budget = t.value;
    clearTimeout(airPlanTimer);
    airPlanTimer = setTimeout(() => void estimateAirCapture(), 260);
    return true;
  }
  return false;
}

function handleFlightChange(e) {
  const t = e.target;
  if (!(t instanceof Element) || !State.flight) return false;
  if (t.id === 'flRouteSelect') { setFlightFocus(t.value); $('#flRouteSelect')?.focus(); return true; }
  const filter = t.closest('[data-air-operation-filter]');
  if (filter) { updateAirOperationsQuery(filter.dataset.airOperationFilter, filter.value); return true; }
  return false;
}

function handleFlightOver(e) {
  const bar = e.target instanceof Element ? e.target.closest('[data-fl-bar]') : null;
  const readout = $('#flBarReadout');
  if (bar && readout) readout.textContent = bar.dataset.flBar;
}

/* ---------------------------------------------------- hotel reputation */
function reputationKeyPath(key, suffix) {
  const bytes = new TextEncoder().encode(String(key));
  const binary = Array.from(bytes, (value) => String.fromCharCode(value)).join('');
  const encoded = btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
  return `/api/hotel-reviews/hk_${encoded}/${suffix}`;
}

function reviewJobPanelHTML() {
  const job = State.reputation.job;
  if (!job) return '';
  const status = job.status === 'completed' ? 'completado' : job.status === 'failed' ? 'fallido' : job.status === 'cancelled' ? 'cancelado' : 'en curso';
  const pct = Math.max(0, Math.min(100, Number(job.progress || 0)));
  return `<div class="review-job" role="status" aria-live="polite"><div><strong>${esc(status)}</strong><span>${esc(job.message || 'Trabajo de reseñas')}</span></div><progress max="100" value="${pct}" aria-label="Progreso del trabajo de reseñas"></progress>${job.error ? `<small class="hotel-review-error">${esc(job.error)}</small>` : ''}</div>`;
}

function hotelSourceLabel(source) {
  return ({ google: 'Google', google_maps: 'Google Maps', google_hotels: 'Google Hotels', booking: 'Booking', booking_graphql: 'Booking', manual: 'Manual' })[source] || source;
}

function hotelReviewSourceHref(value) {
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase();
    if (url.protocol !== 'https:' || !(host === 'google.com' || host.endsWith('.google.com') || host === 'booking.com' || host.endsWith('.booking.com'))) return '';
    return url.href;
  } catch (_) { return ''; }
}

function reviewRunStatus(status) {
  return ({ queued: 'En cola', running: 'En curso', ok: 'OK', empty: 'Sin reseñas visibles', exhausted: 'Recorrido terminado · cobertura no certificada',
    partial: 'Parcial', blocked: 'Bloqueado', budget_exhausted: 'Límite de gasto', parse_error: 'Error de lectura', error: 'Error', cancelled: 'Cancelado' })[status] || status || 'Sin captura';
}

function reviewRunDiagnostics(run) {
  const coverage = run.coverage || {};
  const parts = [];
  if (coverage.pagesVisited != null) parts.push(`${nEs(coverage.pagesVisited)} páginas`);
  if (coverage.scrollIterations != null) parts.push(`${nEs(coverage.scrollIterations)} desplazamientos`);
  if (coverage.observedReviewCount != null && coverage.publishedReviewCount != null) {
    parts.push(`${nEs(coverage.observedReviewCount)} observadas / ${nEs(coverage.publishedReviewCount)} publicadas`);
  }
  if (coverage.completedContextCount != null) parts.push(`${nEs(coverage.completedContextCount)}/${nEs(coverage.configuredContextCount)} vistas`);
  if (coverage.interfaceLanguage) parts.push(`UI ${coverage.interfaceLanguage}`);
  if (coverage.historicalCompletenessVerified === false) parts.push('historial no certificado');
  if (coverage.durationSeconds != null) parts.push(`${nEs(coverage.durationSeconds, 1)} s`);
  const metrics = parts.join(' · ') || 'Sin detalle estructurado';
  const json = JSON.stringify(coverage, null, 2);
  const sourceUrl = hotelReviewSourceHref(run.sourceUrl);
  const sourceLink = sourceUrl ? `<a href="${esc(sourceUrl)}" target="_blank" rel="noopener noreferrer">Abrir fuente pública</a>` : '';
  const message = run.error || coverage.message || '';
  return `<details class="review-run-diagnostics"><summary>${esc(metrics)}</summary>${sourceLink ? `<p>${sourceLink}</p>` : ''}${message ? `<p>${esc(message)}</p>` : ''}<pre>${esc(json)}</pre></details>`;
}

function reviewSourceMap(item, key = 'source') {
  const result = new Map();
  (item[key] || []).forEach((entry) => { if (!result.has(entry.source)) result.set(entry.source, entry); });
  return result;
}

async function renderHotelReputation() {
  const host = mount('reputation');
  if (State.reputation.hotelKey) {
    host.innerHTML = `<div class="page"><div class="sk" style="height:90px;margin-bottom:12px"></div><div class="sk" style="height:340px"></div></div>`;
    try {
      const result = await api(reputationKeyPath(State.reputation.hotelKey, 'profile'));
      State.reputation.profile = result.profile;
      renderHotelReputationProfile(host, result.profile);
      if (State.reputation.tab === 'reviews') {
        await loadHotelReviewsPage(State.reputation.pendingEvidenceId);
        State.reputation.pendingEvidenceId = null;
      }
    } catch (error) {
      host.innerHTML = `<div class="page">${pageHead('Ficha hotelera', 'Inventario y reseñas', '')}<div class="inline-error">No se pudo abrir la ficha: ${esc(error.message)} <button type="button" class="btn btn--sm" data-review-back>Volver al inventario</button></div></div>`;
    }
    return;
  }
  host.innerHTML = `<div class="page"><div class="sk" style="height:90px;margin-bottom:12px"></div><div class="sk" style="height:480px"></div></div>`;
  try {
    const result = await api('/api/hotel-reviews/catalog?limit=200');
    State.reputation.catalog = result.items || [];
    const availableKeys = new Set(State.reputation.catalog.map((item) => item.hotel_key));
    for (const key of State.reputation.selectedKeys) if (!availableKeys.has(key)) State.reputation.selectedKeys.delete(key);
    renderHotelReputationCatalog(host, result.total || 0);
  } catch (error) {
    host.innerHTML = `<div class="page">${pageHead('Inventario y reputación', 'Fuentes públicas, reseñas y calidad hotelera', '')}<div class="inline-error">No se pudo cargar el inventario: ${esc(error.message)}</div></div>`;
  }
}

function reviewCaptureControls(scope) {
  const settings = State.reputation.captureSettings;
  return `<div class="review-capture-controls" data-review-capture-controls="${scope}">
    <label><input type="checkbox" data-review-source="google_maps" ${settings.google_maps ? 'checked' : ''}> Google Maps</label>
    <label><input type="checkbox" data-review-source="google_hotels" ${settings.google_hotels ? 'checked' : ''}> Google Hotels</label>
    <label><input type="checkbox" data-review-source="booking" ${settings.booking ? 'checked' : ''}> Booking</label>
    <label>Máx. reseñas <input type="number" class="input" data-review-max value="${esc(settings.maxReviews)}" min="1" max="10000" step="1" ${settings.unboundedReviews ? 'disabled' : ''}></label>
    <label><input type="checkbox" data-review-unbounded ${settings.unboundedReviews ? 'checked' : ''}> Hasta agotar recorrido</label>
    <label>Tope Jev USD <input type="number" class="input" data-review-budget value="${esc(settings.budgetUsd)}" min="0.001" step="any" placeholder="Por lote"></label>
    <label>Estimación USD/decisión <input type="number" class="input" data-review-unit-cost value="${esc(settings.unitCostUsd)}" min="0.000001" step="any" placeholder="Configurar precio"></label>
    <label>Decisiones máx. por hotel <input type="number" class="input" data-review-decisions value="${esc(settings.maxDecisions)}" min="1" max="120" step="1"></label>
  </div><small>«Hasta agotar» quita el tope numérico. Google Maps conserva un límite técnico de 400 desplazamientos y Booking de 500 páginas; si se alcanza, la captura queda parcial.</small><p class="review-capture-readiness" data-review-capture-readiness="${scope}" role="status"></p>`;
}

function reviewSearchText(value) {
  return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
}

function filterHotelReviewCatalog() {
  const query = reviewSearchText(State.reputation.query.trim());
  let visible = 0;
  $$('[data-reputation-row]').forEach((row) => {
    const match = !query || row.dataset.reviewRowQuery.includes(query);
    row.hidden = !match;
    if (match) visible++;
  });
  const count = $('#reviewCatalogCount');
  if (count) count.textContent = `${visible} de ${State.reputation.catalog.length} hoteles`;
  const selectAll = $('#reviewSelectAll');
  if (selectAll) {
    const shown = $$('[data-reputation-row]:not([hidden]) [data-review-select]');
    const checked = shown.filter((input) => input.checked).length;
    selectAll.checked = shown.length > 0 && checked === shown.length;
    selectAll.indeterminate = checked > 0 && checked < shown.length;
    selectAll.disabled = shown.length === 0;
  }
}

function reviewCaptureAssessment(scope, hotelKeys) {
  const settings = State.reputation.captureSettings;
  const sources = ['google_maps', 'google_hotels', 'booking'].filter((source) => settings[source]);
  const maxReviews = Number(settings.maxReviews);
  const maxDecisions = Number(settings.maxDecisions);
  const budget = Number(settings.budgetUsd);
  const unitCost = Number(settings.unitCostUsd);
  if (!hotelKeys.length) return {valid: false, message: 'Selecciona al menos un hotel.'};
  if (!sources.length) return {valid: false, message: 'Selecciona al menos una fuente.'};
  if (!settings.unboundedReviews && (!Number.isInteger(maxReviews) || maxReviews < 1 || maxReviews > 10000)) return {valid: false, message: 'El máximo de reseñas debe estar entre 1 y 10.000.'};
  if (!Number.isInteger(maxDecisions) || maxDecisions < 1 || maxDecisions > 120) return {valid: false, message: 'Las decisiones por hotel deben estar entre 1 y 120.'};
  const hotelMap = new Map((scope === 'profile' ? [State.reputation.profile] : State.reputation.catalog)
    .filter(Boolean).map((item) => [item.hotel?.hotel_key || item.hotel_key, item]));
  const confirmedCounts = Object.fromEntries(sources.map((source) => [source, hotelKeys.reduce((total, key) => {
    const links = hotelMap.get(key)?.links || [];
    return total + Number(links.some((link) => link.source === source && link.url && link.verified));
  }, 0)]));
  const googleSources = sources.filter((source) => source.startsWith('google_'));
  const confirmedGoogle = googleSources.reduce((total, source) => total + confirmedCounts[source], 0);
  const confirmedBooking = confirmedCounts.booking || 0;
  const omitted = hotelKeys.length * sources.length - confirmedGoogle - confirmedBooking;
  if (!confirmedGoogle && !confirmedBooking) return {valid: false, message: 'No hay fuentes confirmadas para esta selección. Revisa los vínculos en la ficha.'};
  if (confirmedGoogle) {
    if (!Number.isFinite(budget) || budget <= 0 || !Number.isFinite(unitCost) || unitCost <= 0) {
      return {valid: false, message: 'Indica un tope Jev y un coste estimado por decisión, ambos mayores que cero.'};
    }
    const estimatedMaximum = confirmedGoogle * maxDecisions * unitCost;
    if (budget + 1e-9 < estimatedMaximum) {
      return {valid: false, message: `Tope insuficiente: hasta US$ ${nEs(estimatedMaximum, 4)} para ${confirmedGoogle} capturas Google confirmadas.`};
    }
    return {valid: true, message: `${confirmedGoogle} Google · ${confirmedBooking} Booking · ${omitted} fuentes omitidas · máximo Jev estimado US$ ${nEs(estimatedMaximum, 4)}. El recorrido puede ser parcial.`};
  }
  return {valid: true, message: `${confirmedBooking} Booking confirmado${confirmedBooking === 1 ? '' : 's'} · ${omitted} fuentes omitidas · sin gasto Jev.`};
}

function refreshHotelReviewCaptureControls() {
  const scope = State.reputation.hotelKey ? 'profile' : 'catalog';
  const allKeys = (State.reputation.catalog || []).map((item) => item.hotel_key);
  const selectedKeys = [...State.reputation.selectedKeys];
  const keys = scope === 'profile' ? [State.reputation.hotelKey] : allKeys;
  const allAssessment = reviewCaptureAssessment(scope, keys);
  const selectedAssessment = scope === 'catalog' ? reviewCaptureAssessment(scope, selectedKeys) : allAssessment;
  const allButton = $('[data-review-capture-all]');
  const selectedButton = $('[data-review-capture-selected]');
  const profileButton = $('[data-review-capture-profile]');
  if (allButton) allButton.disabled = !allAssessment.valid;
  if (selectedButton) selectedButton.disabled = !selectedAssessment.valid;
  if (profileButton) profileButton.disabled = !allAssessment.valid;
  const readiness = $(`[data-review-capture-readiness="${scope}"]`);
  if (readiness) readiness.textContent = scope === 'catalog' && selectedKeys.length ? selectedAssessment.message : allAssessment.message;
}

function renderHotelReputationCatalog(host, total) {
  const rows = State.reputation.catalog || [];
  const selectedCount = State.reputation.selectedKeys.size;
  const tableRows = rows.map((row) => {
    const counts = reviewSourceMap(row, 'reviewSources');
    const runs = reviewSourceMap(row);
    const maps = row.links?.find((link) => link.source === 'google_maps');
    const booking = row.links?.find((link) => link.source === 'booking');
    return `<tr data-reputation-row data-review-row-query="${esc(reviewSearchText(`${row.hotel_name} ${row.city || ''} ${row.address || ''}`))}">
      <td><input type="checkbox" data-review-select="${esc(row.hotel_key)}" aria-label="Seleccionar ${esc(row.hotel_name)}" ${State.reputation.selectedKeys.has(row.hotel_key) ? 'checked' : ''}></td>
      <td><button type="button" class="review-hotel-link" data-review-open="${esc(row.hotel_key)}"><strong>${esc(row.hotel_name)}</strong><small>${esc(row.city || row.address || 'Zona no informada')}</small></button></td>
      <td class="num">${nEs(counts.get('google')?.captured || 0)}<small>Google</small></td>
      <td class="num">${nEs(counts.get('booking')?.captured || 0)}<small>Booking ${row.stars ? `· ${nEs(row.stars, 0)}★` : ''}</small></td>
      <td>${maps?.verified ? 'Coincidencia confirmada' : maps ? 'Maps · por revisar' : 'Falta Maps'}</td>
      <td>${runs.get('google_maps') ? reviewRunStatus(runs.get('google_maps').status) : 'Sin captura'}</td>
      <td>${runs.get('booking') ? reviewRunStatus(runs.get('booking').status) : (booking ? 'Disponible' : 'Falta URL')}</td>
      <td><button type="button" class="btn btn--sm" data-review-open="${esc(row.hotel_key)}">Abrir ficha</button></td>
    </tr>`;
  }).join('');
  const jobStatus = reviewJobPanelHTML();
  host.innerHTML = `<div class="page review-page">
    ${pageHead('Inventario y reputación', 'Ficha de hotel, cobertura de fuentes y análisis de reseñas', `<a class="btn btn--quiet" href="/api/hotel-reviews/catalog?limit=200">${nEs(total)} hoteles</a>`)}
    ${jobStatus}
    <section class="review-workbench" aria-label="Acciones de captura y comparación">
      <div class="review-workbench__top"><label class="review-search"><span>Buscar hotel</span><input type="search" class="input" id="reviewCatalogSearch" value="${esc(State.reputation.query)}" placeholder="Nombre, dirección o ciudad"></label>
      <div class="review-workbench__actions"><label><input type="checkbox" id="reviewSelectAll"> Seleccionar visibles</label><button type="button" class="btn" data-review-compare ${selectedCount < 2 ? 'disabled' : ''}>Comparar selección (${selectedCount})</button><button type="button" class="btn btn--primary" data-review-capture-selected disabled>Capturar seleccionados</button><button type="button" class="btn" data-review-capture-all disabled>Capturar todo el inventario</button></div></div>
      ${reviewCaptureControls('catalog')}
      <small class="review-budget-help">La captura de Google usa Jev con OpenRouter. El tope de gasto y el coste por decisión limitan la navegación asistida; el coste informado por el proveedor prevalece cuando está disponible. Después, la extracción sigue el máximo de reseñas o el límite técnico de la fuente.</small>
      <div class="review-compare-outlet" id="reviewCompareOutlet" aria-live="polite"></div>
    </section>
    <div class="table-scroll review-table-scroll"><table class="t review-catalog-table"><caption class="sr-only">Inventario hotelero con cobertura de reseñas por fuente</caption>
      <thead><tr><th scope="col"><span class="sr-only">Seleccionar</span></th><th scope="col">Hotel</th><th scope="col" class="r">Capturadas · Google</th><th scope="col" class="r">Capturadas · Booking</th><th scope="col">Google Maps</th><th scope="col">Último Maps</th><th scope="col">Último Booking</th><th scope="col">Ficha</th></tr></thead>
      <tbody>${tableRows || '<tr><td colspan="8">No hay hoteles en el inventario.</td></tr>'}</tbody>
    </table></div>
    <div class="review-list-meta"><span id="reviewCatalogCount">${rows.length} de ${nEs(total)} hoteles</span><span>La ficha procede de Booking y de atributos públicos de Google, con fuente y fecha.</span></div>
  </div>`;
  filterHotelReviewCatalog();
  refreshHotelReviewCaptureControls();
}

function reviewFactsHTML(profile) {
  const hotel = profile.hotel || {};
  const facts = [
    ['Nombre', hotel.hotel_name, hotel.source || 'booking_graphql', hotel.updated_at],
    ['Estrellas', hotel.stars == null ? null : `${nEs(hotel.stars, 0)}★`, hotel.source || 'booking_graphql', hotel.updated_at],
    ['Tipo', hotel.accommodation_type, hotel.source || 'booking_graphql', hotel.updated_at],
    ['Ubicación', [hotel.display_location, hotel.city, hotel.country_code].filter(Boolean).join(' · '), hotel.source || 'booking_graphql', hotel.updated_at],
    ['Dirección', hotel.address, hotel.source || 'booking_graphql', hotel.updated_at],
    ['Descripción', hotel.description, hotel.source || 'booking_graphql', hotel.updated_at],
    ['Distancia a playa', hotel.beach_distance, hotel.source || 'booking_graphql', hotel.updated_at],
  ];
  const extras = Object.entries(profile.attributes || {}).filter(([name]) => !name.endsWith('_aggregate'))
    .flatMap(([name, observations]) => observations.map((item) => [name, item.value, item.source, item.observedAt, name, item.id, item.selected, observations.length]));
  const allFacts = [...facts, ...extras];
  return `<div class="review-facts-scroll"><table class="review-facts-table"><caption class="sr-only">Datos objetivos del hotel y su procedencia</caption><thead><tr><th>Dato</th><th>Valor</th><th>Fuente</th><th>Observado</th></tr></thead><tbody>${allFacts.map(([label, value, source, observed, attribute, observationId, selected, alternatives]) => {
    const shownValue = value == null || value === '' ? '—' : Array.isArray(value) ? value.join(', ') : typeof value === 'object' ? JSON.stringify(value) : value;
    const choice = alternatives > 1 && observationId ? selected ? '<small class="review-selected-fact">Valor principal</small>' : `<button type="button" class="link-button" data-review-select-attribute="${esc(attribute)}" data-review-observation-id="${Number(observationId)}">Usar como principal</button>` : '';
    return `<tr><th scope="row">${esc(label)}</th><td>${esc(shownValue)}${choice}</td><td>${esc(hotelSourceLabel(source))}</td><td>${esc(fmtStamp(observed))}</td></tr>`;
  }).join('')}</tbody></table></div>`;
}

function reviewReputationTable(profile) {
  const sources = profile.sources || [];
  if (!sources.length) return '<div class="empty">Aún no hay puntuaciones o reseñas capturadas.</div>';
  return `<div class="table-scroll"><table class="t review-reputation-table"><caption class="sr-only">Reputación publicada y estadísticas de las reseñas capturadas, separadas por plataforma</caption><thead><tr><th>Fuente</th><th class="r">Nota publicada</th><th class="r">Total publicado</th><th class="r">Capturadas</th><th class="r">Con texto</th><th class="r">Media de la muestra</th><th>Estado de cobertura</th></tr></thead><tbody>${sources.map((source) => {
    const run = source.latestRun || {};
    const scale = source.ratingScale || (source.source === 'google' ? 5 : 10);
    const rating = source.publishedRating == null ? '—' : `${nEs(source.publishedRating, 1)}/${scale}`;
    const status = run.status ? reviewRunStatus(run.status) : 'Pendiente de captura';
    return `<tr><th scope="row">${esc(hotelSourceLabel(source.source))}</th><td class="num">${rating}</td><td class="num">${source.publishedReviewCount == null ? '—' : nEs(source.publishedReviewCount)}</td><td class="num">${nEs(source.captured || 0)}</td><td class="num">${nEs(source.withText || 0)}</td><td class="num">${source.sampleAverage == null ? '—' : `${nEs(source.sampleAverage, 2)}/${scale}`}</td><td>${esc(status)}${run.startedAt ? `<small>${esc(fmtStamp(run.startedAt))}</small>` : ''}</td></tr>`;
  }).join('')}</tbody></table></div><small class="review-source-note">La nota publicada y la media de la muestra son métricas distintas. Google y Booking conservan sus escalas originales; “recorrido terminado” no certifica el historial completo.</small>`;
}

function renderRatingDistribution(profile) {
  const sources = profile.sources || [];
  return sources.map((source) => {
    const values = source.ratingDistribution || [];
    const max = Math.max(1, ...values.map((item) => Number(item.count)));
    const scale = source.ratingScale || (source.source === 'google' ? 5 : 10);
    const rows = values.map((item) => `<div class="review-rating-bar"><span>${nEs(item.rating, item.rating % 1 ? 1 : 0)} / ${scale}</span><div><i style="width:${Math.round(Number(item.count) / max * 100)}%"></i></div><strong>${nEs(item.count)}</strong></div>`).join('');
    return `<section class="review-distribution"><h3>${esc(hotelSourceLabel(source.source))} · puntuación de la muestra</h3>${rows || '<p>Sin puntuaciones capturadas.</p>'}</section>`;
  }).join('');
}

function renderReviewTrend(profile) {
  const sources = (profile.sources || []).filter((source) => (source.datedTrend || []).length >= 2);
  if (!sources.length) return '<p class="review-no-trend">Sin fechas absolutas suficientes para graficar evolución. Las etiquetas relativas no se convierten en fechas.</p>';
  return sources.map((source) => `<section class="review-trend"><h3>${esc(hotelSourceLabel(source.source))} · fechas exactas</h3><div class="review-trend-rows">${source.datedTrend.map((point) => `<div><time>${esc(point.month)}</time><span>${nEs(point.count)} reseñas</span><strong>${point.sampleAverage == null ? '—' : `${nEs(point.sampleAverage, 2)} / ${source.ratingScale || 5}`}</strong></div>`).join('')}</div></section>`).join('');
}

function analysisEvidenceItems(analysis, key) {
  return (analysis?.analysis?.[key] || []).map((item) => `<article class="review-analysis-item"><div><strong>${esc(item.theme)}</strong><span>${nEs(item.mentions || item.evidenceReviewIds?.length || 0)} reseñas de respaldo</span></div><p>${esc(item.observation)}</p><div class="review-evidence-links">${(item.evidenceReviewIds || []).map((id) => `<button type="button" class="link-button" data-review-evidence="${nEs(id)}">#${nEs(id)}</button>`).join('')}</div></article>`).join('');
}

function renderHotelReputationProfile(host, profile) {
  const hotel = profile.hotel || {};
  const tabs = [['profile', 'Ficha'], ['reviews', 'Reseñas'], ['analysis', 'Análisis'], ['notes', 'Notas'], ['captures', 'Capturas']];
  const tabsHtml = tabs.map(([key, label]) => `<button type="button" id="review-tab-${key}" role="tab" class="filter-btn ${State.reputation.tab === key ? 'is-active' : ''}" aria-controls="reviewProfileBody" aria-selected="${State.reputation.tab === key}" tabindex="${State.reputation.tab === key ? 0 : -1}" data-review-profile-tab="${key}">${label}</button>`).join('');
  host.innerHTML = `<div class="page review-page review-profile-page">
    <div class="review-profile-head"><div><button type="button" class="link-button" data-review-back>← Inventario</button><div class="card__kicker">FICHA DE HOTEL · ${esc(hotel.hotel_key)}</div><h1>${esc(hotel.hotel_name)}</h1><p>${esc([hotel.city, hotel.display_location, hotel.accommodation_type].filter(Boolean).join(' · ') || 'Ubicación no informada')}</p></div><div class="review-profile-head__actions"><a class="btn btn--quiet" href="${reputationKeyPath(hotel.hotel_key, 'export.tsv')}" download>Exportar TSV</a><button type="button" class="btn btn--primary" data-review-capture-profile disabled>Capturar fuentes</button></div></div>
    ${reviewJobPanelHTML()}
    ${reviewCaptureControls('profile')}
    <div class="review-profile-tabs" role="tablist" aria-label="Secciones de ficha hotelera">${tabsHtml}</div>
    <div id="reviewProfileBody" class="review-profile-body" role="tabpanel" aria-labelledby="review-tab-${State.reputation.tab}" tabindex="0">${renderHotelReputationTab(profile)}</div>
  </div>`;
  refreshHotelReviewCaptureControls();
}

function renderHotelReputationTab(profile) {
  const tab = State.reputation.tab;
  if (tab === 'profile') {
    const links = (profile.links || []).map((link) => {
      const safeUrl = hotelReviewSourceHref(link.url);
      return safeUrl ? `<a href="${esc(safeUrl)}" target="_blank" rel="noopener noreferrer">${esc(hotelSourceLabel(link.source))} ↗</a>` : '';
    }).filter(Boolean).join(' · ');
    return `<section class="review-section"><div class="review-section-head"><div><h2>Datos objetivos</h2><p>Se conserva cada observación junto a su fuente y fecha.</p></div><span>${Math.round(Number(profile.hotel.completeness || 0) * 100)}% de la ficha disponible</span></div>${reviewFactsHTML(profile)}<p class="review-external-links">${links || 'No hay enlaces asociados a las fuentes.'}</p><p class="review-aliases">Nombres asociados: ${(profile.aliases || []).map(esc).join(' · ') || '—'}</p></section>
      <section class="review-section"><div class="review-section-head"><div><h2>Reputación por fuente</h2><p>Nota publicada y muestra capturada, sin combinar escalas.</p></div></div>${reviewReputationTable(profile)}</section>`;
  }
  if (tab === 'reviews') {
    const filters = State.reputation.reviewFilters;
    const topics = [...new Set((profile.analysis?.analysis?.themes || []).map((item) => item.theme))];
    const ratingScale = filters.source === 'google' ? 5 : filters.source === 'booking' ? 10 : 0;
    return `<section class="review-section"><div class="review-section-head"><div><h2>Reseñas</h2><p id="reviewRowsCount" aria-live="polite">Cargando reseñas…</p></div><a href="${reputationKeyPath(profile.hotel.hotel_key, 'export.tsv')}" download>Exportar TSV</a></div>
      <div class="review-filters"><label>Fuente<select class="input" data-review-filter="source"><option value="">Todas</option><option value="google" ${filters.source === 'google' ? 'selected' : ''}>Google</option><option value="booking" ${filters.source === 'booking' ? 'selected' : ''}>Booking</option></select></label><label>Idioma<input class="input" data-review-filter="language" value="${esc(filters.language)}" maxlength="8" placeholder="EN"></label><label>Nota${ratingScale ? ` / ${ratingScale}` : ''}<select class="input" data-review-filter="rating" ${ratingScale ? '' : 'disabled'}><option value="">${ratingScale ? 'Todas' : 'Elige fuente'}</option>${Array.from({length:ratingScale}, (_, index) => index + 1).map((rating) => `<option value="${rating}" ${filters.rating === String(rating) ? 'selected' : ''}>${rating} / ${ratingScale}</option>`).join('')}</select></label><label>Tema<select class="input" data-review-filter="topic"><option value="">Todos</option>${topics.map((topic) => `<option value="${esc(topic)}" ${filters.topic === topic ? 'selected' : ''}>${esc(topic)}</option>`).join('')}</select></label><label>Fecha desde<input class="input" type="date" data-review-filter="dateFrom" value="${esc(filters.dateFrom)}"></label><label>Fecha hasta<input class="input" type="date" data-review-filter="dateTo" value="${esc(filters.dateTo)}"></label><label class="review-filter-search">Buscar texto<input class="input" type="search" data-review-filter="query" value="${esc(filters.query)}" placeholder="Frase de la reseña"></label></div>
      <div class="review-results" id="hotelReviewRows"></div><div class="review-pagination"><button type="button" class="btn btn--sm" data-review-page="prev">Anterior</button><span id="hotelReviewPager"></span><button type="button" class="btn btn--sm" data-review-page="next">Siguiente</button></div></section>`;
  }
  if (tab === 'analysis') {
    const analysis = profile.analysis;
    const analyzed = Number(analysis?.analysis?.analyzedReviews);
    const pending = Number(analysis?.analysis?.pendingReviews);
    const batchScope = analysis && Number.isFinite(analyzed) && Number.isFinite(pending)
      ? `<p class="review-analysis-batch">Lote analizado: ${nEs(analyzed)} reseñas · Pendientes: ${nEs(pending)}. Las conclusiones describen el lote procesado.</p>` : '';
    const summaryEvidence = (analysis?.analysis?.summaryEvidenceReviewIds || []).map((id) => `<button type="button" class="link-button" data-review-evidence="${nEs(id)}">Reseña #${nEs(id)}</button>`).join('');
    const batchSources = analysis?.analysis?.sourceComparison || [];
    const batchTable = batchSources.length ? `<div class="table-scroll"><table class="t review-batch-table"><caption>Alcance del último lote por fuente</caption><thead><tr><th>Fuente</th><th class="r">Capturadas</th><th class="r">Con texto</th><th class="r">Analizadas en lote</th></tr></thead><tbody>${batchSources.map((item) => `<tr><th scope="row">${esc(hotelSourceLabel(item.source))}</th><td class="num">${nEs(item.captured || 0)}</td><td class="num">${nEs(item.withText || 0)}</td><td class="num">${nEs(item.analyzedInBatch || 0)}</td></tr>`).join('')}</tbody></table></div>` : '';
    return `<section class="review-section"><div class="review-section-head"><div><h2>Análisis de calidad</h2><p>Conclusiones de IA enlazadas a las reseñas que las respaldan. El contenido de una reseña se trata como dato.</p></div><div class="review-analysis-run"><label>Tope USD <input id="reviewAnalysisBudget" class="input" type="number" min="0.001" max="10" step="any" placeholder="Máx. 10"></label><button type="button" class="btn btn--primary" data-review-analyze disabled>Analizar reseñas</button></div></div>
      ${reviewJobPanelHTML()}<div class="review-analysis-meta">${analysis ? `Modelo ${esc(analysis.model)} · ${esc(analysis.prompt_version)} · ${esc(fmtStamp(analysis.created_at))} · ${analysis.cost_usd == null ? 'Coste no informado por proveedor' : `US$ ${nEs(analysis.cost_usd, 4)}`}` : 'Aún no hay un análisis guardado.'}</div>
      ${batchScope}${batchTable}${analysis ? `<div class="review-analysis-summary"><h3>Lectura del lote</h3><p>${esc(analysis.analysis?.summary || '—')}</p>${summaryEvidence ? `<div class="review-evidence-links" aria-label="Reseñas que respaldan el resumen">${summaryEvidence}</div>` : ''}</div><div class="review-analysis-grid"><section><h3>Fortalezas</h3>${analysisEvidenceItems(analysis, 'strengths') || '<p>Sin conclusiones respaldadas.</p>'}</section><section><h3>Problemas recurrentes</h3>${analysisEvidenceItems(analysis, 'issues') || '<p>Sin conclusiones respaldadas.</p>'}</section><section><h3>Temas</h3>${analysisEvidenceItems(analysis, 'themes') || '<p>Sin temas clasificados.</p>'}</section></div>${analysis.analysis?.limitations?.length ? `<p class="review-source-note">${analysis.analysis.limitations.map(esc).join(' · ')}</p>` : ''}` : ''}
      <h3>Distribución de puntuaciones</h3><div class="review-chart-grid">${renderRatingDistribution(profile)}</div><h3>Evolución</h3>${renderReviewTrend(profile)}<h3>Comparación por fuente</h3>${reviewReputationTable(profile)}
      <p class="review-source-note">La evolución se dibuja solo con fechas exactas. Las medias de muestra no representan la nota completa de la plataforma.</p></section>`;
  }
  if (tab === 'notes') {
    const notes = profile.notes || [];
    return `<section class="review-section"><div class="review-section-head"><div><h2>Notas del equipo</h2><p>Las anotaciones se guardan por usuario y pueden vincularse a una reseña.</p></div></div><form data-review-note-form class="review-note-form"><label>Nota<textarea class="input" name="body" maxlength="4000" rows="3" required placeholder="Acción, incidencia o seguimiento"></textarea></label><label>Vincular a reseña (opcional)<input class="input" name="reviewId" type="number" min="1" value="${State.reputation.noteReviewId || ''}" placeholder="ID interno"></label><button class="btn btn--primary" type="submit">Guardar nota</button></form><div class="review-notes-list">${notes.length ? notes.map((note) => `<article><div><strong>${esc(note.body)}</strong><small>${esc(note.ownerKey)} · ${esc(fmtStamp(note.createdAt))}${note.reviewId ? ` · reseña #${nEs(note.reviewId)}` : ''}</small></div><button type="button" class="link-button" data-review-delete-note="${note.id}" aria-label="Eliminar nota">Eliminar</button></article>`).join('') : '<p>No hay notas.</p>'}</div></section>`;
  }
  const links = new Map((profile.links || []).map((link) => [link.source, link]));
  const linkSources = ['google_maps', 'google_hotels', 'booking'];
  return `<section class="review-section"><div class="review-section-head"><div><h2>Capturas y fuentes</h2><p>Asocia los enlaces públicos antes de iniciar la extracción. Las coincidencias nuevas requieren revisión.</p></div></div>
    <div class="review-source-links">${linkSources.map((source) => {const link=links.get(source) || {};return `<form class="review-link-form" data-review-link-form data-source="${source}"><label>${esc(hotelSourceLabel(source))}<input class="input" name="url" type="url" value="${esc(link.url || '')}" placeholder="URL pública del hotel" required></label><label>Nombre observado<input class="input" name="externalName" value="${esc(link.externalName || '')}" maxlength="200"></label><label class="review-link-verified"><input name="verified" type="checkbox" ${link.verified ? 'checked' : ''}> Coincidencia comprobada</label><button class="btn btn--sm" type="submit">Guardar vínculo</button></form>`;}).join('')}</div>
    <div class="table-scroll"><table class="t"><caption class="sr-only">Historial de capturas de reseñas y cobertura</caption><thead><tr><th>Fuente</th><th>Estado</th><th class="r">Vistas</th><th class="r">Nuevas</th><th class="r">Actualizadas</th><th>Presupuesto / coste</th><th>Inicio</th><th>Fin</th><th>Cobertura y procedencia</th></tr></thead><tbody>${(profile.runs || []).map((run) => {const cost=run.coverage?.estimatedCostUsd ?? run.estimatedSpendUsd;return `<tr><th scope="row">${esc(hotelSourceLabel(run.source))}</th><td>${esc(reviewRunStatus(run.status))}</td><td class="num">${nEs(run.rowsSeen)}</td><td class="num">${nEs(run.rowsInserted)}</td><td class="num">${nEs(run.rowsUpdated)}</td><td>${run.budgetUsd == null ? '—' : `Límite US$ ${nEs(run.budgetUsd, 4)}`}<small>${cost == null ? 'Coste no informado' : `Estimado US$ ${nEs(cost, 4)}`}</small></td><td>${esc(fmtStamp(run.startedAt))}</td><td>${esc(fmtStamp(run.completedAt))}</td><td>${reviewRunDiagnostics(run)}</td></tr>`;}).join('') || '<tr><td colspan="9">No hay capturas.</td></tr>'}</tbody></table></div></section>`;
}

async function loadHotelReviewsPage(reviewId = null) {
  const host = $('#hotelReviewRows');
  if (!host || !State.reputation.hotelKey) return;
  const requestId = ++State.reputation.reviewRequestId;
  const filters = State.reputation.reviewFilters;
  const params = new URLSearchParams({limit: '50', offset: String(State.reputation.reviewPage * 50)});
  if (filters.source) params.set('source', filters.source);
  if (filters.language) params.set('language', filters.language);
  if (filters.rating) params.set('rating', filters.rating);
  if (filters.topic) params.set('topic', filters.topic);
  if (filters.dateFrom) params.set('dateFrom', filters.dateFrom);
  if (filters.dateTo) params.set('dateTo', filters.dateTo);
  if (filters.query) params.set('q', filters.query);
  if (reviewId) params.set('reviewId', String(reviewId));
  host.innerHTML = '<div class="empty">Cargando reseñas…</div>';
  try {
    const page = await api(`${reputationKeyPath(State.reputation.hotelKey, 'reviews')}?${params.toString()}`);
    if (requestId !== State.reputation.reviewRequestId || !host.isConnected) return;
    State.reputation.reviews = page;
    const count = $('#reviewRowsCount'); if (count) count.textContent = `${nEs(page.total)} reseñas · página ${State.reputation.reviewPage + 1}`;
    const pager = $('#hotelReviewPager'); if (pager) pager.textContent = `${nEs(State.reputation.reviewPage * 50 + (page.items || []).length)} / ${nEs(page.total)}`;
    const prev = $('[data-review-page="prev"]'); const next = $('[data-review-page="next"]');
    if (prev) prev.disabled = State.reputation.reviewPage <= 0;
    if (next) next.disabled = (State.reputation.reviewPage + 1) * 50 >= page.total;
      host.innerHTML = page.items?.length ? `<div class="table-scroll"><table class="t review-rows-table"><caption class="sr-only">Reseñas hoteleras con fuente, nota, idioma y textos original y español</caption><thead><tr><th>Fuente</th><th>Nota</th><th>Fecha</th><th>Idioma</th><th>Reseña y traducción</th><th></th></tr></thead><tbody>${page.items.map((item) => {const sourceUrl=hotelReviewSourceHref(item.sourceUrl);return `<tr data-review-row-id="${item.id}"><th scope="row">${sourceUrl ? `<a href="${esc(sourceUrl)}" target="_blank" rel="noopener noreferrer">${esc(hotelSourceLabel(item.source))} ↗</a>` : esc(hotelSourceLabel(item.source))}<small>${esc(item.author || 'Anónimo')}</small></th><td class="num">${item.rating == null ? '—' : `${nEs(item.rating, 1)}/${nEs(item.ratingScale, 0)}`}</td><td>${esc(item.publishedAt || item.relativePublishedAt || '—')}<small>${esc(item.datePrecision)}</small></td><td>${esc(item.languageOriginal || 'UND')}<small>${esc(item.translationMethod || '')}</small></td><td class="review-text-cell">${item.title ? `<strong>${esc(item.title)}</strong>` : ''}${item.positiveText ? `<p><b>Positivo</b> ${esc(item.positiveText)}</p>` : ''}${item.negativeText ? `<p><b>Negativo</b> ${esc(item.negativeText)}</p>` : ''}${item.reviewEs ? `<p><b>Español</b> ${esc(item.reviewEs)}</p>` : ''}${item.reviewOriginal ? `<details><summary>Ver original</summary><p>${esc(item.reviewOriginal)}</p></details>` : ''}<small>${esc(item.topics || '')}${item.qualityFlags?.length ? ` · Calidad: ${esc(item.qualityFlags.join(', '))}` : ''}</small></td><td><div class="review-row-actions"><button type="button" class="link-button" data-review-note-for="${item.id}">Anotar</button>${item.versionCount > 1 ? `<button type="button" class="link-button" data-review-history="${item.id}">Historial · ${nEs(item.versionCount)}</button>` : ''}</div><div class="review-history-outlet" data-review-history-outlet hidden></div></td></tr>`;}).join('')}</tbody></table></div>` : '<div class="empty">No hay reseñas que coincidan con los filtros.</div>';
  } catch (error) { if (requestId === State.reputation.reviewRequestId && host.isConnected) host.innerHTML = `<div class="inline-error">No se pudieron cargar las reseñas: ${esc(error.message)}</div>`; }
}

function showHotelReputationTab(tab) {
  const profile = State.reputation.profile;
  if (!profile) return void renderHotelReputation();
  State.reputation.tab = tab;
  renderHotelReputationProfile(mount('reputation'), profile);
  if (tab === 'reviews') void loadHotelReviewsPage(State.reputation.pendingEvidenceId).then(() => { State.reputation.pendingEvidenceId = null; });
  $(`[data-review-profile-tab="${tab}"]`)?.focus();
}

function openHotelReviewProfile(hotelKey, tab = 'profile') {
  State.reputation.hotelKey = hotelKey;
  State.reputation.tab = tab;
  State.reputation.profile = null;
  State.reputation.reviews = null;
  setView('reputation');
  window.scrollTo(0, 0);
}

async function launchHotelReviewCapture(hotelKeys, scope) {
  const root = $(`[data-review-capture-controls="${scope}"]`);
  if (!root) return;
  const assessment = reviewCaptureAssessment(scope, hotelKeys);
  if (!assessment.valid) { setStatus(assessment.message, 'error'); return; }
  const settings = State.reputation.captureSettings;
  const sources = ['google_maps', 'google_hotels', 'booking'].filter((source) => settings[source]);
  const hasGoogle = sources.some((source) => source.startsWith('google_'));
  const body = {
    hotelKeys, sources,
    maxReviews: settings.unboundedReviews ? 0 : Number(settings.maxReviews),
    maxJevDecisions: Number(settings.maxDecisions),
  };
  if (hasGoogle) {
    body.budgetUsd = Number(settings.budgetUsd);
    body.estimatedDecisionCostUsd = Number(settings.unitCostUsd);
  } else {
    body.budgetUsd = 0;
    body.estimatedDecisionCostUsd = 0;
  }
  try {
    const result = await api('/api/hotel-reviews/captures', {method: 'POST', body: JSON.stringify(body)});
    State.reputation.activeJobId = result.job.id;
    State.reputation.activeJobKind = 'capture';
    State.reputation.job = result.job;
    State.reputation.profile = null;
    setStatus(`Captura en cola: ${result.queued} hotel/fuente${result.skipped?.length ? ` · ${result.skipped.length} omitidos por falta de vínculo` : ''}. Máximo estimado US$ ${nEs(result.estimatedMaximumUsd, 4)}.`, 'success');
    await renderHotelReputation();
    void pollHotelReviewJob(result.job.id);
  } catch (error) { setStatus(error.message, 'error'); }
}

async function pollHotelReviewJob(jobId) {
  if (!jobId || State.reputation.activeJobId !== jobId) return;
  try {
    const result = await api(`/api/jobs/${encodeURIComponent(jobId)}`);
    State.reputation.job = result.job;
    if (State.view === 'reputation') {
      const old = $('.review-job');
      if (old) old.outerHTML = reviewJobPanelHTML();
    }
    if (['queued', 'running'].includes(result.job.status)) {
      setTimeout(() => void pollHotelReviewJob(jobId), 1800);
    } else {
      State.reputation.activeJobId = null;
      if (State.view === 'reputation') void renderHotelReputation();
      if (result.job.status === 'completed') setStatus('Trabajo de reseñas completado. Revisa los estados parciales y la cobertura de cada fuente.', 'success');
      else setStatus(result.job.error || 'El trabajo de reseñas terminó con incidencias.', 'error');
    }
  } catch (_) {
    if (State.reputation.activeJobId === jobId) setTimeout(() => void pollHotelReviewJob(jobId), 3000);
  }
}

async function runHotelReviewComparison() {
  const keys = [...State.reputation.selectedKeys].slice(0, 8);
  if (keys.length < 2) return;
  const outlet = $('#reviewCompareOutlet');
  if (outlet) outlet.innerHTML = '<span>Cargando comparación…</span>';
  try {
    const profiles = await Promise.all(keys.map(async (key) => (await api(reputationKeyPath(key, 'profile'))).profile));
    State.reputation.comparison = profiles;
    const sources = ['google', 'booking'];
    const rows = profiles.map((profile) => ({profile, bySource: new Map((profile.sources || []).map((entry) => [entry.source, entry]))}));
    if (outlet) outlet.innerHTML = `<div class="review-compare-table-wrap"><table><caption class="sr-only">Comparación por plataforma con puntuación en escala original y tamaños de muestra</caption><thead><tr><th>Hotel</th>${sources.map((source) => `<th>${hotelSourceLabel(source)} · publicada / muestra</th><th>${hotelSourceLabel(source)} · N</th>`).join('')}</tr></thead><tbody>${rows.map(({profile,bySource}) => `<tr><th>${esc(profile.hotel.hotel_name)}</th>${sources.map((source) => {const item=bySource.get(source); const scale=item?.ratingScale || (source==='google'?5:10); return `<td>${item?.publishedRating == null ? '—' : `${nEs(item.publishedRating,1)}/${scale}`} · ${item?.sampleAverage == null ? '—' : `${nEs(item.sampleAverage,2)}/${scale}`}</td><td>${nEs(item?.captured || 0)} capturadas${item?.latestRun ? ` · ${esc(reviewRunStatus(item.latestRun.status))}` : ''}</td>`;}).join('')}</tr>`).join('')}</tbody></table></div><small>Comparación sin filtros: incluye todas las reseñas capturadas de cada hotel y fuente. La cobertura puede diferir.</small>`;
  } catch (error) { if (outlet) outlet.innerHTML = `<div class="inline-error">No se pudo comparar: ${esc(error.message)}</div>`; }
}

async function saveHotelReviewLink(form) {
  const source = form.dataset.source;
  const data = new FormData(form);
  try {
    await api(reputationKeyPath(State.reputation.hotelKey, 'links'), {method: 'PUT', body: JSON.stringify({
      source, url: data.get('url'), externalName: data.get('externalName'), verified: data.get('verified') === 'on',
    })});
    setStatus(`Vínculo de ${hotelSourceLabel(source)} guardado.`, 'success');
    void renderHotelReputation();
  } catch (error) { setStatus(error.message, 'error'); }
}

function wireHotelReputationEvents() {
  document.addEventListener('keydown', (event) => {
    const current = event.target instanceof Element ? event.target.closest('[data-review-profile-tab]') : null;
    if (!current || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    const tabs = $$('[data-review-profile-tab]');
    const index = tabs.indexOf(current);
    const nextIndex = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
    const key = tabs[nextIndex]?.dataset.reviewProfileTab;
    if (!key) return;
    event.preventDefault();
    showHotelReputationTab(key);
  });
  document.addEventListener('input', (event) => {
    const target = event.target;
    if (target?.id === 'reviewCatalogSearch') {
      State.reputation.query = target.value.slice(0, 120);
      filterHotelReviewCatalog();
      return;
    }
    if (target?.matches('[data-review-capture-controls] input')) {
      const settings = State.reputation.captureSettings;
      if (target.hasAttribute('data-review-max')) settings.maxReviews = target.value;
      else if (target.hasAttribute('data-review-unbounded')) {
        settings.unboundedReviews = target.checked;
        const limit = target.closest('[data-review-capture-controls]')?.querySelector('[data-review-max]');
        if (limit) limit.disabled = target.checked;
      }
      else if (target.hasAttribute('data-review-budget')) settings.budgetUsd = target.value;
      else if (target.hasAttribute('data-review-unit-cost')) settings.unitCostUsd = target.value;
      else if (target.hasAttribute('data-review-decisions')) settings.maxDecisions = target.value;
      refreshHotelReviewCaptureControls();
      return;
    }
    if (target?.id === 'reviewAnalysisBudget') {
      const value = Number(target.value);
      const button = $('[data-review-analyze]');
      if (button) button.disabled = !target.value || !Number.isFinite(value) || value < 0.001 || value > 10;
      return;
    }
    const filter = target?.dataset?.reviewFilter;
    if (filter === 'query' || filter === 'language' || filter === 'dateFrom' || filter === 'dateTo') {
      const maxLength = filter === 'query' ? 120 : filter === 'language' ? 8 : 10;
      State.reputation.reviewFilters[filter] = target.value.slice(0, maxLength);
      State.reputation.reviewPage = 0;
      clearTimeout(State.reputation.reviewFilterTimer);
      State.reputation.reviewFilterTimer = setTimeout(() => void loadHotelReviewsPage(), 280);
    }
  });
  document.addEventListener('change', (event) => {
    const target = event.target;
    if (target?.matches('[data-review-select]')) {
      const key = target.dataset.reviewSelect;
      if (target.checked) State.reputation.selectedKeys.add(key); else State.reputation.selectedKeys.delete(key);
      const button = $('[data-review-compare]'); if (button) button.disabled = State.reputation.selectedKeys.size < 2;
      const label = $('[data-review-compare]'); if (label) label.textContent = `Comparar selección (${State.reputation.selectedKeys.size})`;
      filterHotelReviewCatalog();
      refreshHotelReviewCaptureControls();
      return;
    }
    if (target?.id === 'reviewSelectAll') {
      $$('[data-reputation-row]:not([hidden]) [data-review-select]').forEach((input) => {input.checked = target.checked; if (target.checked) State.reputation.selectedKeys.add(input.dataset.reviewSelect); else State.reputation.selectedKeys.delete(input.dataset.reviewSelect);});
      const compare = $('[data-review-compare]'); if (compare) { compare.disabled = State.reputation.selectedKeys.size < 2; compare.textContent = `Comparar selección (${State.reputation.selectedKeys.size})`; }
      filterHotelReviewCatalog();
      refreshHotelReviewCaptureControls();
      return;
    }
    if (target?.matches('[data-review-source]')) {
      State.reputation.captureSettings[target.dataset.reviewSource] = target.checked;
      refreshHotelReviewCaptureControls();
      return;
    }
    const filter = target?.dataset?.reviewFilter;
    if (filter === 'source') {
      State.reputation.reviewFilters.source = target.value;
      State.reputation.reviewFilters.rating = '';
      State.reputation.reviewPage = 0;
      showHotelReputationTab('reviews');
      $('[data-review-filter="source"]')?.focus();
    } else if (filter && !['query', 'language', 'dateFrom', 'dateTo'].includes(filter)) {
      State.reputation.reviewFilters[filter] = target.value;
      State.reputation.reviewPage = 0;
      void loadHotelReviewsPage();
    }
  });
  document.addEventListener('submit', (event) => {
    const noteForm = event.target.closest('[data-review-note-form]');
    if (noteForm) {
      event.preventDefault();
      const data = new FormData(noteForm);
      const body = {body: data.get('body'), reviewId: data.get('reviewId') ? Number(data.get('reviewId')) : null};
      void api(reputationKeyPath(State.reputation.hotelKey, 'notes'), {method:'POST',body:JSON.stringify(body)})
        .then(() => {State.reputation.tab='notes'; setStatus('Nota guardada.', 'success'); return renderHotelReputation();})
        .catch((error) => setStatus(error.message,'error'));
      return;
    }
    const linkForm = event.target.closest('[data-review-link-form]');
    if (linkForm) { event.preventDefault(); void saveHotelReviewLink(linkForm); }
  });
  document.addEventListener('click', (event) => {
    const target = event.target instanceof Element ? event.target : null;
    if (!target) return;
    const open = target.closest('[data-review-open]'); if (open) {openHotelReviewProfile(open.dataset.reviewOpen); return;}
    if (target.closest('[data-review-back]')) {State.reputation.hotelKey=null; State.reputation.profile=null; State.reputation.tab='profile'; setView('reputation'); window.scrollTo(0, 0); return;}
    const tab = target.closest('[data-review-profile-tab]'); if (tab) {showHotelReputationTab(tab.dataset.reviewProfileTab); return;}
    if (target.closest('[data-review-capture-selected]')) {void launchHotelReviewCapture([...State.reputation.selectedKeys], 'catalog'); return;}
    if (target.closest('[data-review-capture-all]')) {void launchHotelReviewCapture((State.reputation.catalog || []).map((hotel) => hotel.hotel_key), 'catalog'); return;}
    if (target.closest('[data-review-capture-profile]')) {void launchHotelReviewCapture([State.reputation.hotelKey], 'profile'); return;}
    if (target.closest('[data-review-compare]')) {void runHotelReviewComparison(); return;}
    const pageButton = target.closest('[data-review-page]');
    if (pageButton) {State.reputation.reviewPage=Math.max(0,State.reputation.reviewPage+(pageButton.dataset.reviewPage==='next'?1:-1));void loadHotelReviewsPage();return;}
    const evidence = target.closest('[data-review-evidence]');
    if (evidence) {State.reputation.tab='reviews';State.reputation.pendingEvidenceId=Number(evidence.dataset.reviewEvidence);State.reputation.reviewFilters={source:'',language:'',rating:'',topic:'',dateFrom:'',dateTo:'',query:''};State.reputation.reviewPage=0;void renderHotelReputation().then(()=>$(`[data-review-row-id="${evidence.dataset.reviewEvidence}"]`)?.scrollIntoView({block:'center'}));return;}
    const noteFor = target.closest('[data-review-note-for]'); if (noteFor) {State.reputation.noteReviewId=Number(noteFor.dataset.reviewNoteFor);State.reputation.tab='notes';void renderHotelReputation();return;}
    const selectAttribute = target.closest('[data-review-select-attribute]');
    if (selectAttribute) {
      selectAttribute.disabled = true;
      void api(reputationKeyPath(State.reputation.hotelKey, 'attributes/selection'), {method: 'PUT', body: JSON.stringify({
        attribute: selectAttribute.dataset.reviewSelectAttribute,
        observationId: Number(selectAttribute.dataset.reviewObservationId),
      })}).then(() => {setStatus('Valor principal actualizado.', 'success'); return renderHotelReputation();})
        .catch((error) => {selectAttribute.disabled = false; setStatus(error.message, 'error');});
      return;
    }
    const history = target.closest('[data-review-history]');
    if (history) {
      const row = history.closest('[data-review-row-id]');
      const outlet = row?.querySelector('[data-review-history-outlet]');
      if (!outlet) return;
      if (!outlet.hidden) {outlet.hidden=true;return;}
      outlet.hidden=false;
      outlet.innerHTML='<span>Cargando historial…</span>';
      void api(reputationKeyPath(State.reputation.hotelKey,`reviews/${history.dataset.reviewHistory}/versions`))
        .then((result)=>{outlet.innerHTML=(result.versions||[]).map((version)=>{
          const snapshot = version.snapshot || {};
          const reviewEs = snapshot.review_es ?? snapshot.reviewEs;
          const reviewOriginal = snapshot.review_original ?? snapshot.reviewOriginal;
          return `<article><small>${esc(fmtStamp(version.capturedAt))} · ejecución ${esc(version.runId||'importación')}</small><strong>${snapshot.rating==null?'—':`${nEs(snapshot.rating,1)}/${nEs(snapshot.rating_scale||5,0)}`}</strong>${reviewEs?`<p><b>ES</b> ${esc(reviewEs)}</p>`:''}${reviewOriginal?`<p><b>Original</b> ${esc(reviewOriginal)}</p>`:''}${snapshot.positive_text?`<p><b>Positivo</b> ${esc(snapshot.positive_text)}</p>`:''}${snapshot.negative_text?`<p><b>Negativo</b> ${esc(snapshot.negative_text)}</p>`:''}</article>`;
        }).join('')||'<small>No hay versiones de texto registradas.</small>';})
        .catch((error)=>{outlet.innerHTML=`<small class="hotel-review-error">${esc(error.message)}</small>`;});
      return;
    }
    const deleteNote = target.closest('[data-review-delete-note]'); if (deleteNote) {void api(`/api/hotel-reviews/notes/${deleteNote.dataset.reviewDeleteNote}`,{method:'DELETE'}).then(()=>renderHotelReputation()).catch((error)=>setStatus(error.message,'error'));return;}
    if (target.closest('[data-review-analyze]')) {
      const budget=Number($('#reviewAnalysisBudget')?.value||0);
      if (!Number.isFinite(budget) || budget < 0.001 || budget > 10) {setStatus('Introduce un tope de gasto USD entre 0,001 y 10 para este análisis.','error');return;}
      void api(reputationKeyPath(State.reputation.hotelKey,'analyses'),{method:'POST',body:JSON.stringify({budgetUsd:budget,sources:['google','booking']})})
        .then((result)=>{State.reputation.activeJobId=result.job.id;State.reputation.activeJobKind='analysis';State.reputation.job=result.job;void renderHotelReputation();void pollHotelReviewJob(result.job.id);})
        .catch((error)=>setStatus(error.message,'error'));
    }
  });
}

/* ================================================================= CAPTURAS */
async function renderCaptures() {
  const host = mount('captures');
  if (!Number.isInteger(State.targetId)) {
    renderNoActiveTarget(host, 'Capturas', 'Trazabilidad de las fotos guardadas.');
    return;
  }
  skeleton(host, 'list');
  let photos = [];
  try { const r = await getPhotoHistory(State.targetId); photos = r.photos || []; }
  catch (e) { host.innerHTML = `<div class="page">${pageHead('Capturas', 'Trazabilidad', '')}<div class="inline-error">${esc(e.message)}</div></div>`; return; }

  const t = activeTarget();
  const selectedPhoto = photos.find((photo) => photo.id === State.selectedPhotoId) || photos[0] || null;
  const selectedIndex = photos.findIndex((photo) => photo.id === selectedPhoto?.id);
  const previousPhoto = selectedIndex >= 0 ? photos[selectedIndex + 1] || null : null;
  if (selectedPhoto) State.selectedPhotoId = selectedPhoto.id;
  let detail = null;
  try { if (selectedPhoto) detail = await getPhotoDetail(selectedPhoto.id); }
  catch (e) { host.innerHTML = `<div class="page">${pageHead('Capturas', 'Trazabilidad', '')}<div class="inline-error">No se pudo cargar la foto seleccionada: ${esc(e.message)}</div></div>`; return; }
  let previousDetail = null, comparisonError = null;
  if (previousPhoto) {
    try { previousDetail = await getPhotoDetail(previousPhoto.id); }
    catch (e) { comparisonError = e; }
  }
  const summary = detail?.summary || {};
  const captureRows = (detail?.rows || []).slice().sort((a, b) => Number(b.pricePerNight || 0) - Number(a.pricePerNight || 0));
  const search = String(State.captureHotelSearch || '').trim().toLowerCase();
  const visibleRows = captureRows.filter((row) => !search || [row.hotelName, row.board, row.roomType, row.address].filter(Boolean).join(' ').toLowerCase().includes(search));
  const comparisonStats = previousDetail ? captureComparisonStats(detail, previousDetail) : null;
  const comparisonCoverage = comparisonStats && comparisonStats.currentRows.length ? Math.round((comparisonStats.comparable.length / comparisonStats.currentRows.length) * 100) : 0;
  const rowMarkup = visibleRows.map((row, index) => {
    const searchable = [row.hotelName, row.board, row.roomType, row.address].filter(Boolean).join(' ').toLowerCase();
    return `<tr data-capture-hotel-row data-capture-text="${esc(searchable)}">
    <td class="rank">${index + 1}</td>
    <td class="name">${esc(row.hotelName)}<small class="hotel-name-meta">${esc(row.roomType || '—')}</small></td>
    <td class="num">${money(row.pricePerNight, row.currency)}</td>
    <td class="num dim">${money(row.price, row.currency)}</td>
    <td>${boardTag(row.board)}</td>
    <td class="num">${row.rating != null ? nEs(row.rating, 1) : '—'}</td>
    <td>${row.freeCancellation === true ? '<span class="pos">Sí</span>' : row.freeCancellation === false ? '<span class="dim">No</span>' : '<span class="dim">—</span>'}</td>
    <td class="r">${availChip(row)}</td>
  </tr>`;
  }).join('');
  const hist = photos.map((p, i) => {
    const activeRow = p.id === State.selectedPhotoId;
    return `<tr${activeRow ? ' class="capture-history-row is-selected"' : ' class="capture-history-row"'}>
      <td>${activeRow ? `<span class="capture-active-label"><i></i>Foto #${p.id}</span>` : `<span class="name">Foto #${p.id}</span>`}</td>
      <td class="mono dim">${fmtStamp(p.scrapedAt)}</td>
      <td class="num" style="font-weight:700;">${eur(p.avgPricePerNight)}</td>
      <td class="num dim">${eur(p.avgPricePerPersonNight)}</td>
      <td class="mono dim">${nEs(p.minPricePerNight)} — ${nEs(p.maxPricePerNight)} €</td>
      <td class="num">${nEs(p.capturedRows)}</td>
      <td class="r">${activeRow ? '<span class="mono dim">seleccionada</span>' : `<button type="button" class="btn btn--xs" data-load-photo="${p.id}">Ver</button>`}</td>
    </tr>`;
  }).join('');

  host.innerHTML = `<div class="page">
    ${pageHead('Capturas', 'Captura fotos manualmente y revisa su procedencia.', '')}

    <div class="grid mb12 capture-manual-grid">
      <article class="card card--pad">
        <div class="card__kicker" style="margin-bottom:5px;">Captura manual</div>
        <h2 style="margin-bottom:15px;">Nueva captura</h2>
        <div class="grid grid--2" style="gap:11px; margin-bottom:15px;">
          <label class="field"><span>Límite hoteles</span><input class="input input--mono" id="capLimit" value="200" /></label>
          <label class="field"><span>Mercado</span><input class="input" id="capMarket" value="${esc(t ? t.name : '')}" disabled /></label>
        </div>
        <div class="grid grid--2" style="gap:11px; margin-bottom:15px;">
          <label class="field"><span>Primera entrada</span><input type="date" required class="input" id="capCheckIn" /></label>
          <label class="field"><span>Noches</span><input type="number" min="1" max="30" value="7" required class="input" id="capNights" /></label>
          <label class="field"><span>Adultos</span><input type="number" min="1" max="10" value="2" required class="input" id="capAdults" /></label>
          <label class="field"><span>Habitaciones</span><input type="number" min="1" max="1" value="1" readonly class="input" id="capRooms" /></label>
          <label class="field"><span>Entradas semanales</span><select class="input" id="capWeeks"><option value="1">Una fecha · 1 foto</option><option value="4">4 semanas · 4 fotos</option><option value="13">13 semanas · 13 fotos</option><option value="26">Hasta 180 días · 26 fotos</option></select></label>
          <label class="field"><span>Régimen solicitado</span><select class="input" id="capBoard"><option value="all_inclusive">Todo incluido</option><option value="saved_filters">Filtros del mercado guardado</option></select></label>
        </div>
        <p class="capture-profile-note">Moneda solicitada: EUR · una habitación · sin niños. Las ofertas observadas conservan sus condiciones reales. El barrido se ejecuta ahora; no programa repeticiones.</p>
        <div class="choices" id="capMarkets" style="margin-bottom:16px;">
          ${State.targets.map((x) => `<button type="button" class="choice ${x.id === State.targetId ? 'is-active' : ''}" aria-pressed="${x.id === State.targetId}" data-cap-market="${x.id}">${esc(x.name)}</button>`).join('')}
        </div>
        <button type="button" class="btn btn--primary btn--block" id="launchCapture">Lanzar captura · Booking.com</button>
      </article>

      <article class="card card--pad card--dark console">
        <div class="console__head">
          <span class="card__kicker">Registro</span>
          <span class="live" id="workerState"><i></i>worker inactivo</span>
        </div>
        <div class="console__log" id="captureLog">
          <div>[sistema] Listo para lanzar una captura del mercado activo.</div>
          <div class="dim">Cada entrada solicita una foto independiente. Si una serie falla, las fotos ya guardadas permanecen disponibles.</div>
        </div>
      </article>
    </div>

    <div class="grid mb12 capture-analysis-grid">
      <article class="card card--pad">
        <div class="card__head" style="margin-bottom:8px;"><div><div class="card__kicker" style="margin-bottom:5px;">Histórico de ADR</div><h2>Capturas disponibles</h2><p>Un punto por foto guardada del mercado activo.</p></div><span class="pill-tag">${photos.length} fotos</span></div>
        ${adrHistorySVG(photos)}
      </article>
      <article class="card card--pad">
        <div class="card__kicker" style="margin-bottom:5px;">Foto seleccionada</div>
        <h2>Foto #${selectedPhoto ? selectedPhoto.id : '—'}</h2>
        <p class="capture-selected-stamp">${selectedPhoto ? fmtStamp(selectedPhoto.scrapedAt) : 'Sin capturas disponibles'}</p>
        <div class="capture-summary">
          <div><span>ADR hab/noche</span><strong>${eur(summary.avgPricePerNight)}</strong></div>
          <div><span>ADR pers/noche</span><strong>${eur(summary.avgPricePerPersonNight)}</strong></div>
          <div><span>Rango ADR</span><strong>${nEs(summary.minPricePerNight)} — ${nEs(summary.maxPricePerNight)} €</strong></div>
          <div><span>Filas ADR</span><strong>${nEs(summary.comparableRows)} / ${nEs(summary.rows)}</strong></div>
        </div>
        <div class="capture-compare-criteria"><span>Perfil de búsqueda</span><strong>${captureProfileHTML(detail?.snapshot?.captureProfile)}</strong></div>
        <div class="capture-compare-criteria"><span>Base de comparación</span><strong>Hotel · estancia · ocupación · habitación · régimen · moneda · cancelación</strong></div>
        ${previousPhoto ? `<div class="capture-compare-trigger"><span>vs. foto #${previousPhoto.id} · <strong>${comparisonStats ? `${comparisonStats.comparable.length}/${comparisonStats.currentRows.length} filas equivalentes` : 'sin datos comparables'}</strong> <strong class="capture-change capture-change--${comparisonStats?.avgChange != null && comparisonStats.avgChange > .5 ? 'up' : comparisonStats?.avgChange != null && comparisonStats.avgChange < -.5 ? 'down' : 'flat'}">${signPct(comparisonStats?.avgChange ?? null)}</strong></span><span class="capture-compare-coverage">${comparisonStats ? `${comparisonCoverage}% de cobertura` : 'No disponible'}</span><button type="button" class="btn btn--xs" data-capture-compare ${comparisonStats ? '' : 'disabled'}>${State.captureComparisonOpen ? 'Comparación abierta' : 'Comparar hoteles'}</button></div>` : ''}
      </article>
    </div>

    ${State.captureComparisonOpen && previousPhoto ? (previousDetail ? captureComparisonHTML(detail, previousDetail, selectedPhoto, previousPhoto) : `<div class="inline-error mb12">No se pudo cargar la foto de comparación: ${esc(comparisonError?.message || 'sin detalle')}</div>`) : ''}

    <article class="card table-card mb12">
      <div class="table-card__head"><div><div class="card__kicker" style="margin-bottom:5px;">Booking · trazabilidad</div><strong style="font-size:15px;">Histórico de capturas</strong></div><span class="table-filter-status">Selecciona una foto para inspeccionarla</span></div>
      <div class="table-scroll">
        <table class="t" style="min-width:760px;">
          <thead><tr><th>Foto</th><th>Fecha</th><th class="r">ADR hab/noche</th><th class="r">ADR pers/noche</th><th>Rango</th><th class="r">Filas</th><th class="r"></th></tr></thead>
          <tbody>${hist || `<tr><td colspan="7" class="empty">Sin capturas registradas.</td></tr>`}</tbody>
        </table>
      </div>
    </article>

    <article class="card table-card">
      <div class="table-card__head table-card__head--tools">
        <div class="title"><strong>Hoteles de la foto #${selectedPhoto ? selectedPhoto.id : '—'}</strong><span class="count" id="captureHotelCount">${visibleRows.length} / ${captureRows.length} filas</span></div>
        <div class="table-tools"><input type="search" class="input input--search" id="captureHotelSearch" value="${esc(State.captureHotelSearch)}" placeholder="Hotel, régimen o habitación…" aria-label="Buscar en la captura seleccionada" /></div>
      </div>
      <div class="table-scroll">
        <table class="t" style="min-width:900px;" id="captureHotelTable">
          <caption class="sr-only">Hoteles y condiciones de la captura seleccionada</caption>
          <thead><tr><th class="r" style="width:44px;">#</th><th>Hotel / habitación</th><th class="r">ADR/hab</th><th class="r">Total</th><th>Régimen</th><th class="r">Nota</th><th>Cancel.</th><th class="r">Disponibilidad</th></tr></thead>
          <tbody>${rowMarkup || '<tr><td colspan="8" class="empty">No hay hoteles que coincidan con la búsqueda.</td></tr>'}</tbody>
        </table>
      </div>
    </article>
  </div>`;
  runCounters(host);
}

/* ================================================================== COPILOT */
async function renderCopilot() {
  const host = mount('copilot');
  const workspaceScope = State.copilotWorkspaceContext?.targetId === State.targetId ? State.copilotWorkspaceContext : null;
  const workspaceScopeLabel = workspaceScope ? ` · contexto BI: foto #${workspaceScope.snapshotId}${workspaceScope.checkIn ? ` · entrada ${workspaceScope.checkIn}` : ' · todas las entradas'}` : '';
  host.innerHTML = `<div class="copilot ${State.copilotHistoryOpen ? '' : 'is-history-collapsed'}" id="copilotLayout">
    <aside class="copilot__aside" aria-label="Historial de conversaciones">
      <div class="top"><div><h2>Conversaciones</h2><span id="sessCount">…</span></div><div class="copilot-aside-actions"><button type="button" class="icon-btn" id="toggleCopilotHistory" aria-label="Plegar historial" aria-expanded="true" title="Plegar historial">‹</button><button type="button" class="add-btn" id="newSession" aria-label="Nueva conversación">+</button></div></div>
      <label class="copilot-session-search"><span class="sr-only">Buscar conversaciones</span><input type="search" id="copilotSessionSearch" placeholder="Buscar conversaciones…" autocomplete="off" /></label>
      <div class="sessions" id="sessionList"></div>
      <details class="copilot-diagnostics"><summary>Diagnóstico <span>técnico</span></summary><dl class="copilot-evaluation" id="copilotEvaluation"><dt>Control IA</dt><dd>Cargando último control…</dd></dl><div class="copilot-budget" id="copilotBudget" aria-live="polite"></div></details>
      <div class="note-box">Respuestas basadas en capturas de Booking y vuelos. No sustituye pickup ni ocupación del PMS.</div>
    </aside>
    <section class="copilot__main">
      <div class="copilot__head"><div class="copilot-head-title"><button type="button" class="copilot-history-toggle icon-btn" id="toggleCopilotHistoryMain" aria-label="Mostrar u ocultar historial" aria-expanded="${State.copilotHistoryOpen}">☰</button><div><h1>Copilot</h1><p id="copilotCtx">${esc(activeTarget() ? activeTarget().name : 'Mercado')} · asistente de revenue${esc(workspaceScopeLabel)}</p></div></div><div class="copilot__scope"><span class="copilot-auto-status" aria-label="Selección automática de modelo">Selección automática</span><button type="button" class="btn btn--quiet copilot-panel-toggle" id="toggleCopilotPanel" aria-expanded="false">Resultados</button></div></div>
      <div class="thread" id="thread" role="log" aria-live="polite" aria-relevant="additions text"></div>
      <div class="composer">
        <div class="suggest" id="chatSuggestions">
          ${workspaceScope ? '<button type="button" data-ask="Explica el contexto BI seleccionado, sus tarifas y sus límites de interpretación.">Explicar este contexto BI</button>' : ''}
          <button type="button" data-ask="¿Dónde tengo margen frente a la mediana esta semana?">Lectura del ADR frente al mercado</button>
          <button type="button" data-ask="¿Qué hoteles ofrecen mejor relación precio-valoración?">Hoteles con mejor valor</button>
          <button type="button" data-ask="Muéstrame la distribución de precios del set">Gráfica de precios del set</button>
          <button type="button" data-ask="¿Qué rutas aéreas tienen más margen?">Oportunidades aéreas</button>
        </div>
        <button type="button" class="copilot-examples" id="toggleCopilotExamples" hidden aria-expanded="false">Ejemplos</button>
        <div class="copilot-attachments" id="copilotAttachments" aria-live="polite"></div>
        <div class="composer__row">
          <button type="button" class="attach-btn" id="chatAttach" aria-label="Adjuntar archivo" title="Adjuntar CSV, XLSX, PDF o imagen">＋</button>
          <input type="file" id="chatFile" accept=".csv,.xlsx,.pdf,.png,.jpg,.jpeg" hidden />
          <textarea id="chatInput" rows="2" placeholder="Pregunta, compara o pide una gráfica…" aria-label="Mensaje para Copilot" autocomplete="off"></textarea>
          <button type="button" class="send-btn" id="chatSend" aria-label="Enviar">
            <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h13M12 5l7 7-7 7"></path></svg>
          </button>
        </div>
      </div>
      <aside class="copilot__results" id="copilotResults" hidden aria-label="Resultados de Copilot"><div class="copilot-results__head"><strong>Resultados</strong><button type="button" class="icon-btn" id="closeCopilotPanel" aria-label="Cerrar resultados">×</button></div><div class="copilot-results__tabs" role="tablist"><button type="button" class="is-active" data-copilot-panel-tab="result" role="tab" aria-selected="true">Resultado</button><button type="button" data-copilot-panel-tab="sources" role="tab" aria-selected="false">Fuentes</button><button type="button" data-copilot-panel-tab="files" role="tab" aria-selected="false">Archivos</button></div><div class="copilot-results__body" id="copilotResultsBody"><p class="empty">Selecciona un resultado para inspeccionarlo.</p></div></aside>
    </section>
  </div>`;

  try {
    const r = await api('/api/assistant/sessions');
    State.sessions = r.sessions || [];
  } catch (_) { State.sessions = []; }
  $('#sessCount').textContent = `${State.sessions.length} ${State.sessions.length === 1 ? 'sesión' : 'sesiones'}`;
  const sessionSearch = $('#copilotSessionSearch'); if (sessionSearch) sessionSearch.value = State.copilotSessionQuery;
  renderSessionList();
  const aside = $('.copilot__aside'); if (aside) aside.inert = !State.copilotHistoryOpen;
  void renderCopilotEvaluation();
  void renderCopilotBudget();
  const pendingPrompt = State.copilotPrompt;
  State.copilotPrompt = null;
  if (pendingPrompt) {
    // «Preguntar al Copilot» desde otra vista abre una conversación nueva y la envía
    State.activeSession = null; State.copilotAttachments = [];
    renderCopilotAttachments(); renderSessionList(); greetThread();
    void sendChat(pendingPrompt);
    return;
  }
  if (State.sessions.length) loadSession(State.sessions[0].id);
  else greetThread();
}

async function renderCopilotBudget() {
  const box = $('#copilotBudget'); if (!box) return;
  try {
    const result = await api('/api/assistant/budget');
    const budget = result.budgetUsd || 0;
    const spend = result.spentUsd || 0;
    const state = result.warning ? 'is-warning' : 'is-ok';
    box.innerHTML = `<small class="${state}">IA este mes: ${nEs(spend, 2)} / ${nEs(budget, 2)} USD</small>`;
  } catch (_) { /* budget is diagnostic only */ }
}

async function renderCopilotEvaluation() {
  const box = $('#copilotEvaluation'); if (!box) return;
  try {
    const result = await api('/api/assistant/evaluations/latest');
    const evaluation = result.evaluation;
    if (!evaluation) {
      box.innerHTML = '<dt>Control IA</dt><dd>Sin evaluación registrada</dd><small>Ejecuta el control local antes de publicar cambios de routing.</small>';
      return;
    }
    const date = evaluation.createdAt ? fmtStamp(evaluation.createdAt) : '—';
    const state = evaluation.passed ? 'is-ok' : 'is-warning';
    const status = evaluation.passed ? 'Correcto' : 'Revisar';
    box.innerHTML = `<dt>Control IA</dt><dd class="${state}">${status} · ${nEs(evaluation.passedCount)} / ${nEs(evaluation.caseCount)} casos</dd><small>${esc(evaluation.profile)} · ${esc(date)}</small>`;
  } catch (_) {
    box.innerHTML = '<dt>Control IA</dt><dd>Estado no disponible</dd>';
  }
}

function renderSessionList() {
  const list = $('#sessionList'); if (!list) return;
  if (!State.sessions.length) { list.innerHTML = '<div class="empty" style="padding:20px 0;">Sin conversaciones que coincidan.</div>'; return; }
  list.innerHTML = State.sessions.map((s) => `<div class="session-wrap ${s.id === State.activeSession ? 'is-active' : ''}">
    <button type="button" class="session" data-session="${s.id}" aria-current="${s.id === State.activeSession ? 'true' : 'false'}" title="${esc(s.title || 'Conversación')}"><strong>${s.pinned ? '<span class="session-pin" aria-label="Fijada">●</span>' : ''}${esc(s.title || 'Conversación')}</strong><span class="session-date">${fmtStamp(s.lastMessageAt || s.updatedAt)}</span></button>
    <div class="session-actions" aria-label="Acciones de conversación"><button type="button" data-session-action="pin" data-session-id="${s.id}" aria-label="${s.pinned ? 'Desfijar' : 'Fijar'} conversación">${s.pinned ? '★' : '☆'}</button><button type="button" data-session-action="rename" data-session-id="${s.id}" aria-label="Renombrar conversación">✎</button><button type="button" data-session-action="archive" data-session-id="${s.id}" aria-label="Archivar conversación">×</button></div>
  </div>`).join('');
}

function copilotDraftKey(sessionId = State.activeSession) { return `atlas:copilot:draft:${sessionId || 'new'}`; }
function saveCopilotDraft(value) { try { sessionStorage.setItem(copilotDraftKey(), String(value || '').slice(0, 2000)); } catch (_) {} }
function restoreCopilotDraft() { try { return sessionStorage.getItem(copilotDraftKey()) || ''; } catch (_) { return ''; } }
function updateCopilotHistory(open) {
  State.copilotHistoryOpen = Boolean(open);
  const layout = $('#copilotLayout'); if (layout) layout.classList.toggle('is-history-collapsed', !State.copilotHistoryOpen);
  const aside = $('.copilot__aside'); if (aside) aside.inert = !State.copilotHistoryOpen;
  ['toggleCopilotHistory','toggleCopilotHistoryMain'].forEach((id) => { const el = $(`#${id}`); if (el) { el.setAttribute('aria-expanded', String(State.copilotHistoryOpen)); el.setAttribute('title', State.copilotHistoryOpen ? 'Plegar historial' : 'Mostrar historial'); } });
  try { localStorage.setItem('atlas:copilot:history-open', State.copilotHistoryOpen ? '1' : '0'); } catch (_) {}
}
function copilotPanelHTML(tab = 'result', focusOrigin = null) {
  const panel = $('#copilotResults'); if (!panel) return;
  if (panel.hidden) State.copilotPanelFocusOrigin = focusOrigin || document.activeElement;
  panel.hidden = false; State.copilotPanel = tab;
  // Split view keeps at least ~600 px for the conversation after reserving the
  // compact result panel. Narrower workspaces use the accessible overlay.
  const main = $('.copilot__main'); if (main) main.classList.toggle('has-results', main.clientWidth >= 938);
  const toggle = $('#toggleCopilotPanel'); if (toggle) toggle.setAttribute('aria-expanded', 'true');
  requestAnimationFrame(() => $('#closeCopilotPanel')?.focus());
  $$('.copilot-results__tabs [data-copilot-panel-tab]').forEach((button) => { const active = button.dataset.copilotPanelTab === tab; button.classList.toggle('is-active', active); button.setAttribute('aria-selected', String(active)); });
  const body = $('#copilotResultsBody'); if (!body) return;
  if (tab === 'files') { body.innerHTML = State.copilotAttachments.length ? State.copilotAttachments.map((item) => { const state = item.extractionStatus || item.status || 'ready'; const label = state === 'partial' ? 'lectura parcial' : state === 'ocr_pending' ? 'OCR pendiente' : state === 'error' ? 'error de lectura' : 'listo'; return `<div class="result-file"><strong>${esc(item.filename)}</strong><span>${esc(item.mimeType || item.contentType || 'Archivo')} · ${label}${item.sizeBytes ? ` · ${nEs(item.sizeBytes / 1024, 0)} KB` : ''}</span></div>`; }).join('') : '<p class="empty">No hay archivos asociados a esta conversación.</p>'; return; }
  const result = State.copilotLastResult || {};
  if (tab === 'sources') {
    const meta = result.dataMeta || {};
    const toolRefs = Array.isArray(meta.toolEvidence) ? meta.toolEvidence : [];
    const evidenceRefs = Array.isArray(meta.references) ? meta.references : [];
    const ids = toolRefs.length ? toolRefs : (evidenceRefs.length ? evidenceRefs : (Array.isArray(meta.toolEvidenceIds) ? meta.toolEvidenceIds.map((id, index) => ({ evidenceId: id, tool: (meta.toolNames || [])[index] })) : []));
    body.innerHTML = ids.length ? `<div class="result-source-list">${ids.map((ref, index) => `<div class="result-source"><strong>Fuente ${index + 1}${ref.tool ? ` · ${esc(ref.tool)}` : ref.metric ? ` · ${esc(ref.metric)}` : ''}</strong><span>${esc(String(ref.evidenceId || ref))}</span><small>${ref.sourceObservedAt || ref.observedAt ? `Dato observado ${esc(fmtStamp(ref.sourceObservedAt || ref.observedAt))}` : 'Consulta registrada'}${ref.queriedAt ? ` · consultada ${esc(fmtStamp(ref.queriedAt))}` : ''}${ref.snapshotId ? ` · foto #${esc(String(ref.snapshotId))}` : ''}</small></div>`).join('')}</div>` : '<p class="empty">Fuente histórica no disponible para esta respuesta.</p>';
    return;
  }
  body.innerHTML = result.visualization ? copilotVisualizationHTML(result.visualization) : '<p class="empty">La última respuesta no contiene una gráfica estructurada.</p>';
}

function greetThread() {
  const thread = $('#thread'); if (!thread) return;
  setCopilotSuggestionsState(true);
  thread.innerHTML = `<div class="msg-bot"><div class="msg-bot__who"><div class="m"><i></i></div><span>Copilot</span></div>
    <div class="msg-bot__body"><p>Hola. Puedo leer el mercado activo (${esc(activeTarget() ? activeTarget().name : '—')}), comparar hoteles y rutas, y calcular gráficas sobre tus capturas. Pregúntame o usa una sugerencia.</p></div></div>`;
}

function setCopilotSuggestionsState(emptyConversation, expanded = false) {
  const suggestions = $('#chatSuggestions');
  const examples = $('#toggleCopilotExamples');
  if (!suggestions || !examples) return;
  suggestions.hidden = !emptyConversation && !expanded;
  examples.hidden = emptyConversation;
  examples.textContent = expanded ? 'Ocultar ejemplos' : 'Ejemplos';
  examples.setAttribute('aria-expanded', String(expanded));
}

async function loadSession(id) {
  State.activeSession = id;
  State.copilotLastResult = null;
  renderSessionList();
  const thread = $('#thread');
  thread.innerHTML = '<div class="empty">Cargando…</div>';
  try {
    const r = await api(`/api/assistant/sessions/${id}`);
    if (State.activeSession !== id) return;
    try { const files = await api(`/api/assistant/sessions/${id}/attachments`); State.copilotAttachments = files.attachments || []; renderCopilotAttachments(); } catch (_) { State.copilotAttachments = []; renderCopilotAttachments(); }
    if (State.activeSession !== id) return;
    const msgs = r.messages || [];
    if (!msgs.length) { greetThread(); restoreCopilotDraftIntoInput(); return; }
    setCopilotSuggestionsState(false);
    thread.innerHTML = msgs.map(renderMsg).join('');
    thread.scrollTop = thread.scrollHeight;
    restoreCopilotDraftIntoInput();
  } catch (e) { if (State.activeSession !== id || !thread.isConnected) return; thread.innerHTML = `<div class="inline-error">${esc(e.message)}</div>`; }
}

function restoreCopilotDraftIntoInput() { const input = $('#chatInput'); if (input) { input.value = restoreCopilotDraft(); input.dispatchEvent(new Event('input', { bubbles: true })); } }

function renderMsg(m) {
  if (m.role !== 'user') State.copilotLastResult = m;
  if (m.role === 'user') return `<div class="msg-user">${esc(m.content)}</div>`;
  return `<div class="msg-bot"><div class="msg-bot__who"><div class="m"><i></i></div><span>Copilot</span></div>
    <div class="msg-bot__body">${md(m.content)}${copilotVisualizationHTML(m.visualization)}</div>${copilotTraceHTML(m.dataMeta)}</div>`;
}

function copilotVisualizationHTML(visualization) {
  if (!visualization || !Array.isArray(visualization.points) || !visualization.points.length) return '';
  const validValues = visualization.points.map((point) => Number(point.value)).filter((value) => Number.isFinite(value));
  const max = Math.max(...validValues, 1);
  const rows = visualization.points.map((point) => {
    const value = Number(point.value);
    const known = Number.isFinite(value);
    const width = known ? Math.max(2, Math.round((value / max) * 100)) : 0;
    return `<div class="copilot-viz__row ${known ? '' : 'is-missing'}"><span title="${esc(point.label || '')}">${esc(point.label || '—')}</span><div class="copilot-viz__bar">${known ? `<i style="width:${width}%"></i>` : '<em>Sin dato</em>'}</div><strong>${known ? `${nEs(value, 2)} ${esc(visualization.unit || '')}` : '—'}</strong></div>`;
  }).join('');
  return `<section class="copilot-viz" aria-label="${esc(visualization.title || 'Visualización')}"><div class="copilot-viz__head"><strong>${esc(visualization.title || 'Visualización')}</strong><small>${esc(visualization.subtitle || '')}</small></div>${rows}<small class="copilot-viz__source">Fuente: ${esc(visualization.source || 'Fuente no especificada')}</small></section>`;
}

function copilotModelLabel(model) {
  const known = {
    'openai/gpt-5.6-luna': 'Luna',
    'openai/gpt-5.6-terra': 'Terra',
    'openai/gpt-5.6-sol': 'Sol',
    'minimax/minimax-m3': 'MiniMax M3',
    'deepseek/deepseek-v4-pro-0813': 'DeepSeek V4 Pro',
    'google/gemini-3.8-flash': 'Gemini Flash',
    'z-ai/glm-5.3-flash': 'GLM 5.3 Flash',
  };
  return known[model] || model || 'Sin modelo';
}

function copilotTraceHTML(meta) {
  if (!meta || typeof meta !== 'object') return '';
  const routing = meta.routing || {};
  const moa = meta.moa || {};
  const quality = meta.responseQuality || {};
  const hasTrace = meta.model || routing.strategy || moa.executed || meta.airFallback || quality.status || meta.toolCalls || (meta.toolEvidenceIds && meta.toolEvidenceIds.length);
  if (!hasTrace) return '';
  const route = {
    direct: 'Consulta directa',
    single_call_synthesis: 'Análisis especializado',
    multi_call_synthesis: 'Panel de expertos',
  }[routing.aggregation] || 'Consulta';
  const expertNames = {
    hotel_revenue: 'Revenue hotelero',
    air_access: 'Accesibilidad aérea',
    market_checker: 'Contraste de mercado',
    data_quality: 'Calidad de datos',
  };
  const experts = (moa.executed ? moa.experts : routing.experts) || [];
  const rows = [];
  const row = (label, value, extra = '') => { if (value) rows.push(`<div${extra ? ` class="${extra}"` : ''}><dt>${esc(label)}</dt><dd>${esc(String(value))}</dd></div>`); };
  row('Modelo', copilotModelLabel(meta.model));
  row('Ruta', route);
  if (routing.selectionReason) row('Selección', routing.selectionReason);
  if (experts.length) row('Especialistas', experts.map((expert) => expertNames[expert] || expert).join(' · '));
  if (moa.executed) {
    const calls = Number(moa.expertCalls || 0);
    const failed = Number(moa.failedExperts || 0);
    row('Panel', `${calls} consultas especializadas${failed ? ` · ${failed} con incidencia` : ''}`);
  }
  if (Number(meta.toolCalls)) row('Herramientas', `${meta.toolCalls} consulta(s)${meta.toolErrors ? ` · ${meta.toolErrors} con incidencia` : ''}`);
  if (Array.isArray(meta.toolNames) && meta.toolNames.length) row('Consultas', meta.toolNames.join(' · '));
  if (Array.isArray(meta.toolEvidenceIds) && meta.toolEvidenceIds.length) row('Fuentes identificadas', `${meta.toolEvidenceIds.length} referencias · ${meta.toolEvidenceIds.join(' · ')}`, 'is-mono');
  if (meta.airFallback) row('Fallback aéreo', `${copilotModelLabel(meta.airFallback.from)} → ${copilotModelLabel(meta.airFallback.to)}`, 'is-warning');
  if (meta.modelFallback) row('Fallback de modelo', `${copilotModelLabel(meta.modelFallback.from)} → ${copilotModelLabel(meta.modelFallback.to)}`, 'is-warning');
  if (quality.status && quality.status !== 'ok') {
    const missing = Array.isArray(quality.missingBlocks) && quality.missingBlocks.length
      ? `Faltan: ${quality.missingBlocks.join(', ')}`
      : 'El formato requiere revisión manual.';
    row('Control de respuesta', missing, 'is-warning');
  }
  if (meta.verification?.status) row('Cifras', meta.verification.status === 'verified' ? 'Evidencia comprobada' : meta.verification.status === 'partial' ? 'Evidencia parcial' : 'Evidencia insuficiente', meta.verification.status === 'verified' ? 'is-ok' : 'is-warning');
  if (Number.isFinite(Number(meta.latencyMs))) row('Tiempo', `${nEs(meta.latencyMs, 0)} ms`);
  if (meta.requestId) row('Referencia', meta.requestId, 'is-mono');
  const qualityLabel = quality.status === 'ok' ? 'Formato comprobado' : quality.status ? 'Revisar respuesta' : 'Sin comprobación';
  const qualityState = quality.status === 'ok' ? 'is-ok' : quality.status ? 'is-warning' : 'is-neutral';
  const sources = Array.isArray(meta.toolEvidenceIds) && meta.toolEvidenceIds.length ? `<button type="button" class="trace-sources" data-open-copilot-sources>Ver ${meta.toolEvidenceIds.length} fuentes</button>` : '';
  return `<details class="copilot-trace"><summary><span>Trazabilidad</span><span class="copilot-trace__status ${qualityState}">${qualityLabel}</span></summary><dl>${rows.join('')}</dl>${sources}</details>`;
}
function paras(text) {
  return String(text || '').split(/\n{2,}/).map((p) => `<p>${esc(p).replace(/\n/g, '<br>')}</p>`).join('');
}

/* render ligero de markdown para las respuestas del Copilot */
function mdInline(s) {
  return esc(s)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*(?!\*)([^*]+?)\*(?!\*)/g, '$1<em>$2</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
}
function mdTable(rows) {
  const cells = rows.map((r) => r.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim()));
  let header = null, start = 0;
  if (cells[1] && cells[1].every((c) => /^:?-{2,}:?$/.test(c))) { header = cells[0]; start = 2; }
  const thead = header ? `<thead><tr>${header.map((c) => `<th>${mdInline(c)}</th>`).join('')}</tr></thead>` : '';
  const tb = `<tbody>${cells.slice(start).map((r) => `<tr>${r.map((c) => `<td>${mdInline(c)}</td>`).join('')}</tr>`).join('')}</tbody>`;
  return `<div class="table-scroll md-table-wrap"><table class="t md-table">${thead}${tb}</table></div>`;
}
function md(text) {
  const lines = String(text || '')
    .replace(/\r/g, '').split('\n');
  let html = '', i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) { i++; continue; }
    if (/^\s*\|.*\|\s*$/.test(line)) {
      const tbl = []; while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) { tbl.push(lines[i]); i++; }
      html += mdTable(tbl); continue;
    }
    const h = line.match(/^\s*#{1,6}\s+(.*)$/);
    if (h) { html += `<p class="md-h">${mdInline(h[1].replace(/\*\*/g, ''))}</p>`; i++; continue; }
    if (/^\s*[-*]\s+/.test(line)) {
      const items = []; while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) { items.push(lines[i].replace(/^\s*[-*]\s+/, '')); i++; }
      html += `<ul class="md-ul">${items.map((it) => `<li>${mdInline(it)}</li>`).join('')}</ul>`; continue;
    }
    const para = [line]; i++;
    while (i < lines.length && lines[i].trim() && !/^\s*[|#]/.test(lines[i]) && !/^\s*[-*]\s+/.test(lines[i])) { para.push(lines[i]); i++; }
    html += `<p>${mdInline(para.join(' '))}</p>`;
  }
  return html || '<p></p>';
}

async function sendChat(text) {
  text = (text || '').trim(); if (!text) return;
  const requestSessionId = State.activeSession;
  const requestTargetId = State.targetId;
  const sendingKey = requestSessionId || 'new';
  if (State.copilotSendingBySession[sendingKey]) return;
  State.copilotSendingBySession[sendingKey] = true;
  State.copilotSending = true;
  const thread = $('#thread');
  setCopilotSuggestionsState(false);
  if (thread.querySelector('.empty')) thread.innerHTML = '';
  thread.insertAdjacentHTML('beforeend', `<div class="msg-user">${esc(text)}</div>`);
  const pend = document.createElement('div');
  pend.className = 'msg-bot';
  pend.innerHTML = `<div class="msg-bot__who"><div class="m"><i></i></div><span>Copilot</span></div><div class="msg-bot__body"><p style="color:var(--faint);">Analizando el mercado<span class="caret">▊</span></p></div>`;
  thread.appendChild(pend);
  thread.scrollTop = thread.scrollHeight;
  const input = $('#chatInput'); if (input) { input.value = ''; saveCopilotDraft(''); }
  try {
    const wantsVisualization = /gr[aá]fica|visualiza|distribuci[oó]n|evoluci[oó]n|tendencia/i.test(text);
    const requestId = (window.crypto?.randomUUID ? window.crypto.randomUUID() : `assistant-${Date.now()}-${Math.random().toString(16).slice(2)}`);
    const requestBody = { message: text, requestId, targetId: State.targetId, sessionId: State.activeSession, mode: 'auto', visualize: wantsVisualization, attachmentIds: State.copilotAttachments.map((item) => item.id), workspaceContext: State.copilotWorkspaceContext?.targetId === State.targetId ? { snapshotId: State.copilotWorkspaceContext.snapshotId, checkIn: State.copilotWorkspaceContext.checkIn || null } : null };
    // Documents, decision requests and long analyses run in the persistent
    // queue so the browser can reconnect, show progress and cancel safely.
    const useBackgroundJob = State.copilotAttachments.length > 0 || text.length > 900 || State.copilotMode === 'decision';
    const r = await api(useBackgroundJob ? '/api/assistant/jobs' : '/api/assistant/chat', {
      method: 'POST',
      body: JSON.stringify(requestBody),
    });
    if (useBackgroundJob) {
      const jobId = r.job && r.job.id;
      pend.dataset.assistantJobId = jobId || '';
      pend.querySelector('.msg-bot__body').innerHTML = `<p class="assistant-job-progress">Trabajo en cola · preparando análisis…</p>${jobId ? `<button type="button" class="job-cancel" data-cancel-assistant-job="${esc(jobId)}">Dejar de seguir</button>` : ''}`;
      State.copilotActiveJobs[requestSessionId || 'new'] = jobId;
      await pollAssistantJob(jobId, pend, requestSessionId, requestTargetId);
      return;
    }
    const responseFresh = requestSessionId === State.activeSession && requestTargetId === State.targetId && pend.isConnected;
    if (responseFresh) State.copilotLastResult = r;
    if (responseFresh) {
      pend.querySelector('.msg-bot__body').innerHTML = md(r.reply) + copilotVisualizationHTML(r.visualization);
      const trace = copilotTraceHTML(r.dataMeta); if (trace) pend.insertAdjacentHTML('beforeend', trace);
    }
    if (r.session && requestSessionId === State.activeSession) {
      State.activeSession = r.session.id;
      const exists = State.sessions.find((s) => s.id === r.session.id);
      if (exists) Object.assign(exists, r.session); else State.sessions.unshift(r.session);
      renderSessionList();
    }
  } catch (e) {
    if (requestSessionId !== State.activeSession || requestTargetId !== State.targetId || !pend.isConnected) return;
    const msg = e.status === 503 ? 'El Copilot no está configurado en este entorno (falta OPENROUTER_API_KEY).' : e.message;
    pend.querySelector('.msg-bot__body').innerHTML = `<p style="color:var(--red);">${esc(msg)}</p>`;
    if (input) { input.value = text; saveCopilotDraft(text); }
  }
  delete State.copilotSendingBySession[sendingKey];
  State.copilotSending = false;
  if (requestSessionId === State.activeSession) thread.scrollTop = thread.scrollHeight;
}

function applyAssistantResponse(response, pend, requestTargetId = State.targetId) {
  const isActive = (!response._requestSessionId || response._requestSessionId === State.activeSession) && requestTargetId === State.targetId;
  if (isActive && pend?.isConnected) State.copilotLastResult = response;
  const body = pend?.isConnected ? pend.querySelector('.msg-bot__body') : null;
  if (body && isActive) body.innerHTML = md(response.reply || '') + copilotVisualizationHTML(response.visualization);
  const trace = copilotTraceHTML(response.dataMeta); if (trace && pend?.isConnected && isActive) pend.insertAdjacentHTML('beforeend', trace);
  if (response.session && (!response._requestSessionId || response._requestSessionId === State.activeSession)) {
    State.activeSession = response.session.id;
    const exists = State.sessions.find((s) => s.id === response.session.id);
    if (exists) Object.assign(exists, response.session); else State.sessions.unshift(response.session);
    renderSessionList();
  }
}

async function pollAssistantJob(jobId, pend, requestSessionId = State.activeSession, requestTargetId = State.targetId) {
  if (!jobId) throw new Error('No se pudo crear el trabajo de Copilot');
  let tries = 0;
  return new Promise((resolve) => {
    const tick = async () => {
      tries++;
      try {
        const r = await api(`/api/assistant/jobs/${encodeURIComponent(jobId)}`);
        const job = r.job || {};
        if (!pend.isConnected) { delete State.copilotActiveJobs[requestSessionId || 'new']; delete State.copilotSendingBySession[requestSessionId || 'new']; State.copilotSending = false; resolve(); return; }
        const body = pend.querySelector('.msg-bot__body');
        if (job.status === 'succeeded') {
          applyAssistantResponse({ ...(job.result || {}), _requestSessionId: requestSessionId }, requestSessionId === State.activeSession ? pend : null, requestTargetId);
          delete State.copilotActiveJobs[requestSessionId || 'new']; delete State.copilotSendingBySession[requestSessionId || 'new']; State.copilotSending = false; resolve(); return;
        }
        if (job.status === 'cancelled') {
          body.innerHTML = '<p class="assistant-job-cancelled">Trabajo cancelado.</p>';
          delete State.copilotActiveJobs[requestSessionId || 'new']; delete State.copilotSendingBySession[requestSessionId || 'new']; State.copilotSending = false; resolve(); return;
        }
        if (job.status === 'failed') {
          body.innerHTML = `<p style="color:var(--red);">No se pudo completar el análisis: ${esc(job.error || 'error del trabajo')}</p>`;
          delete State.copilotSendingBySession[requestSessionId || 'new']; State.copilotSending = false; resolve(); return;
        }
        body.innerHTML = `<p class="assistant-job-progress">${esc(job.message || 'Analizando…')}<span class="caret">▊</span></p><button type="button" class="job-cancel" data-cancel-assistant-job="${esc(jobId)}">Dejar de seguir</button>`;
      } catch (error) {
        if (tries > 10) { pend.querySelector('.msg-bot__body').innerHTML = `<p style="color:var(--red);">No se pudo consultar el trabajo: ${esc(error.message)}</p>`; delete State.copilotSendingBySession[requestSessionId || 'new']; State.copilotSending = false; resolve(); return; }
      }
      if (tries > 600) { pend.querySelector('.msg-bot__body').innerHTML = '<p style="color:var(--red);">Seguimiento detenido; el trabajo puede continuar en segundo plano.</p>'; delete State.copilotSendingBySession[requestSessionId || 'new']; State.copilotSending = false; resolve(); return; }
      setTimeout(tick, 900);
    };
    void tick();
  });
}

function renderCopilotAttachments() {
  const host = $('#copilotAttachments'); if (!host) return;
  host.innerHTML = State.copilotAttachments.map((item) => { const state = item.extractionStatus || item.status || 'ready'; const label = state === 'partial' ? 'lectura parcial' : state === 'ocr_pending' ? 'OCR pendiente' : state === 'error' ? 'error' : 'listo'; return `<span class="attachment-chip"><span>${esc(item.filename)}</span><small>${label}</small><button type="button" data-remove-attachment="${item.id}" aria-label="Quitar ${esc(item.filename)}">×</button></span>`; }).join('');
}

async function uploadCopilotAttachment(file) {
  if (!State.activeSession) {
    try {
      const created = await api('/api/assistant/sessions', { method: 'POST', body: JSON.stringify({ title: `Análisis · ${file.name}`, targetId: State.targetId, mode: State.copilotMode }) });
      State.activeSession = created.session.id; State.sessions.unshift(created.session); renderSessionList();
    } catch (error) { alert(error.message || 'No se pudo crear la conversación'); return; }
  }
  const uploadSessionId = State.activeSession;
  const body = new FormData(); body.append('sessionId', uploadSessionId); body.append('file', file);
  try {
    const result = await api('/api/assistant/attachments', { method: 'POST', body });
    if (State.activeSession !== uploadSessionId) return;
    State.copilotAttachments.push(result.attachment); renderCopilotAttachments();
  } catch (error) { alert(error.message || 'No se pudo adjuntar el archivo'); }
}

/* =============================================================== WORKSPACE */
const WORKSPACE_BLOCK_LIBRARY = {
  'market-kpis': { badge: 'KPI', title: 'KPIs certificados', description: 'Mediana, IQR y cobertura', size: 'wide', linkGroup: 'none' },
  'hotel-table': { badge: 'TAB', title: 'Tabla hotelera', description: 'Selecciona y enlaza', size: 'wide', linkGroup: 'A' },
  'hotel-trend': { badge: 'LIN', title: 'Gráfica ADR', description: 'Evolución del mercado', size: 'medium', linkGroup: 'A' },
  'flight-chart': { badge: 'AIR', title: 'Gráfica aérea', description: 'Mediana por ruta', size: 'medium', linkGroup: 'B' },
  'data-quality': { badge: 'QA', title: 'Calidad de datos', description: 'Vigencia y límites', size: 'medium', linkGroup: 'none' },
};

function workspaceCopy(value) { return JSON.parse(JSON.stringify(value)); }

function defaultWorkspaceDraft(targetId) {
  return {
    id: null,
    name: 'Nuevo análisis',
    targetIds: [targetId],
    globalFilters: { links: { A: null, B: null, C: null }, captureAnchorSnapshotId: null, checkIn: null },
    layers: [
      { id: 'layer-default-kpis', type: 'market-kpis', size: 'wide', title: 'KPIs certificados', linkGroup: 'none' },
      { id: 'layer-default-hotels', type: 'hotel-table', size: 'wide', title: 'Tabla hotelera', linkGroup: 'A' },
      { id: 'layer-default-trend', type: 'hotel-trend', size: 'medium', title: 'Gráfica ADR', linkGroup: 'A' },
    ],
    version: null,
  };
}

function workspaceLayerId() {
  return `layer-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function activeWorkspaceDraft(workspaces, targetId) {
  if (State.workspaceDraft && State.workspaceDraftTargetId === targetId) return State.workspaceDraft;
  const matching = (workspaces || []).find((workspace) => (workspace.targetIds || []).includes(targetId)) || (workspaces || [])[0];
  State.workspaceDraft = matching ? workspaceCopy(matching) : defaultWorkspaceDraft(targetId);
  State.workspaceDraftTargetId = targetId;
  State.workspaceDirty = false;
  State.workspaceSaveError = '';
  return State.workspaceDraft;
}

function setWorkspaceDirty() {
  State.workspaceDirty = true;
  State.workspaceSaveError = '';
}

async function getWorkspaceRevisions(workspaceId, force = false) {
  if (!workspaceId) return [];
  if (!force && State.workspaceRevisions[workspaceId]) return State.workspaceRevisions[workspaceId];
  const payload = await api(`/api/workspaces/${workspaceId}/revisions`);
  State.workspaceRevisions[workspaceId] = payload.revisions || [];
  return State.workspaceRevisions[workspaceId];
}

function restoreWorkspaceRevision(revisionId) {
  const draft = State.workspaceDraft;
  if (!draft?.id || !Number.isInteger(Number(revisionId))) return;
  const revision = (State.workspaceRevisions[draft.id] || []).find((item) => item.id === Number(revisionId));
  if (!revision || revision.workspaceVersion === draft.version) return;
  Object.assign(draft, {
    name: revision.name,
    targetIds: workspaceCopy(revision.targetIds || []),
    globalFilters: workspaceCopy(revision.globalFilters || {}),
    layers: workspaceCopy(revision.layers || []),
  });
  setWorkspaceDirty();
  renderWorkspace();
}

function workspaceRevisionHistoryHTML(revisions, currentVersion) {
  if (!revisions.length) return '';
  const rows = revisions.map((revision) => {
    const current = revision.workspaceVersion === currentVersion;
    const label = current ? 'Versión actual' : `Restaurar versión ${revision.workspaceVersion}`;
    return `<li><div><strong>v${nEs(revision.workspaceVersion)}</strong><span>${esc(fmtStamp(revision.createdAt))} · ${nEs((revision.layers || []).length)} bloques</span></div><button type="button" class="btn btn--quiet" data-workspace-restore="${nEs(revision.id)}"${current ? ' disabled' : ''}>${label}</button></li>`;
  }).join('');
  return `<details class="workspace-revisions"><summary>Historial de versiones <span>${nEs(revisions.length)}</span></summary><p>Restaurar carga una versión como borrador; debes guardar para crear una nueva versión.</p><ol>${rows}</ol></details>`;
}

function workspaceContext(draft, captures) {
  const saved = draft.globalFilters && typeof draft.globalFilters === 'object' ? draft.globalFilters : {};
  const configuredAnchor = Number(saved.captureAnchorSnapshotId);
  const capture = (captures || []).find((item) => item.anchorSnapshotId === configuredAnchor) || (captures || [])[0] || null;
  const availableCheckIns = capture?.checkIns || [];
  const requestedCheckIn = typeof saved.checkIn === 'string' ? saved.checkIn : null;
  return {
    capture,
    anchorSnapshotId: capture?.anchorSnapshotId || null,
    checkIn: requestedCheckIn && availableCheckIns.includes(requestedCheckIn) ? requestedCheckIn : null,
    availableCheckIns,
  };
}

function setWorkspaceContext(field, value) {
  const draft = State.workspaceDraft;
  if (!draft) return;
  draft.globalFilters = { ...(draft.globalFilters || {}) };
  if (field === 'captureAnchorSnapshotId') {
    draft.globalFilters.captureAnchorSnapshotId = Number(value) || null;
    draft.globalFilters.checkIn = null;
  } else if (field === 'checkIn') {
    draft.globalFilters.checkIn = value || null;
  }
  setWorkspaceDirty();
  renderWorkspace();
}

async function getWorkspaceSemanticData(targetId, context) {
  if (!context.anchorSnapshotId) return null;
  const key = `${targetId}:${context.anchorSnapshotId}:${context.checkIn || 'all'}`;
  if (State.workspaceSemanticData[key]) return State.workspaceSemanticData[key];
  const filters = context.checkIn ? { checkIn: context.checkIn } : {};
  const payload = await api('/api/analytics/query', {
    method: 'POST',
    body: JSON.stringify({
      targetId,
      snapshotId: context.anchorSnapshotId,
      metrics: ['adr_mean', 'adr_median', 'hotel_count', 'adr_min', 'adr_max'],
      dimensions: ['hotel'],
      filters,
      limit: 500,
    }),
  });
  State.workspaceSemanticData[key] = payload;
  return payload;
}

function workspaceMetricValue(payload, metric) {
  return Number((payload?.values || []).find((item) => item.metric === metric)?.value);
}

function workspaceSemanticHotels(payload) {
  const marketAdr = workspaceMetricValue(payload, 'adr_mean');
  return (payload?.breakdown || []).map((item) => {
    const pricePerNight = Number((item.values || []).find((value) => value.metric === 'adr_mean')?.value);
    return {
      hotelKey: item.dimensions?.hotel,
      hotelName: item.labels?.hotel || item.dimensions?.hotel || 'Hotel no identificado',
      pricePerNight,
      gapVsMarketPct: Number.isFinite(pricePerNight) && marketAdr ? ((pricePerNight / marketAdr) - 1) * 100 : null,
    };
  }).filter((item) => item.hotelKey && Number.isFinite(item.pricePerNight)).sort((a, b) => b.pricePerNight - a.pricePerNight);
}

function workspaceContextHTML(context, semantic) {
  if (!context.capture) return '<div class="workspace-context empty">No hay extracciones disponibles para fijar el contexto del tablero.</div>';
  const captureLabel = context.capture.snapshotIds?.length > 1
    ? `fotos #${context.capture.snapshotIds[0]}–#${context.capture.snapshotIds.at(-1)}`
    : `foto #${context.anchorSnapshotId}`;
  const scope = context.checkIn ? `Entrada ${context.checkIn}` : 'Todas las entradas del barrido';
  const inferred = context.capture.kind === 'legacy_inferred_capture_group' ? ' · agrupación histórica inferida' : '';
  const population = semantic?.population;
  return `<section class="workspace-context" aria-label="Contexto común del tablero"><div><span class="nav-label">Contexto común</span><strong>${esc(scope)}</strong><small>${esc(captureLabel)} · observada ${esc(fmtStamp(context.capture.observedAt))}${esc(inferred)}</small></div><div class="workspace-context__fields"><label>Extracción<select class="input" data-workspace-context="captureAnchorSnapshotId">${(State.captureHistories[State.targetId]?.captures || []).map((capture) => `<option value="${nEs(capture.anchorSnapshotId)}"${capture.anchorSnapshotId === context.anchorSnapshotId ? ' selected' : ''}>${esc(fmtStamp(capture.observedAt))} · #${nEs(capture.snapshotIds?.[0])}–#${nEs(capture.snapshotIds?.at(-1))}</option>`).join('')}</select></label><label>Entrada<select class="input" data-workspace-context="checkIn"><option value="">Todas</option>${context.availableCheckIns.map((checkIn) => `<option value="${esc(checkIn)}"${checkIn === context.checkIn ? ' selected' : ''}>${esc(checkIn)}</option>`).join('')}</select></label></div><p>Aplicado a KPIs, tabla hotelera y gráfica ADR · ${population ? `${nEs(population.comparableRows)} observaciones comparables` : 'consulta pendiente'}</p></section>`;
}

function workspaceSelectionKey(targetId, linkGroup) { return `${targetId}:${linkGroup || 'none'}`; }

function workspaceHotelSelection(targetId, linkGroup) {
  if (!linkGroup || linkGroup === 'none') return null;
  return State.workspaceHotelSelections[workspaceSelectionKey(targetId, linkGroup)] || null;
}

function toggleWorkspaceHotelSelection(hotelKey, hotelName, linkGroup) {
  if (!hotelKey || !linkGroup || linkGroup === 'none') return;
  const key = workspaceSelectionKey(State.targetId, linkGroup);
  if (State.workspaceHotelSelections[key]?.hotelKey === hotelKey) delete State.workspaceHotelSelections[key];
  else State.workspaceHotelSelections[key] = { hotelKey, hotelName };
  renderWorkspace();
}

async function saveWorkspaceDraft() {
  const draft = State.workspaceDraft;
  if (!draft || !Number.isInteger(State.workspaceDraftTargetId)) return;
  if (State.workspaceSaving) return;
  const saveTargetId = State.workspaceDraftTargetId;
  const saveId = draft.id || null;
  const saveVersion = draft.version;
  const payload = {
    name: String(draft.name || '').trim() || 'Análisis sin título',
    targetIds: [...new Set([...(draft.targetIds || []), saveTargetId])],
    globalFilters: JSON.parse(JSON.stringify(draft.globalFilters || {})),
    layers: JSON.parse(JSON.stringify(draft.layers || [])),
  };
  if (saveId) payload.expectedVersion = saveVersion;
  State.workspaceSaving = true;
  try {
    const response = await api(saveId ? `/api/workspaces/${saveId}` : '/api/workspaces', {
      method: saveId ? 'PUT' : 'POST',
      body: JSON.stringify(payload),
    });
    if (State.workspaceDraftTargetId !== saveTargetId) return;
    State.workspaceDraft = response.workspace;
    delete State.workspaceRevisions[response.workspace.id];
    State.workspaceDirty = false;
    State.workspaceSaveError = '';
    renderWorkspace();
  } catch (error) {
    if (State.workspaceDraftTargetId !== saveTargetId) return;
    State.workspaceSaveError = error.status === 409
      ? 'Este tablero cambió en otra sesión. Recarga antes de guardar para no sobrescribir ese cambio.'
      : error.message;
    renderWorkspace();
  } finally {
    State.workspaceSaving = false;
  }
}

function addWorkspaceLayer(type) {
  const definition = WORKSPACE_BLOCK_LIBRARY[type];
  if (!definition || !State.workspaceDraft) return;
  if ((State.workspaceDraft.layers || []).length >= 40) { State.workspaceSaveError = 'Un tablero admite un máximo de 40 bloques.'; renderWorkspace(); return; }
  State.workspaceDraft.layers.push({
    id: workspaceLayerId(), type, size: definition.size, title: definition.title, linkGroup: definition.linkGroup,
  });
  setWorkspaceDirty();
  renderWorkspace();
}

function removeWorkspaceLayer(layerId) {
  if (!State.workspaceDraft || !layerId) return;
  State.workspaceDraft.layers = (State.workspaceDraft.layers || []).filter((layer) => layer.id !== layerId);
  setWorkspaceDirty();
  renderWorkspace();
}

function moveWorkspaceLayer(layerId, direction) {
  if (!State.workspaceDraft || !layerId) return;
  const layers = State.workspaceDraft.layers || [];
  const from = layers.findIndex((layer) => layer.id === layerId);
  const to = from + Number(direction);
  if (from < 0 || to < 0 || to >= layers.length) return;
  [layers[from], layers[to]] = [layers[to], layers[from]];
  setWorkspaceDirty();
  renderWorkspace();
}

async function renderWorkspace() {
  const host = mount('workspace');
  if (!Number.isInteger(State.targetId)) {
    renderNoActiveTarget(host, 'Espacio de trabajo', 'Pizarra de análisis del mercado activo.');
    return;
  }
  skeleton(host, 'list');
  const renderTargetId = State.targetId;
  let ws = null, m = null, revisions = [], captures = [], context = null, semantic = null;
  try {
    const [wr, mr, capturePayload] = await Promise.all([api('/api/workspaces'), getMetrics(renderTargetId), getCaptureHistory(renderTargetId)]);
    if (State.targetId !== renderTargetId) return;
    ws = activeWorkspaceDraft(wr.workspaces || [], renderTargetId); m = mr; captures = capturePayload.captures || [];
    context = workspaceContext(ws, captures);
    semantic = await getWorkspaceSemanticData(renderTargetId, context);
    if (State.targetId !== renderTargetId) return;
    revisions = ws.id ? await getWorkspaceRevisions(ws.id) : [];
    if (State.targetId !== renderTargetId) return;
  } catch (e) { if (State.targetId !== renderTargetId) return; host.innerHTML = `<div class="page">${pageHead('Espacio de trabajo', 'Pizarra', '')}<div class="inline-error">${esc(e.message)}</div></div>`; return; }

  const layers = ws.layers || [];
  const selectionGroups = [...new Set(layers.map((layer) => layer.linkGroup).filter((group) => group && group !== 'none'))];
  const selections = Object.fromEntries(selectionGroups.map((group) => [group, workspaceHotelSelection(renderTargetId, group)]));
  const selectionHistories = {};
  try {
    await Promise.all(Object.values(selections).filter(Boolean).map(async (selection) => {
      selectionHistories[selection.hotelKey] = await getHotelPriceHistory(renderTargetId, selection.hotelKey);
    }));
    if (State.targetId !== renderTargetId) return;
  } catch (_) { if (State.targetId !== renderTargetId) return; /* cada bloque expresa el error de su histórico sin bloquear el tablero */ }
  const blocks = layers.map((l, index) => renderLayer(l, m, selections, selectionHistories, index, layers.length, semantic, context)).join('');
  const saveLabel = State.workspaceDirty ? 'Cambios sin guardar' : 'Guardado';

  host.innerHTML = `<div class="workspace">
    <aside class="workspace__aside">
      <div>
        <div class="nav-label" style="padding:0 0 5px;">Composición</div>
        <h2>Fuentes y capas</h2>
        <p>Añade bloques al tablero. Los grupos de enlace se muestran sólo cuando el bloque declara una dimensión compatible.</p>
      </div>
      <div class="block-list">
        ${Object.entries(WORKSPACE_BLOCK_LIBRARY).map(([type, block]) => blockAdd(type, block)).join('')}
      </div>
      <div class="note-box"><strong>Enlaces seguros</strong>Hoteles por hotel y estancia; vuelos por ruta. No hay cruces many-to-many.</div>
    </aside>
    <section class="workspace__main">
      <div class="page-head" style="margin-bottom:18px;">
        <div>
          <div class="nav-label" style="padding:0 0 5px;">Pizarra personal</div>
          <div class="workspace-title-row">
            <label class="workspace-title-label"><span class="sr-only">Nombre del análisis</span><input id="workspaceName" value="${esc(ws.name)}" maxlength="120" aria-label="Nombre del análisis"></label>
            <span class="saved-chip${State.workspaceDirty ? ' is-dirty' : ''}"><i></i>${saveLabel}</span>
          </div>
        </div>
        <div class="workspace-actions"><button type="button" class="btn btn--quiet" data-workspace-ask data-workspace-anchor="${nEs(context?.anchorSnapshotId)}" data-workspace-checkin="${esc(context?.checkIn || '')}">Preguntar al Copilot</button><button type="button" class="btn btn--sm" id="workspaceSave"${State.workspaceDirty ? '' : ' disabled'}>Guardar cambios</button></div>
      </div>
      ${State.workspaceSaveError ? `<div class="inline-error workspace-save-error" role="alert">${esc(State.workspaceSaveError)}</div>` : ''}
      ${workspaceContextHTML(context, semantic)}
      ${workspaceRevisionHistoryHTML(revisions, ws.version)}
      <div class="board">${blocks || '<div class="empty workspace-empty">Añade un bloque para iniciar este análisis.</div>'}
        <article class="wblock wide" id="workspaceWeatherExample">
          <div class="wblock__head"><div class="lhs"><span class="badge">MET</span><strong>Cobertura meteorológica por mercado</strong></div><button type="button" class="btn btn--quiet" data-weather-market>Consultar ahora</button></div>
          <div class="empty">Agrupa hoteles cercanos y consulta una previsión por grupo geográfico.</div>
        </article>
      </div>
    </section>
  </div>`;
  runCounters(host);
  loadWorkspaceWeatherExample(host);
}

async function loadWorkspaceWeatherExample(host) {
  const card = $('#workspaceWeatherExample', host);
  if (!card) return;
  const button = $('[data-weather-market]', card);
  const renderMarketWeather = async () => {
   if (button) { button.disabled = true; button.textContent = 'Consultando…'; }
    try {
    const payload = await api(`/api/weather/market-example?targetId=${encodeURIComponent(State.targetId)}`);
    const summaries = payload.snapshots || [];
    const known = (payload.assignments || []).filter((item) => item.knownAtMarketCapture).length;
    const association = await api(`/api/analytics/weather-price-association?targetId=${encodeURIComponent(State.targetId)}&snapshots=12`).catch(() => null);
    const associationLabel = association?.status === 'ready' ? `${nEs(association.samplePairs)} pares` : 'Muestra insuficiente';
    card.innerHTML = `<div class="wblock__head"><div class="lhs"><span class="badge">MET</span><strong>Cobertura meteorológica por mercado</strong></div><span class="link-badge">Open-Meteo</span></div>
      <p class="dim" style="margin:0 0 12px;">${nEs(payload.hotelCount)} hoteles · ${nEs(payload.hotelsWithCoordinates)} con coordenadas · ${nEs(payload.geographicGroups)} grupos · ${nEs(payload.weatherRequests)} peticiones</p>
      <div class="mini-kpis" style="grid-template-columns:repeat(4,1fr);">${miniKpi('Asignaciones', nEs((payload.assignments || []).length))}${miniKpi('Grupos guardados', nEs(summaries.length))}${miniKpi('Conocidas en foto', nEs(known))}${miniKpi('Asociación', associationLabel)}</div>
      <small class="dim">Foto de mercado #${esc(payload.marketSnapshotId)} · Las consultas posteriores se marcan como enriquecimiento posterior. La asociación no demuestra demanda ni causalidad.</small>`;
   } catch (error) {
    card.innerHTML = `<div class="wblock__head"><div class="lhs"><span class="badge">MET</span><strong>Cobertura meteorológica por mercado</strong></div></div><div class="inline-error">${esc(error.message)}</div>`;
   }
  };
  button?.addEventListener('click', renderMarketWeather, { once: true });
}

function blockAdd(type, block) {
  return `<button type="button" class="block-add" data-workspace-add="${esc(type)}"><span class="badge">${esc(block.badge)}</span><span class="t"><strong>${esc(block.title)}</strong><small>${esc(block.description)}</small></span><span aria-hidden="true">+</span></button>`;
}

function renderLayer(l, m, selections = {}, selectionHistories = {}, index = 0, layerCount = 0, semantic = null, context = null) {
  const badge = { 'market-kpis': 'KPI', 'hotel-table': 'TAB', 'hotel-trend': 'LIN', 'flight-table': 'AIR', 'flight-chart': 'AIR', 'data-quality': 'QA' }[l.type] || '·';
  const link = l.linkGroup && l.linkGroup !== 'none' ? `<span class="link-badge">Enlace ${l.linkGroup}</span>` : '';
  const wide = l.size === 'wide' ? ' wide' : '';
  let inner = '';
  const market = m.market || {}, rs = m.rateShoppingIndex || {}, dq = m.dataQuality || {};
  const scopedHotels = workspaceSemanticHotels(semantic);
  const cs = scopedHotels.length ? scopedHotels : (m.competitiveSet || []);
  const selectedHotel = selections[l.linkGroup] || null;
  if (l.type === 'market-kpis') {
    if (semantic) {
      const minimum = workspaceMetricValue(semantic, 'adr_min');
      const maximum = workspaceMetricValue(semantic, 'adr_max');
      inner = `<div class="mini-kpis">
        ${miniKpi('ADR mediano', eur(workspaceMetricValue(semantic, 'adr_median')))}
        ${miniKpi('Rango ADR', `${eur(minimum)} — ${eur(maximum)}`)}
        ${miniKpi('Cobertura', `${nEs(semantic.population?.comparablePct || 0)}%`)}
        ${miniKpi('Comparables', nEs(semantic.population?.comparableRows || 0))}
      </div>`;
    } else {
      inner = `<div class="mini-kpis">
        ${miniKpi('Mediana', eur(market.medianPricePerNight))}
        ${miniKpi('IQR', eur((rs.topQuartileThreshold || 0) - (rs.bottomQuartileThreshold || 0)))}
        ${miniKpi('Cobertura', `${nEs(dq.comparablePct || 0)}%`)}
        ${miniKpi('Comparables', nEs(dq.comparableRows || 0))}
      </div>`;
    }
  } else if (l.type === 'hotel-table') {
    const selectable = l.linkGroup && l.linkGroup !== 'none';
    inner = `<table class="t workspace-hotel-table"><tbody>${cs.slice(0, 4).map((h) => `<tr class="${selectedHotel?.hotelKey === h.hotelKey ? 'is-selected' : ''}"><td class="name" style="padding:0;">${selectable && h.hotelKey ? `<button type="button" class="workspace-hotel-select" data-workspace-hotel="${esc(h.hotelKey)}" data-workspace-hotel-name="${esc(h.hotelName)}" data-workspace-link="${esc(l.linkGroup)}" aria-pressed="${selectedHotel?.hotelKey === h.hotelKey ? 'true' : 'false'}">${esc(h.hotelName)}</button>` : esc(h.hotelName)}</td><td class="num" style="padding:9px 0;">${eur(h.pricePerNight)}</td><td class="num" style="padding:9px 0 9px 12px; color:var(--ac);">${signPct(h.gapVsMarketPct)}</td></tr>`).join('')}</tbody></table>`;
  } else if (l.type === 'hotel-trend') {
    const selectedHistory = selectedHotel ? selectionHistories[selectedHotel.hotelKey] : null;
    const scopedHistory = context?.checkIn ? (selectedHistory || []).filter((entry) => entry.checkIn === context.checkIn) : selectedHistory;
    inner = selectedHotel
      ? `<div class="workspace-selection-note">Hotel seleccionado · <strong>${esc(selectedHotel.hotelName)}</strong>${context?.checkIn ? ` · entrada ${esc(context.checkIn)}` : ''}</div>${scopedHistory?.length ? dashboardHotelTrendHTML({ hotelName: selectedHotel.hotelName, currency: 'EUR' }, scopedHistory, 620) : '<div class="dashboard-trend-empty">No hay histórico del hotel para la fecha de entrada seleccionada.</div>'}`
      : (() => {
        const pts = (m.trend || []).filter((t) => t.avgPricePerNight != null && t.currency === 'EUR').map((t) => ({ v: t.avgPricePerNight }));
        return pts.length >= 2 ? `${lineSVG(pts)}<small>Selecciona un hotel de la tabla enlazada para comparar dos extracciones por fecha de entrada.</small>` : '<div class="empty">Se necesitan dos fotos con tarifa por noche en EUR.</div>';
      })();
  } else if (l.type === 'flight-chart' || l.type === 'flight-table') {
    const routes = (State.air ? State.air.routes : []).slice(0, 5).map((r) => ({ v: r.avg_price }));
    inner = routes.length ? lineSVG(routes) : `<div class="empty" style="height:120px;">Captura vuelos para ver esta gráfica.</div>`;
  } else if (l.type === 'data-quality') {
    const population = semantic?.population;
    inner = `<div class="mini-kpis" style="grid-template-columns:repeat(2,1fr);">
      ${miniKpi('Filas', nEs(population?.totalRows ?? dq.totalRows ?? 0))}
      ${miniKpi('Con precio', nEs(population?.pricedRows ?? dq.pricedRows ?? 0))}
    </div>${(dq.notes || []).slice(0, 2).map((n) => `<p style="margin:10px 0 0; font-size:11.5px; color:var(--muted);">${esc(n)}</p>`).join('')}`;
  }
  return `<article class="wblock${wide}">
    <div class="wblock__head"><div class="lhs"><span class="badge">${badge}</span><strong>${esc(l.title)}</strong></div><div class="wblock__tools">${link}<div class="workspace-layer-order" role="group" aria-label="Orden de ${esc(l.title)}"><button type="button" class="icon-btn workspace-layer-move" data-workspace-move="${esc(l.id || '')}" data-workspace-direction="-1" aria-label="Subir ${esc(l.title)}"${index === 0 ? ' disabled' : ''}>↑</button><button type="button" class="icon-btn workspace-layer-move" data-workspace-move="${esc(l.id || '')}" data-workspace-direction="1" aria-label="Bajar ${esc(l.title)}"${index === layerCount - 1 ? ' disabled' : ''}>↓</button></div><button type="button" class="icon-btn workspace-layer-remove" data-workspace-remove="${esc(l.id || '')}" aria-label="Quitar ${esc(l.title)}">×</button></div></div>
    ${inner}
  </article>`;
}
function miniKpi(k, v) { return `<div class="mini-kpi"><div class="k">${esc(k)}</div><strong>${v}</strong></div>`; }

/* ================================================================= CAPTURA */
function captureProfileHTML(profile) {
  if (!profile) return 'Sin perfil verificable';
  const quality = profile.captureQuality;
  const qualityText = quality ? (() => {
    const captured = quality.capturedRows ?? '—';
    const expected = quality.expectedRows ?? '—';
    const pct = quality.coveragePct == null ? '' : ` · ${nEs(quality.coveragePct, 1)}%`;
    const label = {complete: 'Cobertura completa', sampled: 'Muestra limitada', partial: 'Cobertura parcial', empty: 'Sin hoteles recibidos', unknown: 'Cobertura no verificable'}[quality.status] || 'Cobertura no verificable';
    const pages = quality.pagesFailed > 0 ? ` · ${nEs(quality.pagesFailed)} página(s) fallida(s)` : '';
    const block = quality.blockDetected ? ' · bloqueo detectado' : '';
    return ` · ${label} (${captured}/${expected}${pct}${pages}${block})`;
  })() : '';
  return `${esc(profile.checkIn || 'Entrada desconocida')} → ${esc(profile.checkOut || 'Salida desconocida')} · ${profile.adults ?? '—'} adultos · ${profile.children ?? '—'} niños · ${profile.rooms ?? '—'} habitaciones · ${esc(profile.currency || 'Moneda solicitada desconocida')} · ${profile.origin === 'legacy_url' ? 'Reconstruido de URL histórica' : 'Parámetros efectivos guardados'}${qualityText}`;
}

async function launchCapture() {
  const btn = $('#launchCapture'); if (!btn || btn.disabled) return;
  const t = activeTarget(); if (!t) return;
  if (State.captureJob) { toast('Ya hay una captura en curso.', 'info'); return; }
  const limit = Math.max(1, Math.min(500, parseInt($('#capLimit').value, 10) || 200));
  for (const id of ['capCheckIn', 'capNights', 'capAdults', 'capRooms']) {
    if (!$('#' + id).reportValidity()) return;
  }
  const profile = {checkIn: $('#capCheckIn').value, nights: Number($('#capNights').value),
    adults: Number($('#capAdults').value), rooms: Number($('#capRooms').value), children: 0,
    currency: 'EUR', board: $('#capBoard').value};
  const arrivalWeeks = Number($('#capWeeks').value);
  const log = $('#captureLog'); const worker = $('#workerState');
  btn.disabled = true; btn.textContent = 'Captura en curso…';
  worker.innerHTML = '<i></i>worker activo';
  const stamp = () => new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const push = (html) => { log.insertAdjacentHTML('beforeend', `<div>[${stamp()}] ${html}</div>`); log.scrollTop = log.scrollHeight; };
  log.innerHTML = ''; push(`Lanzando captura de <span class="ok">${esc(t.name)}</span> · ${arrivalWeeks} foto(s) · entrada ${esc(profile.checkIn)} · ${profile.nights} noches · límite ${limit}`);
  try {
    const r = await api('/api/jobs/hotel-capture', { method: 'POST', body: JSON.stringify({ targetId: t.id, url: t.url, limit, profile, arrivalWeeks }) });
    const jobId = r.job && r.job.id;
    State.captureJob = { id: jobId, pct: 1, targetId: t.id };
    setCaptureProgress(1);
    push(`job#${jobId} <span class="ok">encolado</span> · esperando al worker`);
    await pollJob(jobId, push, worker, t.id);
  } catch (e) {
    push(`<span class="warn">error</span> ${esc(e.message)}`);
    worker.innerHTML = '<i style="background:#e7bd5f;"></i>worker con error';
  } finally {
    btn.disabled = false; btn.textContent = 'Lanzar captura · Booking.com';
  }
}

async function pollJob(jobId, push, worker, targetId) {
  let tries = 0;
  return new Promise((resolve) => {
    const tick = async () => {
      tries++;
      try {
        const r = await api(`/api/jobs/${jobId}`);
        const j = r.job || {};
        if (j.status === 'succeeded' || j.status === 'completed') {
          push(`job#${jobId} <span class="ok">completado</span> · snapshot guardado`);
          push('<span class="done">listo <span class="caret">▊</span></span>');
          worker.innerHTML = '<i></i>worker inactivo';
          void finishCapture(targetId, true);
          renderCaptures(); resolve(); return;
        }
        if (j.status === 'failed' || j.status === 'error') {
          push(`job#${jobId} <span class="warn">falló</span> · ${esc(j.error || 'sin detalle')}`);
          worker.innerHTML = '<i style="background:#e7bd5f;"></i>worker con error';
          void finishCapture(targetId, false, j.error); resolve(); return;
        }
        if (State.captureJob && State.captureJob.id === jobId) { State.captureJob.pct = Number(j.progress) || State.captureJob.pct; setCaptureProgress(State.captureJob.pct); }
        if (tries % 3 === 0) push(`job#${jobId} · ${esc(j.message || j.status || 'en curso')}…`);
      } catch (e) { push(`<span class="warn">poll</span> ${esc(e.message)}`); }
      if (tries > 2880) { push('<span class="warn">seguimiento detenido</span> · el trabajo puede continuar; revisa su estado antes de lanzar otra captura'); State.captureJob = null; setCaptureProgress(null); resolve(); return; }
      setTimeout(tick, 2500);
    };
    setTimeout(tick, 1500);
  });
}

/* ================================================================ CHROME */
const ICON_MOON = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"></path></svg>';
const ICON_SUN = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="4"></circle><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"></path></svg>';

function applyTheme(theme, persist = true) {
  State.theme = THEMES.includes(theme) ? theme : 'claro';
  const dark = State.theme === 'oscuro';
  if (dark) document.documentElement.dataset.theme = 'oscuro'; else document.documentElement.removeAttribute('data-theme');
  $('meta[name="theme-color"]')?.setAttribute('content', dark ? '#0e1014' : '#f5f6f9');
  if ($('#themeBtn')) {
    $('#themeLabel').textContent = dark ? 'Tema claro' : 'Tema oscuro';
    $('#themeIcon').innerHTML = dark ? ICON_SUN : ICON_MOON;
  }
  if (persist) writePref(PREFS.theme, State.theme);
  restyleMaps();
}
function toggleTheme() { applyTheme(State.theme === 'oscuro' ? 'claro' : 'oscuro'); }

function applyDensity(density, persist = true) {
  State.density = DENSITIES.includes(density) ? density : 'equilibrada';
  document.body.dataset.density = State.density;
  if (persist) writePref(PREFS.density, State.density);
}

function applySidebar(collapsed, persist = true) {
  State.sidebarCollapsed = Boolean(collapsed);
  document.body.classList.toggle('is-sidebar-collapsed', State.sidebarCollapsed);
  const button = $('#collapseBtn');
  if (button) {
    const label = State.sidebarCollapsed ? 'Expandir barra lateral' : 'Contraer barra lateral';
    button.setAttribute('aria-label', label);
    button.setAttribute('aria-expanded', String(!State.sidebarCollapsed));
    button.title = label;
  }
  if (persist) writePref(PREFS.sidebar, State.sidebarCollapsed ? 'contraida' : 'expandida');
  setTimeout(() => State.dashboardMap?.resize(), 300);
}
function toggleSidebar() { applySidebar(!State.sidebarCollapsed); }

function applyPreferences() {
  applyDensity(readPref(PREFS.density, DENSITIES, 'equilibrada'), false);
  applySidebar(readPref(PREFS.sidebar, ['expandida', 'contraida'], 'expandida') === 'contraida', false);
  applyTheme(readPref(PREFS.theme, THEMES, 'claro'), false);
}

/* avisos emergentes */
function toast(message, kind = 'info', ms = TOAST_MS) {
  const host = $('#toasts');
  if (!host) return;
  const el = document.createElement('div');
  el.className = `toast toast--${kind}`;
  el.innerHTML = `<i aria-hidden="true"></i><span>${esc(message)}</span>`;
  host.appendChild(el);
  setTimeout(() => el.remove(), ms);
  while (host.children.length > 4) host.firstElementChild.remove();
}

/* capas modales (paleta y confirmación de captura) */
function overlayFocusable(overlay) {
  return [...overlay.querySelectorAll('button, input, select, textarea, [href]')].filter((el) => !el.disabled && el.offsetParent !== null && el.tabIndex >= 0);
}
function openOverlay(id, focusSelector) {
  const overlay = $(`#${id}`);
  if (!overlay || !overlay.hidden) return;
  State.overlayReturnFocus = document.activeElement;
  overlay.hidden = false;
  $('.atlas-root')?.setAttribute('inert', '');
  if (!overlay.dataset.trapWired) {
    overlay.addEventListener('keydown', (event) => {
      if (event.key !== 'Tab') return;
      const items = overlayFocusable(overlay);
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      else if (!items.includes(document.activeElement)) { event.preventDefault(); first.focus(); }
    });
    overlay.addEventListener('mousedown', (event) => { if (event.target === overlay) { if (id === 'sidePanel') closeSidePanel(); else closeOverlay(id); } });
    overlay.dataset.trapWired = '1';
  }
  ($(focusSelector, overlay) || overlayFocusable(overlay)[0])?.focus();
}
function closeOverlay(id, { restoreFocus = true } = {}) {
  const overlay = $(`#${id}`);
  if (!overlay || overlay.hidden) return false;
  overlay.hidden = true;
  if (!$('.overlay:not([hidden])')) $('.atlas-root')?.removeAttribute('inert');
  const previous = State.overlayReturnFocus;
  State.overlayReturnFocus = null;
  if (restoreFocus && previous && previous.isConnected) previous.focus();
  return true;
}

/* selector de mercado */
function marketHotelCount(id) {
  const rows = State.snapshots[id]?.latest?.rows;
  return rows ? new Set(rows.map((row) => row.hotelKey)).size : null;
}
function renderMarketList() {
  const active = activeTarget();
  $('#marketName').textContent = active ? active.name : 'Sin mercado';
  $('#marketBtn').title = active ? `Mercado: ${active.name}` : 'Sin mercados';
  $('#marketMenu').innerHTML = State.targets.map((t) => {
    const count = marketHotelCount(t.id);
    return `<button type="button" class="market-menu__item ${t.id === State.targetId ? 'is-active' : ''}" role="menuitemradio" aria-checked="${t.id === State.targetId}" data-market="${t.id}">
      <span>${esc(t.name)}</span>${count == null ? '' : `<small>${count} htl</small>`}</button>`;
  }).join('');
  $('#sessionMeta').textContent = `${State.targets.length} ${State.targets.length === 1 ? 'mercado' : 'mercados'}`;
}
async function openMarketMenu() {
  const menu = $('#marketMenu'), button = $('#marketBtn');
  if (!State.targets.length) return;
  menu.hidden = false;
  button.setAttribute('aria-expanded', 'true');
  ($('.market-menu__item.is-active', menu) || $('.market-menu__item', menu))?.focus();
  // los recuentos de hoteles de los demás mercados se cargan al abrir, no en el arranque
  const missing = State.targets.filter((t) => !State.snapshots[t.id]);
  if (missing.length) {
    await Promise.allSettled(missing.map((t) => getSnapshot(t.id)));
    if (!menu.hidden) { const focused = document.activeElement?.dataset?.market; renderMarketList(); if (focused) $(`.market-menu__item[data-market="${focused}"]`, menu)?.focus(); }
  }
}
function closeMarketMenu(restoreFocus = false) {
  const menu = $('#marketMenu');
  if (!menu || menu.hidden) return false;
  menu.hidden = true;
  $('#marketBtn').setAttribute('aria-expanded', 'false');
  if (restoreFocus) $('#marketBtn').focus();
  return true;
}
function toggleMarketMenu() {
  if (State.sidebarCollapsed) { applySidebar(false); void openMarketMenu(); return; }
  if ($('#marketMenu').hidden) void openMarketMenu(); else closeMarketMenu();
}

/* barra superior: ticker, antigüedad de los datos e insignia de señales */
function renderTicker(metrics) {
  const host = $('#ticker');
  const moved = ((metrics && metrics.competitiveSet) || []).filter((h) => h.priceChangePct != null && Number(h.priceChangePct) !== 0);
  if (!moved.length) { host.innerHTML = ''; return; }
  const inner = moved.map((h) => {
    const delta = Number(h.priceChangePct);
    return `<button type="button" class="ticker__item" data-ticker-hotel="${esc(h.hotelName)}"><span>${esc(h.hotelName)}</span><b>${eur(h.pricePerNight)}</b><span class="${delta > 0 ? 'up' : 'down'}">${delta > 0 ? '▲' : '▼'}${nEs(Math.abs(delta), 1)}%</span></button>`;
  }).join('');
  host.innerHTML = `<div class="ticker__group">${inner}</div><div class="ticker__group" aria-hidden="true">${inner.replace(/<button /g, '<button tabindex="-1" ')}</div>`;
}

function dataAgeDays(iso) {
  const ts = Date.parse(iso || '');
  return Number.isNaN(ts) ? null : Math.max(0, Math.floor((Date.now() - ts) / 86400000));
}
function renderDataAge(metrics) {
  const pill = $('#dataAge');
  if (!pill) return;
  if (!Number.isInteger(State.targetId)) { pill.hidden = true; return; }
  const snapshot = metrics && metrics.latestSnapshot;
  const at = (snapshot && snapshot.scrapedAt) || null;
  State.lastExtractionAt = at;
  const days = dataAgeDays(at);
  const fresh = days === 0 && State.freshCaptureTargetId === State.targetId;
  const label = fresh ? 'Actualizado · ahora' : days == null ? 'Sin capturas' : days === 0 ? 'Datos de hoy' : `Datos de hace ${days} ${days === 1 ? 'día' : 'días'}`;
  pill.hidden = false;
  pill.className = `data-age${fresh ? ' data-age--fresh' : ''}`;
  pill.dataset.fresh = fresh ? 'true' : 'false';
  pill.innerHTML = `<i aria-hidden="true"></i>${esc(label)}`;
  pill.title = fresh ? `Foto #${snapshot.id} · ${new Date(at).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' })}` : at ? `Última extracción ${fmtStamp(at)} · pulsa para capturar` : 'Sin capturas · pulsa para capturar';
  pill.setAttribute('aria-label', `${label}. ${pill.title}`);
}

function renderNavBadge(metrics) {
  const badge = $('#navBadgeDashboard');
  if (!badge) return;
  const attention = ((metrics && metrics.insights) || []).filter((item) => item.severity === 'warning' || item.severity === 'critical').length;
  badge.hidden = attention === 0;
  badge.textContent = String(attention);
  badge.title = `${attention} ${attention === 1 ? 'señal requiere' : 'señales requieren'} atención`;
  badge.setAttribute('aria-label', badge.title);
}

async function renderChromeData() {
  const targetId = State.targetId;
  let metrics = null;
  if (Number.isInteger(targetId)) { try { metrics = await getMetrics(targetId); } catch (_) { metrics = null; } }
  if (targetId !== State.targetId) return;
  renderTicker(metrics);
  renderDataAge(metrics);
  renderNavBadge(metrics);
}

function selectMarket(id) {
  id = Number(id);
  if (id === State.targetId) return;
  State.targetId = id;
  State.selectedPhotoId = null;
  State.captureHotelSearch = '';
  State.captureComparisonOpen = false;
  State.hotelQueryTargetId = null;
  renderMarketList();
  void renderChromeData();
  // recarga la vista actual con el nuevo mercado (todas las vistas dependen del mercado), desde arriba
  window.scrollTo(0, 0);
  renderView(State.view);
}

/* saltos entre vistas */
function askCopilot(text) {
  State.copilotPrompt = String(text || '').trim() || null;
  setView('copilot');
}

/* captura del mercado activo con los parámetros de la última foto */
function localIsoDate(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}
function shortIsoDate(iso) {
  const [y, m, d] = String(iso || '').split('-');
  return y && m && d ? `${d}/${m}/${y}` : '—';
}
function reusableCaptureProfile(latest) {
  const snapshot = latest && latest.snapshot;
  const profile = snapshot && snapshot.captureProfile;
  if (!profile || !profile.checkIn) return { reason: 'La última foto no guarda los parámetros de captura.' };
  const checkIn = String(profile.checkIn).slice(0, 10);
  if (checkIn < localIsoDate()) return { reason: `La entrada de la última captura (${shortIsoDate(checkIn)}) ya ha pasado.` };
  const nights = Number(profile.nights), adults = Number(profile.adults);
  if (!(nights >= 1 && nights <= 30) || !(adults >= 1 && adults <= 10) || Number(profile.rooms || 1) !== 1 || Number(profile.children || 0) !== 0) {
    return { reason: 'Los parámetros de la última captura no admiten una captura rápida.' };
  }
  const filters = [].concat(profile.filters || []).join(';');
  const board = /mealplan=4/.test(filters) ? 'all_inclusive' : 'saved_filters';
  const limit = Math.max(1, Math.min(500, Number(snapshot.requestedLimit) || 120));
  return { profile: { checkIn, nights, adults, rooms: 1, children: 0, currency: 'EUR', board }, limit };
}

function setCaptureProgress(pct) {
  const button = $('#captureTop');
  if (!button) return;
  const running = pct != null;
  button.classList.toggle('is-running', running);
  $('#captureFill').style.width = running ? `${Math.max(2, Math.min(100, pct))}%` : '0';
  $('#captureLabel').textContent = running ? `Capturando ${Math.round(pct)}%` : 'Capturar';
  button.setAttribute('aria-label', running ? `Captura en curso, ${Math.round(pct)} %` : 'Capturar mercado activo');
}

async function openCaptureDialog() {
  if (!Number.isInteger(State.targetId)) { toast('No hay ningún mercado activo para capturar.', 'warn'); return; }
  if (State.captureJob) { toast('Ya hay una captura en curso.', 'info'); return; }
  const target = activeTarget();
  let latest = null;
  try { latest = (await getSnapshot(State.targetId)).latest; } catch (_) { latest = null; }
  const plan = reusableCaptureProfile(latest);
  if (!plan.profile) {
    toast(`${plan.reason} Configura la captura en Capturas.`, 'warn');
    setView('captures');
    return;
  }
  const p = plan.profile;
  State.captureDialogParams = { targetId: State.targetId, url: target.url, limit: plan.limit, profile: p };
  const end = new Date(`${p.checkIn}T00:00:00`); end.setDate(end.getDate() + p.nights);
  const rows = [
    ['Mercado', esc(target.name)],
    ['Entrada', `${shortIsoDate(p.checkIn)} → ${shortIsoDate(localIsoDate(end))}`],
    ['Noches', String(p.nights)],
    ['Adultos', String(p.adults)],
    ['Régimen', p.board === 'all_inclusive' ? 'Todo incluido' : 'Filtros guardados'],
    ['Límite de hoteles', String(plan.limit)],
    ['Fotos', '1'],
  ];
  $('#captureDialogText').textContent = 'Se repetirá la última captura de este mercado con los mismos parámetros. La extracción consulta Booking.';
  $('#captureDialogParams').innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
  openOverlay('captureDialog', '#captureConfirm');
}

function invalidateTargetData(targetId) {
  delete State.snapshots[targetId]; delete State.metrics[targetId]; delete State.demandCurves[targetId]; delete State.hotelStability[targetId]; delete State.photoHistories[targetId]; delete State.captureHistories[targetId];
  delete State.hotelPriceHistories[targetId]; delete State.hotelRateDetails[targetId];
  if (State.bi && State.bi.targetId === targetId) State.bi.data = null;
  State.workspaceSemanticData = {};
  State.selectedPhotoId = null; State.captureHotelSearch = ''; State.captureComparisonOpen = false;
}

async function confirmCapture() {
  const params = State.captureDialogParams;
  const button = $('#captureConfirm');
  if (!params || !button || button.disabled) return;
  button.disabled = true;
  try {
    const r = await api('/api/jobs/hotel-capture', { method: 'POST', body: JSON.stringify({ targetId: params.targetId, url: params.url, limit: params.limit, profile: params.profile, arrivalWeeks: 1 }) });
    closeOverlay('captureDialog');
    State.captureDialogParams = null;
    const jobId = r.job && r.job.id;
    if (!jobId) { toast('El servidor no devolvió el identificador del trabajo.', 'warn'); return; }
    toast(`Captura en cola · ${activeTarget() ? activeTarget().name : 'mercado activo'} · Booking.com`, 'info');
    void trackCaptureJob(jobId, params.targetId);
  } catch (error) {
    toast(error.message || 'No se pudo iniciar la captura.', 'warn', 6000);
  } finally {
    button.disabled = false;
  }
}

/* Cierra el ciclo de una captura: datos nuevos, avisos y barra superior al día. */
async function finishCapture(targetId, succeeded, detail) {
  State.captureJob = null;
  setCaptureProgress(null);
  if (!succeeded) { toast(detail ? `La captura falló: ${detail}` : 'La captura falló.', 'warn', 6000); return; }
  invalidateTargetData(targetId);
  State.freshCaptureTargetId = targetId;
  let message = 'Captura completada';
  try {
    const latest = (await getSnapshot(targetId, true)).latest;
    const rows = latest.rows || [];
    const priced = new Set(rows.filter((row) => row.pricePerNight > 0).map((row) => row.hotelKey)).size;
    message = `Foto #${latest.snapshot.id} guardada · ${priced} ${priced === 1 ? 'hotel' : 'hoteles'} con tarifa`;
  } catch (_) { /* el aviso genérico basta si no se pueden releer los datos */ }
  toast(message, 'ok');
  renderMarketList();
  if (targetId === State.targetId) void renderChromeData();
}

async function trackCaptureJob(jobId, targetId) {
  State.captureJob = { id: jobId, pct: 1, targetId };
  setCaptureProgress(1);
  let misses = 0;
  for (let tries = 0; tries < 2880; tries++) {
    await new Promise((resolve) => setTimeout(resolve, 2500));
    try {
      const job = (await api(`/api/jobs/${jobId}`)).job || {};
      misses = 0;
      if (job.status === 'succeeded' || job.status === 'completed') {
        await finishCapture(targetId, true);
        if (targetId === State.targetId) renderView(State.view);
        return;
      }
      if (job.status === 'failed' || job.status === 'error' || job.status === 'cancelled') {
        await finishCapture(targetId, false, job.error || job.message);
        return;
      }
      State.captureJob.pct = Number(job.progress) || State.captureJob.pct;
      setCaptureProgress(State.captureJob.pct);
    } catch (_) {
      if (++misses >= 5) { State.captureJob = null; setCaptureProgress(null); toast('Se perdió el seguimiento de la captura; el trabajo puede continuar. Revisa Capturas antes de lanzar otra.', 'warn', 7000); return; }
    }
  }
  State.captureJob = null; setCaptureProgress(null);
  toast('Seguimiento detenido: el trabajo puede continuar. Revisa su estado antes de lanzar otra captura.', 'warn', 7000);
}

/* paleta de comandos ⌘K */

const PALETTE_VIEW_GROUPS = { dashboard: 'Análisis', hotels: 'Análisis', reputation: 'Análisis', flights: 'Análisis', copilot: 'Herramientas', workspace: 'Herramientas', captures: 'Herramientas' };

function paletteGroups(rawQuery) {
  const query = rawQuery.trim();
  const q = normalizeText(query);
  const match = (label) => !q || normalizeText(label).includes(q);
  const metrics = State.metrics[State.targetId];
  const hotels = q && metrics ? (metrics.competitiveSet || []).filter((h) => match(h.hotelName)).slice(0, 6)
    .map((h) => ({ tag: 'HTL', label: h.hotelName, hint: eur(h.pricePerNight), run: () => openHotelInHotels(h.hotelName) })) : [];
  const views = VIEWS.filter((view) => match(LABELS[view]))
    .map((view) => ({ tag: 'IR', label: LABELS[view], hint: PALETTE_VIEW_GROUPS[view], run: () => setView(view) }));
  const actions = [
    { tag: 'CAP', label: 'Capturar mercado activo', hint: 'Booking', run: () => { void openCaptureDialog(); } },
    { tag: 'AI', label: query ? `Preguntar al Copilot: «${query}»` : 'Preguntar al Copilot', hint: '⌘O', ask: true, run: () => askCopilot(query) },
    { tag: 'UI', label: State.theme === 'oscuro' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro', hint: 'Tema', run: toggleTheme },
    { tag: 'UI', label: 'Densidad compacta', hint: 'Tablas', run: () => applyDensity('compacta') },
    { tag: 'UI', label: 'Densidad equilibrada', hint: 'Tablas', run: () => applyDensity('equilibrada') },
    { tag: 'UI', label: State.sidebarCollapsed ? 'Expandir barra lateral' : 'Contraer barra lateral', hint: 'Navegación', run: toggleSidebar },
    // solo existe cuando el entorno exige contraseña (producción): sustituye al antiguo botón del pie
    ...(State.authRequired ? [{ tag: 'UI', label: 'Bloquear sesión', hint: 'Sesión', run: () => { void lockSession(); } }] : []),
  ].filter((action) => match(action.label) || (action.ask && q));
  // con una consulta escrita, «Preguntar al Copilot» va al final para que Enter ejecute antes la acción que coincide
  if (q) actions.sort((a, b) => Number(Boolean(a.ask)) - Number(Boolean(b.ask)));
  return [{ label: 'Hoteles', items: hotels }, { label: 'Ir a', items: views }, { label: 'Acciones', items: actions }].filter((g) => g.items.length);
}

function renderPalette() {
  const list = $('#paletteList');
  const query = State.palette.query;
  const groups = paletteGroups(query);
  const flat = groups.flatMap((group) => group.items);
  State.palette.items = flat;
  State.palette.index = Math.min(State.palette.index, Math.max(0, flat.length - 1));
  let i = 0;
  list.innerHTML = flat.length ? groups.map((group) => `<div role="group" aria-label="${esc(group.label)}"><div class="palette__group" aria-hidden="true">${esc(group.label)}</div>${group.items.map((item) => {
    const index = i++;
    return `<button type="button" class="palette__item ${index === State.palette.index ? 'is-active' : ''}" role="option" id="paletteItem${index}" aria-selected="${index === State.palette.index}" tabindex="-1" data-palette-index="${index}"><span class="palette__tag" aria-hidden="true">${item.tag}</span><span class="palette__label">${esc(item.label)}</span>${item.hint ? `<span class="palette__hint">${esc(item.hint)}</span>` : ''}</button>`;
  }).join('')}</div>`).join('') : `<div class="palette__empty">Sin resultados para «${esc(query)}»</div>`;
  const input = $('#paletteInput');
  if (flat.length) input.setAttribute('aria-activedescendant', `paletteItem${State.palette.index}`); else input.removeAttribute('aria-activedescendant');
}

function setPaletteIndex(index, scroll = true) {
  const count = State.palette.items.length;
  if (!count) return;
  State.palette.index = Math.max(0, Math.min(count - 1, index));
  $$('.palette__item').forEach((el) => {
    const active = Number(el.dataset.paletteIndex) === State.palette.index;
    el.classList.toggle('is-active', active);
    el.setAttribute('aria-selected', String(active));
    if (active) { if (scroll) el.scrollIntoView({ block: 'nearest' }); $('#paletteInput').setAttribute('aria-activedescendant', el.id); }
  });
}

function openPalette() {
  if (State.palette.open) return;
  State.palette.open = true;
  State.palette.query = '';
  State.palette.index = 0;
  $('#paletteInput').value = '';
  renderPalette();
  openOverlay('palette', '#paletteInput');
}
function closePalette(restoreFocus = true) {
  if (!State.palette.open) return false;
  State.palette.open = false;
  closeOverlay('palette', { restoreFocus });
  return true;
}
function togglePalette() { if (State.palette.open) closePalette(); else openPalette(); }
function runPaletteItem(index) {
  const item = State.palette.items[index];
  if (!item) return;
  closePalette(false);
  item.run();
}

function chromeLayerOpen() { return Boolean($('.overlay:not([hidden])')) || !$('#marketMenu')?.hidden; }

/* Cierra la capa superior abierta (paleta, diálogo o menú); devuelve si cerró algo. */
function closeTopOverlay() {
  if (closePalette()) return true;
  if (closeOverlay('captureDialog')) { State.captureDialogParams = null; return true; }
  if (closeSidePanel()) return true;
  return closeMarketMenu(true);
}

/* eventos globales por delegación */
function wireEvents() {
  wireHotelReputationEvents();
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !chromeLayerOpen() && !$('#copilotResults')?.hidden) {
      const close = $('#closeCopilotPanel'); close?.click(); e.preventDefault(); return;
    }
  });
  document.addEventListener('mouseover', (e) => {
    const item = e.target instanceof Element ? e.target.closest('.palette__item') : null;
    if (item && Number(item.dataset.paletteIndex) !== State.palette.index) setPaletteIndex(Number(item.dataset.paletteIndex), false);
    handleDashboardOver(e);
    handleBiOver(e);
    handleFlightOver(e);
  });
  document.addEventListener('focusin', (e) => {
    if (e.target instanceof Element && !e.target.closest('.market-switch')) closeMarketMenu();
    handleDashboardOver(e);
    handleBiOver(e);
  });
  document.addEventListener('click', async (e) => {
    if (!e.target.closest('.market-switch')) closeMarketMenu();
    if (handleDashboardClick(e)) return;
    if (handleFlightClick(e)) return;
    if (e.target.closest('[data-side-close]')) { closeSidePanel(); return; }
    if (handleBiClick(e)) return;
    if (handleHotelSheetClick(e)) return;
    const tickerHotel = e.target.closest('[data-ticker-hotel]');
    if (tickerHotel) { openHotelInHotels(tickerHotel.dataset.tickerHotel); return; }
    if (e.target.closest('#marketBtn')) { toggleMarketMenu(); return; }
    const marketItem = e.target.closest('.market-menu__item[data-market]');
    if (marketItem) {
      closeMarketMenu(true);
      const changed = Number(marketItem.dataset.market) !== State.targetId;
      selectMarket(marketItem.dataset.market);
      if (changed && activeTarget()) toast(`Mercado activo: ${activeTarget().name}`);
      return;
    }
    if (e.target.closest('#themeBtn')) { toggleTheme(); return; }
    if (e.target.closest('#collapseBtn')) { toggleSidebar(); return; }
    if (e.target.closest('#paletteBtn')) { openPalette(); return; }
    const paletteItem = e.target.closest('[data-palette-index]');
    if (paletteItem) { runPaletteItem(Number(paletteItem.dataset.paletteIndex)); return; }
    if (e.target.closest('#dataAge')?.dataset.fresh === 'true') { const id = State.metrics[State.targetId]?.latestSnapshot?.id; toast(`Datos al día · foto #${id}`); return; }
    if (e.target.closest('#dataAge') || e.target.closest('#captureTop')) { void openCaptureDialog(); return; }
    if (e.target.closest('#captureCancel')) { closeOverlay('captureDialog'); State.captureDialogParams = null; return; }
    if (e.target.closest('#captureConfirm')) { void confirmCapture(); return; }
    const nav = e.target.closest('.nav__item[data-view]');
    if (nav) { setView(nav.dataset.view); return; }
    const navBtn = e.target.closest('[data-nav]');
    if (navBtn) { setView(navBtn.dataset.nav); return; }
    const workspaceAdd = e.target.closest('[data-workspace-add]');
    if (workspaceAdd) { addWorkspaceLayer(workspaceAdd.dataset.workspaceAdd); return; }
    const workspaceRemove = e.target.closest('[data-workspace-remove]');
    if (workspaceRemove) { removeWorkspaceLayer(workspaceRemove.dataset.workspaceRemove); return; }
    const workspaceMove = e.target.closest('[data-workspace-move]');
    if (workspaceMove) { moveWorkspaceLayer(workspaceMove.dataset.workspaceMove, Number(workspaceMove.dataset.workspaceDirection)); return; }
    const workspaceAsk = e.target.closest('[data-workspace-ask]');
    if (workspaceAsk) {
      State.copilotWorkspaceContext = {
        targetId: State.targetId,
        snapshotId: Number(workspaceAsk.dataset.workspaceAnchor),
        checkIn: workspaceAsk.dataset.workspaceCheckin || null,
      };
      setView('copilot');
      return;
    }
    const workspaceHotel = e.target.closest('[data-workspace-hotel]');
    if (workspaceHotel) { toggleWorkspaceHotelSelection(workspaceHotel.dataset.workspaceHotel, workspaceHotel.dataset.workspaceHotelName, workspaceHotel.dataset.workspaceLink); return; }
    const workspaceRestore = e.target.closest('[data-workspace-restore]');
    if (workspaceRestore) { restoreWorkspaceRevision(workspaceRestore.dataset.workspaceRestore); return; }
    if (e.target.closest('#workspaceSave')) { void saveWorkspaceDraft(); return; }
    const mk = e.target.closest('[data-market]');
    if (mk) { selectMarket(mk.dataset.market); return; }
    const capMk = e.target.closest('[data-cap-market]');
    if (capMk) { selectMarket(capMk.dataset.capMarket); return; }
    if (e.target.closest('#launchCapture')) { launchCapture(); return; }
    if (e.target.closest('#lockBtn')) { void lockSession(); return; }
    if (e.target.closest('#unlockBtn')) { void unlockSession(); return; }
    if (e.target.closest('#chatSend')) { sendChat($('#chatInput').value); return; }
    if (e.target.closest('#toggleCopilotExamples')) { const suggestions = $('#chatSuggestions'); setCopilotSuggestionsState(false, suggestions?.hidden); return; }
    if (e.target.closest('#toggleCopilotHistory') || e.target.closest('#toggleCopilotHistoryMain')) { updateCopilotHistory(!State.copilotHistoryOpen); return; }
    const copilotPanelToggle = e.target.closest('#toggleCopilotPanel');
    if (copilotPanelToggle) { copilotPanelHTML(State.copilotPanel || 'result', copilotPanelToggle); return; }
    const copilotSources = e.target.closest('[data-open-copilot-sources]');
    if (copilotSources) { copilotPanelHTML('sources', copilotSources); return; }
    if (e.target.closest('#closeCopilotPanel')) { const panel = $('#copilotResults'); if (panel) panel.hidden = true; $('.copilot__main')?.classList.remove('has-results'); const toggle = $('#toggleCopilotPanel'); if (toggle) toggle.setAttribute('aria-expanded', 'false'); State.copilotPanel = null; State.copilotPanelFocusOrigin?.focus?.(); State.copilotPanelFocusOrigin = null; return; }
    const panelTab = e.target.closest('[data-copilot-panel-tab]');
    if (panelTab) { copilotPanelHTML(panelTab.dataset.copilotPanelTab); return; }
    if (e.target.closest('#chatAttach')) { $('#chatFile')?.click(); return; }
    const cancelAssistantJob = e.target.closest('[data-cancel-assistant-job]');
    if (cancelAssistantJob) {
      cancelAssistantJob.disabled = true;
      cancelAssistantJob.textContent = 'Cancelando…';
      try { await api(`/api/assistant/jobs/${encodeURIComponent(cancelAssistantJob.dataset.cancelAssistantJob)}/cancel`, { method: 'POST', body: JSON.stringify({}) }); }
      catch (error) { cancelAssistantJob.disabled = false; cancelAssistantJob.textContent = 'Dejar de seguir'; alert(error.message || 'No se pudo cancelar el trabajo'); }
      return;
    }
    const removeAttachment = e.target.closest('[data-remove-attachment]');
    if (removeAttachment) {
      const attachmentId = Number(removeAttachment.dataset.removeAttachment);
      try { await api(`/api/assistant/attachments/${attachmentId}`, { method: 'DELETE' }); State.copilotAttachments = State.copilotAttachments.filter((item) => item.id !== attachmentId); renderCopilotAttachments(); }
      catch (error) { alert(error.message || 'No se pudo eliminar el archivo; sigue asociado a esta consulta.'); }
      return;
    }
    const sessionAction = e.target.closest('[data-session-action]');
    if (sessionAction) {
      e.stopPropagation();
      const id = Number(sessionAction.dataset.sessionId);
      const current = State.sessions.find((item) => item.id === id);
      if (!current) return;
      try {
        if (sessionAction.dataset.sessionAction === 'rename') {
          const title = window.prompt('Nombre de la conversación', current.title || 'Conversación');
          if (!title || !title.trim()) return;
          const result = await api(`/api/assistant/sessions/${id}`, { method: 'PATCH', body: JSON.stringify({ title: title.trim(), expectedVersion: current.version }) }); Object.assign(current, result.session || {});
        } else if (sessionAction.dataset.sessionAction === 'pin') {
          const result = await api(`/api/assistant/sessions/${id}`, { method: 'PATCH', body: JSON.stringify({ pinned: !current.pinned, expectedVersion: current.version }) }); Object.assign(current, result.session || {});
        } else {
          await api(`/api/assistant/sessions/${id}`, { method: 'PATCH', body: JSON.stringify({ status: 'archived', expectedVersion: current.version }) }); State.sessions = State.sessions.filter((item) => item.id !== id); if (State.activeSession === id) { State.activeSession = null; greetThread(); }
        }
        renderSessionList();
      } catch (error) { alert(error.message || 'No se pudo actualizar la conversación'); }
      return;
    }
    if (e.target.closest('#newSession')) { State.activeSession = null; State.copilotAttachments = []; renderCopilotAttachments(); renderSessionList(); greetThread(); return; }
    const ses = e.target.closest('[data-session]');
    if (ses) { loadSession(Number(ses.dataset.session)); return; }
    const ask = e.target.closest('[data-ask]');
    if (ask) { sendChat(ask.dataset.ask); return; }
    if (e.target.closest('[data-capture-compare-close]')) { State.captureComparisonOpen = false; renderCaptures(); return; }
    if (e.target.closest('[data-capture-compare]')) { State.captureComparisonOpen = true; renderCaptures(); return; }
    const loadPhoto = e.target.closest('[data-load-photo]');
    if (loadPhoto) { State.selectedPhotoId = Number(loadPhoto.dataset.loadPhoto); State.captureHotelSearch = ''; State.captureComparisonOpen = false; renderCaptures(); return; }
  });

  document.addEventListener('keydown', (e) => {
    const locked = $('#lock')?.classList.contains('is-visible');
    if (handleHotelSheetKey(e)) return;
    if (!locked && e.key === 'Escape' && closeTopOverlay()) { e.preventDefault(); return; }
    const biDay = (e.key === 'Enter' || e.key === ' ') && e.target instanceof Element ? e.target.closest('#biCalGrid [data-d][role="button"]') : null;
    if (biDay) { e.preventDefault(); biDay.click(); $(`#biCalGrid [data-d="${biDay.dataset.d}"][role="button"]`)?.focus(); return; }
    if (!locked && (e.metaKey || e.ctrlKey) && !e.altKey && !e.shiftKey && (e.key === 'k' || e.key === 'K')) { e.preventDefault(); togglePalette(); return; }
    if (e.target && e.target.id === 'paletteInput') {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); setPaletteIndex(State.palette.index + (e.key === 'ArrowDown' ? 1 : -1)); return; }
      if (e.key === 'Enter' && !e.isComposing) { e.preventDefault(); runPaletteItem(State.palette.index); return; }
    }
    const marketItemFocus = e.target instanceof Element ? e.target.closest('.market-menu__item') : null;
    if (marketItemFocus && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
      e.preventDefault();
      const items = $$('.market-menu__item');
      items[(items.indexOf(marketItemFocus) + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length]?.focus();
      return;
    }
    if (e.key === 'Escape' && closeDashboardPopover()) {
      e.preventDefault();
      return;
    }
    if (e.key === 'Escape' && State.airOperations.fullscreen) {
      e.preventDefault();
      toggleAirOperationsFullscreen(false);
      void paintAirOperations();
      return;
    }
    if (e.key === 'Enter' && e.target && e.target.id === 'chatInput' && !e.shiftKey && !e.isComposing) { e.preventDefault(); sendChat(e.target.value); }
    if ((e.key === 'ArrowRight' || e.key === 'ArrowLeft') && e.target?.matches?.('[data-copilot-panel-tab]')) {
      const tabs = $$('.copilot-results__tabs [data-copilot-panel-tab]');
      const index = tabs.indexOf(e.target);
      if (index >= 0) { e.preventDefault(); tabs[(index + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length]?.focus(); }
    }
    if (e.key === 'Enter' && e.target && e.target.id === 'lockPass') { e.preventDefault(); void unlockSession(); }
    if ((e.metaKey || e.ctrlKey) && (e.key === 'o' || e.key === 'O')) { e.preventDefault(); setView('copilot'); }
  });
  document.addEventListener('change', (e) => {
    if (handleBiChange(e)) return;
    if (e.target && e.target.id === 'copilotMode') { State.copilotMode = e.target.value; return; }
    if (e.target && e.target.id === 'chatFile' && e.target.files?.[0]) {
      void uploadCopilotAttachment(e.target.files[0]); e.target.value = '';
    }
  });

  document.addEventListener('input', (e) => {
    if (handleBiInput(e)) return;
    if (e.target && e.target.id === 'paletteInput') { State.palette.query = e.target.value.slice(0, 200); State.palette.index = 0; renderPalette(); return; }
    if (e.target && e.target.id === 'copilotSessionSearch') {
      State.copilotSessionQuery = e.target.value;
      const term = State.copilotSessionQuery.trim().toLowerCase();
      $$('.session-wrap').forEach((item) => { item.hidden = term && !item.textContent.toLowerCase().includes(term); });
    }
    if (e.target && e.target.id === 'chatInput') { saveCopilotDraft(e.target.value); e.target.style.height = 'auto'; e.target.style.height = `${Math.min(e.target.scrollHeight, 150)}px`; }
    if (e.target && e.target.id === 'workspaceName' && State.workspaceDraft) {
      State.workspaceDraft.name = e.target.value.slice(0, 120);
      setWorkspaceDirty();
      const chip = $('.saved-chip', mount('workspace'));
      if (chip) { chip.classList.add('is-dirty'); chip.innerHTML = '<i></i>Cambios sin guardar'; }
      const save = $('#workspaceSave', mount('workspace'));
      if (save) save.disabled = false;
    }
    if (e.target && e.target.id === 'hotelSearch') { State.hotelSearch = e.target.value.slice(0, 160); paintHotelSheet(); }
    if (e.target && e.target.id === 'captureHotelSearch') { State.captureHotelSearch = e.target.value; filterCaptureHotelTable(); }
    if (handleFlightInput(e)) return;
  });
  document.addEventListener('change', (e) => {
    if (handleFlightChange(e)) return;
    const workspaceContextSelect = e.target && e.target.closest('[data-workspace-context]');
    if (workspaceContextSelect) {
      setWorkspaceContext(workspaceContextSelect.dataset.workspaceContext, workspaceContextSelect.value);
      return;
    }
    if (e.target && e.target.id === 'hotelGroup' && SHEET_GROUPS.some((g) => g.id === e.target.value)) { State.hotelGroup = e.target.value; paintHotelSheet(); }
  });
}

function filterCaptureHotelTable() {
  const table = $('#captureHotelTable'); if (!table) return;
  const q = String(State.captureHotelSearch || '').trim().toLowerCase();
  const rows = $$('[data-capture-hotel-row]', table);
  let visible = 0;
  rows.forEach((row, index) => {
    const show = !q || (row.dataset.captureText || '').includes(q);
    row.style.display = show ? '' : 'none';
    if (show) { visible += 1; const rank = row.querySelector('.rank'); if (rank) rank.textContent = String(visible); }
  });
  const count = $('#captureHotelCount'); if (count) count.textContent = `${visible} / ${rows.length} filas`;
}

function lockFocusable() {
  const lock = $('#lock');
  if (!lock) return [];
  return [...lock.querySelectorAll('input, button')].filter((el) => !el.disabled && el.offsetParent !== null);
}

function trapLockTab(event) {
  if (event.key !== 'Tab') return;
  const items = lockFocusable();
  if (!items.length) return;
  const first = items[0], last = items[items.length - 1];
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
}

function showLock(on) {
  const lock = $('#lock');
  if (!lock) return;
  lock.classList.toggle('is-visible', on);
  lock.setAttribute('aria-hidden', on ? 'false' : 'true');
  // El fondo nunca es interactivo tras el velo; Escape no desbloquea (hay que autenticarse).
  document.querySelector('.atlas-root')?.toggleAttribute('inert', on);
  if (!lock.dataset.trapWired) { lock.addEventListener('keydown', trapLockTab); lock.dataset.trapWired = '1'; }
  if (on) {
    const error = $('#lockError');
    if (error) { error.hidden = true; error.textContent = ''; }
    setTimeout(() => { const p = $('#lockPass'); if (p) p.focus(); }, 60);
  } else {
    const p = $('#lockPass'); if (p) p.value = '';
  }
}

function setLockError(message) {
  const error = $('#lockError');
  if (error) { error.hidden = !message; error.textContent = message || ''; }
}

async function unlockSession() {
  if (State.authBusy) return;
  const input = $('#lockPass');
  const password = input?.value || '';
  if (!password.trim()) { setLockError('Introduce una contraseña.'); input?.focus(); return; }
  State.authBusy = true;
  const button = $('#unlockBtn');
  if (button) { button.disabled = true; button.textContent = 'Comprobando…'; }
  try {
    const result = await api('/api/auth/session', { method: 'POST', body: JSON.stringify({ password }) });
    State.authRequired = Boolean(result.authRequired);
    State.authenticated = Boolean(result.authenticated);
    setLockError('');
    showLock(false);
    $('#lockBtn')?.focus();
  } catch (error) {
    setLockError(error.message || 'No se pudo validar la sesión.');
    input?.focus();
  } finally {
    State.authBusy = false;
    if (button) { button.disabled = false; button.textContent = 'Entrar'; }
  }
}

async function lockSession() {
  if (State.authBusy) return;
  State.authBusy = true;
  try {
    if (State.authRequired) await api('/api/auth/session', { method: 'DELETE' });
    State.authenticated = false;
    showLock(true);
  } catch (error) {
    setLockError(error.message || 'No se pudo bloquear la sesión.');
    showLock(true);
  } finally {
    State.authBusy = false;
  }
}

/* -------------------------------------------------------------------- boot */
async function boot() {
  applyPreferences();
  wireEvents();
  const hash = (location.hash || '').replace(/^#/, '');
  const [route, query = ''] = hash.split('?', 2);
  const storedView = readPref(PREFS.view, VIEWS, 'dashboard');
  skeleton(mount(VIEWS.includes(route) ? route : storedView), 'dashboard');
  try {
    const auth = await api('/api/auth/session');
    State.authRequired = Boolean(auth.authRequired);
    State.authenticated = Boolean(auth.authenticated);
    if (State.authRequired && !State.authenticated) { showLock(true); return; }
  } catch (_) {
    showLock(true);
    setLockError('No se pudo comprobar la sesión.');
    return;
  }
  try {
    const r = await api('/api/targets');
    State.targets = (r.targets || []).sort((a, b) => a.id - b.id);
  } catch (_) { State.targets = []; }
  if (State.targets.length) State.targetId = State.targets[0].id;
  renderMarketList();
  void renderChromeData();
  if (route === 'reputation') {
    const params = new URLSearchParams(query);
    State.reputation.hotelKey = params.get('hotelKey') || null;
  }
  setView(VIEWS.includes(route) ? route : storedView);
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
else boot();
