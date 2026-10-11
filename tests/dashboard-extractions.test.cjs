const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('backend/app/static/atlas.js', 'utf8');
const context = vm.createContext({
  median: (values) => {
    const sorted = values.slice().sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
  },
  fmtStamp: (value) => value,
  eur: (value) => `${value} €`,
  esc: (value) => String(value),
  State: { targetId: 1, dashboard: { ptHover: null }, hotelPriceHistories: {}, captureHistories: {} },
});
vm.runInContext(source.slice(source.indexOf('function dashboardDateSeries('), source.indexOf('function dashboardPopoverFacts(')), context);
const row = (snapshotId, checkIn, pricePerNight) => ({ snapshotId, checkIn, pricePerNight });
const capture = (snapshotIds, observedAt, checkIns) => ({ snapshotIds, observedAt, checkIns });

test('compares only the two latest extraction groups with hotel rates, even when captures are minutes apart', () => {
  const history = [row(1, '2026-10-12', 90), row(2, '2026-10-12', 100), row(3, '2026-10-12', 120), row(4, '2026-10-19', 130)];
  const captures = [
    capture([1], '2026-09-01T10:00:00Z', ['2026-10-12']),
    capture([2], '2026-10-06T10:00:00Z', ['2026-10-12']),
    capture([3, 4], '2026-10-06T10:02:00Z', ['2026-10-12', '2026-10-19']),
  ];
  const series = context.dashboardDateSeries(history, captures);
  assert.equal(series.currentLabel, captures[2].observedAt);
  assert.equal(series.previousLabel, captures[1].observedAt);
  assert.deepEqual(Array.from(series.points, (p) => [p.value, p.prev]), [[120, 100], [130, null]]);
});

test('keeps all dates from a capture and missing rates instead of borrowing older observations', () => {
  const history = [row(1, '2026-10-19', 50), row(2, '2026-10-12', 100), row(3, '2026-10-12', 120), row(4, '2026-10-26', 140)];
  const captures = [
    capture([3, 4], '2026-10-06T12:00:00Z', ['2026-10-12', '2026-10-19', '2026-10-26']),
    capture([2], '2026-10-02T12:00:00Z', ['2026-10-12']),
    capture([1], '2026-09-28T12:00:00Z', ['2026-10-19']),
  ];
  const series = context.dashboardDateSeries(history, captures);
  assert.deepEqual(Array.from(series.points, (p) => p.date), ['2026-10-12', '2026-10-19', '2026-10-26']);
  assert.equal(series.points[1].value, null);
  assert.equal(series.points[1].prev, null);
  assert.equal(series.points[1].currentExpected, true);
});

test('uses the previous extraction with hotel rates and does not invent a second series', () => {
  const history = [row(1, '2026-12-28', 100), row(3, '2027-01-04', 110)];
  const captures = [
    capture([3], '2026-10-06T12:00:00Z', ['2027-01-04']),
    capture([2], '2026-10-06T11:59:00Z', ['2027-01-04']),
    capture([1], '2026-10-02T12:00:00Z', ['2026-12-28']),
  ];
  assert.equal(context.dashboardDateSeries(history, captures).previousLabel, captures[2].observedAt);
  assert.equal(context.dashboardDateSeries(history, [captures[0]]).previousLabel, null);
  assert.equal(context.dashboardDateSeries([], captures), null);
});

test('renders both extraction series with accessible dates and cuts a line at an observed gap', () => {
  context.State.hotelPriceHistories[1] = { hotel: [row(1, '2026-10-12', 100), row(2, '2026-10-19', 105), row(3, '2026-10-12', 120), row(4, '2026-10-26', 140)] };
  context.State.captureHistories[1] = { captures: [
    capture([3, 4], '2026-10-06T12:00:00Z', ['2026-10-12', '2026-10-19', '2026-10-26']),
    capture([1, 2], '2026-10-02T12:00:00Z', ['2026-10-12', '2026-10-19']),
  ] };
  const html = context.dashboardPopoverChartHTML({ key: 'hotel' });
  assert.match(html, /Última extracción/);
  assert.match(html, /Anterior con tarifas/);
  assert.match(html, /dash-pop__pt--previous/);
  assert.match(html, /2026-10-26/);
  // The older capture has two adjacent rates; the latest has an unobserved date between its two rates.
  assert.equal((html.match(/<polyline /g) || []).length, 1);
  assert.equal((html.match(/<circle /g) || []).length, 4);
});
