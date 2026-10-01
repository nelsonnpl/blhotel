(function(){
const Z = {
  'Maspalomas': [27.748, -15.586], 'Meloneras': [27.744, -15.603], 'Playa del Inglés': [27.758, -15.571],
  'San Agustín': [27.771, -15.547], 'Salobre': [27.779, -15.622], 'Puerto Rico': [27.787, -15.711],
  'Amadores': [27.791, -15.724], 'Taurito': [27.822, -15.749], 'Mogán': [27.816, -15.764],
};
const raw = [
  ['Seaside Palm Beach','Seaside','Maspalomas',667,334,0,91,9.0,296,1,null,0,'Habitación Doble · 2 camas'],
  ['Paradisus Gran Canaria - All Inclusive','Paradisus','Salobre',527,263,4.2,91,9.1,377,0,null,1,'Prémium vistas a las montañas'],
  ['H10 Playa Meloneras Horizons Collection','H10','Meloneras',439,220,3.1,91,8.8,620,0,null,0,'Habitación Doble Superior'],
  ['Gloria Palace Royal Hotel & Spa','Gloria Palace','Amadores',429,215,-4.5,94,9.0,1122,1,'Queda 1',0,'Doble vistas al mar'],
  ['Don Gregory by Dunas - Adults Only','Dunas','San Agustín',396,198,3.4,94,8.8,425,1,'Quedan 4',1,'Doble vistas al océano'],
  ['Maspalomas Villas by Dunas - Adults Only','Dunas','Maspalomas',394,197,0,98,8.9,43,1,null,1,'Villa entera'],
  ['Corallium Dunamar by Lopesan Hotels - Adults Only','Lopesan','Playa del Inglés',390,195,0,83,8.3,1147,1,null,1,'Habitación Doble Deluxe'],
  ['Seaside Sandy Beach','Seaside','Playa del Inglés',374,187,8.4,97,8.8,289,1,null,0,'Doble Superior · 1 o 2 camas'],
  ['HD Parque Cristobal Gran Canaria','HD','Playa del Inglés',374,187,10.3,90,8.6,245,1,'Quedan 2',0,'Suite privada'],
  ['Corallium Beach by Lopesan Hotels - Adults Only','Lopesan','Meloneras',354,177,-2.4,81,8.5,2170,1,null,1,'Doble Estándar con vistas'],
  ['Lopesan Costa Meloneras Resort','Lopesan','Meloneras',342,171,1.8,92,8.7,3210,1,null,0,'Habitación Doble'],
  ['HL Miraflor Suites Hotel','HL','Playa del Inglés',334,167,0,86,8.4,468,1,'Quedan 5',0,'Suite privada'],
  ['Lopesan Baobab Resort','Lopesan','Meloneras',318,159,-1.1,90,8.8,2640,1,null,0,'Habitación Doble'],
  ['Barceló Margaritas Royal Level Adults Only','Barceló','Playa del Inglés',313,157,2.4,95,8.6,570,0,'Quedan 5',1,'Suite privada'],
  ['H10 Costa Mogán - Adults Only','H10','Mogán',306,153,1.4,94,8.4,894,0,null,1,'Suite privada'],
  ['Suites & Villas by Dunas','Dunas','Maspalomas',306,153,0,93,8.5,394,1,null,0,'Suite privada'],
  ['HL Suitehotel Playa del Inglés - Adults Only','HL','Playa del Inglés',293,146,0,91,8.6,1163,1,'Quedan 2',1,'Suite'],
  ['Kumara Serenoa By Lopesan Hotels','Lopesan','Maspalomas',287,143,0,91,8.4,1006,1,'Quedan 3',0,'Habitación Doble'],
  ['HL Suite Nardos - Only Adults','HL','Playa del Inglés',278,139,0,97,8.6,132,1,'Queda 1',1,'Suite'],
  ['Servatur Puerto Azul','Servatur','Puerto Rico',277,139,15.2,89,8.8,940,1,null,0,'Apartamento 1 dormitorio'],
  ['Hotel Sahara Playa','Independiente','Playa del Inglés',270,135,3.9,97,7.7,271,1,'Quedan 5',0,'Habitación Doble'],
  ['Gloria Palace San Agustín Thalasso & Hotel','Gloria Palace','San Agustín',267,133,-11.1,95,8.6,1610,1,'Quedan 2',0,'Doble vistas al mar'],
  ['Cordial Mogán Playa','Cordial','Mogán',258,129,0.6,93,8.7,2480,1,null,0,'Habitación Doble'],
  ['Hotel Riu Vistamar Gran Canaria - All Inclusive','Riu','Amadores',253,127,null,95,8.5,946,1,null,0,'Habitación Doble vista mar'],
  ['Relaxia Beverly Park','Relaxia','San Agustín',245,123,0,87,8.6,1443,0,'Quedan 4',0,'Habitación Doble'],
  ['Barceló Margaritas','Barceló','Playa del Inglés',234,117,3.1,94,8.3,1203,0,'Queda 1',0,'Habitación Doble'],
  ['Abora Buenaventura by Lopesan Hotels','Lopesan','Playa del Inglés',229,115,1.5,89,7.9,976,1,null,0,'Habitación Familiar'],
  ['Mirador Maspalomas by Dunas','Dunas','Maspalomas',226,113,0.8,92,8.2,1320,1,null,0,'Habitación Doble'],
  ['Abora Catarina by Lopesan Hotels','Lopesan','Playa del Inglés',219,110,-1.2,88,8.0,2210,1,null,0,'Habitación Doble'],
  ['Abora Interclub Atlantic by Lopesan Hotels','Lopesan','San Agustín',214,107,0,90,7.8,1540,1,'Quedan 3',0,'Bungalow'],
  ['Abora Continental by Lopesan Hotels','Lopesan','Playa del Inglés',208,104,2.0,86,7.6,1890,0,null,0,'Habitación Doble'],
  ['Hotel LIVVO Valle Taurito & Aquapark','LIVVO','Taurito',192,96,null,93,8.1,610,1,null,0,'Apartamento'],
  ['BLUESEA Marieta','BLUESEA','Playa del Inglés',188,94,-2.1,84,7.5,820,1,null,0,'Apartamento'],
  ['Servatur Altamadores','Servatur','Amadores',174,87,0,96,8.3,512,1,null,0,'Apartamento'],
  ['Servatur Riosol','Servatur','Puerto Rico',174,87,-0.6,95,8.0,730,1,'Quedan 2',0,'Apartamento'],
  ['BLUESEA Rey Carlos','BLUESEA','Playa del Inglés',168,84,0,90,7.2,450,0,null,0,'Apartamento'],
  ['Bungalows Maspalomas Oasis Club','Independiente','Maspalomas',158,79,-1.9,88,7.9,1270,1,null,0,'Bungalow'],
  ['Hotel LIVVO Costa Taurito & Aquapark','LIVVO','Taurito',150,75,-3.8,82,7.4,1150,1,null,0,'Habitación Doble'],
];
const MEDIAN = 268;
const hotels = raw.map((r, i) => {
  const [lat, lng] = Z[r[2]];
  const j = ((i * 37) % 17) / 17 - .5, k = ((i * 53) % 13) / 13 - .5;
  return {
    id: 'h' + (i + 1), name: r[0], chain: r[1], zone: r[2], adr: r[3], pers: r[4], delta: r[5],
    stab: r[6], nota: r[7], reviews: r[8], cancel: !!r[9], avail: r[10], adults: !!r[11] || /adults|only/i.test(r[0]),
    room: r[12], isNew: r[5] === null, prev: r[5] === null ? null : Math.round(r[3] / (1 + r[5] / 100)),
    lat: lat + j * .012, lng: lng + k * .016, vsMedian: (r[3] / MEDIAN - 1) * 100,
  };
});
const signals = [
  { level: 'Atención', title: 'Movimiento competitivo', text: '17 hoteles cambiaron precio: 13 subidas y 4 bajadas.', value: '+0,5 %', hotel: null },
  { level: 'Atención', title: 'Precio agresivo', text: 'Relaxia Beverly Park está un 15,2 % por debajo de la media del set.', value: '245 €', hotel: 'Relaxia Beverly Park' },
  { level: 'Atención', title: 'Protege tu tarifa', text: 'Gloria Palace San Agustín ha bajado un 11,1 %.', value: '267 €', hotel: 'Gloria Palace San Agustín Thalasso & Hotel' },
  { level: 'Lectura', title: 'Hoteles desaparecidos', text: 'Princess Taurito, Gran Canaria Princess y Maspalomas Resort ya no aparecen. Posible sold-out.', value: '3', hotel: null },
  { level: 'Lectura', title: 'Líder de precio', text: 'Seaside Palm Beach está un 130,8 % por encima de la media.', value: '667 €', hotel: 'Seaside Palm Beach' },
  { level: 'Lectura', title: 'Nuevos competidores', text: 'Riu Vistamar y LIVVO Valle Taurito entran en el set.', value: '2', hotel: null },
];
const captures = [
  { n: 1, d: '11/08', adr: 282 }, { n: 2, d: '11/08', adr: 274 }, { n: 3, d: '11/08', adr: 272 }, { n: 4, d: '11/08', adr: 266 },
  { n: 5, d: '11/08', adr: 288 }, { n: 6, d: '11/08', adr: 288 }, { n: 13, d: '23/08', adr: 289 }, { n: 14, d: '23/08', adr: 281 },
  { n: 15, d: '23/08', adr: 285 }, { n: 16, d: '23/08', adr: 269 }, { n: 17, d: '23/08', adr: 290 }, { n: 18, d: '23/08', adr: 289 },
];
const routes = [
  ['ZRH','Zúrich',710,710],['MUC','Múnich',362,362],['LIS','Lisboa',352,352],['CPH','Copenhague',210,264],['BRU','Bruselas',296,296],
  ['ARN','Estocolmo',240,301],['AMS','Ámsterdam',175,239],['FRA','Fráncfort',206,206],['DUS','Düsseldorf',160,198],['LGW','Londres',145,188],
  ['BCN','Barcelona',110,146],['MAD','Madrid',98,132],['DUB','Dublín',50,111],
].map(([code, city, min, avg]) => ({ code, city, min, avg }));
const flights = [
  ['06/10','MAD','Iberia','IB3942','07:25','09:10','2h 45m',0,98],['06/10','BCN','Vueling','VY3004','08:05','10:20','3h 15m',0,110],
  ['06/10','LGW','easyJet','U28035','06:40','10:55','4h 15m',0,145],['06/10','AMS','Transavia','HV6721','09:30','13:50','4h 20m',0,175],
  ['06/10','DUB','Ryanair','FR7072','06:15','10:35','4h 20m',0,50],['07/10','FRA','Condor','DE1520','10:05','13:55','4h 50m',0,206],
  ['07/10','MUC','Lufthansa','LH1784','11:40','15:35','4h 55m',0,362],['07/10','ZRH','Edelweiss','WK364','08:50','12:40','4h 50m',0,710],
  ['07/10','CPH','Norwegian','D83604','12:10','17:05','5h 55m',0,210],['07/10','BRU','Brussels Airlines','SN3791','09:15','13:20','5h 05m',0,296],
  ['08/10','LIS','TAP','TP1470','14:35','16:10','2h 35m',0,352],['08/10','ARN','SAS','SK1817','07:00','12:35','6h 35m',0,240],
  ['08/10','DUS','Eurowings','EW9580','06:55','11:05','5h 10m',0,160],['08/10','MAD','Air Europa','UX9112','16:20','18:05','2h 45m',0,121],
].map(([date, from, airline, code, dep, arr, dur, stops, price]) => {
  const r = routes.find(x => x.code === from);
  const pos = r.avg === r.min ? .5 : Math.max(0, Math.min(1, (price - r.min) / ((r.avg - r.min) * 2)));
  return { date, from, city: r.city, airline, code, dep, arr, dur, stops, price, pos };
});
const inventory = [
  ['Abora Buenaventura by Lopesan Hotels','Gánigo 6, Plaza de Ansite'],['Abora Catarina by Lopesan Hotels','Avenida de Tirajana, 1'],
  ['Abora Continental by Lopesan Hotels','Avenida de Italia, 2'],['Abora Interclub Atlantic by Lopesan Hotels','Los Jazmines, 2'],
  ['Barceló Margaritas','Avenida Gran Canaria, 38-40'],['Barceló Margaritas Royal Level Adults Only','40 Avenida de Gran Canaria, Playa del Inglés'],
  ['BLUESEA Marieta','Avenida de Italia, 11'],['BLUESEA Rey Carlos','Avenida de Tirajana, 14'],
  ['Bungalows Maspalomas Oasis Club','Avenida de Gran Canaria, 58'],['Cordial Mogán Playa','Avenida de los Marrero, 2, Mogán'],
  ['Corallium Beach by Lopesan Hotels - Adults Only','Mar Mediterráneo, 1, Meloneras'],['Corallium Dunamar by Lopesan Hotels - Adults Only','Avenida de Italia, 6'],
  ['Don Gregory by Dunas - Adults Only','Calle Las Retamas, 11, San Agustín'],['Gloria Palace Royal Hotel & Spa','Calle Tamarán, 1, Amadores'],
  ['Gloria Palace San Agustín Thalasso & Hotel','Calle Las Margaritas, San Agustín'],['H10 Costa Mogán - Adults Only','Avenida de las Artes, 3, Mogán'],
  ['H10 Playa Meloneras Horizons Collection','Mar Mediterráneo, 7, Meloneras'],['HD Parque Cristobal Gran Canaria','Avenida de Tirajana, 23'],
].map(([name, addr], i) => ({ id: 'r' + i, name, addr, google: 0, booking: 0, maps: i % 5 === 2 ? 'Verificado' : 'Por revisar', lastMaps: null, lastBooking: null }));

window.AtlasData = { MEDIAN, hotels, signals, captures, routes, flights, inventory };
})();

