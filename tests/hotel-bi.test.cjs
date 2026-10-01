const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

// Solo las utilidades y el bloque de lógica pura del panel de análisis (sin DOM ni State).
const source = fs.readFileSync('backend/app/static/atlas.js', 'utf8');
const utils = source.slice(source.indexOf('const NBSP ='), source.indexOf('function hotelComparisonSignature('));
const logic = source.slice(source.indexOf('/* >>> panel-bi:logica'), source.indexOf('/* <<< panel-bi:logica */'));
const ctx = {};
vm.createContext(ctx);
vm.runInContext(`${utils}\n${logic}\nObject.assign(globalThis, { biQuantile, biValueScore, biHeat, biMapTone, biCalendarHead, biRankAt, biRecommendation, biWeeks, biAlerts, biDayLong, biPinSize });`, ctx);
const plain = (value) => JSON.parse(JSON.stringify(value));

test('cuantil con interpolación lineal, igual que el backend', () => {
  assert.equal(ctx.biQuantile([200, 300, 400], 0.25), 250);
  assert.equal(ctx.biQuantile([200, null, 300], 0.5), 250);
  assert.equal(ctx.biQuantile([], 0.5), null);
});

test('value score con la fórmula del README y acotado a 0–100', () => {
  assert.equal(ctx.biValueScore(8.5, 270, 270, 8.0), 61); // 50 + 0,5 × 22
  assert.equal(ctx.biValueScore(8.0, 405, 270, 8.0), 20); // 50 − 0,5 × 60
  assert.equal(ctx.biValueScore(9.9, 100, 300, 7), 100);
  assert.equal(ctx.biValueScore(null, 200, 270, 8), null);
  assert.equal(ctx.biValueScore(8, null, 270, 8), null);
});

test('celdas de calor: neutras a ±5 %, alfa máximo 0,6', () => {
  assert.equal(ctx.biHeat(103, 100).bg, 'var(--line-soft)');
  assert.equal(ctx.biHeat(80, 100).bg, 'rgba(31,122,82,0.32)');
  assert.equal(ctx.biHeat(300, 100).bg, 'rgba(185,79,80,0.60)');
  assert.equal(ctx.biHeat(null, 100), null);
});

test('semáforo del mapa por relación con la mediana del día', () => {
  assert.equal(ctx.biMapTone(85, 100), 'low');
  assert.equal(ctx.biMapTone(114, 100), 'mid');
  assert.equal(ctx.biMapTone(115, 100), 'high');
  assert.equal(ctx.biMapTone(null, 100), 'closed');
  assert.equal(ctx.biPinSize(10000), 24);
  assert.equal(ctx.biPinSize(0), 10);
});

test('cabecera del calendario: días con ≤ 30, meses y lunes con más', () => {
  const dates = (n) => Array.from({ length: n }, (_, i) => new Date(Date.UTC(2026, 9, 1 + i)).toISOString().slice(0, 10));
  const short = plain(ctx.biCalendarHead(dates(30)));
  assert.equal(short[0].text, '1');
  assert.equal(short[29].text, '30');
  const long = plain(ctx.biCalendarHead(dates(90)));
  assert.equal(long[0].text, 'OCT');
  assert.equal(long[31].text, 'NOV'); // 1 de noviembre
  assert.equal(long[4].text, '5'); // lunes 5 de octubre
  assert.equal(long[29].text, ''); // jueves cualquiera
  assert.equal(long[32].text, ''); // lunes 2 de noviembre: a 1 día del cambio de mes
  assert.equal(ctx.biDayLong('2026-10-08'), 'jue 08/10');
});

test('puesto en una fecha: 1 es el más caro y los cerrados no cuentan', () => {
  const hotels = [{ key: 'a', prices: [200] }, { key: 'b', prices: [300] }, { key: 'c', prices: [null] }];
  assert.deepEqual(plain(ctx.biRankAt(hotels, 'a', 0)), { rank: 2, of: 2 });
  assert.equal(ctx.biRankAt(hotels, 'c', 0), null);
});

test('tarifa sugerida: suma de los seis componentes del README', () => {
  const reco = ctx.biRecommendation({ openPrices: [200, 250, 300, 350], dayMedian: 275, targetPct: 60, valueScore: 70, closed: 2, low: 2, scopeSize: 10, deltas: [5, -5, 10], leadDays: 15 });
  const parts = Object.fromEntries(reco.parts.map((p) => [p.id, Math.round(p.value * 100) / 100]));
  assert.equal(parts.median, 275);
  assert.equal(parts.target, 15); // P60 = 290 (interpolación lineal)
  assert.equal(parts.value, 5.5); // (70 − 50) / 50 × 5 % × 275
  assert.equal(parts.scarcity, 22); // (2 + 0,5 × 2) / 10 × 0,35 = 10,5 % → tope del 8 %
  assert.equal(parts.movement, 2.75); // media 1 % × 275
  assert.equal(parts.lead, 8.25); // < 21 días: +3 %
  assert.equal(reco.suggested, Math.round(275 + 15 + 5.5 + 22 + 2.75 + 8.25));
  assert.equal(ctx.biRecommendation({ openPrices: [], dayMedian: null, targetPct: 60, valueScore: null, closed: 0, low: 0, scopeSize: 0, deltas: [], leadDays: 30 }), null);
});

test('semanas: solo cuentan las celdas observadas; sin captura queda sin dato', () => {
  const dates = Array.from({ length: 14 }, (_, i) => `2026-10-${String(i + 1).padStart(2, '0')}`);
  const status = Array(14).fill(null);
  status[2] = 'closed'; status[3] = 'low';
  const weeks = plain(ctx.biWeeks(dates, [{ status }, { status: Array(14).fill(null).map((_, i) => (i === 2 ? 'ok' : null)) }]));
  assert.deepEqual(weeks[0], { start: '2026-10-01', closed: 1, low: 1, total: 3 });
  assert.equal(weeks[1].total, 0);
});

test('alertas: nuevos, bajadas, subidas, última unidad y cierres', () => {
  const base = { status: [], adr: 300, prevAdr: 320 };
  const alerts = plain(ctx.biAlerts([
    { ...base, key: 'n', name: 'Nuevo', isNew: true, delta: null },
    { ...base, key: 'b', name: 'Baja', delta: -6.2 },
    { ...base, key: 's', name: 'Sube', delta: 5 },
    { ...base, key: 'q', name: 'Queda', delta: 1, latestUnits: 1 },
    { ...base, key: 'c', name: 'Cierra', delta: 0, status: ['closed', 'ok', 'closed'] },
  ]));
  assert.deepEqual(alerts.map((a) => a.tag), ['Bajada', 'Queda 1', 'Subida', 'Nuevo', 'Cierres']);
  assert.equal(alerts[0].value, '−6,2 %');
});
