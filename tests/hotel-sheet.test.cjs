const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

// Se ejecutan solo las utilidades y el bloque de lógica pura de la hoja de mercado (sin DOM ni State).
const source = fs.readFileSync('backend/app/static/atlas.js', 'utf8');
const utils = source.slice(source.indexOf('const NBSP ='), source.indexOf('function runCounters('));
const start = source.indexOf('/* >>> hoja-de-mercado:logica');
const end = source.indexOf('/* <<< hoja-de-mercado:logica */');
assert.ok(start > 0 && end > start, 'faltan los marcadores del bloque de lógica pura');
const context = vm.createContext({});
vm.runInContext(`${utils}\n${source.slice(start, end)}\nthis.api = {hotelSheetModel, hotelSheetFilter, hotelSheetSort, hotelSheetGroups, hotelSheetCsv, hotelStockInfo, hotelZoneLabels, SHEET_VIEWS, SHEET_CHIPS};`, context);
const {hotelSheetModel, hotelSheetFilter, hotelSheetSort, hotelSheetGroups, hotelSheetCsv, hotelStockInfo, hotelZoneLabels} = context.api;

const row = (key, name, adr, extra = {}) => ({hotelKey: key, hotelName: name, pricePerNight: adr, pricePerPersonPerNight: adr / 2, rating: 8, reviewCount: 100, freeCancellation: false, unitsLeft: null, city: 'Maspalomas', ...extra});
const rows = () => [
  row('a', 'Hotel A', 100, {chain: 'Dunas', freeCancellation: true, city: 'Playa del Ingles'}),
  row('b', 'Hotel B Adults Only', 200, {adultsOnly: true, unitsLeft: 1, city: 'Playa del Inglés'}),
  row('c', 'Hotel C', 300, {chain: 'Lopesan', rating: 9.1, unitsLeft: 2, city: 'Playa Del Inglés'}),
  row('d', 'Hotel D', 400, {chain: 'Dunas', unitsLeft: 7, rating: null}),
  row('e', 'Hotel E', null, {soldOut: true, city: null, rating: 7}),
];
const metrics = () => ({
  market: {medianPricePerNight: 250},
  rateShoppingIndex: {bottomQuartileThreshold: 175, topQuartileThreshold: 325},
  competitiveSet: [{hotelKey: 'a', priceChangePct: 4.2}, {hotelKey: 'c', priceChangePct: 0}, {hotelKey: 'd', priceChangePct: -12}],
  newEntrants: [{hotelKey: 'b'}],
});
const stability = () => [
  {hotelKey: 'a', consistencyScore: 96, observations: 3},
  {hotelKey: 'a', consistencyScore: 50, observations: 1}, // se prefiere la entrada con más observaciones
  {hotelKey: 'c', consistencyScore: 82, observations: 4},
  {hotelKey: 'd', consistencyScore: 89.4, observations: 2},
  {hotelKey: 'b', consistencyScore: 89.6, observations: 2}, // se muestra como 90: no es «menos estable»
];
const model = () => hotelSheetModel(rows(), metrics(), stability());
const plain = (value) => JSON.parse(JSON.stringify(value));
const names = (list) => Array.from(list, (h) => h.name);

test('el modelo calcula posición frente a la mediana, tramo, rango y variación', () => {
  const m = model();
  const by = Object.fromEntries(m.hotels.map((h) => [h.key, h]));
  assert.equal(m.median, 250);
  assert.ok(Math.abs(by.a.vsMedian + 60) < 1e-9);
  assert.ok(Math.abs(by.d.vsMedian - 60) < 1e-9);
  assert.equal(by.a.tier, 'low');
  assert.equal(by.b.tier, 'mid');
  assert.equal(by.d.tier, 'high');
  assert.equal(by.e.tier, 'none');
  assert.equal(by.e.vsMedian, null);
  assert.deepEqual(plain(m.hotels.filter((h) => h.adr != null).sort((x, y) => x.rank - y.rank).map((h) => h.key)), ['d', 'c', 'b', 'a']);
  assert.equal(by.a.delta, 4.2);
  assert.ok(Math.abs(by.a.prevAdr - 100 / 1.042) < 1e-9);
  assert.equal(by.b.delta, null);
  assert.equal(by.b.isNew, true);
  assert.equal(by.a.stab, 96);
  assert.equal(by.b.stab, 90); // 89,6 se redondea a lo que se muestra
  assert.equal(m.minAdr, 100);
  assert.equal(m.maxAdr, 400);
});

