const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('backend/app/static/atlas.js', 'utf8');
const context = vm.createContext({});
vm.runInContext(source.slice(source.indexOf('function hotelComparisonSignature('), source.indexOf('async function api(')) + source.slice(source.indexOf('function captureComparisonStats('), source.indexOf('function captureComparisonHTML(')), context);
const hotel = (changes={}) => ({hotelKey:'a',checkIn:'2026-10-01',checkOut:'2026-10-08',nights:7,pax:2,roomType:'Double',board:'All inclusive',currency:'EUR',freeCancellation:false,pricePerNight:100,...changes});
for(const field of ['board','roomType','currency','pax','freeCancellation']) test(`unknown ${field} cannot be compared`, () => {
  const row = hotel({[field]:null});
  assert.equal(context.captureComparisonStats({rows:[row]},{rows:[row]}).comparable.length,0);
});
test('unmatched expensive hotel does not inflate paired movement',()=>{
  const result=context.captureComparisonStats({rows:[hotel(),hotel({hotelKey:'b',pricePerNight:1000})]},{rows:[hotel()]});
  assert.equal(result.avgChange,0);
});
test('duplicate identity is excluded',()=>{
  assert.equal(context.captureComparisonStats({rows:[hotel()]},{rows:[hotel(),hotel({pricePerNight:200})]}).comparable.length,0);
});
test('currency groups cannot produce a single average',()=>{
  const rows=[hotel(),hotel({hotelKey:'b',currency:'USD'})];
  assert.equal(context.captureComparisonStats({rows},{rows}).avgChange,null);
});
