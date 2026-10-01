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
function polar(cx, cy, r, deg) {
  const a = (deg * Math.PI) / 180;
  return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
}
function arc(cx, cy, r, startDeg, endDeg) {
  const [x0, y0] = polar(cx, cy, r, startDeg);
  const [x1, y1] = polar(cx, cy, r, endDeg);
  const large = Math.abs(endDeg - startDeg) > 180 ? 1 : 0;
  const sweep = endDeg > startDeg ? 1 : 0;
  return `M ${x0.toFixed(1)} ${y0.toFixed(1)} A ${r} ${r} 0 ${large} ${sweep} ${x1.toFixed(1)} ${y1.toFixed(1)}`;
}

/* Beeswarm de tarifas */
function beeswarmSVG(prices, med, p75) {
  const W = 760, x0 = 8, x1 = 752, baseY = 75, r = 4.6, step = 10;
  const vals = prices.filter((p) => p > 0);
  if (!vals.length) return emptyChart(178);
  const min = Math.min(...vals), max = Math.max(...vals);
  const scale = (p) => x0 + (max > min ? (p - min) / (max - min) : 0.5) * (x1 - x0);
  const sorted = [...vals].sort((a, b) => a - b);
  const placed = [];
  const circles = sorted.map((p) => {
    const x = scale(p);
    const used = new Set(placed.filter((q) => Math.abs(q.x - x) < r * 1.9).map((q) => q.level));
    let level = 0;
    for (let m = 0; ; m++) {
      if (m === 0) { if (!used.has(0)) { level = 0; break; } continue; }
      if (!used.has(m)) { level = m; break; }
      if (!used.has(-m)) { level = -m; break; }
    }
    placed.push({ x, level });
    const y = baseY + level * step;
    const fill = p < med ? 'var(--lo)' : p < p75 ? 'var(--mid)' : 'var(--hi)';
    return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r}" fill="${fill}" opacity="0.9"></circle>`;
  }).join('');
  const mx = scale(med);
  const ax = [min, med, p75, max];
  const labels = ax.map((v, i) => {
    const x = scale(v);
    const anchor = i === 0 ? 'start' : i === ax.length - 1 ? 'end' : 'middle';
    const tx = i === 0 ? x0 : i === ax.length - 1 ? x1 : x;
    return `<text x="${tx.toFixed(1)}" y="156" text-anchor="${anchor}">${nEs(v)}${i === ax.length - 1 ? ' €' : ''}</text>`;
  }).join('');
  return `<svg viewBox="0 0 ${W} 178" width="100%" height="178" class="svg-block">
    <line x1="${mx.toFixed(1)}" y1="8" x2="${mx.toFixed(1)}" y2="132" stroke="var(--ac)" stroke-width="1" stroke-dasharray="3 3" opacity="0.5"></line>
    <text x="${(mx + 5).toFixed(1)}" y="16" font-family="'Space Mono',monospace" font-size="9.5" fill="var(--ac)">mediana ${nEs(med)} €</text>
    <g style="animation:atFade 700ms ease 300ms both;">${circles}</g>
    <line x1="8" y1="140" x2="752" y2="140" stroke="var(--border)" stroke-width="1"></line>
    <g font-family="'Space Mono',monospace" font-size="10" fill="var(--faint)">${labels}</g>
  </svg>`;
}

/* Gauge radial de percentil (0..100) */
function gaugeSVG(pct) {
  const cx = 110, cy = 110, r = 86, start = 135, span = 270;
  const f = Math.max(0, Math.min(100, pct)) / 100;
  const bg = arc(cx, cy, r, start, start + span);
  const val = arc(cx, cy, r, start, start + span * f);
  return `<svg viewBox="0 0 220 200" width="100%" height="182" class="svg-block" style="margin:auto;">
    <path d="${bg}" fill="none" stroke="rgba(255,255,255,.1)" stroke-width="13" stroke-linecap="round"></path>
    <path d="${val}" fill="none" stroke="var(--ac)" stroke-width="13" stroke-linecap="round" stroke-dasharray="1400" style="animation:atDraw 1400ms cubic-bezier(.22,1,.36,1) 420ms both;"></path>
    <text x="110" y="112" text-anchor="middle" font-family="Archivo,sans-serif" font-size="42" font-weight="700" fill="#fff" letter-spacing="-0.03em">${nEs(pct)}</text>
    <text x="110" y="132" text-anchor="middle" font-family="'Space Mono',monospace" font-size="10" fill="var(--faint)">PERCENTIL</text>
  </svg>`;
}

/* Densidad tipo ridgeline por mercado */
function ridgelineSVG(rows) {
  // rows: [{name, prices:[], median}]
  const all = rows.flatMap((r) => r.prices).filter((p) => p > 0);
  if (!all.length) return emptyChart(200);
  const dmin = Math.min(...all), dmax = Math.max(...all);
  const x0 = 150, x1 = 600, rowH = 48, top = 10, bw = 54;
  const N = 61;
  const bandwidth = (dmax - dmin) / 12 || 1;
  const kde = (prices) => {
    const xs = [], ys = [];
    let maxy = 0;
    for (let i = 0; i < N; i++) {
      const x = dmin + (i / (N - 1)) * (dmax - dmin);
      let s = 0;
      for (const p of prices) { const u = (x - p) / bandwidth; s += Math.exp(-0.5 * u * u); }
      xs.push(x); ys.push(s); if (s > maxy) maxy = s;
    }
    return { xs, ys, maxy };
  };
  let body = '';
  const colors = ['#2f55d4', '#4d74f0', '#7f93c9', '#a3aec9', '#c3cbdd'];
  const fills = ['rgba(47,85,212,0.16)', 'rgba(47,85,212,0.13)', 'rgba(47,85,212,0.10)', 'rgba(47,85,212,0.08)', 'rgba(47,85,212,0.06)'];
  rows.forEach((rw, ri) => {
    const { xs, ys, maxy } = kde(rw.prices);
    const sx = (v) => x0 + (v - dmin) / (dmax - dmin || 1) * (x1 - x0);
    const sy = (v) => bw - (maxy ? (v / maxy) * bw : 0);
    let d = `M ${sx(xs[0]).toFixed(1)} ${sy(ys[0]).toFixed(1)}`;
    for (let i = 1; i < N; i++) d += ` L ${sx(xs[i]).toFixed(1)} ${sy(ys[i]).toFixed(1)}`;
    d += ` L ${x1} ${bw} L ${x0} ${bw} Z`;
    body += `<g transform="translate(0,${top + ri * rowH})">
      <text x="140" y="44" text-anchor="end" font-family="Archivo,sans-serif" font-size="12" font-weight="500" fill="var(--ink)">${esc(rw.name)}</text>
      <path d="${d}" fill="${fills[ri % fills.length]}" stroke="${colors[ri % colors.length]}" stroke-width="1.6"></path>
      <text x="612" y="52" font-family="'Space Mono',monospace" font-size="11" fill="var(--ink)">${nEs(rw.median)}</text>
    </g>`;
  });
  const h = top + rows.length * rowH + 40;
  return `<svg viewBox="0 0 640 ${h}" width="100%" height="${h}" class="svg-block">
    <g style="animation:atFade 600ms ease 420ms both;">${body}</g>
    <g font-family="'Space Mono',monospace" font-size="10" fill="var(--faint)">
      <text x="150" y="${h - 6}">${nEs(dmin)} €</text>
      <text x="375" y="${h - 6}" text-anchor="middle">${nEs((dmin + dmax) / 2)} €</text>
      <text x="600" y="${h - 6}" text-anchor="end">${nEs(dmax)} €</text>
    </g>
  </svg>`;
}