test('sin métricas usa la mediana y los cuartiles de las propias filas', () => {
  const m = hotelSheetModel(rows(), null, []);
  assert.equal(m.median, 250);
  assert.ok(m.p25 > 100 && m.p75 < 400);
});

test('las variantes de una zona (acentos, mayúsculas) se unen en la más frecuente', () => {
  const labels = hotelZoneLabels([
    {city: 'Playa del Inglés'}, {city: 'Playa del Inglés'}, {city: 'Playa del Ingles'}, {city: 'Playa Del Inglés'},
    {city: null, popularDistrict: null, displayLocation: 'Taurito'}, {city: null},
  ]);
  assert.equal(labels.get('playa del ingles'), 'Playa del Inglés');
  assert.equal(labels.get('taurito'), 'Taurito');
  assert.equal(labels.size, 2);
  const zones = new Set(model().hotels.map((h) => h.zoneKey));
  assert.equal(zones.has('playa del ingles'), true);
  assert.equal(model().hotels.filter((h) => h.zoneKey === 'playa del ingles').length, 3);
});

test('vistas guardadas: tarifa alta ≥ +30 %, cancelación flexible, escasez (aviso de cupo) y estabilidad < 90', () => {
  const m = model();
  assert.deepEqual(names(hotelSheetFilter(m, {view: 'high'})), ['Hotel D']); // 300 → +20 %: no entra; 400 → +60 %
  assert.deepEqual(names(hotelSheetFilter(m, {view: 'flexible'})), ['Hotel A']);
  assert.deepEqual(names(hotelSheetFilter(m, {view: 'scarcity'})), ['Hotel B Adults Only', 'Hotel C', 'Hotel D', 'Hotel E']); // cualquier aviso de cupo o sold-out
  assert.deepEqual(names(hotelSheetFilter(m, {view: 'unstable'})), ['Hotel C', 'Hotel D']); // 82 y 89,4; el 96, el 89,6 (= 90 mostrado) y los sin dato no
});

test('tramos: «Bajo» es estrictamente menor que P25 y «Alto» desde P75', () => {
  const m = hotelSheetModel([row('a', 'A', 175), row('b', 'B', 174.9), row('c', 'C', 325)], {market: {medianPricePerNight: 250}, rateShoppingIndex: {bottomQuartileThreshold: 175, topQuartileThreshold: 325}}, []);
  assert.deepEqual(plain(m.hotels.map((h) => h.tier)), ['mid', 'low', 'high']);
});

test('«Tarifa alta» respeta el límite exacto de +30 %', () => {
  const m = hotelSheetModel([row('x', 'X', 130), row('y', 'Y', 129.9), row('z', 'Z', 100)], {market: {medianPricePerNight: 100}}, []);
  assert.deepEqual(names(hotelSheetFilter(m, {view: 'high'})), ['X']);
});

