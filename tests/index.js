// Punto de entrada para `node --test tests/`: Node resuelve el directorio a este archivo,
// que carga cada suite. `node --test` sin argumentos sigue encontrando los *.test.cjs por sí solo.
const fs = require('node:fs');
const path = require('node:path');

fs.readdirSync(__dirname)
  .filter((name) => name.endsWith('.test.cjs'))
  .sort()
  .forEach((name) => require(path.join(__dirname, name)));