(function(){
const D = window.AtlasData;
const rnd = n => { const x = Math.sin(n * 12.9898 + 78.233) * 43758.5453; return x - Math.floor(x); };
const beach = ['50 m','120 m','250 m','400 m','700 m','1,1 km','1,6 km'];
const ROOMS = ['Habitación Doble Superior','Junior Suite','Suite vista mar','Habitación Familiar','Bungalow 1 dormitorio','Doble vista piscina'];
const checkins = ['06/10','07/10','08/10','09/10','10/10','11/10','12/10','13/10'];
D.hotels.forEach((h, i) => {
  const r = k => rnd(i * 31 + k);
  h.genius = r(1) > .42; h.geniusLevel = h.genius ? (r(2) > .5 ? 'Genius nivel 2' : 'Genius nivel 1') : null;
  h.beach = beach[Math.floor(r(3) * beach.length)];
  // price history across 12 captures
  h.history = D.captures.map((c, k) => {
    if (h.isNew && k < 11) return null;
    if (k === 11) return h.adr; if (k === 10 && h.prev) return h.prev;
    return Math.round(h.adr * (c.adr / 285) * (0.955 + r(10 + k) * .09));
  });
  // by check-in date: previous vs current sweep
  h.byDate = checkins.map((d, k) => { const cur = Math.round(h.adr * (0.93 + r(40 + k) * .16)); const prev = h.isNew ? null : Math.round(cur / (1 + (h.delta || 0) / 100) * (0.97 + r(60 + k) * .06)); return { d, cur, prev }; });
  // room types & rates
  const nTypes = 2 + Math.floor(r(4) * 3);
  const pool = [h.room, ...ROOMS.filter(x => x !== h.room)];
  h.rooms = pool.slice(0, nTypes).map((name, t) => {
    const occ = [2, 2, 3, 4, 4, 3][t];
    const base = h.adr * (1 + t * (0.14 + r(70 + t) * .1));
    const nRates = 1 + Math.floor(r(80 + t) * 3);
    const rates = [
      { board: 'Todo incluido', cancel: true, cancelText: 'Gratis hasta 3 días antes', pay: 'Sin pago por adelantado', f: 1 },
      { board: 'Todo incluido', cancel: false, cancelText: 'No reembolsable', pay: 'Pago por adelantado', f: .9 },
      { board: 'Todo incluido Premium', cancel: true, cancelText: 'Gratis hasta 7 días antes', pay: 'Pago en el alojamiento', f: 1.18 },
    ].slice(0, nRates).map((rt, q) => {
      const adr = Math.round((t === 0 && q === 0) ? h.adr : base * rt.f);
      const prog = h.genius && r(90 + t * 3 + q) > .35 ? h.geniusLevel : (r(95 + t + q) > .78 ? 'Oferta de temporada' : null);
      const disc = prog ? (prog.includes('2') ? 15 : prog.includes('1') ? 10 : 12) : 0;
      const units = t === 0 && q === 0 && h.avail ? parseInt(h.avail.replace(/\D/g, '')) : (r(100 + t * 5 + q) > .6 ? 1 + Math.floor(r(110 + t + q) * 5) : null);
      return { board: rt.board, maxOcc: occ, cancel: rt.cancel, cancelText: rt.cancelText, pay: rt.pay, units, program: prog, discount: disc, total: adr * 7, original: disc ? Math.round(adr * 7 / (1 - disc / 100)) : null, adr };
    });
    return { name, maxOcc: occ, rates };
  });
});
// ---- air
const AP = {
  ZRH: ['Zúrich', 'Suiza', 'Suiza', 47.458, 8.555], MUC: ['Múnich', 'Alemania', 'Alemania', 48.354, 11.786], LIS: ['Lisboa Humberto Delgado', 'Portugal', 'Portugal', 38.774, -9.134],
  CPH: ['Copenhague Kastrup', 'Nórdicos', 'Dinamarca', 55.618, 12.656], BRU: ['Bruselas Zaventem', 'Benelux', 'Bélgica', 50.901, 4.484], ARN: ['Estocolmo Arlanda', 'Nórdicos', 'Suecia', 59.652, 17.919],
  AMS: ['Ámsterdam Schiphol', 'Benelux', 'Países Bajos', 52.310, 4.768], FRA: ['Fráncfort', 'Alemania', 'Alemania', 50.037, 8.562], DUS: ['Düsseldorf', 'Alemania', 'Alemania', 51.289, 6.767],
  LGW: ['Londres Gatwick', 'Reino Unido', 'Reino Unido', 51.148, -0.190], BCN: ['Barcelona-El Prat', 'España', 'España', 41.297, 2.078], MAD: ['Madrid-Barajas', 'España', 'España', 40.472, -3.561],
  DUB: ['Dublín', 'Irlanda', 'Irlanda', 53.421, -6.270],
};
D.LPA = [27.932, -15.387];
const AL = {
  MAD: [['Iberia', 'IB', 'A320neo', 1], ['Air Europa', 'UX', 'Boeing 737-800', .96], ['Binter', 'NT', 'Embraer E195-E2', 1.08]],
  BCN: [['Vueling', 'VY', 'A320', 1], ['Binter', 'NT', 'Embraer E195-E2', 1.12]],
  LGW: [['easyJet', 'U2', 'A320neo', 1], ['British Airways', 'BA', 'A320', 1.22], ['TUI Airways', 'BY', 'Boeing 737 MAX 8', 1.1]],
  AMS: [['Transavia', 'HV', 'Boeing 737-800', 1], ['KLM', 'KL', 'Boeing 737-900', 1.18]],
  DUB: [['Ryanair', 'FR', 'Boeing 737-8200', 1], ['Aer Lingus', 'EI', 'A320neo', 1.35]],
  FRA: [['Condor', 'DE', 'A321neo', 1], ['Discover', '4Y', 'A320', 1.07]],
  MUC: [['Lufthansa', 'LH', 'A320neo', 1], ['Condor', 'DE', 'A321', .93]],
  ZRH: [['Edelweiss', 'WK', 'A320', 1], ['Swiss', 'LX', 'A220-300', 1.06]],
  CPH: [['Norwegian', 'D8', 'Boeing 737 MAX 8', 1], ['SAS', 'SK', 'A320neo', 1.14, 'MAD']],
  BRU: [['Brussels Airlines', 'SN', 'A320', 1], ['TUI fly Belgium', 'TB', 'Boeing 737-800', .94]],
  ARN: [['Norwegian', 'DY', 'Boeing 737 MAX 8', 1], ['SAS', 'SK', 'A320neo', 1.1, 'MAD']],
  DUS: [['Eurowings', 'EW', 'A320', 1], ['Condor', 'DE', 'A321neo', 1.04, 'PMI']],
  LIS: [['TAP Air Portugal', 'TP', 'A320neo', 1], ['Binter', 'NT', 'ATR 72-600', 1.05]],
};
const DUR = { MAD: 165, BCN: 195, LGW: 255, AMS: 260, DUB: 260, FRA: 290, MUC: 295, ZRH: 290, CPH: 355, BRU: 305, ARN: 395, DUS: 310, LIS: 155 };
const dates = []; const base = new Date(2026, 7, 24);
for (let k = 0; k < 14; k++) dates.push(k + 1);
for (let k = 1; dates.length < 25; k++) dates.push(14 + k * 7);
const fmtD = n => { const d = new Date(2026, 7, 23 + n); return String(d.getDate()).padStart(2, '0') + '/' + String(d.getMonth() + 1).padStart(2, '0'); };
const hm = m => String(Math.floor(m / 60) % 24).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0');
const lead = n => n <= 14 ? 1.14 : n <= 30 ? 1.02 : n <= 60 ? .92 : .97;
const out = []; let seq = 0;
D.routes.forEach((rt, ri) => {
  const a = AP[rt.code]; Object.assign(rt, { airport: a[0], segment: a[1], country: a[2], lat: a[3], lng: a[4] });
  (AL[rt.code] || []).forEach((al, ai) => {
    dates.forEach((dn, di) => {
      if (rnd(ri * 97 + ai * 13 + di) < .12) return;
      const via = al[4] || null;
      const p = Math.max(Math.round(rt.min * .86), Math.round(rt.avg * al[3] * lead(dn) * (0.84 + rnd(ri * 7 + ai * 3 + di * 11) * .3)));
      const dep = 360 + Math.floor(rnd(ri + ai * 5 + di) * 14) * 50;
      const dur = DUR[rt.code] + (via ? 110 + Math.floor(rnd(ri * 3 + di) * 60) : 0) + Math.floor(rnd(di + ai) * 3) * 5;
      const fn = al[1] + (1000 + Math.floor(rnd(ri * 11 + ai) * 8000));
      out.push({ id: 'f' + (seq++), from: rt.code, city: rt.city, airport: a[0], segment: a[1], country: a[2], to: 'LPA', dateN: dn, date: fmtD(dn), days: dn,
        airline: al[0], iata: al[1], code: via ? fn + ' · ' + al[1] + (1000 + Math.floor(rnd(ai * 17 + ri) * 8000)) : fn, aircraft: al[2], cls: 'Turista',
        dep: hm(dep), arr: hm(dep + dur - (['LGW','DUB','LIS'].includes(rt.code) ? 0 : 60)), durMin: dur, direct: !via, via, price: p, ret: 'Solo ida', captured: '23/08/2026 14:41' });
    });
  });
  const fs = out.filter(f => f.from === rt.code);
  const ps = fs.map(f => f.price).sort((x, y) => x - y);
  rt.options = fs.length; rt.minP = ps[0]; rt.avgP = Math.round(ps.reduce((x, y) => x + y, 0) / ps.length); rt.maxP = ps[ps.length - 1];
  rt.airlines = [...new Set(fs.map(f => f.airline))]; rt.directPct = Math.round(fs.filter(f => f.direct).length / fs.length * 100);
  rt.durAvg = Math.round(fs.reduce((x, f) => x + f.durMin, 0) / fs.length);
  rt.delta = Math.round((rnd(ri * 5 + 3) - .55) * 80) / 10;
});
out.forEach(f => { const rt = D.routes.find(r => r.code === f.from); f.aai = Math.round(f.price / rt.avgP * 100) / 100; f.pos = Math.max(0, Math.min(1, (f.price - rt.minP) / Math.max(1, rt.maxP - rt.minP))); });
D.flightsAll = out; D.airDates = dates.map(fmtD); D.airDatesN = dates;
})();