test('los filtros combinables se acumulan (AND) y la búsqueda ignora acentos y mayúsculas', () => {
  const m = model();
  assert.deepEqual(names(hotelSheetFilter(m, {view: 'market', chips: ['adults']})), ['Hotel B Adults Only']);
  assert.deepEqual(names(hotelSheetFilter(m, {view: 'market', chips: ['moved']})), ['Hotel A', 'Hotel D']); // Δ 0 no cuenta como movimiento
  assert.deepEqual(names(hotelSheetFilter(m, {view: 'market', chips: ['new']})), ['Hotel B Adults Only']);
  assert.deepEqual(names(hotelSheetFilter(m, {view: 'flexible', chips: ['moved']})), ['Hotel A']);
  assert.deepEqual(names(hotelSheetFilter(m, {view: 'market', chips: ['adults', 'moved']})), []);
  assert.deepEqual(names(hotelSheetFilter(m, {view: 'market', search: 'LOPESAN'})), ['Hotel C']); // por cadena
  assert.deepEqual(names(hotelSheetFilter(m, {view: 'market', search: 'playa del ingles'})), ['Hotel A', 'Hotel B Adults Only', 'Hotel C']); // por zona sin acento
  assert.deepEqual(names(hotelSheetFilter(m, {view: 'market', search: '  hotel d '})), ['Hotel D']);
  assert.equal(hotelSheetFilter(m, {view: 'market', search: 'zzz'}).length, 0);
});

test('ordenar deja los valores vacíos siempre al final, en ambos sentidos', () => {
  const m = model();
  assert.deepEqual(names(hotelSheetSort(m.hotels, {key: 'nota', dir: -1})), ['Hotel C', 'Hotel B Adults Only', 'Hotel A', 'Hotel E', 'Hotel D']); // A y B empatan en 8: gana el ADR más alto
  assert.deepEqual(names(hotelSheetSort(m.hotels, {key: 'nota', dir: 1})), ['Hotel E', 'Hotel B Adults Only', 'Hotel A', 'Hotel C', 'Hotel D']);
  assert.deepEqual(names(hotelSheetSort(m.hotels, {key: 'stab', dir: 1})).slice(0, 4), ['Hotel C', 'Hotel D', 'Hotel B Adults Only', 'Hotel A']);
  assert.deepEqual(names(hotelSheetSort(m.hotels, {key: 'delta', dir: -1})).slice(0, 3), ['Hotel A', 'Hotel C', 'Hotel D']);
  assert.deepEqual(names(hotelSheetSort(m.hotels, {key: 'name', dir: 1})), ['Hotel A', 'Hotel B Adults Only', 'Hotel C', 'Hotel D', 'Hotel E']);
  assert.deepEqual(names(hotelSheetSort(m.hotels, {key: 'adr', dir: -1})), ['Hotel D', 'Hotel C', 'Hotel B Adults Only', 'Hotel A', 'Hotel E']);
  assert.deepEqual(names(hotelSheetSort(m.hotels, {key: 'avail', dir: 1})).slice(0, 3), ['Hotel E', 'Hotel B Adults Only', 'Hotel C']); // sold-out, 1, 2 unidades
  assert.deepEqual(names(hotelSheetSort(m.hotels, {key: 'inexistente', dir: -1}))[0], 'Hotel D'); // clave desconocida → ADR
});

test('no se muta la lista original al ordenar', () => {
  const m = model();
  const before = names(m.hotels);
  hotelSheetSort(m.hotels, {key: 'name', dir: -1});
  assert.deepEqual(names(m.hotels), before);
});

test('agrupar: cadena (desconocidas al final), segmento, tramo en orden fijo y zona', () => {
  const m = model();
  const list = hotelSheetSort(m.hotels, {key: 'adr', dir: -1});
  assert.equal(hotelSheetGroups(list, 'none', m), null);
  const chain = hotelSheetGroups(list, 'chain', m);
  assert.deepEqual(plain(chain.map((g) => [g.label, g.hotels.length])), [['Dunas', 2], ['Lopesan', 1], ['Sin cadena reconocida', 2]]);
  assert.equal(chain[0].median, 250); // mediana de 400 y 100
  const segment = hotelSheetGroups(list, 'segment', m);
  assert.deepEqual(plain(segment.map((g) => g.label)), ['Familiar y mixto', 'Adults only']); // como el prototipo: por número de hoteles
  const tier = hotelSheetGroups(list, 'tier', m);
  assert.deepEqual(plain(tier.map((g) => g.id)), ['t:high', 't:mid', 't:low', 't:none']);
  assert.match(tier[0].label, /^Alto · más de 325/);
  assert.match(tier[1].label, /^Central · 175–325/);
  assert.match(tier[2].label, /^Bajo · menos de 175/);
  const zone = hotelSheetGroups(list, 'zone', m);
  assert.equal(zone[0].label, 'Playa del Inglés'); // la de más hoteles y con acento
  assert.equal(zone[zone.length - 1].label, 'Sin zona');
});