/* Slope de movimiento entre dos fotos */
function dumbbellSVG(routes) {
  const vals = routes.flatMap((r) => [r.min, r.avg]).filter((v) => v > 0);
  if (!vals.length) return emptyChart(250);
  const dmin = Math.floor(Math.min(...vals) / 50) * 50;
  const dmax = Math.ceil(Math.max(...vals) / 50) * 50;
  const x0 = 175, x1 = 620, top = 20, rh = 32;
  const sx = (v) => x0 + (v - dmin) / (dmax - dmin || 1) * (x1 - x0);
  let grid = '', axis = '';
  const ticks = 5;
  for (let i = 0; i < ticks; i++) {
    const v = dmin + (i / (ticks - 1)) * (dmax - dmin);
    const x = sx(v);
    grid += `<line x1="${x.toFixed(1)}" y1="6" x2="${x.toFixed(1)}" y2="${top + routes.length * rh - 8}"></line>`;
    axis += `<text x="${x.toFixed(1)}" y="${top + routes.length * rh + 6}" text-anchor="middle">${nEs(v)}${i === ticks - 1 ? ' €' : ''}</text>`;
  }
  const body = routes.map((r, i) => {
    const y = top + i * rh;
    const a = sx(r.min), b = sx(r.avg);
    return `<g transform="translate(0,${y})">
      <text x="${x0 - 7}" y="4" text-anchor="end" font-family="Archivo,sans-serif" font-size="11.5" font-weight="500" fill="var(--ink)">${esc(r.label)}</text>
      <text x="${x0 - 7}" y="17" text-anchor="end" font-family="'Space Mono',monospace" font-size="9" fill="var(--fainter)">${esc(r.market || '')}</text>
      <line x1="${a.toFixed(1)}" y1="0" x2="${b.toFixed(1)}" y2="0" stroke="var(--lo)" stroke-width="6" stroke-linecap="round" style="transform-origin:${a.toFixed(1)}px 0; animation:atWipe 700ms cubic-bezier(.22,1,.36,1) ${380 + i * 40}ms both;"></line>
      <circle cx="${a.toFixed(1)}" cy="0" r="4.6" fill="var(--card)" stroke="var(--ac)" stroke-width="2.4"></circle>
      <circle cx="${b.toFixed(1)}" cy="0" r="4.4" fill="var(--ink)"></circle>
      <text x="${(b + 19).toFixed(1)}" y="4" font-family="'Space Mono',monospace" font-size="10" fill="var(--ink)">${nEs(r.avg)}</text>
    </g>`;
  }).join('');
  const h = top + routes.length * rh + 28;
  return `<svg viewBox="0 0 700 ${h}" width="100%" height="${h}" class="svg-block">
    <g stroke="var(--line-soft)" stroke-width="1">${grid}</g>
    <g font-family="'Space Mono',monospace" font-size="9.5" fill="var(--fainter)">${axis}</g>
    <g style="animation:atFade 500ms ease 320ms both;">${body}</g>
  </svg>`;
}

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
  heatmaps: {},  // cache por targetId
  demandCurves: {}, // cache por targetId
  externalObservations: {}, // caché global de fuentes públicas normalizadas
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
  dashboardMapRows: {},
  dashboardMapResizeObserver: null,
  dashboardMapResizeFrame: null,
  dashboardDrawerFocusOrigin: null,
  dashboardView: 'market',
  dashboardViewRestored: false,
  dashboardExplorerSnapshotId: null,
  dashboardExplorerResult: null,
  dashboardExplorerResultKey: null,
  dashboardExplorerSearch: '',
  dashboardExplorerSort: 'adr-desc',
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
  hotelTab: 'sheet',            // pestaña de Hoteles: hoja de mercado o panel de análisis
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
  flightTab: 'overview',
  airOperations: {
    page: 1,
    pageSize: 100,
    query: '',
    market: '',
    origin: '',
    destination: '',
    airline: '',
    connection: '',
    price: '',
    runId: 'all',
    dateFrom: '',
    dateTo: '',
    sort: 'price-asc',
    requestId: 0,
    fullscreen: false,
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

function restoreDashboardView() {
  if (State.dashboardViewRestored) return State.dashboardView;
  State.dashboardViewRestored = true;
  try {
    const saved = localStorage.getItem('atlas.dashboard.view.v1');
    if (saved === 'market' || saved === 'charts' || saved === 'explorer') State.dashboardView = saved;
  } catch (_) { /* la preferencia local no debe bloquear el dashboard */ }
  return State.dashboardView;
}

function persistDashboardView() {
  try { localStorage.setItem('atlas.dashboard.view.v1', State.dashboardView); }
  catch (_) { /* la vista sigue funcionando aunque no haya almacenamiento local */ }
}

function activateDashboardView(view) {
  const next = ['market', 'charts', 'explorer'].includes(view) ? view : 'market';
  if (next === State.dashboardView) return;
  State.dashboardView = next;
  persistDashboardView();
  document.querySelectorAll('[data-dashboard-view]').forEach((button) => {
    const selected = button.dataset.dashboardView === next;
    button.setAttribute('aria-selected', String(selected));
    button.tabIndex = selected ? 0 : -1;
  });
  document.querySelectorAll('.dashboard-view-panel').forEach((panel) => {
    panel.getAnimations().forEach((animation) => animation.cancel());
    panel.hidden = panel.id !== `dashboard-panel-${next}`;
    if (!panel.hidden && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      panel.animate([{ opacity: 0, transform: 'translateY(5px)' }, { opacity: 1, transform: 'translateY(0)' }], { duration: 190, easing: 'ease-out' });
    }
  });
  if (next === 'market') {
    if (State.dashboardMap) State.dashboardMap.resize();
    else {
      const rows = State.snapshots[State.targetId]?.latest?.rows || [];
      void renderDashboardHotelMap(rows.filter((row) => row.latitude != null && row.longitude != null && row.pricePerNight > 0), rows);
    }
  }
}

function dashboardViewSwitcherHTML(view) {
  const active = ['market', 'charts', 'explorer'].includes(view) ? view : 'market';
  const selected = (key) => active === key ? 'true' : 'false';
  return `<div class="dashboard-view-switcher mb12" aria-label="Vista principal del dashboard">
    <div class="dashboard-view-tabs flight-tabs" role="tablist" aria-label="Bloques del dashboard">
      <button type="button" role="tab" id="dashboard-view-tab-market" tabindex="${active === 'market' ? 0 : -1}" aria-selected="${selected('market')}" aria-controls="dashboard-panel-market" data-dashboard-view="market">Mapa y hoteles</button>
      <button type="button" role="tab" id="dashboard-view-tab-charts" tabindex="${active === 'charts' ? 0 : -1}" aria-selected="${selected('charts')}" aria-controls="dashboard-panel-charts" data-dashboard-view="charts">Gráficas</button>
      <button type="button" role="tab" id="dashboard-view-tab-explorer" tabindex="${active === 'explorer' ? 0 : -1}" aria-selected="${selected('explorer')}" aria-controls="dashboard-panel-explorer" data-dashboard-view="explorer">Explorar</button>
    </div>
  </div>`;
}

function dashboardExplorerHTML(captures, latestSnapshot) {
  const availableCaptures = (captures || []).filter((capture) => capture.anchorSnapshotId && capture.observedAt);
  const fallbackId = latestSnapshot?.snapshot?.id || availableCaptures[0]?.anchorSnapshotId || null;
  const selectedId = availableCaptures.some((capture) => Number(capture.anchorSnapshotId) === Number(State.dashboardExplorerSnapshotId))
    ? Number(State.dashboardExplorerSnapshotId) : Number(fallbackId);
  State.dashboardExplorerSnapshotId = Number.isInteger(selectedId) ? selectedId : null;
  const options = availableCaptures.map((capture) => {
    const dates = capture.checkIns || [];
    const span = dates.length ? `${rateShortDate(dates[0])}${dates.length > 1 ? ` → ${rateShortDate(dates.at(-1))}` : ''}` : 'entrada no disponible';
    const legacy = capture.kind === 'legacy_inferred_capture_group' ? ' · histórico inferido' : '';
    return `<option value="${capture.anchorSnapshotId}"${Number(capture.anchorSnapshotId) === selectedId ? ' selected' : ''}>Extracción #${capture.anchorSnapshotId} · ${esc(fmtStamp(capture.observedAt))} · ${esc(span)} · ${nEs(capture.comparableRows)} observaciones${legacy}</option>`;
  }).join('');
  return `<article class="card card--pad dashboard-explorer-card">
    <div class="dashboard-explorer-card__head">
      <div><div class="card__kicker">Consulta certificada</div><h2>Explorar tarifas por extracción</h2><p>Agrega las observaciones del barrido seleccionado por hotel y conserva las fechas de entrada en cada resultado.</p></div>
      <label class="dashboard-explorer-select"><span>Extracción</span><select id="dashboardExplorerPhoto" aria-label="Extracción para explorar"${options ? '' : ' disabled'}>${options || '<option>Sin extracciones</option>'}</select></label>
    </div>
    <div class="dashboard-explorer-controls" aria-label="Controles de resultados">
      <label><span>Buscar hotel</span><input id="dashboardExplorerSearch" type="search" value="${esc(State.dashboardExplorerSearch)}" placeholder="Nombre del hotel" autocomplete="off"></label>
      <label><span>Ordenar</span><select id="dashboardExplorerSort" aria-label="Orden de resultados"><option value="adr-desc"${State.dashboardExplorerSort === 'adr-desc' ? ' selected' : ''}>ADR medio: mayor a menor</option><option value="adr-asc"${State.dashboardExplorerSort === 'adr-asc' ? ' selected' : ''}>ADR medio: menor a mayor</option><option value="name-asc"${State.dashboardExplorerSort === 'name-asc' ? ' selected' : ''}>Hotel: A–Z</option></select></label>
    </div>
    <section id="dashboardExplorerComparison" class="dashboard-explorer-comparison" aria-live="polite" hidden></section>
    <div id="dashboardExplorerData" class="dashboard-explorer-data" aria-live="polite"><div class="dashboard-explorer-loading">Cargando consulta certificada…</div></div>
  </article>`;
}

function dashboardExplorerValue(item, metric) {
  return (item.values || []).find((value) => value.metric === metric)?.value ?? null;
}

function dashboardExplorerDateSummary(item) {
  const count = Number(item?.population?.distinctCheckIns || 0);
  return count === 1 ? '1 fecha de entrada' : `${nEs(count)} fechas de entrada`;
}

function dashboardExplorerObservationLabel(value) {
  const count = Number(value || 0);
  return `${nEs(count)} ${count === 1 ? 'observación' : 'observaciones'}`;
}

function dashboardExplorerCheckIns(item) {
  const dates = (item?.population?.checkIns || []).filter(Boolean);
  if (!dates.length) return '—';
  const labels = dates.slice(0, 3).map(rateShortDate);
  return `${labels.join(', ')}${dates.length > 3 ? ` +${dates.length - 3}` : ''}`;
}

function dashboardExplorerPreviousCapture(selectedId) {
  const captures = State.captureHistories[State.targetId]?.captures || [];
  const selectedIndex = captures.findIndex((capture) => Number(capture.anchorSnapshotId) === Number(selectedId));
  return selectedIndex >= 0 ? captures[selectedIndex + 1] || null : null;
}

function dashboardExplorerCheckInPoints(payload) {
  return new Map((payload?.breakdown || []).map((item) => [item.dimensions?.checkIn, dashboardExplorerValue(item, 'adr_mean')]).filter(([date, value]) => Boolean(date) && Number.isFinite(Number(value))));
}

function dashboardExplorerComparisonSVG(currentPayload, previousPayload) {
  const current = dashboardExplorerCheckInPoints(currentPayload);
  const previous = dashboardExplorerCheckInPoints(previousPayload);
  const dates = [...new Set([...current.keys(), ...previous.keys()])].sort();
  const values = [...current.values(), ...previous.values()].map(Number).filter(Number.isFinite);
  if (!dates.length || values.length < 2) return emptyChart(138);
  const W = 720, H = 178, x0 = 42, x1 = 704, y0 = 18, y1 = 132;
  const min = Math.min(...values), max = Math.max(...values);
  const sx = (index) => dates.length === 1 ? (x0 + x1) / 2 : x0 + (index / (dates.length - 1)) * (x1 - x0);
  const sy = (value) => y0 + (max > min ? (1 - (value - min) / (max - min)) : 0.5) * (y1 - y0);
  const pathFor = (points) => dates.reduce((path, date, index) => {
    const value = points.get(date);
    if (!Number.isFinite(Number(value))) return `${path}M ${sx(index).toFixed(1)} ${sy(Number.NaN).toFixed(1)} `;
    const prior = points.get(dates[index - 1]);
    return `${path}${Number.isFinite(Number(prior)) ? 'L' : 'M'} ${sx(index).toFixed(1)} ${sy(Number(value)).toFixed(1)} `;
  }, '').replace(/M [^ ]+ NaN /g, '');
  const dotsFor = (points, color) => dates.map((date, index) => {
    const value = points.get(date);
    return Number.isFinite(Number(value)) ? `<circle cx="${sx(index).toFixed(1)}" cy="${sy(Number(value)).toFixed(1)}" r="3" fill="var(${color})"/>` : '';
  }).join('');
  const labels = dates.map((date, index) => `<text x="${sx(index).toFixed(1)}" y="157" text-anchor="middle">${esc(rateShortDate(date))}</text>`).join('');
  return `<svg class="dashboard-explorer-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="ADR medio por fecha de entrada para dos extracciones"><g stroke="var(--line-soft)" stroke-width="1"><line x1="${x0}" y1="${y0}" x2="${x1}" y2="${y0}"/><line x1="${x0}" y1="${(y0 + y1) / 2}" x2="${x1}" y2="${(y0 + y1) / 2}"/><line x1="${x0}" y1="${y1}" x2="${x1}" y2="${y1}"/></g><g fill="var(--faint)" font-family="'Space Mono',monospace" font-size="9"><text x="${x0 - 7}" y="${y0 + 3}" text-anchor="end">${nEs(max)} €</text><text x="${x0 - 7}" y="${y1 + 3}" text-anchor="end">${nEs(min)} €</text>${labels}</g><path d="${pathFor(previous)}" fill="none" stroke="var(--warn-ink)" stroke-width="2" stroke-linecap="round" stroke-dasharray="5 4"/><path d="${pathFor(current)}" fill="none" stroke="var(--ac)" stroke-width="2.2" stroke-linecap="round"/>${dotsFor(previous, '--warn-ink')}${dotsFor(current, '--ac')}</svg>`;
}

function renderDashboardExplorerComparison(host, currentPayload, previousPayload, previousCapture) {
  const outlet = $('#dashboardExplorerComparison', host);
  if (!outlet) return;
  if (!previousPayload || !previousCapture) { outlet.hidden = true; outlet.innerHTML = ''; return; }
  const currentId = currentPayload.provenance?.snapshotId;
  const previousId = previousPayload.provenance?.snapshotId;
  outlet.hidden = false;
  outlet.innerHTML = `<div class="dashboard-explorer-comparison__head"><div><div class="card__kicker">Comparación entre extracciones</div><h3>ADR por fecha de entrada</h3><p>El eje X es la fecha de entrada; cada línea agrega las tarifas comparables de su barrido.</p></div><div class="dashboard-explorer-legend"><span><i class="is-current"></i>Extracción #${esc(currentId)}</span><span><i class="is-previous"></i>Extracción #${esc(previousId)}</span></div></div>${dashboardExplorerComparisonSVG(currentPayload, previousPayload)}`;
}

function dashboardExplorerRows(payload) {
  const needle = String(State.dashboardExplorerSearch || '').trim().toLocaleLowerCase('es');
  const nameOf = (item) => String(item.labels?.hotel || item.dimensions?.hotel || '');
  const adrOf = (item) => Number(dashboardExplorerValue(item, 'adr_mean'));
  const rows = (payload.breakdown || []).filter((item) => !needle || nameOf(item).toLocaleLowerCase('es').includes(needle));
  return rows.sort((a, b) => {
    const nameOrder = nameOf(a).localeCompare(nameOf(b), 'es');
    if (State.dashboardExplorerSort === 'name-asc') return nameOrder;
    const ascending = State.dashboardExplorerSort === 'adr-asc';
    const left = Number.isFinite(adrOf(a)) ? adrOf(a) : (ascending ? Infinity : -Infinity);
    const right = Number.isFinite(adrOf(b)) ? adrOf(b) : (ascending ? Infinity : -Infinity);
    return ascending ? left - right || nameOrder : right - left || nameOrder;
  });
}

function renderDashboardExplorerResults(outlet, payload) {
  if (!outlet) return;
  const rows = dashboardExplorerRows(payload);
  const totalHotels = (payload.breakdown || []).length;
  const metricFormula = (payload.values || []).find((value) => value.metric === 'adr_mean')?.formula || 'Media de tarifa por habitación/noche sobre observaciones comparables.';
  const observedAt = payload.provenance?.observedAt ? fmtStamp(payload.provenance.observedAt) : 'fecha de extracción no disponible';
  const body = rows.length ? rows.map((item) => {
    const name = item.labels?.hotel || item.dimensions?.hotel || 'Hotel no identificado';
    const count = item.population?.comparableRows;
    return `<tr><th scope="row" class="name" title="${esc(item.dimensions?.hotel || '')}">${esc(name)}</th><td class="num">${eur(dashboardExplorerValue(item, 'adr_mean'), 2)}</td><td class="num">${eur(dashboardExplorerValue(item, 'adr_median'), 2)}</td><td class="num">${eur(dashboardExplorerValue(item, 'adr_min'), 2)} — ${eur(dashboardExplorerValue(item, 'adr_max'), 2)}</td><td class="dashboard-explorer-checkin">${esc(dashboardExplorerCheckIns(item))}<small>${dashboardExplorerDateSummary(item)} · ${dashboardExplorerObservationLabel(count)} · ${nEs(item.population?.comparablePct, 0)}% comparables</small></td></tr>`;
  }).join('') : `<tr><td colspan="5" class="empty">${totalHotels ? 'No hay hoteles que coincidan con la búsqueda.' : 'La extracción no contiene observaciones comparables para esta consulta.'}</td></tr>`;
  const resultCount = rows.length === totalHotels ? `${nEs(totalHotels)} hoteles` : `${nEs(rows.length)} de ${nEs(totalHotels)} hoteles`;
  outlet.innerHTML = `<div class="dashboard-explorer-meta"><span>Extracción anclada en #${esc(payload.provenance?.snapshotId)} · observada ${esc(observedAt)}</span><span>${resultCount} · ${nEs(payload.population?.comparableRows)} observaciones comparables de ${nEs(payload.population?.totalRows)} filas</span></div><div class="table-scroll"><table class="t dashboard-explorer-table"><caption>Tarifas agregadas por hotel en la extracción seleccionada</caption><thead><tr><th scope="col">Hotel</th><th scope="col" class="r">ADR medio</th><th scope="col" class="r">ADR mediano</th><th scope="col" class="r">Rango ADR</th><th scope="col">Entrada</th></tr></thead><tbody>${body}</tbody></table></div><details class="dashboard-explorer-method"><summary>Definición y alcance de la consulta</summary><p>${esc(metricFormula)} Los importes son EUR por habitación/noche; una cobertura incompleta no se interpreta como cero.</p></details>`;
}

async function loadDashboardExplorer(host) {
  const targetId = State.targetId;
  const selectedId = Number(State.dashboardExplorerSnapshotId);
  const outlet = $('#dashboardExplorerData', host);
  const comparisonOutlet = $('#dashboardExplorerComparison', host);
  if (!outlet || !Number.isInteger(targetId) || !Number.isInteger(selectedId)) return;
  outlet.innerHTML = '<div class="dashboard-explorer-loading">Cargando consulta certificada…</div>';
  if (comparisonOutlet) { comparisonOutlet.hidden = true; comparisonOutlet.innerHTML = ''; }
  try {
    const query = (snapshotId, dimensions, metrics) => api('/api/analytics/query', {
      method: 'POST',
      body: JSON.stringify({ targetId, snapshotId, dimensions, metrics, limit: 500 }),
    });
    const previousCapture = dashboardExplorerPreviousCapture(selectedId);
    const [payload, byCheckIn, previousByCheckIn] = await Promise.all([
      query(selectedId, ['hotel'], ['adr_mean', 'adr_median', 'adr_min', 'adr_max']),
      query(selectedId, ['checkIn'], ['adr_mean']),
      previousCapture ? query(Number(previousCapture.anchorSnapshotId), ['checkIn'], ['adr_mean']) : Promise.resolve(null),
    ]);
    if (State.view !== 'dashboard' || State.targetId !== targetId || Number(State.dashboardExplorerSnapshotId) !== selectedId) return;
    State.dashboardExplorerResult = payload;
    State.dashboardExplorerResultKey = `${targetId}:${selectedId}`;
    renderDashboardExplorerResults(outlet, payload);
    renderDashboardExplorerComparison(host, byCheckIn, previousByCheckIn, previousCapture);
  } catch (error) {
    if (State.view === 'dashboard' && State.targetId === targetId) outlet.innerHTML = `<div class="inline-error">No se pudo cargar la consulta: ${esc(error.message)}</div>`;
  }
}

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
async function getHeatmap(targetId, photos = 1, force = false) {
  return cachedApi(State.heatmaps, targetId, `heatmap:${targetId}:${photos}`, `/api/hotels/heatmap?targetId=${targetId}&photos=${photos}`, force);
}
async function getDemandCurve(targetId, force = false) {
  return cachedApi(State.demandCurves, targetId, `demand:${targetId}`, `/api/analytics/demand-curve?targetId=${targetId}`, force);
}
async function getExternalObservations(force = false) {
  return cachedApi(State.externalObservations, 'all', 'external-observations', '/api/external/observations?limit=250', force);
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

function latestAdrComparison(photos) {
  const rows = (photos || []).filter((photo) => {
    if (!photo.scrapedAt || !Number.isFinite(Number(photo.avgPricePerNight))) return false;
    const date = new Date(photo.scrapedAt);
    return !Number.isNaN(date.getTime());
  }).slice().sort((a, b) => new Date(b.scrapedAt) - new Date(a.scrapedAt) || Number(b.id || 0) - Number(a.id || 0));
  if (rows.length < 2) return '<div class="empty">Se necesitan dos extracciones para representar la evolución del ADR.</div>';
  const current = rows[0];
  const previous = rows[1];
  const currentAdr = Number(current.avgPricePerNight);
  const previousAdr = Number(previous.avgPricePerNight);
  const change = previousAdr ? ((currentAdr - previousAdr) / previousAdr) * 100 : null;
  return `<div class="dashboard-weekly-compare" aria-label="Evolución del ADR entre las dos últimas extracciones"><div class="dashboard-week"><span>Extracción anterior · #${previous.id}</span><strong>${eur(previousAdr)}</strong><small>${fmtStamp(previous.scrapedAt)} · ${nEs(previous.capturedRows)} filas</small></div><div class="dashboard-weekly-delta"><strong>${signPct(change)}</strong><span>última vs. anterior</span><small>Cambio descriptivo de la media</small></div><div class="dashboard-week dashboard-week--current"><span>Última extracción · #${current.id}</span><strong>${eur(currentAdr)}</strong><small>${fmtStamp(current.scrapedAt)} · ${nEs(current.capturedRows)} filas</small></div></div>`;
}

function demandCurveHTML(points, currency = null) {
  if (currency == null) {
    const currencies = [...new Set((points || []).map((point) => point.currency).filter(Boolean))];
    if (!currencies.length) return '<div class="empty">Sin observaciones con moneda verificable.</div>';
    return currencies.map((code) => `<div><strong>${esc(code)} · tarifas observadas</strong>${demandCurveHTML(points.filter((point) => point.currency === code), code)}</div>`).join('');
  }
  const eur = (value) => `${nEs(value)} ${esc(currency)}`;
  const rows = (points || []).filter((point) => Number.isFinite(Number(point.daysUntilCheckIn)) && Number.isFinite(Number(point.avgAdr)) && Number.isFinite(Number(point.medianAdr))).slice().sort((a, b) => Number(a.daysUntilCheckIn) - Number(b.daysUntilCheckIn));
  if (rows.length < 2) return '<div class="empty">No hay suficientes observaciones para dibujar la curva por fecha de entrada.</div>';
  const values = rows.flatMap((row) => [Number(row.avgAdr), Number(row.medianAdr)]);
  const min = Math.floor(Math.min(...values) / 10) * 10;
  const max = Math.ceil(Math.max(...values) / 10) * 10;
  const W = 820, H = 226, x0 = 52, x1 = 800, y0 = 18, y1 = 166;
  const minDays = Number(rows[0].daysUntilCheckIn), maxDays = Number(rows[rows.length - 1].daysUntilCheckIn);
  const sx = (days) => x0 + ((Number(days) - minDays) / Math.max(1, maxDays - minDays)) * (x1 - x0);
  const sy = (value) => y0 + (1 - (Number(value) - min) / Math.max(1, max - min)) * (y1 - y0);
  const path = (field) => rows.map((row, index) => `${index ? 'L' : 'M'} ${sx(row.daysUntilCheckIn).toFixed(1)} ${sy(row[field]).toFixed(1)}`).join(' ');
  const marker = (field, color, label) => rows.map((row) => `<circle cx="${sx(row.daysUntilCheckIn).toFixed(1)}" cy="${sy(row[field]).toFixed(1)}" r="3.6" fill="var(--card)" stroke="${color}" stroke-width="2"><title>${label} · ${nEs(row.daysUntilCheckIn)} días hasta entrada: ${eur(row[field])}; ${nEs(row.observations)} observaciones (rango ${eur(row.minAdr)}–${eur(row.maxAdr)})</title></circle>`).join('');
  const labels = rows.map((row, index) => (index === 0 || index === rows.length - 1 || index % 3 === 0 ? `<text x="${sx(row.daysUntilCheckIn).toFixed(1)}" y="194" text-anchor="middle">${nEs(row.daysUntilCheckIn)} d</text>` : '')).join('');
  const group = (name, predicate) => {
    const values = rows.filter(predicate).map((row) => Number(row.avgAdr));
    return values.length ? { name, value: values.reduce((sum, value) => sum + value, 0) / values.length, points: values.length } : null;
  };
  const windows = [group('≤ 21 días', (row) => Number(row.daysUntilCheckIn) <= 21), group('22–42 días', (row) => Number(row.daysUntilCheckIn) >= 22 && Number(row.daysUntilCheckIn) <= 42), group('> 42 días', (row) => Number(row.daysUntilCheckIn) > 42)].filter(Boolean);
  const windowMarkup = windows.map((window) => `<div><span>${window.name}</span><strong>${eur(window.value)}</strong><small>${window.points} ${window.points === 1 ? 'punto' : 'puntos'}</small></div>`).join('');
  return `<div class="demand-curve-layout"><div class="demand-curve-chart"><svg viewBox="0 0 ${W} ${H}" width="100%" height="226" class="svg-block" role="img" aria-label="Tarifa pública media y mediana por días hasta la entrada"><g stroke="var(--line-soft)" stroke-width="1"><line x1="${x0}" y1="${y0}" x2="${x1}" y2="${y0}"></line><line x1="${x0}" y1="${(y0 + y1) / 2}" x2="${x1}" y2="${(y0 + y1) / 2}"></line><line x1="${x0}" y1="${y1}" x2="${x1}" y2="${y1}"></line></g><g font-family="'Space Mono',monospace" font-size="9" fill="var(--fainter)"><text x="${x0 - 8}" y="${y0 + 3}" text-anchor="end">${eur(max)}</text><text x="${x0 - 8}" y="${y1 + 3}" text-anchor="end">${eur(min)}</text>${labels}</g><path d="${path('medianAdr')}" fill="none" stroke="#b18322" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"></path><path d="${path('avgAdr')}" fill="none" stroke="var(--ac)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"></path>${marker('medianAdr', '#b18322', 'ADR mediano')}${marker('avgAdr', 'var(--ac)', 'ADR medio')}</svg><div class="legend demand-curve-legend"><span><i style="width:12px;height:2px;border-radius:0;background:var(--ac);"></i>ADR medio</span><span><i style="width:12px;height:2px;border-radius:0;background:#b18322;"></i>ADR mediano</span><span>cada punto incluye sus observaciones reales</span></div></div><aside class="demand-curve-windows" aria-label="ADR por horizonte de entrada">${windowMarkup}</aside></div>`;
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

function dashboardPrioritiesHTML(insights, rows) {
  const rank = { critical: 0, warning: 1, info: 2 };
  const hotelKeys = new Map((rows || []).filter((row) => row.hotelName && row.hotelKey).map((row) => [row.hotelName, row.hotelKey]));
  const list = (insights || []).slice().sort((a, b) => (rank[a.severity] ?? 3) - (rank[b.severity] ?? 3) || String(a.title || '').localeCompare(String(b.title || ''), 'es')).slice(0, 6);
  if (!list.length) return `<article class="card card--pad dashboard-priorities mb12"><div class="dashboard-priorities__head"><div><div class="card__kicker">Prioridades de mercado</div><h2>Sin señales prioritarias</h2></div><span class="table-filter-status">Lectura actual</span></div><p class="dashboard-priorities__empty">No hay alertas calculadas con la captura actual.</p></article>`;
  const severityLabel = { critical: 'Crítica', warning: 'Atención', info: 'Lectura' };
  const items = list.map((insight) => {
    const hotelKey = insight.hotelKey || hotelKeys.get(insight.hotelName);
    const value = insight.value != null && ['price_leader', 'protect_rate', 'aggressive_pricing', 'premium_opportunity'].includes(insight.type) ? eur(insight.value) : insight.changePct != null ? signPct(insight.changePct) : insight.value != null ? nEs(insight.value) : '—';
    const action = hotelKey ? `<button type="button" class="dashboard-priority__action" data-dashboard-hotel="${esc(hotelKey)}" data-priority-hotel="true" aria-label="Abrir ${esc(insight.hotelName || insight.title)} en el mapa">Mapa ↗</button>` : '';
    return `<li class="dashboard-priority dashboard-priority--${esc(insight.severity || 'info')}"><span class="dashboard-priority__severity">${severityLabel[insight.severity] || 'Lectura'}</span><div class="dashboard-priority__body"><strong>${esc(insight.title || 'Señal de mercado')}</strong><p>${esc(insight.message || '')}</p></div><div class="dashboard-priority__metric"><strong>${value}</strong>${insight.benchmark != null ? `<span>ref. ${eur(insight.benchmark)}</span>` : ''}</div>${action}</li>`;
  }).join('');
  return `<article class="card card--pad dashboard-priorities mb12" aria-label="Prioridades de mercado"><div class="dashboard-priorities__head"><div><div class="card__kicker">Prioridades de mercado</div><h2>Señales que requieren revisión</h2></div><span class="table-filter-status">${list.length} ${list.length === 1 ? 'señal' : 'señales'} calculadas</span></div><ol class="dashboard-priority-list">${items}</ol></article>`;
}

/* Contexto público: se muestra separado de las capturas para no mezclar
   señales comparables con la tarifa observada del hotel. */
function externalSegmentMap(segment) {
  return String(segment || '').split(';').reduce((acc, part) => {
    const i = part.indexOf('=');
    if (i > 0) acc[part.slice(0, i).trim()] = part.slice(i + 1).trim();
    return acc;
  }, {});
}

function externalProvinceForTarget(name) {
  const value = String(name || '').toLowerCase();
  if (/tenerife|santa cruz|la gomera|el hierro/.test(value)) return 'Santa Cruz de Tenerife';
  if (/gran canaria|fuerteventura|lanzarote|las palmas/.test(value)) return 'Las Palmas';
  return '';
}

function externalMonthKey(value) {
  return /^\d{4}-\d{2}/.test(String(value || '')) ? String(value).slice(0, 7) : '';
}

function externalMonthLabel(value) {
  if (!value) return 'Periodo no informado';
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return 'Periodo no informado';
  return date.toLocaleDateString('es-ES', { month: 'long', year: 'numeric', timeZone: 'UTC' });
}

function externalDateLabel(value) {
  if (!value) return 'Fecha no informada';
  const date = new Date(`${String(value).slice(0, 10)}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return 'Fecha no informada';
  return date.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric', timeZone: 'UTC' });
}

function externalUnitValue(row) {
  const value = Number(row?.value);
  if (!Number.isFinite(value)) return '—';
  const unit = String(row.unit || '').toLowerCase();
  const descriptor = `${row.metric || ''} ${row.segment || ''}`.toLowerCase();
  if (unit.includes('percent') || /ocupaci|tasa/.test(descriptor)) return `${nEs(value, 1)}%`;
  if (unit.includes('eur') || /adr|revpar|tarifa|precio/.test(descriptor)) return eur(value, 0);
  if (row.metric === 'accommodation_capacity' || /plaza|habitaci|room|cama/.test(descriptor)) return nEs(value, 0);
  if (row.metric === 'travellers_or_nights') return nEs(value, 1);
  return `${nEs(value, Number.isInteger(value) ? 0 : 1)}${row.unit ? ` ${esc(row.unit)}` : ''}`;
}

function externalMetricLabel(row) {
  const descriptor = `${row.metric || ''} ${row.segment || ''}`.toLowerCase();
  if (/revpar|ingreso.*habit/.test(descriptor)) return 'RevPAR';
  if (/adr|tarifa media|tarifa_media/.test(descriptor)) return 'ADR';
  if (/ocupaci|tasa/.test(descriptor)) return 'Ocupación';
  if (/plaza|habitaci|room|cama/.test(descriptor)) return 'Capacidad';
  if (row.metric === 'travellers_or_nights') return /pernoct|noche/.test(descriptor) ? 'Pernoctaciones' : 'Viajeros';
  if (row.metric === 'accommodation_capacity') return 'Capacidad';
  return String(row.metric || 'Indicador').replace(/_/g, ' ');
}

function externalStatusBadge(period, targetMonth, quality) {
  const stale = quality === 'stale';
  const comparable = period && targetMonth && externalMonthKey(period) === targetMonth;
  const label = stale ? 'Desactualizado' : comparable ? 'Comparable' : period ? 'Periodo distinto' : 'Sin periodo';
  const tone = stale ? 'warn' : comparable ? 'good' : 'neutral';
  return `<span class="dashboard-external-status dashboard-external-status--${tone}">${label}</span>`;
}

function dashboardExternalHTML(observations, target, snapshot, rows) {
  const sourceRows = (observations || []).filter((row) => row && Number.isFinite(Number(row.value)));
  const profile = snapshot?.snapshot?.captureProfile || {};
  const firstRow = (rows || []).find((row) => row.checkIn) || {};
  const checkIn = profile.checkIn || firstRow.checkIn || '';
  const checkOut = profile.checkOut || firstRow.checkOut || '';
  const targetMonth = externalMonthKey(checkIn);
  const province = externalProvinceForTarget(target?.name);
  const fetchedAt = sourceRows.map((row) => row.fetchedAt).filter(Boolean).sort().pop();
  const fetchedLabel = fetchedAt ? `Última actualización ${fmtStamp(fetchedAt)}` : 'Actualización no informada';
  const stayLabel = checkIn && checkOut ? `${esc(externalDateLabel(checkIn))} → ${esc(externalDateLabel(checkOut))}` : 'Estancia no informada';
  const stayMonthLabel = targetMonth ? externalMonthLabel(`${targetMonth}-01`) : 'Mes no informado';

  const istacRows = sourceRows.filter((row) => row.sourceId === 'istac-accommodation');
  const istacPeriod = istacRows.map((row) => row.periodStart).filter(Boolean).sort().pop() || '';
  const istacLatest = istacRows.filter((row) => !istacPeriod || row.periodStart === istacPeriod);
  const seenMetrics = new Set();
  const istacMetrics = istacLatest.filter((row) => {
    const label = externalMetricLabel(row);
    if (seenMetrics.has(label)) return false;
    seenMetrics.add(label);
    return true;
  }).slice(0, 4);
  const istacBody = istacMetrics.length ? `<div class="dashboard-external-metrics">${istacMetrics.map((row) => `<div class="dashboard-external-metric"><span>${esc(externalMetricLabel(row))}</span><strong>${externalUnitValue(row)}</strong><small>${esc(row.geographyCode || row.geographyType || 'Ámbito no informado')}</small></div>`).join('')}</div>` : `<div class="dashboard-external-empty"><strong>Sin observaciones ISTAC sincronizadas</strong><span>El conector está preparado; no se muestran ceros ni estimaciones.</span></div>`;
  const istacFoot = istacRows.length ? `Periodo observado: ${esc(externalMonthLabel(istacPeriod))} · ${externalStatusBadge(istacPeriod, targetMonth, istacLatest[0]?.qualityStatus)}` : 'Fuente pendiente de sincronización';

  const dataesturAll = sourceRows.filter((row) => row.sourceId === 'dataestur-segittur' && (!province || row.geographyCode === province));
  const dataesturPeriod = dataesturAll.map((row) => row.periodStart).filter(Boolean).sort().pop() || '';
  const dataesturLatest = dataesturAll.filter((row) => !dataesturPeriod || row.periodStart === dataesturPeriod);
  const grouped = new Map();
  dataesturLatest.forEach((row) => {
    const seg = Object.assign({}, row.metadata || {}, externalSegmentMap(row.segment));
    const category = seg.category || 'Categoría no informada';
    const lead = seg.leadTime || seg.lead_time || 'Antelación no informada';
    const key = `${category}|${lead}`;
    if (!grouped.has(key)) grouped.set(key, { category, lead, weekday: null, weekend: null });
    const item = grouped.get(key);
    if ((seg.dayType || seg.day_type) === 'weekend') item.weekend = row.value;
    else item.weekday = row.value;
  });
  const leadOrder = { '1 Semana': 1, '2 Semanas': 2, '1 Mes': 3, '3 Meses': 4 };
  const categoryOrder = (value) => { const match = String(value).match(/(\d+)/); return match ? -Number(match[1]) : 0; };
  const dataesturGroups = [...grouped.values()].sort((a, b) => categoryOrder(a.category) - categoryOrder(b.category) || (leadOrder[a.lead] || 99) - (leadOrder[b.lead] || 99)).slice(0, 10);
  const dataesturBody = dataesturGroups.length ? `<div class="dashboard-external-table-wrap"><table class="dashboard-external-table"><caption class="sr-only">Precios Dataestur por categoría y antelación</caption><thead><tr><th scope="col">Categoría</th><th scope="col">Antelación</th><th scope="col" class="r">Laborable</th><th scope="col" class="r">Fin de semana</th></tr></thead><tbody>${dataesturGroups.map((item) => `<tr><td>${esc(item.category)}</td><td>${esc(item.lead)}</td><td class="num">${item.weekday == null ? '—' : eur(item.weekday, 0)}</td><td class="num">${item.weekend == null ? '—' : eur(item.weekend, 0)}</td></tr>`).join('')}</tbody></table></div>` : `<div class="dashboard-external-empty"><strong>Sin observaciones Dataestur para este ámbito</strong><span>Comprueba la sincronización o amplía el periodo de consulta.</span></div>`;
  const dataesturFoot = dataesturAll.length ? `Periodo observado: ${esc(externalMonthLabel(dataesturPeriod))} · ${externalStatusBadge(dataesturPeriod, targetMonth, dataesturLatest[0]?.qualityStatus)}` : `Ámbito: ${esc(province || 'Canarias')}`;

  return `<article class="card card--pad dashboard-external-card mb12" aria-label="Contexto externo de fuentes públicas">
    <div class="dashboard-external__head"><div><div class="card__kicker">Contexto externo</div><h2>Referencia pública para la estancia</h2><p>Indicadores agregados para contrastar el mercado; no sustituyen las capturas de tarifas.</p></div><div class="dashboard-external__meta"><span>Estancia objetivo <strong>${stayLabel}</strong></span><span>Mes de estancia <strong>${esc(stayMonthLabel)}</strong></span><span>${esc(fetchedLabel)}</span></div></div>
    <div class="dashboard-external-grid">
      <section class="dashboard-external-source dashboard-external-source--istac" aria-labelledby="dashboardExternalIstacTitle"><div class="dashboard-external-source__head"><div><div class="card__kicker">ISTAC · DESTINO</div><h3 id="dashboardExternalIstacTitle">Actividad y capacidad</h3></div><a href="https://www.gobiernodecanarias.org/istac/datos-abiertos/documentacion-api/index.html" target="_blank" rel="noreferrer">API ↗</a></div>${istacBody}<div class="dashboard-external__foot">${istacFoot}</div></section>
      <section class="dashboard-external-source dashboard-external-source--dataestur" aria-labelledby="dashboardExternalDataesturTitle"><div class="dashboard-external-source__head"><div><div class="card__kicker">DATAESTUR · MERCADO Y ANTELACIÓN</div><h3 id="dashboardExternalDataesturTitle">Precio hotelero de referencia</h3></div><a href="https://www.dataestur.es/apidata/" target="_blank" rel="noreferrer">API ↗</a></div>${dataesturBody}<div class="dashboard-external__foot">${dataesturFoot} · EUR/habitación-noche</div></section>
    </div>
    <div class="dashboard-external__legend">Periodo de estancia y periodo observado se muestran por separado. Los datos externos se conservan como observaciones agregadas con su fuente, ámbito, unidad y fecha de actualización.</div>
  </article>`;
}

/* =============================================================== DASHBOARD */
async function renderDashboard() {
  const host = mount('dashboard');
  const request = {};
  host._dashboardRequest = request;
  const targetId = State.targetId;
  const t = activeTarget();
  destroyDashboardMap();
  skeleton(host, 'dashboard');
  if (!Number.isInteger(State.targetId)) {
    renderNoActiveTarget(host, 'Lectura de mercado', 'Panel principal');
    return;
  }
  let d, s, history, captures, demand, external;
  try { [d, s, history, captures, demand, external] = await Promise.all([getMetrics(State.targetId), getSnapshot(State.targetId), getPhotoHistory(State.targetId), getCaptureHistory(State.targetId), getDemandCurve(State.targetId), getExternalObservations().catch(() => ({ observations: [] }))]); }
  catch (e) { if (host._dashboardRequest === request && State.targetId === targetId) host.innerHTML = `<div class="page">${pageHead('Lectura de mercado', 'Panel principal', '')}<div class="inline-error">No se pudieron cargar las métricas: ${esc(e.message)}</div></div>`; return; }
  if (host._dashboardRequest !== request || State.targetId !== targetId || State.view !== 'dashboard') return;

  if (d.currencyPolicy?.status === 'blocked') { host.innerHTML = `<div class="page"><div class="inline-error">${esc(d.currencyPolicy.reason)}</div></div>`; return; }
  const m = d.market || {}, mv = d.movement || {}, rs = d.rateShoppingIndex || {}, cmp = d.comparison || {};
  const cs = d.competitiveSet || [];
  const snapshot = s.latest || {};
  const allRows = snapshot.rows || [];
  const heatmap = {points: allRows.filter((row) => row.latitude != null && row.longitude != null && row.pricePerNight > 0)
    .map((row) => ({...row, avgPricePerNight: row.pricePerNight, samples: 1}))};
  const pricedRows = allRows.filter((row) => Number(row.pricePerNight) > 0);
  const prices = cs.map((h) => h.pricePerNight).filter((p) => p > 0);
  const p75 = rs.topQuartileThreshold || percentileVal(prices, 75);
  const p25 = percentileVal(prices, 25);
  const med = m.medianPricePerNight || median(prices);
  const range = (m.maxPricePerNight || 0) - (m.minPricePerNight || 0);
  const detailsByKey = Object.fromEntries(allRows.map((row) => [row.hotelKey, row]));

  // La tabla es compacta, pero cada fila conserva el detalle real de la captura.
  const top = (cs.length ? cs : pricedRows).slice(0, 12);
  const maxTop = top.length ? top[0].pricePerNight : 1;
  const rows = top.map((h) => {
    const detail = detailsByKey[h.hotelKey] || h;
    const gap = h.gapVsMedianPct;
    const w = Math.max(6, Math.round((h.pricePerNight / maxTop) * 100));
    const col = h.pricePerNight >= p75 ? 'var(--hi)' : h.pricePerNight >= med ? 'var(--mid)' : 'var(--lo)';
    return `<tr class="dashboard-hotel-row">
      <td class="row-toggle-cell"><button type="button" class="row-expand-toggle" data-dashboard-expand="${esc(h.hotelKey)}" aria-expanded="false" aria-label="Ver detalle de ${esc(h.hotelName)}">▸</button></td>
      <td class="name">${esc(h.hotelName)}${detail.city ? `<small class="hotel-name-meta">${esc(detail.city)}</small>` : ''}</td>
      <td class="num">${eur(h.pricePerNight)}</td>
      <td><div class="bar"><div class="bar__track"><div class="bar__fill" style="width:${w}%; background:${col};"></div></div><span class="bar__val">${signPct(gap)}</span></div></td>
      <td class="num">${h.rating != null ? nEs(h.rating, 1) : '—'}</td>
      <td class="r">${availChip(detail)}</td>
    </tr><tr class="dashboard-detail-row" data-dashboard-detail="${esc(h.hotelKey)}" hidden><td colspan="6">${dashboardHotelDetailHTML(detail, h)}</td></tr>`;
  }).join('');

  const ridgeRows = buildDashboardZoneRows(allRows);
  const heatRows = pricedRows.slice().sort((a, b) => Math.abs(Number(b.pricePerNight) - med) - Math.abs(Number(a.pricePerNight) - med)).slice(0, 14);
  const latestAt = snapshot.snapshot?.scrapedAt || d.latestSnapshot?.scrapedAt;
  const dashboardView = restoreDashboardView();
  const heatCells = heatRows.length ? heatRows.map((row) => {
    const gap = med ? ((Number(row.pricePerNight) - med) / med) * 100 : 0;
    const level = Math.max(0, Math.min(4, Math.floor(((Number(row.pricePerNight) - (m.minPricePerNight || 0)) / (range || 1)) * 5)));
    return `<button type="button" class="dashboard-heat-cell dashboard-heat-cell--${level}" data-dashboard-hotel="${esc(row.hotelKey)}" aria-label="${esc(row.hotelName)}, ADR ${eur(row.pricePerNight)}, ${signPct(gap)} frente a la mediana"><span>${esc(row.hotelName)}</span><strong>${eur(row.pricePerNight)}</strong><small>${signPct(gap)} vs. mediana</small></button>`;
  }).join('') : '<div class="empty">No hay tarifas comparables para construir el heatmap.</div>';

  const marketPanelHTML = `<div class="grid dashboard-map-grid mb12">
      <article class="card card--pad dashboard-map-card">
        <div class="card__head dashboard-map-card__head">
          <div><div class="card__kicker" style="margin-bottom:5px;">Mapa hotelero</div><h2>Precio por ubicación</h2><p>El color representa la intensidad del ADR. Selecciona un punto para ver su detalle.</p></div>
          <div class="dashboard-map-meta"><span id="dashboardMapCount">${heatmap.points?.length || 0} hoteles</span><span id="dashboardMapLegend" class="legend"><span><i style="background:#2f7d5c;"></i>bajo</span><span><i style="background:#c88925;"></i>medio</span><span><i style="background:#b94f50;"></i>alto</span></span></div>
        </div>
        <div class="dashboard-map-layout">
          <div id="dashboardHotelMap" class="dashboard-map" aria-label="Mapa de hoteles del mercado activo"><aside id="dashboardHotelDrawer" class="dashboard-drawer" role="complementary" aria-labelledby="dashboardHotelDrawerTitle" aria-live="polite" hidden></aside></div>
        </div>
      </article>
      <article class="card card--pad dashboard-price-card">
        <div class="card__head" style="margin-bottom:14px;">
          <div><div class="card__kicker" style="margin-bottom:5px;">Heatmap de ADR</div><h2>Hoteles fuera del centro</h2><p>Ordenado por distancia a la mediana del mercado.</p></div>
          <span class="pill-tag">${heatRows.length} hoteles</span>
        </div>
        <div class="dashboard-heat-grid" aria-label="Heatmap de precios hoteleros">${heatCells}</div>
      </article>
    </div>`;

  const chartsPanelHTML = `<div class="grid mb12 dashboard-distribution-grid">
      <article class="card card--pad">
        <div class="card__head" style="margin-bottom:6px;">
          <div><div class="card__kicker" style="margin-bottom:5px;">Dispersión del set</div><h2>Enjambre de tarifas</h2><p>Un punto por hotel. La aglomeración marca dónde compite el mercado.</p></div>
          <div class="legend"><span><i style="background:var(--lo);"></i>&lt;${nEs(med)}</span><span><i style="background:var(--mid);"></i>${nEs(med)}–${nEs(p75)}</span><span><i style="background:var(--ac);"></i>&gt;${nEs(p75)}</span></div>
        </div>
        ${beeswarmSVG(prices, med, p75)}
      </article>
      <article class="card card--pad card--dark" style="display:flex; flex-direction:column;">
        <div class="card__kicker" style="margin-bottom:4px;">Posición</div>
        <h2 style="color:#fff;">Percentil del set</h2>
        ${gaugeSVG(50)}
        <p style="margin:6px 0 0; font-size:12px; line-height:1.5;">La mediana (${eur(med)}) representa el P50 de las tarifas observadas.</p>
      </article>
    </div>

    <article class="card card--pad mb12">
      <div class="card__head" style="margin-bottom:8px;">
        <div><div class="card__kicker" style="margin-bottom:5px;">Histórico de capturas</div><h2>Evolución entre extracciones</h2><p>ADR medio de las capturas disponibles para ${esc(t ? t.name : 'el mercado activo')}.</p></div>
        <span class="pill-tag">${(history.photos || []).length} extracciones</span>
      </div>
      ${adrHistorySVG(history.photos || [])}
      ${latestAdrComparison(history.photos || [])}
    </article>

    <article class="card card--pad mb12">
      <div class="card__head demand-curve-head">
        <div><div class="card__kicker" style="margin-bottom:5px;">Curva de entrada</div><h2>ADR según días hasta la estancia</h2><p>Agregado de observaciones reales por horizonte de entrada; no es una previsión.</p></div>
        <span class="pill-tag">${(demand.demandCurve || []).length} puntos</span>
      </div>
      ${demandCurveHTML(demand.demandCurve || [])}
    </article>

    <article class="card card--pad mb12">
      <div class="card__head" style="margin-bottom:14px;">
        <div><div class="card__kicker" style="margin-bottom:5px;">Distribución del mercado</div><h2>Densidad de ADR por zona</h2><p>Dónde se concentra la tarifa dentro del mercado seleccionado.</p></div>
        <span class="pill-tag">${ridgeRows.length} zonas</span>
      </div>
      ${ridgelineSVG(ridgeRows)}
    </article>`;

  const tablePanelHTML = `<article class="card table-card">
      <div class="table-card__head">
        <div><div class="card__kicker" style="margin-bottom:5px;">Lectura operativa</div><h2>Cola alta del mercado</h2></div>
        <button type="button" class="btn btn--sm" data-nav="hotels">Ver los ${allRows.length} →</button>
      </div>
      <table class="t">
        <thead><tr><th aria-label="Detalle"></th><th>Hotel</th><th class="r">ADR</th><th style="width:180px;">vs. mediana</th><th class="r">Nota</th><th class="r">Disponibilidad</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </article>`;

  destroyDashboardMap();
  host.innerHTML = `<div class="page dashboard-page">
    ${pageHead('Lectura de mercado',
      `${esc(t ? t.name : 'Mercado')} · ${allRows.length} hoteles observados · un mercado activo.`,
      '', `${esc(d.dataQuality?.freshness?.etiqueta || 'Sin fecha verificable')} · Extracción ${fmtStamp(latestAt)}`)}

    <div class="grid grid--4 mb12">
      <article class="kpi">
        <div class="kpi__label">ADR mediano</div>
        <div class="kpi__value"><strong data-count="${Math.round(med)}">${Math.round(med)}</strong><span class="kpi__unit">€</span></div>
        <div class="kpi__foot">Tarifa pública · habitación/noche</div>
      </article>
      <article class="kpi">
        <div class="kpi__label">Hoteles con tarifa</div>
        <div class="kpi__value"><strong data-count="${pricedRows.length}">0</strong><span class="kpi__unit">/ ${allRows.length}</span></div>
        <div class="meter"><i style="width:${allRows.length ? Math.round((pricedRows.length / allRows.length) * 100) : 0}%;"></i></div>
        <div class="kpi__foot">${allRows.length ? `${nEs((pricedRows.length / allRows.length) * 100, 0)}% con precio observable` : 'Sin hoteles observados'}</div>
      </article>
      <article class="kpi">
        <div class="kpi__label">Banda central ADR</div>
        <div class="kpi__value"><strong>${eur(p25, 0)}</strong><span class="kpi__unit">— ${eur(p75, 0)}</span></div>
        <div class="kpi__sub">P25 — P75 · ${eur(m.minPricePerNight)} — ${eur(m.maxPricePerNight)}</div>
      </article>
      <article class="kpi">
        <div class="kpi__label">Movimiento ADR</div>
        <div class="kpi__value"><strong class="${(mv.avgPricePerNightChangePct || 0) < 0 ? 'pos' : (mv.avgPricePerNightChangePct || 0) > 0 ? 'neg' : ''}">${signPct(mv.avgPricePerNightChangePct)}</strong></div>
        <div class="kpi__foot">${mv.isComparable ? `${mv.changedHotels} hoteles movidos · ▲${mv.priceIncreases} ▼${mv.priceDrops}` : 'Sin comparativa disponible'}</div>
      </article>
    </div>

    ${dashboardViewSwitcherHTML(dashboardView)}

    <section id="dashboard-panel-market" class="dashboard-view-panel" role="tabpanel" aria-labelledby="dashboard-view-tab-market"${dashboardView === 'market' ? '' : ' hidden'}>${marketPanelHTML}</section>
    <section id="dashboard-panel-charts" class="dashboard-view-panel" role="tabpanel" aria-labelledby="dashboard-view-tab-charts"${dashboardView === 'charts' ? '' : ' hidden'}>${chartsPanelHTML}</section>
    <section id="dashboard-panel-explorer" class="dashboard-view-panel" role="tabpanel" aria-labelledby="dashboard-view-tab-explorer"${dashboardView === 'explorer' ? '' : ' hidden'}>${dashboardExplorerHTML(captures.captures || [], s.latest || {})}</section>

    ${dashboardPrioritiesHTML(d.insights, allRows)}

    ${dashboardExternalHTML(external?.observations || [], t, s.latest || {}, allRows)}

    ${tablePanelHTML}
  </div>`;
  runCounters(host);
  if (dashboardView === 'market') renderDashboardHotelMap(heatmap.points || [], allRows);
  void loadDashboardExplorer(host);
}

function availChipInline(h) {
  // competitiveSet no trae disponibilidad; se muestra guion salvo señal.
  return '<span class="dim">—</span>';
}

function buildDashboardZoneRows(rows) {
  const groups = new Map();
  (rows || []).filter((row) => Number(row.pricePerNight) > 0).forEach((row) => {
    const name = row.city || row.popularDistrict || row.displayLocation || 'Mercado activo';
    if (!groups.has(name)) groups.set(name, []);
    groups.get(name).push(Number(row.pricePerNight));
  });
  return [...groups.entries()].sort((a, b) => b[1].length - a[1].length).slice(0, 5).map(([name, values]) => ({ name, prices: values, median: Math.round(median(values)) }));
}

function dashboardHotelDetailHTML(row, summary = row) {
  const checkIn = row.checkIn || summary.checkIn;
  const checkOut = row.checkOut || summary.checkOut;
  return `<div class="dashboard-detail-grid">
    <div><span>Habitación</span><strong>${esc(row.roomType || summary.roomType || '—')}</strong></div>
    <div><span>Régimen</span><strong>${esc(row.board || summary.board || '—')}</strong></div>
    <div><span>Estancia</span><strong>${esc(checkIn || '—')} → ${esc(checkOut || '—')}</strong></div>
    <div><span>Precio total</span><strong>${eur(row.price)}</strong></div>
    <div><span>Precio original</span><strong>${eur(row.priceOriginal)}</strong></div>
    <div><span>Descuento</span><strong>${row.discountPct != null ? signPct(row.discountPct) : '—'}</strong></div>
    <div><span>Cancelación</span><strong>${row.freeCancellation === true ? 'Gratis' : row.freeCancellation === false ? 'No incluida' : '—'}</strong></div>
    <div><span>Ubicación</span><strong>${esc(row.address || row.displayLocation || row.city || '—')}</strong></div>
  </div><div class="dashboard-detail-foot"><span>Fuente: Booking${row.detailUrl ? ' · detalle disponible' : ''}</span>${row.detailUrl ? `<a href="${esc(row.detailUrl)}" target="_blank" rel="noreferrer">Abrir fuente ↗</a>` : ''}</div>`;
}

function dashboardDrawerOfferHTML(row, summary = row) {
  const checkIn = row.checkIn || summary.checkIn;
  const checkOut = row.checkOut || summary.checkOut;
  const location = row.address || row.displayLocation || row.city || '—';
  return `<div class="dashboard-offer__head"><div><strong>Condiciones de la oferta</strong><span>Producto, precio y flexibilidad observados</span></div></div>
    <div class="dashboard-offer__groups">
      <section aria-label="Producto y estancia"><h4>Producto y estancia</h4><dl class="dashboard-offer__grid">
        <div><dt>Habitación</dt><dd>${esc(row.roomType || summary.roomType || '—')}</dd></div>
        <div><dt>Régimen</dt><dd>${esc(row.board || summary.board || '—')}</dd></div>
        <div><dt>Estancia</dt><dd>${esc(checkIn || '—')} → ${esc(checkOut || '—')}</dd></div>
        <div><dt>Ubicación</dt><dd>${esc(location)}</dd></div>
      </dl></section>
      <section aria-label="Precio y flexibilidad"><h4>Precio y flexibilidad</h4><dl class="dashboard-offer__grid">
        <div><dt>Precio total</dt><dd>${eur(row.price)}</dd></div>
        <div><dt>Precio original</dt><dd>${eur(row.priceOriginal)}</dd></div>
        <div><dt>Descuento</dt><dd>${row.discountPct != null ? signPct(row.discountPct) : '—'}</dd></div>
        <div><dt>Cancelación</dt><dd>${row.freeCancellation === true ? 'Gratis' : row.freeCancellation === false ? 'No incluida' : '—'}</dd></div>
      </dl></section>
    </div>
    <div class="dashboard-offer__foot"><span>Fuente: Booking${row.detailUrl ? ' · detalle disponible' : ''}</span>${row.detailUrl ? `<a href="${esc(row.detailUrl)}" target="_blank" rel="noreferrer">Abrir fuente ↗</a>` : ''}</div>`;
}

function rateNights(checkIn, checkOut) {
  if (!checkIn || !checkOut) return null;
  const start = Date.parse(`${checkIn}T00:00:00Z`);
  const end = Date.parse(`${checkOut}T00:00:00Z`);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return null;
  return Math.round((end - start) / 86400000);
}

function rateShortDate(value) {
  if (!value) return '—';
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('es-ES', { day: '2-digit', month: 'short', timeZone: 'UTC' }).replace('.', '');
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

function dashboardHotelForKey(key) {
  if (key && typeof key === 'object') return key;
  const rows = State.snapshots[State.targetId]?.latest?.rows || [];
  return rows.find((row) => row.hotelKey === key) || State.metrics[State.targetId]?.competitiveSet?.find((row) => row.hotelKey === key) || null;
}

function dashboardSameStayComparisonHTML(history, chartWidth, amount) {
  const valid = (history || []).filter((entry) => entry.snapshotId != null && Number.isFinite(Date.parse(entry.scrapedAt)) && Number.isFinite(Number(entry.pricePerNight)));
  const snapshots = new Map();
  valid.forEach((entry) => {
    if (!snapshots.has(entry.snapshotId)) snapshots.set(entry.snapshotId, []);
    snapshots.get(entry.snapshotId).push(entry);
  });
  const orderedSnapshots = [...snapshots.entries()].map(([snapshotId, entries]) => ({
    snapshotId,
    entries,
    at: Math.max(...entries.map((entry) => Date.parse(entry.scrapedAt))),
  })).sort((a, b) => a.at - b.at || a.snapshotId - b.snapshotId);
  const groups = [];
  const maxGap = 20 * 60 * 1000;
  orderedSnapshots.forEach((snapshot) => {
    let group = groups.at(-1);
    if (!group || snapshot.at - group.lastAt > maxGap) {
      group = { snapshots: [], lastAt: snapshot.at };
      groups.push(group);
    }
    group.snapshots.push(snapshot);
    group.lastAt = snapshot.at;
  });
  if (groups.length < 2) return '<section class="dashboard-drawer__section"><div class="dashboard-trend-empty">Se necesitan dos barridos de extracción para comparar la misma fecha de entrada.</div></section>';
  const aggregateGroup = (group) => {
    const byStay = new Map();
    group.snapshots.flatMap((snapshot) => snapshot.entries).forEach((entry) => {
      const stay = entry.checkIn;
      if (!stay) return;
      const item = byStay.get(stay) || { stay, values: [], snapshotIds: [] };
      item.values.push(Number(entry.pricePerNight));
      if (!item.snapshotIds.includes(entry.snapshotId)) item.snapshotIds.push(entry.snapshotId);
      byStay.set(stay, item);
    });
    return [...byStay.values()].map((item) => ({
      stay: item.stay,
      pricePerNight: median(item.values),
      snapshotIds: item.snapshotIds,
    }));
  };
  const previous = aggregateGroup(groups.at(-2));
  const current = aggregateGroup(groups.at(-1));
  const previousByStay = new Map(previous.map((entry) => [entry.stay, entry]));
  const currentByStay = new Map(current.map((entry) => [entry.stay, entry]));
  const shared = [...new Set([...previousByStay.keys()].filter((stay) => currentByStay.has(stay)))].sort();
  if (!shared.length) return '<section class="dashboard-drawer__section"><div class="dashboard-trend-empty">Los dos últimos barridos no comparten fechas de entrada comparables.</div></section>';
  const pairs = shared.map((stay) => {
    const before = previousByStay.get(stay), after = currentByStay.get(stay);
    return { stay, previous: before.pricePerNight, current: after.pricePerNight, changePct: before.pricePerNight ? ((after.pricePerNight / before.pricePerNight) - 1) * 100 : null };
  });
  const values = pairs.flatMap((pair) => [pair.previous, pair.current]);
  const minRaw = Math.min(...values), maxRaw = Math.max(...values);
  const chartMin = Math.floor((minRaw - 5) / 10) * 10, chartMax = Math.ceil((maxRaw + 5) / 10) * 10;
  const W = Math.max(240, Number(chartWidth) || 324), H = 158, x0 = 35, x1 = W - 10, y0 = 13, y1 = 108;
  const sx = (index) => x0 + (index / Math.max(1, pairs.length - 1)) * (x1 - x0);
  const sy = (value) => y0 + (1 - (value - chartMin) / Math.max(1, chartMax - chartMin)) * (y1 - y0);
  const shortDate = (iso) => { const parts = String(iso || '').slice(0, 10).split('-'); return parts.length === 3 ? `${parts[2]}/${parts[1]}` : String(iso || '—'); };
  const labels = pairs.map((pair, index) => `<text x="${sx(index).toFixed(1)}" y="130" text-anchor="middle">${esc(shortDate(pair.stay))}</text>`).join('');
  const pathFor = (key) => pairs.map((pair, index) => `${index ? 'L' : 'M'} ${sx(index).toFixed(1)} ${sy(pair[key]).toFixed(1)}`).join(' ');
  const pointsFor = (key, color, label) => pairs.map((pair, index) => `<circle cx="${sx(index).toFixed(1)}" cy="${sy(pair[key]).toFixed(1)}" r="3.4" fill="var(--card)" stroke="${color}" stroke-width="2"><title>${label} · entrada ${esc(pair.stay)} · ${amount(pair[key])} por noche</title></circle>`).join('');
  const firstPrevious = groups.at(-2).snapshots[0]?.snapshotId, lastPrevious = groups.at(-2).snapshots.at(-1)?.snapshotId;
  const firstCurrent = groups.at(-1).snapshots[0]?.snapshotId, lastCurrent = groups.at(-1).snapshots.at(-1)?.snapshotId;
  const groupLabel = (first, last) => first === last ? `foto #${first}` : `fotos #${first}–#${last}`;
  return `<section class="dashboard-drawer__section dashboard-drawer__same-date"><div class="dashboard-trend-head"><div><strong>Comparación por fecha de entrada</strong><span>Eje X = fecha de entrada · ${groupLabel(firstPrevious, lastPrevious)} frente a ${groupLabel(firstCurrent, lastCurrent)}</span></div></div><svg viewBox="0 0 ${W} ${H}" width="100%" height="158" class="dashboard-trend-svg" role="img" aria-label="Comparación del precio por fecha de entrada entre la captura anterior y la última captura"><g stroke="var(--line-soft)" stroke-width="1"><line x1="${x0}" y1="${y0}" x2="${x1}" y2="${y0}"></line><line x1="${x0}" y1="${(y0 + y1) / 2}" x2="${x1}" y2="${(y0 + y1) / 2}"></line><line x1="${x0}" y1="${y1}" x2="${x1}" y2="${y1}"></line></g><g font-family="'Space Mono',monospace" font-size="8.5" fill="var(--faint)"><text x="${x0 - 5}" y="${y0 + 3}" text-anchor="end">${eur(chartMax)}</text><text x="${x0 - 5}" y="${y1 + 3}" text-anchor="end">${eur(chartMin)}</text>${labels}</g><path d="${pathFor('previous')}" fill="none" stroke="var(--warn-ink)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path><path d="${pathFor('current')}" fill="none" stroke="var(--ac)" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"></path><g>${pointsFor('previous', 'var(--warn-ink)', 'Captura anterior')}${pointsFor('current', 'var(--ac)', 'Última captura')}</g></svg><div class="dashboard-trend-legend"><span><i style="background:var(--warn-ink);"></i>Captura anterior · ${groupLabel(firstPrevious, lastPrevious)}</span><span><i style="background:var(--ac);"></i>Última captura · ${groupLabel(firstCurrent, lastCurrent)}</span></div><div class="dashboard-trend-legend">Pasa el cursor por los puntos para consultar el precio de cada fecha. La diferencia refleja el cambio observado entre capturas.</div></section>`;
}

function dashboardHotelTrendHTML(row, history, chartWidth = 324) {
  const snapshots = new Map();
  for (const entry of history || []) {
    if (entry.snapshotId == null) continue;
    if (!snapshots.has(entry.snapshotId)) snapshots.set(entry.snapshotId, []);
    snapshots.get(entry.snapshotId).push(entry);
  }
  const series = [...snapshots.entries()].map(([snapshotId, entries]) => {
    const valid = entries.filter((entry) => Number.isFinite(Date.parse(entry.scrapedAt)) && Number.isFinite(Number(entry.pricePerNight)));
    if (!valid.length) return null;
    const prices = valid.map((entry) => Number(entry.pricePerNight));
    const stays = [...new Set(valid.map((entry) => entry.checkIn).filter(Boolean))];
    const latest = valid.slice().sort((a, b) => Date.parse(a.scrapedAt) - Date.parse(b.scrapedAt)).at(-1);
    return {
      snapshotId,
      scrapedAt: latest.scrapedAt,
      pricePerNight: median(prices),
      checkIn: stays.length === 1 ? stays[0] : `${stays[0] || '—'}${stays.length > 1 ? ` +${stays.length - 1}` : ''}`,
      observationCount: valid.length,
    };
  }).filter(Boolean).sort((a, b) => Date.parse(a.scrapedAt) - Date.parse(b.scrapedAt) || a.snapshotId - b.snapshotId).map((entry, index, all) => {
    const previous = all[index - 1];
    return { ...entry, changePct: previous && previous.pricePerNight ? ((entry.pricePerNight / previous.pricePerNight) - 1) * 100 : null };
  });
  if (series.length < 2) return '<div class="dashboard-trend-empty">Se necesitan dos fotos con precio válido para representar la evolución.</div>';
  const extractionGroups = [];
  const maxGap = 20 * 60 * 1000;
  series.forEach((entry) => {
    let group = extractionGroups.at(-1);
    const at = Date.parse(entry.scrapedAt);
    if (!group || at - group.lastAt > maxGap) {
      group = { entries: [], lastAt: at };
      extractionGroups.push(group);
    }
    group.entries.push(entry);
    group.lastAt = at;
  });
  const previousGroup = extractionGroups.at(-2) || { entries: [series.at(-2)] };
  const currentGroup = extractionGroups.at(-1) || { entries: [series.at(-1)] };
  const previous = { pricePerNight: median(previousGroup.entries.map((entry) => entry.pricePerNight)), scrapedAt: previousGroup.entries.at(-1).scrapedAt, snapshotId: previousGroup.entries.at(-1).snapshotId };
  const current = { pricePerNight: median(currentGroup.entries.map((entry) => entry.pricePerNight)), scrapedAt: currentGroup.entries.at(-1).scrapedAt, snapshotId: currentGroup.entries.at(-1).snapshotId };
  const change = previous.pricePerNight ? ((current.pricePerNight / previous.pricePerNight) - 1) * 100 : null;
  const amount = (value) => value == null ? '—' : `${nEs(value, 2)} ${esc(row.currency || 'EUR')}`;
  const groupLabel = (group) => {
    const first = group.entries[0]?.snapshotId, last = group.entries.at(-1)?.snapshotId;
    return first == null ? '—' : first === last ? `foto #${first}` : `fotos #${first}–#${last}`;
  };
  const previousMarkup = `<strong>${amount(previous.pricePerNight)}</strong><small>${groupLabel(previousGroup)} · ${fmtStamp(previous.scrapedAt)}</small>`;
  const currentMarkup = `<strong>${amount(current.pricePerNight)}</strong><small>${groupLabel(currentGroup)} · ${fmtStamp(current.scrapedAt)}</small>`;
  const W = Math.max(240, Number(chartWidth) || 324);
  return `<div class="dashboard-trend-stats"><div><span>Captura anterior</span>${previousMarkup}</div><div class="dashboard-trend-stat--current"><span>Última captura</span>${currentMarkup}</div><div><span>Variación entre capturas</span><strong>${signPct(change)}</strong><small>Mediana del precio por barrido</small></div></div>${dashboardSameStayComparisonHTML(history, W, amount)}`;
}

function dashboardTrendWidth(drawer) {
  return Math.max(240, Math.round(drawer.clientWidth - 26));
}

function renderDashboardHotelTrend(drawer, row, history) {
  const trend = $(`[data-dashboard-history-key="${CSS.escape(row.hotelKey)}"]`, drawer);
  if (!trend) return;
  drawer._dashboardTrend = { row, history };
  trend.innerHTML = dashboardHotelTrendHTML(row, history, dashboardTrendWidth(drawer));
}

function closeDashboardHotel() {
  const drawer = $('#dashboardHotelDrawer');
  if (!drawer || drawer.hidden) return false;
  drawer.hidden = true;
  drawer._dashboardResize?.disconnect();
  drawer._dashboardTrend = null;
  drawer._dashboardRequest = null;
  $$('.dashboard-map-marker').forEach((marker) => marker.setAttribute('aria-pressed', 'false'));
  drawer.classList.remove('is-expanded');
  drawer.innerHTML = '';
  const origin = State.dashboardDrawerFocusOrigin;
  State.dashboardDrawerFocusOrigin = null;
  if (origin instanceof HTMLElement && origin.isConnected) origin.focus({ preventScroll: true });
  return true;
}

function toggleDashboardHotelInspector() {
  const drawer = $('#dashboardHotelDrawer');
  if (!drawer || drawer.hidden) return;
  const expanded = drawer.classList.toggle('is-expanded');
  const button = drawer.querySelector('[data-dashboard-drawer-expand]');
  if (button) {
    button.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    button.setAttribute('aria-label', expanded ? 'Reducir análisis' : 'Ampliar análisis');
    button.textContent = expanded ? '↙' : '↗';
  }
  window.requestAnimationFrame(() => {
    if (drawer._dashboardTrend) renderDashboardHotelTrend(drawer, drawer._dashboardTrend.row, drawer._dashboardTrend.history);
  });
}

function dashboardHotelFallbackHTML(row) {
  const adr = row.pricePerNight ?? row.avgPricePerNight ?? null;
  return `<div class="dashboard-drawer__head"><div><div class="card__kicker">Inspector de tarifa</div><h3 id="dashboardHotelDrawerTitle">${esc(row.hotelName || 'Hotel sin identificar')}</h3></div><div class="dashboard-drawer__tools"><button type="button" class="icon-btn" data-dashboard-drawer-close aria-label="Cerrar detalle">×</button></div></div>
    <div class="dashboard-drawer__overview"><div class="dashboard-drawer__price">${eur(adr)}<span>ADR hab/noche</span></div><dl class="dashboard-drawer__facts"><div><dt>Nota</dt><dd>${row.rating != null ? nEs(row.rating, 1) : '—'}</dd></div><div><dt>Régimen</dt><dd>${esc(row.board || '—')}</dd></div><div><dt>Disponibilidad</dt><dd>${row.soldOut ? 'Sin disponibilidad' : row.unitsLeft != null ? `Quedan ${nEs(row.unitsLeft)}` : 'Observable'}</dd></div><div><dt>Ubicación</dt><dd>${esc(row.displayLocation || row.city || '—')}</dd></div></dl></div>
    <section class="dashboard-drawer__section"><div class="dashboard-trend-empty">Este punto no tiene una ficha completa en la captura actual; se muestra la tarifa geolocalizada disponible.</div></section>`;
}

function openDashboardHotel(key) {
  const row = dashboardHotelForKey(key);
  const drawer = $('#dashboardHotelDrawer');
  if (!drawer || !row) return;
  drawer._dashboardResize?.disconnect();
  drawer._dashboardTrend = null;
  const request = {};
  drawer._dashboardRequest = request;
  if (!drawer.hidden && drawer.dataset.hotelKey !== row.hotelKey) State.dashboardDrawerFocusOrigin = document.activeElement instanceof HTMLElement ? document.activeElement : State.dashboardDrawerFocusOrigin;
  if (drawer.hidden) State.dashboardDrawerFocusOrigin = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  drawer.dataset.hotelKey = row.hotelKey;
  drawer.classList.remove('is-expanded');
  try {
    drawer.innerHTML = `<div class="dashboard-drawer__head"><div><div class="card__kicker">Inspector de tarifa</div><h3 id="dashboardHotelDrawerTitle">${esc(row.hotelName)}</h3></div><div class="dashboard-drawer__tools"><button type="button" class="icon-btn" data-dashboard-drawer-expand aria-label="Ampliar análisis" aria-expanded="false">↗</button><button type="button" class="icon-btn" data-dashboard-drawer-close aria-label="Cerrar detalle">×</button></div></div>
      <div class="dashboard-drawer__overview"><div class="dashboard-drawer__price">${eur(row.pricePerNight)}<span>ADR hab/noche</span></div><dl class="dashboard-drawer__facts"><div><dt>Nota</dt><dd title="${esc(row.rating != null ? nEs(row.rating, 1) : '—')}">${row.rating != null ? nEs(row.rating, 1) : '—'}</dd></div><div><dt>Régimen</dt><dd title="${esc(row.board || '—')}">${esc(row.board || '—')}</dd></div><div><dt>Disponibilidad</dt><dd title="${esc(row.soldOut ? 'Sin disponibilidad' : row.unitsLeft != null ? `Quedan ${nEs(row.unitsLeft)}` : 'Observable')}">${row.soldOut ? 'Sin disponibilidad' : row.unitsLeft != null ? `Quedan ${nEs(row.unitsLeft)}` : 'Observable'}</dd></div><div><dt>Distancia playa</dt><dd title="${esc(row.beachDistance || '—')}">${esc(row.beachDistance || '—')}</dd></div></dl></div>
      <section class="dashboard-drawer__section dashboard-drawer__trend" data-dashboard-history-key="${esc(row.hotelKey)}"><div class="dashboard-trend-loading"><i></i> Cargando evolución por extracción…</div></section>
      <section class="dashboard-drawer__section dashboard-drawer__offer">${dashboardDrawerOfferHTML(row)}</section>`;
  } catch (_) {
    drawer.innerHTML = dashboardHotelFallbackHTML(row);
  }
  drawer.hidden = false;
  drawer.scrollTop = 0;
  $$('.dashboard-map-marker').forEach((marker) => marker.setAttribute('aria-pressed', String(State.dashboardMapRows[marker.dataset.dashboardMapMarker]?.hotelKey === row.hotelKey)));
  drawer.querySelector('[data-dashboard-drawer-close]')?.focus({ preventScroll: true });
  if (typeof ResizeObserver !== 'undefined') {
    let width = drawer.clientWidth;
    drawer._dashboardResize = new ResizeObserver(() => {
      if (drawer.clientWidth === width || drawer.hidden) return;
      width = drawer.clientWidth;
      if (drawer._dashboardTrend) renderDashboardHotelTrend(drawer, row, drawer._dashboardTrend.history);
    });
    drawer._dashboardResize.observe(drawer);
  }
  if (!row.hotelKey) {
    const trend = $('[data-dashboard-history-key=""]', drawer);
    if (trend) trend.innerHTML = '<div class="dashboard-trend-empty">No hay histórico identificable para este punto del mapa.</div>';
    return;
  }
  getHotelPriceHistory(State.targetId, row.hotelKey).then((history) => {
    if (!drawer.isConnected || drawer._dashboardRequest !== request) return;
    renderDashboardHotelTrend(drawer, row, history);
  }).catch((error) => {
    if (!drawer.isConnected || drawer._dashboardRequest !== request) return;
    const trend = $(`[data-dashboard-history-key="${CSS.escape(row.hotelKey)}"]`, drawer);
    if (trend) trend.innerHTML = `<div class="dashboard-trend-empty">No se pudo cargar la evolución: ${esc(error.message)}</div>`;
  });
}

function loadMapLibre() {
  if (window.maplibregl) return Promise.resolve(window.maplibregl);
  if (State.mapLoader) return State.mapLoader;
  State.mapLoader = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js';
    script.onload = () => resolve(window.maplibregl);
    script.onerror = () => { State.mapLoader = null; script.remove(); reject(new Error('No se pudo cargar el mapa base')); };
    document.head.appendChild(script);
  });
  return State.mapLoader;
}

function dashboardMapStyle() {
  // Teselas OSM (la CSP solo permite este origen ráster); el tema oscuro se aplica con un filtro CSS sobre el canvas.
  return {
    version: 8,
    sources: {
      osm: {
        type: 'raster',
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '© OpenStreetMap contributors',
      },
    },
    layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
  };
}

function destroyDashboardMap() {
  const drawer = $('#dashboardHotelDrawer');
  drawer?._dashboardResize?.disconnect();
  if (State.dashboardMapResizeObserver) {
    State.dashboardMapResizeObserver.disconnect();
    State.dashboardMapResizeObserver = null;
  }
  if (State.dashboardMapResizeFrame) {
    window.cancelAnimationFrame(State.dashboardMapResizeFrame);
    State.dashboardMapResizeFrame = null;
  }
  State.dashboardMapMarkers.forEach((marker) => marker.remove());
  State.dashboardMapMarkers = [];
  State.dashboardMapRows = {};
  if (State.dashboardMap) { State.dashboardMap.remove(); State.dashboardMap = null; }
}

async function renderDashboardHotelMap(points, rows) {
  const container = $('#dashboardHotelMap');
  if (!container) return;
  const request = {};
  container._mapRequest = request;
  const valid = (points || []).filter((point) => point.latitude != null && point.longitude != null && String(point.latitude).trim() !== '' && String(point.longitude).trim() !== '' && Number.isFinite(Number(point.latitude)) && Math.abs(Number(point.latitude)) <= 90 && Number.isFinite(Number(point.longitude)) && Math.abs(Number(point.longitude)) <= 180 && Number(point.pricePerNight ?? point.avgPricePerNight) > 0);
  const showStatus = (message) => {
    container.querySelector('.dashboard-map-status')?.remove();
    container.insertAdjacentHTML('beforeend', `<div class="empty dashboard-map-status" role="status">${message}</div>`);
  };
  const count = $('#dashboardMapCount');
  if (count) count.textContent = `${valid.length} hoteles`;
  if (!valid.length) { showStatus('No hay hoteles con tarifa y coordenadas válidas en esta foto.'); return; }
  try { await loadMapLibre(); } catch (e) { if (container.isConnected && container._mapRequest === request) showStatus(`${esc(e.message)}. <button type="button" class="btn" data-dashboard-map-retry>Reintentar</button>`); return; }
  if (!window.maplibregl || !container.isConnected || container._mapRequest !== request || State.dashboardView !== 'market' || State.view !== 'dashboard') return;
  container.querySelector('.dashboard-map-status')?.remove();
  destroyDashboardMap();
  const oldCanvas = container.querySelector('.dashboard-map__canvas');
  if (oldCanvas) oldCanvas.remove();
  const mapHost = document.createElement('div'); mapHost.className = 'dashboard-map__canvas'; container.appendChild(mapHost);
  const map = new window.maplibregl.Map({ container: mapHost, style: dashboardMapStyle(), center: [-15.57, 27.78], zoom: 9.5, attributionControl: true });
  State.dashboardMap = map;
  map.addControl(new window.maplibregl.NavigationControl({ showCompass: false }), 'top-left');
  let userHasMovedMap = false;
  let hasFittedBounds = false;
  const fitMarkers = () => {
    if (bounds.isEmpty()) return;
    map.fitBounds(bounds, { padding: 42, maxZoom: 12.3, duration: 0 });
    hasFittedBounds = true;
  };
  const syncMapSize = () => {
    if (State.dashboardMapResizeFrame) window.cancelAnimationFrame(State.dashboardMapResizeFrame);
    State.dashboardMapResizeFrame = window.requestAnimationFrame(() => {
      State.dashboardMapResizeFrame = null;
      if (State.dashboardMap !== map) return;
      map.resize();
      // Hasta la primera interacción mantenemos todos los hoteles encuadrados.
      // Después, resize conserva exactamente la vista elegida por la persona usuaria.
      if (!hasFittedBounds || !userHasMovedMap) fitMarkers();
    });
  };
  if (typeof ResizeObserver !== 'undefined') {
    State.dashboardMapResizeObserver = new ResizeObserver(syncMapSize);
    State.dashboardMapResizeObserver.observe(mapHost);
  }
  map.on('dragstart', () => { userHasMovedMap = true; });
  map.on('zoomstart', (event) => { if (event.originalEvent) userHasMovedMap = true; });
  const priceFor = (point) => Number(point.pricePerNight ?? point.avgPricePerNight);
  const scale = { min: Math.min(...valid.map(priceFor)), max: Math.max(...valid.map(priceFor)) };
  const interactivePoints = [];
  const bounds = new window.maplibregl.LngLatBounds();
  const rowByKey = Object.fromEntries((rows || []).map((row) => [row.hotelKey, row]));
  valid.forEach((point, index) => {
    const sourceRow = rowByKey[point.hotelKey] || {};
    const row = {
      ...point,
      ...sourceRow,
      hotelKey: sourceRow.hotelKey || point.hotelKey || '',
      hotelName: sourceRow.hotelName || point.hotelName || 'Hotel sin identificar',
      pricePerNight: sourceRow.pricePerNight ?? point.pricePerNight ?? point.avgPricePerNight ?? null,
    };
    const price = Number(row.pricePerNight || point.avgPricePerNight || 0);
    const ratio = scale.max > scale.min ? (price - scale.min) / (scale.max - scale.min) : .5;
    const tier = ratio > .66 ? 'high' : ratio < .33 ? 'low' : 'mid';
    const markerId = `${row.hotelKey || point.hotelKey || 'point'}-${index}`;
    State.dashboardMapRows[markerId] = row;
    interactivePoints.push({ row, coordinates: [Number(point.longitude), Number(point.latitude)] });
    const marker = document.createElement('button'); marker.type = 'button'; marker.className = `dashboard-map-marker dashboard-map-marker--${tier}`; marker.dataset.dashboardMapMarker = markerId; marker.setAttribute('aria-label', `${row.hotelName || point.hotelName}. ${eur(price)} por noche. Abrir detalle.`); marker.title = `${row.hotelName || point.hotelName} · ${eur(price)}`; marker.innerHTML = `<span aria-hidden="true"></span><b>${eur(price)}</b>`;
    const markerInstance = new window.maplibregl.Marker({ element: marker, anchor: 'center' }).setLngLat([Number(point.longitude), Number(point.latitude)]).addTo(map);
    marker.setAttribute('aria-pressed', 'false');
    marker.setAttribute('aria-controls', 'dashboardHotelDrawer');
    State.dashboardMapMarkers.push(markerInstance);
    bounds.extend([Number(point.longitude), Number(point.latitude)]);
  });
  map.on('click', (event) => {
    let nearest = null;
    interactivePoints.forEach((candidate) => {
      const screenPoint = map.project(candidate.coordinates);
      const distance = Math.hypot(event.point.x - screenPoint.x, event.point.y - screenPoint.y);
      if (!nearest || distance < nearest.distance) nearest = { ...candidate, distance };
    });
    if (nearest && nearest.distance <= 18) openDashboardHotel(nearest.row);
  });
  syncMapSize();
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
  State.hotelTab = readPref(HOTEL_TAB_KEY, ['sheet', 'bi'], 'sheet');
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
  const snapshotId = State.snapshots[targetId]?.latest?.snapshot?.id;
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
  const biPanel = `<div class="pending-card">
      <i aria-hidden="true"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg></i>
      <strong>El panel de análisis llega en la siguiente fase</strong>
      <p>Calendario de tarifas, mapa de precios, tarifa sugerida y value score. Mientras tanto, la hoja de mercado reúne las tarifas y condiciones del set.</p>
      <button type="button" class="btn btn--primary" data-hotel-tab="sheet">Ver la hoja de mercado</button>
    </div>`;
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
  if (!isSheet) return;
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

/* ========================================================== OPERACIÓN AÉREA */
let airOperationsSearchTimer = null;

function flightTabsHTML(active) {
  return `<div class="flight-tabs" role="tablist" aria-label="Vistas de vuelos">
    <button type="button" role="tab" data-flight-tab="overview" aria-selected="${active === 'overview' ? 'true' : 'false'}" class="${active === 'overview' ? 'is-active' : ''}">Resumen</button>
    <button type="button" role="tab" data-flight-tab="operations" aria-selected="${active === 'operations' ? 'true' : 'false'}" class="${active === 'operations' ? 'is-active' : ''}">Operación aérea</button>
  </div>`;
}

function flightsPageHeader(subtitle) {
  return `${pageHead('Vuelos', subtitle, '')}${flightTabsHTML(State.flightTab)}`;
}

function airOperationParams() {
  const q = State.airOperations;
  const params = new URLSearchParams({ page: String(q.page), pageSize: String(q.pageSize), sort: q.sort });
  ['query', 'market', 'origin', 'destination', 'airline', 'connection', 'price', 'dateFrom', 'dateTo'].forEach((key) => {
    if (q[key]) params.set(key, q[key]);
  });
  if (q.runId === 'all') params.set('scope', 'history');
  else if (q.runId) params.set('runId', q.runId);
  return params.toString();
}

function persistAirOperationsQuery() {
  try {
    const q = State.airOperations;
    localStorage.setItem('atlas.air-operations.query.v2', JSON.stringify({
      pageSize: q.pageSize, query: q.query, market: q.market, origin: q.origin, destination: q.destination,
      airline: q.airline, connection: q.connection, price: q.price, dateFrom: q.dateFrom, dateTo: q.dateTo,
      runId: q.runId, sort: q.sort,
    }));
  } catch (_) { /* la consulta sigue operativa sin almacenamiento local */ }
}

function restoreAirOperationsQuery() {
  const q = State.airOperations;
  if (q.restored) return;
  q.restored = true;
  try {
    const stored = JSON.parse(localStorage.getItem('atlas.air-operations.query.v2') || 'null');
    if (!stored || typeof stored !== 'object') return;
    q.pageSize = [25, 50, 100].includes(Number(stored.pageSize)) ? Number(stored.pageSize) : q.pageSize;
    q.query = typeof stored.query === 'string' ? stored.query.slice(0, 160) : '';
    ['market', 'origin', 'destination', 'airline', 'connection', 'price', 'dateFrom', 'dateTo'].forEach((key) => {
      q[key] = typeof stored[key] === 'string' ? stored[key].slice(0, 80) : '';
    });
    q.runId = stored.runId === 'all' || stored.runId === '' || (typeof stored.runId === 'string' && /^\d+$/.test(stored.runId)) ? stored.runId : 'all';
    q.sort = ['price-asc', 'price-desc', 'duration-asc', 'duration-desc', 'aai-asc', 'aai-desc', 'stops-asc', 'date-asc', 'airline-asc'].includes(stored.sort) ? stored.sort : q.sort;
  } catch (_) { /* una preferencia local dañada no bloquea la vista */ }
}

function airSelectOptions(items, current, placeholder) {
  const values = [...new Set(items || [])].filter(Boolean).sort((a, b) => String(a).localeCompare(String(b), 'es'));
  return `<option value="">${esc(placeholder)}</option>${values.map((value) => `<option value="${esc(value)}" ${value === current ? 'selected' : ''}>${esc(value)}</option>`).join('')}`;
}

function airCaptureOptions(runs, current) {
  const totalFlights = (runs || []).reduce((sum, run) => sum + Number(run.flightsCaptured || 0), 0);
  const scopeOptions = `<option value="all" ${current === 'all' ? 'selected' : ''}>Todas las capturas · ${nEs(totalFlights)} vuelos</option><option value="" ${current === '' ? 'selected' : ''}>Última captura</option>`;
  return scopeOptions + (runs || []).map((run) => {
    const id = String(run.id);
    const label = `${fmtStamp(run.capturedAt)} · ${nEs(run.flightsCaptured || 0)} vuelos`;
    return `<option value="${esc(id)}" ${id === String(current) ? 'selected' : ''}>${esc(label)}</option>`;
  }).join('');
}

function airDate(value) {
  if (!value) return '—';
  const date = new Date(`${value}T12:00:00Z`);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' });
}

function durationLabel(minutes) {
  const value = Number(minutes);
  if (!Number.isFinite(value) || value < 0) return '—';
  return `${Math.floor(value / 60)}h ${String(value % 60).padStart(2, '0')}m`;
}

function airPricePosition(row) {
  const min = Number(row.typical_price_min);
  const max = Number(row.typical_price_max);
  const price = Number(row.price ?? row.lowest_price);
  const label = row.price_quality_label || 'Sin dato';
  const tone = label === 'Barato' ? 'good' : label === 'Caro' ? 'bad' : 'neutral';
  if (!Number.isFinite(min) || !Number.isFinite(max) || !Number.isFinite(price) || max <= min) {
    return `<span class="air-position air-position--${tone}"><span>${esc(label)}</span><b>—</b></span>`;
  }
  const point = Math.max(0, Math.min(100, ((price - min) / (max - min)) * 100));
  const tooltipId = `air-price-range-${String(row.id || row.itinerary_id || `${row.market}-${row.origin}-${row.destination}-${price}`).replace(/[^a-zA-Z0-9_-]/g, '-')}`;
  const description = `${label}: ${eur(price)}. Barato por debajo de ${eur(min)}, normal entre ${eur(min)} y ${eur(max)}, caro por encima de ${eur(max)}.`;
  return `<span class="air-position air-position--${tone} air-position--interactive" tabindex="0" aria-describedby="${tooltipId}" aria-label="${esc(description)}"><span class="air-position__label"><span>${esc(label)}</span><b>${eur(price)}</b></span><span class="air-position__scale"><i class="air-position__low"></i><i class="air-position__mid"></i><i class="air-position__high"></i><em style="left:${point.toFixed(2)}%"></em></span><span class="air-position__help" id="${tooltipId}" role="tooltip"><strong>Rango de precio</strong><span class="air-position__help-row"><i class="air-position__low"></i>Bajo <b>&lt; ${eur(min)}</b></span><span class="air-position__help-row"><i class="air-position__mid"></i>Normal <b>${eur(min)}–${eur(max)}</b></span><span class="air-position__help-row"><i class="air-position__high"></i>Alto <b>&gt; ${eur(max)}</b></span><small>Precio observado <b>${eur(price)}</b></small></span></span>`;
}

function airportCell(code, name) {
  const label = [code, name].filter(Boolean).join(' · ') || '—';
  return `<span class="air-airport" title="${esc(label)}">${esc(code || '—')}</span>`;
}

function airlineCode(airline) {
  return {
    'Iberia Express': 'I2', Iberia: 'IB', 'Air Europa': 'UX', Vueling: 'VY', Eurowings: 'EW', Condor: 'DE',
    'British Airways': 'BA', Transavia: 'HV', 'Air France': 'AF', Jet2: 'LS', Lufthansa: 'LH', KLM: 'KL', SWISS: 'LX',
    'Brussels Airlines': 'SN', Austrian: 'OS', 'Austrian Airlines': 'OS', 'Tap Air Portugal': 'TP', 'TAP Air Portugal': 'TP', TAP: 'TP',
    'Discover Airlines': '4Y', 'Edelweiss Air': 'WK', Edelweiss: 'WK', 'Binter Canarias': 'NT', Binter: 'NT',
    'Aer Lingus': 'EI', Ryanair: 'FR', easyJet: 'U2', Norwegian: 'DY', 'Scandinavian Airlines': 'SK', SAS: 'SK',
    Finnair: 'AY', 'Wizz Air': 'W6', 'TUI fly': 'X3', TUI: 'X3', Volotea: 'V7',
  }[airline] || String(airline || '?').slice(0, 2).toUpperCase();
}

function airlineCell(row) {
  const airline = row.main_airline || (row.airlines || []).join(' · ') || '—';
  const code = airlineCode(airline);
  const logoUrl = row.airline_logo || `https://www.gstatic.com/flights/airline_logos/70px/${encodeURIComponent(code)}.png`;
  return `<span class="flight-airline"><span class="flight-airline__logo" aria-hidden="true"><span>${esc(code)}</span><img class="flight-airline__logo-img" src="${esc(logoUrl)}" alt="" loading="lazy" decoding="async"></span><span class="flight-airline__name">${esc(airline)}</span></span>`;
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

function airMarketCell(row) {
  const mapped = airMarketFromIata(row);
  const segment = row.market_segment || mapped.segment;
  const country = row.market_country || mapped.country;
  const city = row.market || 'Origen no informado';
  const title = [segment, country, city].filter((value, index, values) => value && values.indexOf(value) === index).join(' · ');
  return `<span class="flight-market" title="${esc(title)}"><strong>${esc(segment)}</strong><small>${esc(city)}</small></span>`;
}

function airOperationRow(row) {
  const connection = row.is_direct
    ? '<span class="chip chip--direct">Directo</span>'
    : `<span class="chip chip--warn">${nEs(row.num_layovers || row.stops || 0)} escala${Number(row.num_layovers || row.stops || 0) === 1 ? '' : 's'}</span>`;
  const aai = row.air_accessibility_index == null ? '—' : nEs(row.air_accessibility_index, 2);
  const classes = (row.travel_classes || []).join(' · ') || '—';
  const layovers = (row.layover_airports || []).join(' · ') || 'Sin escala';
  return `<tr class="air-option-row">
    <td class="air-route">${airMarketCell(row)}</td>
    <td>${airportCell(row.origin, row.departure_airport_name)}</td>
    <td>${airportCell(row.destination, row.arrival_airport_name)}</td>
    <td class="air-date">${airDate(row.outbound_date)}${row.days_ahead == null ? '' : ` <small>${nEs(row.days_ahead)}d</small>`}</td>
    <td class="name">${airlineCell(row)}</td>
    <td class="mono air-flight" title="${esc((row.flight_numbers || []).join(' · '))}">${esc((row.flight_numbers || []).join(' · ') || '—')}</td>
    <td class="air-aircraft" title="${esc((row.aircraft_models || []).join(' · '))}">${esc((row.aircraft_models || []).join(' · ') || '—')}</td>
    <td class="air-class">${esc(classes)}</td>
    <td class="mono r">${esc(row.departure_time || '—')}</td>
    <td class="mono r">${esc(row.arrival_time || '—')}</td>
    <td title="${esc(layovers)}">${connection}</td>
    <td class="num air-price">${eur(row.price ?? row.lowest_price)}</td>
    <td class="air-position-cell">${airPricePosition(row)}</td>
    <td class="num" title="Precio observado dividido por el promedio típico">${aai}</td>
    <td class="mono r">${durationLabel(row.total_duration_min)}</td>
    <td class="air-return mono">${airDate(row.return_date)}</td>
    <td class="air-capture-date mono">${fmtStamp(row.capture_run_at || row.search_datetime)}</td>
  </tr>`;
}

async function renderAirOperations({ focusSearch = false } = {}) {
  const host = mount('flights');
  restoreAirOperationsQuery();
  skeleton(host, 'list');
  const requestId = ++State.airOperations.requestId;
  let data, runsData;
  try {
    [data, runsData] = await Promise.all([
      api(`/api/air-data/options?${airOperationParams()}`),
      State.airRuns ? Promise.resolve(State.airRuns) : api('/api/air-data/runs?limit=100'),
    ]);
    State.airRuns = runsData;
  }
  catch (e) {
    if (requestId !== State.airOperations.requestId) return;
    host.innerHTML = `<div class="page">${flightsPageHeader('Opciones de vuelo capturadas para el destino.')}<div class="inline-error">No se pudieron cargar las opciones aéreas: ${esc(e.message)}</div></div>`;
    return;
  }
  if (requestId !== State.airOperations.requestId) return;
  const q = State.airOperations;
  const rows = data.rows || [];
  const total = Number(data.total || 0);
  const pageCount = Math.max(1, Math.ceil(total / q.pageSize));
  if (q.page > pageCount) { q.page = pageCount; return renderAirOperations({ focusSearch }); }
  const from = total ? ((q.page - 1) * q.pageSize) + 1 : 0;
  const to = Math.min(total, q.page * q.pageSize);
  const capture = data.capture || {};
  const historicalScope = data.scope === 'history';
  const sourceLabel = historicalScope ? 'Histórico completo' : data.is_live ? 'Captura SerpApi' : 'Datos de demostración';
  const sourceClass = data.is_live ? 'air-capture--live' : 'air-capture--demo';
  const facets = data.facets || {};
  const runs = runsData?.runs || [];
  const historicalFlights = Number(runsData?.totalFlights || 0);
  const filtered = ['query', 'market', 'origin', 'destination', 'airline', 'connection', 'price', 'dateFrom', 'dateTo'].filter((key) => q[key]).length;
  const tbody = rows.map(airOperationRow).join('') || '<tr><td colspan="17" class="empty"><strong>Sin opciones para esta consulta</strong>Ajusta los filtros o restablece la vista.</td></tr>';

  host.innerHTML = `<div class="page air-operations-page">
    ${flightsPageHeader('Detalle de cada opción de vuelo capturada para el destino.')}
    <article class="card table-card air-operations-card${q.fullscreen ? ' is-fullscreen' : ''}">
      <div class="air-operations-card__head">
        <div><div class="card__kicker">Opciones de conectividad</div><strong>Tabla de vuelos</strong><span class="air-operations-card__count">${nEs(total)} opciones · ${nEs(data.facets?.markets?.length || 0)} mercados</span><span class="air-history-coverage">${nEs(runs.length)} capturas · ${nEs(historicalFlights)} opciones históricas</span></div>
        <div class="air-capture ${sourceClass}"><i></i><span>${sourceLabel}</span><b>${historicalScope ? `${nEs(runs.length)} capturas consolidadas` : capture.capturedAt ? fmtStamp(capture.capturedAt) : 'sin fecha'}</b></div>
      </div>
      <div class="air-operations-toolbar" aria-label="Filtros de opciones aéreas">
        <label class="air-capture-filter"><span>Captura aérea</span><select class="input" data-air-operation-filter="runId">${airCaptureOptions(runs, q.runId)}</select></label>
        <label class="air-operations-search"><span class="sr-only">Buscar opción aérea</span><input type="search" class="input input--search" id="airOperationsSearch" value="${esc(q.query)}" placeholder="Mercado, IATA, aerolínea, vuelo o aeronave…" /></label>
        <label><span>Mercado</span><select class="input" data-air-operation-filter="market">${airSelectOptions(facets.markets, q.market, 'Todos')}</select></label>
        <label><span>Origen</span><select class="input" data-air-operation-filter="origin">${airSelectOptions(facets.origins, q.origin, 'Todos')}</select></label>
        <label><span>Destino</span><select class="input" data-air-operation-filter="destination">${airSelectOptions(facets.destinations, q.destination, 'Todos')}</select></label>
        <label><span>Aerolínea</span><select class="input" data-air-operation-filter="airline">${airSelectOptions(facets.airlines, q.airline, 'Todas')}</select></label>
        <label><span>Conexión</span><select class="input" data-air-operation-filter="connection"><option value="">Todas</option><option value="direct" ${q.connection === 'direct' ? 'selected' : ''}>Directo</option><option value="non_direct" ${q.connection === 'non_direct' ? 'selected' : ''}>Con escala</option><option value="1 escala" ${q.connection === '1 escala' ? 'selected' : ''}>1 escala</option><option value="2 escalas" ${q.connection === '2 escalas' ? 'selected' : ''}>2 escalas</option><option value="3+ escalas" ${q.connection === '3+ escalas' ? 'selected' : ''}>3+ escalas</option></select></label>
        <label><span>Precio</span><select class="input" data-air-operation-filter="price">${airSelectOptions(facets.prices, q.price, 'Cualquier posición')}</select></label>
        <label><span>Salida desde</span><input class="input" type="date" value="${esc(q.dateFrom)}" data-air-operation-filter="dateFrom" /></label>
        <label><span>Salida hasta</span><input class="input" type="date" value="${esc(q.dateTo)}" data-air-operation-filter="dateTo" /></label>
      </div>
      <div class="air-operations-table-head">
        <span class="air-operations-status" aria-live="polite">${filtered ? `${filtered} filtro${filtered === 1 ? '' : 's'} · ` : ''}${from}–${to} de ${nEs(total)} opciones</span>
        <div class="air-operations-table-tools">
          <label><span>Ordenar</span><select class="input" data-air-operation-filter="sort"><option value="price-asc" ${q.sort === 'price-asc' ? 'selected' : ''}>Precio ↑</option><option value="price-desc" ${q.sort === 'price-desc' ? 'selected' : ''}>Precio ↓</option><option value="date-asc" ${q.sort === 'date-asc' ? 'selected' : ''}>Salida próxima</option><option value="duration-asc" ${q.sort === 'duration-asc' ? 'selected' : ''}>Duración ↑</option><option value="duration-desc" ${q.sort === 'duration-desc' ? 'selected' : ''}>Duración ↓</option><option value="aai-asc" ${q.sort === 'aai-asc' ? 'selected' : ''}>AAI favorable</option><option value="aai-desc" ${q.sort === 'aai-desc' ? 'selected' : ''}>AAI alto</option><option value="stops-asc" ${q.sort === 'stops-asc' ? 'selected' : ''}>Menos escalas</option><option value="airline-asc" ${q.sort === 'airline-asc' ? 'selected' : ''}>Aerolínea A–Z</option></select></label>
          <label><span>Filas</span><select class="input" data-air-operation-filter="pageSize"><option value="25" ${q.pageSize === 25 ? 'selected' : ''}>25</option><option value="50" ${q.pageSize === 50 ? 'selected' : ''}>50</option><option value="100" ${q.pageSize === 100 ? 'selected' : ''}>100</option></select></label>
          <button type="button" class="btn btn--quiet" data-air-operation-reset ${filtered || q.runId !== 'all' || q.sort !== 'price-asc' || q.pageSize !== 100 ? '' : 'disabled'}>Restablecer</button>
          <button type="button" class="btn btn--quiet air-fullscreen-toggle" data-air-operations-fullscreen aria-pressed="${q.fullscreen ? 'true' : 'false'}" aria-label="${q.fullscreen ? 'Salir de la vista de tabla a pantalla completa' : 'Ver la tabla a pantalla completa'}"><span aria-hidden="true">${q.fullscreen ? '↙' : '↗'}</span>${q.fullscreen ? 'Salir de pantalla completa' : 'Pantalla completa'}</button>
        </div>
      </div>
      <div class="table-scroll air-operations-scroll">
        <table class="t air-operations-table" id="airOperationsTable">
          <caption class="sr-only">Opciones de vuelo capturadas, con conexión, precio, posición frente al rango típico, índice de accesibilidad y duración</caption>
          <thead><tr><th>Mercado</th><th>Origen</th><th>Destino</th><th>Salida</th><th>Aerolínea</th><th>Vuelo</th><th>Aeronave</th><th>Clase</th><th class="r">Despegue</th><th class="r">Llegada</th><th>Conexión</th><th class="r">Precio</th><th>Posición precio</th><th class="r" title="Precio observado dividido por el promedio típico">AAI</th><th class="r">Duración</th><th>Vuelta</th><th>Captura</th></tr></thead>
          <tbody>${tbody}</tbody>
        </table>
      </div>
      <footer class="air-operations-pager">
        <span>Página ${nEs(q.page)} de ${nEs(pageCount)}</span>
        <div><button type="button" class="btn btn--xs" data-air-operation-page="prev" ${q.page <= 1 ? 'disabled' : ''}>Anterior</button><button type="button" class="btn btn--xs" data-air-operation-page="next" ${q.page >= pageCount ? 'disabled' : ''}>Siguiente</button></div>
      </footer>
    </article>
  </div>`;
  document.body.classList.toggle('air-operations-fullscreen', q.fullscreen);
  persistAirOperationsQuery();
  if (focusSearch) requestAnimationFrame(() => $('#airOperationsSearch')?.focus());
}

function toggleAirOperationsFullscreen(force) {
  const card = $('.air-operations-card');
  if (!card) return;
  const button = $('[data-air-operations-fullscreen]', card);
  const next = typeof force === 'boolean' ? force : !State.airOperations.fullscreen;
  State.airOperations.fullscreen = next;
  card.classList.toggle('is-fullscreen', next);
  document.body.classList.toggle('air-operations-fullscreen', next);
  if (button) {
    button.setAttribute('aria-pressed', next ? 'true' : 'false');
    button.setAttribute('aria-label', next ? 'Salir de la vista de tabla a pantalla completa' : 'Ver la tabla a pantalla completa');
    button.innerHTML = `<span aria-hidden="true">${next ? '↙' : '↗'}</span>${next ? 'Salir de pantalla completa' : 'Pantalla completa'}`;
    if (!next) requestAnimationFrame(() => button.focus());
  }
}

function updateAirOperationsQuery(key, value, focusSearch = false) {
  const q = State.airOperations;
  if (!Object.prototype.hasOwnProperty.call(q, key)) return;
  q[key] = value;
  if (key === 'runId') {
    ['query', 'market', 'origin', 'destination', 'airline', 'connection', 'price', 'dateFrom', 'dateTo'].forEach((filterKey) => { q[filterKey] = ''; });
  }
  q.page = 1;
  renderAirOperations({ focusSearch });
}

function resetAirOperationsQuery() {
  const q = State.airOperations;
  Object.assign(q, { page: 1, pageSize: 100, query: '', market: '', origin: '', destination: '', airline: '', connection: '', price: '', runId: 'all', dateFrom: '', dateTo: '', sort: 'price-asc' });
  renderAirOperations({ focusSearch: true });
}

function airComparisonSVG(points, status) {
  const grouped = new Map();
  (points || []).filter((point) => point.comparable && point.currentPrice != null && point.previousPrice != null).forEach((point) => {
    const date = String(point.outboundDate || '');
    if (!grouped.has(date)) grouped.set(date, { date, current: [], previous: [], routes: [] });
    const group = grouped.get(date);
    group.current.push(Number(point.currentPrice));
    group.previous.push(Number(point.previousPrice));
    group.routes.push(point.routeKey);
  });
  const usable = [...grouped.values()].map((group) => ({
    outboundDate: group.date,
    currentPrice: median(group.current),
    previousPrice: median(group.previous),
    routes: group.routes,
  }));
  if (!usable.length) {
    const message = status === 'incompatible_profile'
      ? 'No se pueden comparar las fotos: el perfil de búsqueda ha cambiado.'
      : 'No hay dos fotos SerpAPI comparables para las mismas rutas y fechas.';
    return `<div class="air-comparison-empty">${message}</div>`;
  }
  const width = 780, height = 250, pad = { left: 54, right: 22, top: 22, bottom: 42 };
  const values = usable.flatMap((point) => [Number(point.currentPrice), Number(point.previousPrice)]);
  const min = Math.min(...values), max = Math.max(...values), span = Math.max(1, max - min);
  const sx = (index) => pad.left + (index / Math.max(1, usable.length - 1)) * (width - pad.left - pad.right);
  const sy = (value) => pad.top + (1 - ((value - min) / span)) * (height - pad.top - pad.bottom);
  const path = (field) => usable.map((point, index) => `${index ? 'L' : 'M'} ${sx(index).toFixed(1)} ${sy(Number(point[field])).toFixed(1)}`).join(' ');
  const dateLabel = (value) => {
    const parts = String(value || '').split('-');
    return parts.length === 3 ? `${parts[2]}/${parts[1]}` : '—';
  };
  const labels = usable.map((point, index) => `<text x="${sx(index).toFixed(1)}" y="${height - 19}" text-anchor="middle">${dateLabel(point.outboundDate)}</text>`).join('');
  const dots = (field, colour) => usable.map((point, index) => `<circle cx="${sx(index).toFixed(1)}" cy="${sy(Number(point[field])).toFixed(1)}" r="3.5" fill="${colour}"><title>${esc(point.outboundDate)} · ${point.routes.length} rutas · mediana ${eur(point[field])}</title></circle>`).join('');
  return `<svg class="air-comparison-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Comparación de precios entre las dos últimas fotos, por fecha de salida"><line x1="${pad.left}" y1="${height - pad.bottom}" x2="${width - pad.right}" y2="${height - pad.bottom}" stroke="var(--line)"/><line x1="${pad.left}" y1="${pad.top}" x2="${width - pad.right}" y2="${pad.top}" stroke="var(--line)"/><path d="${path('previousPrice')}" fill="none" stroke="#9aa4b2" stroke-width="2" stroke-dasharray="5 4"/><path d="${path('currentPrice')}" fill="none" stroke="var(--ac)" stroke-width="2.5"/>${dots('previousPrice', '#9aa4b2')}${dots('currentPrice', 'var(--ac)')}${labels}<text class="air-axis-value" x="${pad.left - 8}" y="${pad.top + 3}" text-anchor="end">${eur(max)}</text><text class="air-axis-value" x="${pad.left - 8}" y="${height - pad.bottom + 3}" text-anchor="end">${eur(min)}</text><text class="air-axis-title air-axis-title--y" x="14" y="${height / 2}" text-anchor="middle" transform="rotate(-90 14 ${height / 2})">€ por viajero</text><text class="air-axis-title" x="${(pad.left + width - pad.right) / 2}" y="${height - 2}" text-anchor="middle">Fecha de salida</text></svg>`;
}

function airComparisonReadout(points) {
  const groups = new Map();
  (points || []).filter((point) => point.comparable && point.currentPrice != null && point.previousPrice != null).forEach((point) => {
    const date = String(point.outboundDate || '');
    if (!groups.has(date)) groups.set(date, { current: [], previous: [], routes: 0 });
    const group = groups.get(date);
    group.current.push(Number(point.currentPrice));
    group.previous.push(Number(point.previousPrice));
    group.routes += 1;
  });
  return [...groups.entries()].map(([date, group]) => {
    const current = median(group.current), previous = median(group.previous);
    const delta = current - previous;
    const pct = previous ? (delta / previous) * 100 : null;
    const parts = date.split('-');
    const label = parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0]}` : date;
    return `<div class="air-chart-readout"><strong>${label}</strong><span>Última foto <b>${eur(current)}</b></span><span>Foto anterior <b>${eur(previous)}</b></span><span class="${delta > 0 ? 'is-up' : delta < 0 ? 'is-down' : ''}">${delta > 0 ? '+' : ''}${eur(delta)} (${signPct(pct)})</span><small>${group.routes} rutas comparables · mediana</small></div>`;
  }).join('');
}

function airCaptureStartDate() {
  const date = new Date();
  date.setHours(12, 0, 0, 0);
  return date.toISOString().slice(0, 10);
}

async function estimateAirCapture() {
  const start = $('#airCaptureStart')?.value;
  const maxQueries = Number($('#airCaptureBudget')?.value || 500);
  const status = $('#airCaptureEstimate');
  const startButton = $('[data-air-capture-start]');
  if (!start || !status) return;
  status.textContent = 'Calculando consultas…';
  if (startButton) startButton.disabled = true;
  try {
    const estimate = await api('/api/air-data/capture/estimate', {
      method: 'POST',
      body: JSON.stringify({ areaIds: ['gran-canaria'], routeKeys: [], countryIds: [], direct: true, outboundDate: start, dailyDays: 14, weeklyUntilDays: 90, maxQueries: maxQueries }),
    });
    State.airCaptureEstimate = estimate;
    const configured = estimate.serpapiConfigured !== false;
    const tone = estimate.withinBudget && configured ? 'is-valid' : 'is-invalid';
    status.className = `air-capture-estimate ${tone}`;
    const providerMessage = configured ? '' : ' · falta configurar SERPAPI_API_KEY';
    status.innerHTML = `<strong>${nEs(estimate.queries)} consultas estimadas</strong><span>${nEs(estimate.routes)} rutas · ${nEs(estimate.dateCount)} fechas · ${estimate.withinBudget ? 'dentro' : 'fuera'} del presupuesto de ${nEs(estimate.maxQueries)}${providerMessage}</span>`;
    if (startButton) startButton.disabled = !estimate.withinBudget || !configured;
  } catch (error) {
    State.airCaptureEstimate = null;
    status.className = 'air-capture-estimate is-invalid';
    status.textContent = error.message;
  }
}

async function startAirCapture() {
  const estimate = State.airCaptureEstimate;
  const status = $('#airCaptureEstimate');
  if (!estimate || !estimate.withinBudget || !status) return;
  const startButton = $('[data-air-capture-start]');
  const maxQueries = Number($('#airCaptureBudget')?.value || 500);
  if (startButton) startButton.disabled = true;
  status.className = 'air-capture-estimate';
  status.textContent = 'Enviando captura manual…';
  try {
    const response = await api('/api/jobs/air-capture', {
      method: 'POST',
      body: JSON.stringify({ areaIds: ['gran-canaria'], routeKeys: [], countryIds: [], direct: true, outboundDate: $('#airCaptureStart').value, dailyDays: 14, weeklyUntilDays: 90, maxQueries: maxQueries }),
    });
    status.className = 'air-capture-estimate is-valid';
    status.innerHTML = `<strong>Captura en cola</strong><span>Trabajo ${esc(response.job?.id || '—')} · consulta Operación aérea para seguir el progreso.</span>`;
    State.airCaptureEstimate = null;
  } catch (error) {
    status.className = 'air-capture-estimate is-invalid';
    status.textContent = error.message;
    if (startButton) startButton.disabled = false;
  }
}

/* ================================================================== VUELOS */
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

async function renderFlights() {
  if (State.flightTab === 'operations') return renderAirOperations();
  const host = mount('flights');
  skeleton(host, 'list');
  let d, comparison;
  try {
    [d, comparison] = await Promise.all([
      State.air || api('/api/air-data?direction=arrival'),
      api('/api/air-data/comparison?direction=arrival').catch(() => ({ points: [], comparable: 0 })),
    ]);
    State.air = d;
  }
  catch (e) { host.innerHTML = `<div class="page">${flightsPageHeader('Conectividad del destino.')}<div class="inline-error">No se pudo cargar la conectividad aérea: ${esc(e.message)}</div></div>`; return; }

  const sum = d.summary || {};
  const routes = (d.routes || []);
  const flights = (d.flights || []);
  const dist = sum.price_quality_distribution || {};

  const dumb = routes.slice().sort((a, b) => (b.avg_price || 0) - (a.avg_price || 0)).slice(0, 8).map((r) => ({
    label: `${r.origin} → ${r.destination}`, market: r.market, min: r.lowest_price || 0, avg: r.avg_price || 0,
  })).filter((r) => r.avg > 0);

  const fbody = flights.slice(0, 40).map((f) => {
    const q = (f.price_quality_label || '').toLowerCase();
    const chip = q.includes('barat') ? 'chip--good' : q.includes('caro') ? 'chip--bad' : 'tag';
    const conn = f.is_direct ? '<span class="chip chip--direct">Directo</span>' : `<span class="dim">${f.num_layovers || 1} escala${(f.num_layovers || 1) > 1 ? 's' : ''}</span>`;
    return `<tr>
      <td class="mono">${esc(f.origin)} → ${esc(f.destination)}</td>
      <td class="name">${airlineCell(f)}</td>
      <td>${airMarketCell(f)}</td>
      <td class="mono">${esc(airDate(f.outbound_date))}</td>
      <td>${conn}</td>
      <td class="num" style="font-weight:700;">${eur(f.price)}</td>
      <td><span class="${chip === 'tag' ? 'tag' : 'chip ' + chip}">${esc(f.price_quality_label || 'Normal')}</span></td>
    </tr>`;
  }).join('');

  host.innerHTML = `<div class="page">
    ${flightsPageHeader('Conectividad, precio y calidad de las rutas que alimentan el destino.')}

    <div class="grid grid--5 mb12">
      ${kpiSm('Rutas de llegada', sum.total_routes || routes.length, '', `${flights.length} opciones observadas`)}
      ${kpiSm('Precio de acceso', Math.round(sum.avg_lowest_price || 0), ' €', 'mínimo medio · 1 adulto')}
      ${kpiSmRaw('Variación entre fotos', comparison.comparable ? signPct(comparison.points.filter((p) => p.changePct != null).reduce((a, p) => a + p.changePct, 0) / comparison.comparable) : '—', '', `${comparison.comparable || 0} parejas comparables`)}
      ${kpiSm('Cobertura de rutas', sum.total_routes ? Math.round((routes.length / sum.total_routes) * 100) : 0, '%', 'rutas con resultado agregado')}
      ${kpiSm('Vuelos directos', Math.round((sum.direct_pct || 0) * 100), '%', 'filtro de llegada aplicado')}
    </div>

    <article class="card card--pad mb12 air-capture-plan">
      <div class="card__head" style="margin-bottom:10px;"><div><div class="card__kicker">Captura manual</div><h2>Preparar una foto de conectividad</h2><p>SerpAPI · 1 adulto · turista · solo ida · próximas 14 fechas diarias y después una fecha semanal hasta 90 días.</p></div><span class="tag">sin recurrencia</span></div>
      <div class="air-capture-plan__controls"><label><span>Primera salida</span><input class="input" type="date" id="airCaptureStart" value="${airCaptureStartDate()}" /></label><label><span>Presupuesto de consultas</span><input class="input" type="number" id="airCaptureBudget" min="1" max="5000" step="1" value="500" /></label><button type="button" class="btn btn--quiet" data-air-capture-estimate>Estimar consumo</button><button type="button" class="btn btn--primary" data-air-capture-start disabled>Iniciar captura</button></div>
      <div id="airCaptureEstimate" class="air-capture-estimate" role="status">Calcula el consumo antes de iniciar.</div>
    </article>

    <article class="card card--pad mb12">
      <div class="card__head" style="margin-bottom:16px;">
        <div><div class="card__kicker" style="margin-bottom:5px;">Precio de entrada vs. medio</div><h2>Amplitud de tarifa por ruta</h2><p>Diferencia entre la tarifa mínima y la media de las ofertas observadas; no son precios de billetes vendidos.</p></div>
        <div class="legend"><span><i style="background:var(--card); border:2px solid var(--ac);"></i>mínimo</span><span><i style="background:var(--ink);"></i>medio</span></div>
      </div>
      ${dumbbellSVG(dumb)}
    </article>

    <article class="card card--pad mb12 air-comparison-card">
      <div class="card__head" style="margin-bottom:10px;">
        <div><div class="card__kicker">Comparación de fotos</div><h2>Precio mínimo por fecha de salida</h2><p>Dos fotos SerpAPI · misma ruta y fecha · cada punto resume la mediana de las rutas comparables.</p></div>
        <div class="legend"><span><i style="background:var(--ac);"></i>última foto</span><span><i style="background:#9aa4b2;"></i>foto anterior</span></div>
      </div>
      ${airComparisonSVG(comparison.points, comparison.comparisonStatus)}
      <div class="air-chart-readouts">${airComparisonReadout(comparison.points)}</div>
      <div class="air-chart-reading"><span><b>Eje X</b> Fecha de salida del vuelo</span><span><b>Eje Y</b> Precio observado por viajero</span><span><b>Línea</b> Azul: última foto · gris: foto anterior</span></div>
      <p class="air-data-disclaimer">Precio observado en SerpAPI/Google Flights. No representa reservas confirmadas, ocupación aérea ni demanda hotelera.</p>
    </article>

    <article class="card table-card">
      <div class="table-card__head">
        <div class="title"><strong>Opciones capturadas</strong><span class="count">${flights.length} filas</span></div>
      </div>
      <div class="table-scroll">
        <table class="t" style="min-width:820px;">
          <thead><tr><th>Ruta</th><th>Compañía</th><th>Mercado</th><th>Salida</th><th>Conexión</th><th class="r">Precio</th><th>Señal</th></tr></thead>
          <tbody>${fbody || `<tr><td colspan="7" class="empty">Sin vuelos capturados todavía.</td></tr>`}</tbody>
        </table>
      </div>
    </article>
  </div>`;
  runCounters(host);
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
    overlay.addEventListener('mousedown', (event) => { if (event.target === overlay) closeOverlay(id); });
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
  State.dashboardExplorerResult = null;
  State.dashboardExplorerResultKey = null;
  State.dashboardExplorerSearch = '';
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
  delete State.snapshots[targetId]; delete State.metrics[targetId]; delete State.heatmaps[targetId]; delete State.demandCurves[targetId]; delete State.hotelStability[targetId]; delete State.photoHistories[targetId]; delete State.captureHistories[targetId];
  delete State.hotelPriceHistories[targetId]; delete State.hotelRateDetails[targetId];
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
  return closeMarketMenu(true);
}

/* eventos globales por delegación */
function wireEvents() {
  wireHotelReputationEvents();
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !chromeLayerOpen() && !$('#copilotResults')?.hidden) {
      const close = $('#closeCopilotPanel'); close?.click(); e.preventDefault(); return;
    }
    const tab = e.target.closest('[data-dashboard-view]');
    if (!tab || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
    e.preventDefault();
    const tabs = [...document.querySelectorAll('[data-dashboard-view]')];
    const current = tabs.indexOf(tab);
    const nextIndex = e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length - 1 : (current + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
    const next = tabs[nextIndex]?.dataset.dashboardView || 'market';
    activateDashboardView(next);
    document.querySelector(`[data-dashboard-view="${next}"]`)?.focus();
  });
  document.addEventListener('change', (e) => {
    const control = e.target instanceof HTMLSelectElement ? e.target : null;
    if (!control) return;
    if (control.id === 'dashboardExplorerPhoto') {
      const snapshotId = Number(control.value);
      if (!Number.isInteger(snapshotId)) return;
      State.dashboardExplorerSnapshotId = snapshotId;
      State.dashboardExplorerResult = null;
      State.dashboardExplorerResultKey = null;
      void loadDashboardExplorer(mount('dashboard'));
      return;
    }
    if (control.id === 'dashboardExplorerSort') {
      State.dashboardExplorerSort = ['adr-desc', 'adr-asc', 'name-asc'].includes(control.value) ? control.value : 'adr-desc';
      const outlet = $('#dashboardExplorerData', mount('dashboard'));
      if (State.dashboardExplorerResult && State.dashboardExplorerResultKey === `${State.targetId}:${State.dashboardExplorerSnapshotId}`) renderDashboardExplorerResults(outlet, State.dashboardExplorerResult);
    }
  });
  document.addEventListener('input', (e) => {
    const control = e.target instanceof HTMLInputElement ? e.target : null;
    if (!control || control.id !== 'dashboardExplorerSearch') return;
    State.dashboardExplorerSearch = control.value.slice(0, 160);
    const outlet = $('#dashboardExplorerData', mount('dashboard'));
    if (State.dashboardExplorerResult && State.dashboardExplorerResultKey === `${State.targetId}:${State.dashboardExplorerSnapshotId}`) renderDashboardExplorerResults(outlet, State.dashboardExplorerResult);
  });
  document.addEventListener('error', (e) => {
    if (e.target instanceof HTMLImageElement && e.target.classList.contains('flight-airline__logo-img')) e.target.remove();
  }, true);
  document.addEventListener('mouseover', (e) => {
    const item = e.target instanceof Element ? e.target.closest('.palette__item') : null;
    if (item && Number(item.dataset.paletteIndex) !== State.palette.index) setPaletteIndex(Number(item.dataset.paletteIndex), false);
  });
  document.addEventListener('focusin', (e) => {
    if (e.target instanceof Element && !e.target.closest('.market-switch')) closeMarketMenu();
  });
  document.addEventListener('click', (e) => {
    const target = e.target instanceof Element ? e.target : null;
    const marker = target?.closest('[data-dashboard-map-marker]');
    if (!marker) return;
    const row = State.dashboardMapRows[marker.dataset.dashboardMapMarker];
    if (!row) return;
    e.preventDefault();
    e.stopPropagation();
    openDashboardHotel(row);
  }, true);
  document.addEventListener('click', async (e) => {
    if (e.target.closest('[data-dashboard-map-retry]')) {
      const rows = State.snapshots[State.targetId]?.latest?.rows || [];
      void renderDashboardHotelMap(rows, rows);
      return;
    }
    if (!e.target.closest('.market-switch')) closeMarketMenu();
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
    const dashboardView = e.target.closest('[data-dashboard-view]');
    if (dashboardView) {
      const nextView = dashboardView.dataset.dashboardView;
      activateDashboardView(nextView);
      return;
    }
    const mk = e.target.closest('[data-market]');
    if (mk) { selectMarket(mk.dataset.market); return; }
    const capMk = e.target.closest('[data-cap-market]');
    if (capMk) { selectMarket(capMk.dataset.capMarket); return; }
    const dashboardHotel = e.target.closest('[data-dashboard-hotel]');
    if (dashboardHotel) {
      if (dashboardHotel.dataset.priorityHotel === 'true') {
        if (State.dashboardView !== 'market') {
          activateDashboardView('market');
        }
        $('#dashboardHotelMap')?.scrollIntoView({ block: 'center', behavior: 'auto' });
      }
      openDashboardHotel(dashboardHotel.dataset.dashboardHotel); return;
    }
    const dashboardExpand = e.target.closest('[data-dashboard-expand]');
    if (dashboardExpand) {
      const key = dashboardExpand.dataset.dashboardExpand;
      const detail = $(`[data-dashboard-detail="${CSS.escape(key)}"]`);
      const expanded = detail && detail.hidden;
      if (detail) detail.hidden = !expanded;
      dashboardExpand.setAttribute('aria-expanded', expanded ? 'true' : 'false');
      dashboardExpand.classList.toggle('is-expanded', expanded);
      dashboardExpand.textContent = expanded ? '▾' : '▸';
      return;
    }
    if (e.target.closest('[data-dashboard-drawer-expand]')) { toggleDashboardHotelInspector(); return; }
    if (e.target.closest('[data-dashboard-drawer-close]')) {
      closeDashboardHotel();
      return;
    }
    const flightTab = e.target.closest('[data-flight-tab]');
    if (flightTab) { State.flightTab = flightTab.dataset.flightTab === 'operations' ? 'operations' : 'overview'; renderFlights(); return; }
    if (e.target.closest('[data-air-capture-estimate]')) { void estimateAirCapture(); return; }
    if (e.target.closest('[data-air-capture-start]')) { void startAirCapture(); return; }
    const airOperationPage = e.target.closest('[data-air-operation-page]');
    if (airOperationPage) {
      const delta = airOperationPage.dataset.airOperationPage === 'next' ? 1 : -1;
      State.airOperations.page = Math.max(1, State.airOperations.page + delta);
      renderAirOperations();
      return;
    }
    if (e.target.closest('[data-air-operation-reset]')) { resetAirOperationsQuery(); return; }
    if (e.target.closest('[data-air-operations-fullscreen]')) { toggleAirOperationsFullscreen(); return; }
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
    if (e.key === 'Escape' && closeDashboardHotel()) {
      e.preventDefault();
      return;
    }
    if (e.key === 'Escape' && State.airOperations.fullscreen) {
      e.preventDefault();
      toggleAirOperationsFullscreen(false);
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
    if (e.target && e.target.id === 'copilotMode') { State.copilotMode = e.target.value; return; }
    if (e.target && e.target.id === 'chatFile' && e.target.files?.[0]) {
      void uploadCopilotAttachment(e.target.files[0]); e.target.value = '';
    }
  });

  document.addEventListener('input', (e) => {
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
    if (e.target && e.target.id === 'airOperationsSearch') {
      clearTimeout(airOperationsSearchTimer);
      const value = e.target.value;
      airOperationsSearchTimer = setTimeout(() => updateAirOperationsQuery('query', value, true), 220);
    }
  });
  document.addEventListener('change', (e) => {
    if (e.target && (e.target.id === 'airCaptureStart' || e.target.id === 'airCaptureBudget')) {
      State.airCaptureEstimate = null;
      const status = $('#airCaptureEstimate');
      const startButton = $('[data-air-capture-start]');
      if (status) { status.className = 'air-capture-estimate'; status.textContent = 'Vuelve a estimar el consumo con esta configuración.'; }
      if (startButton) startButton.disabled = true;
      return;
    }
    const workspaceContextSelect = e.target && e.target.closest('[data-workspace-context]');
    if (workspaceContextSelect) {
      setWorkspaceContext(workspaceContextSelect.dataset.workspaceContext, workspaceContextSelect.value);
      return;
    }
    if (e.target && e.target.id === 'hotelGroup' && SHEET_GROUPS.some((g) => g.id === e.target.value)) { State.hotelGroup = e.target.value; paintHotelSheet(); }
    const airFilter = e.target && e.target.closest('[data-air-operation-filter]');
    if (airFilter) {
      const key = airFilter.dataset.airOperationFilter;
      const value = key === 'pageSize' ? Number(airFilter.value) : airFilter.value;
      updateAirOperationsQuery(key, value);
    }
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