test('cupo: Queda 1 (crítico), Quedan N (aviso), sin dato y agotado', () => {
  assert.deepEqual({...hotelStockInfo({unitsLeft: 1})}, {text: 'Queda 1', tone: 'bad'});
  assert.deepEqual({...hotelStockInfo({unitsLeft: 3})}, {text: 'Quedan 3', tone: 'warn'});
  assert.deepEqual({...hotelStockInfo({unitsLeft: 7})}, {text: 'Quedan 7', tone: 'warn'});
  assert.deepEqual({...hotelStockInfo({unitsLeft: null})}, {text: '—', tone: 'none'});
  assert.deepEqual({...hotelStockInfo({unitsLeft: 0})}, {text: 'Sin disponibilidad', tone: 'bad'});
  assert.deepEqual({...hotelStockInfo({soldOut: true, unitsLeft: 5})}, {text: 'Sin disponibilidad', tone: 'bad'});
  assert.deepEqual({...hotelStockInfo({observationStatus: 'parse_error'})}, {text: 'Precio no interpretable', tone: 'bad'});
  assert.deepEqual({...hotelStockInfo({observationStatus: 'closed'})}, {text: 'Hotel cerrado', tone: 'plain'});
});

test('CSV: BOM, separador «;», decimales con coma, comillas escapadas y filas filtradas', () => {
  const m = model();
  const list = hotelSheetSort(hotelSheetFilter(m, {view: 'high'}), {key: 'adr', dir: -1});
  const csv = hotelSheetCsv(list);
  assert.equal(csv.charCodeAt(0), 0xfeff);
  const lines = csv.slice(1).split('\r\n');
  assert.equal(lines.length, 2); // cabecera + el único hotel de «Tarifa alta»
  assert.equal(lines[0], '"Hotel";"Cadena";"Zona";"ADR hab (€)";"ADR pers (€)";"Δ foto (%)";"vs mediana (%)";"Estabilidad";"Nota";"Reseñas";"Cancelación gratis";"Disponibilidad"');
  assert.equal(lines[1], '"Hotel D";"Dunas";"Maspalomas";"400,00";"200,00";"-12,0";"60,0";"89";"";"100";"No";"Quedan 7"');
  const all = hotelSheetCsv(hotelSheetSort(m.hotels, {key: 'adr', dir: -1})).slice(1).split('\r\n');
  assert.equal(all.length, 6); // cabecera + 5 hoteles, también el que no tiene precio
  assert.ok(all[5].startsWith('"Hotel E";"";"";"";'));
});

test('CSV: protege contra fórmulas y escapa comillas', () => {
  const m = hotelSheetModel([row('x', '=HYPERLINK("http://x")', 100, {chain: '+cmd'}), row('y', 'Hotel "Sol"', 120)], null, []);
  const lines = hotelSheetCsv(m.hotels).slice(1).split('\r\n');
  assert.ok(lines[1].startsWith('"\'=HYPERLINK(""http://x"")";"\'+cmd";'));
  assert.ok(lines[2].startsWith('"Hotel ""Sol""";'));
  assert.equal(hotelSheetCsv([]).slice(1).split('\r\n').length, 1); // solo cabecera
});

test('un set vacío no rompe el modelo', () => {
  const m = hotelSheetModel([], null, []);
  assert.deepEqual(plain(m.hotels), []);
  assert.equal(m.minAdr, null);
  assert.deepEqual(hotelSheetFilter(m, {view: 'market'}), []);
  assert.equal(hotelSheetGroups([], 'chain', m).length, 0);
});
