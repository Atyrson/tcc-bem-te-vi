// Classifica os dez casos fictícios da ASIA com o algoritmo do Praxis Spinal Cord
// Institute (pacote npm isncsci, versão fixada em package.json) e compara com o
// resultado esperado obtido à mão e com o servidor do aplicativo.
//
// Uso, em entregas/praxis/:
//   npm install
//   python -X utf8 exportar_casos_asia.py
//   node conferir_praxis.mjs
//
// O algoritmo é distribuído sob a Licença Apache 2.0 pelo Praxis Spinal Cord
// Institute (https://github.com/praxis-isncsci/algorithm).
import { readFileSync } from 'node:fs';
import { ISNCSCI } from 'isncsci';

const casos = JSON.parse(readFileSync(new URL('./casos_asia.json', import.meta.url), 'utf8'));

const fmt = (v) => (Array.isArray(v) ? v.join(' | ') : String(v));

function praxis(exame) {
  const r = new ISNCSCI(exame);
  const c = r.classification;
  return {
    sens: [c.neurologicalLevels.sensoryRight, c.neurologicalLevels.sensoryLeft],
    motor: [c.neurologicalLevels.motorRight, c.neurologicalLevels.motorLeft],
    nli: c.neurologicalLevelOfInjury,
    ais: c.ASIAImpairmentScale ?? c.asiaImpairmentScale,
    zpp_s: [c.zoneOfPartialPreservations.sensoryRight, c.zoneOfPartialPreservations.sensoryLeft],
    zpp_m: [c.zoneOfPartialPreservations.motorRight, c.zoneOfPartialPreservations.motorLeft],
    _bruto: c,
  };
}

const ROTULOS = [
  ['sens', 'Nível sensitivo (D, E)'],
  ['motor', 'Nível motor (D, E)'],
  ['nli', 'Nível neurológico'],
  ['ais', 'Grau AIS'],
  ['zpp_s', 'ZPP sensitiva (D, E)'],
  ['zpp_m', 'ZPP motora (D, E)'],
];

const resumo = [];
for (const caso of casos) {
  console.log(`\n## ${caso.titulo}`);
  const p = praxis(caso.exame);
  for (const [k, rotulo] of ROTULOS) {
    const esp = fmt(caso.esperado[k]);
    const prx = fmt(p[k]);
    const srv = caso.servidor.erro ? `erro (${caso.servidor.erro})` : fmt(caso.servidor[k]);
    const marcaEsp = esp === prx ? 'esperado=Praxis' : 'esperado≠Praxis';
    const marcaSrv = srv === prx ? 'servidor=Praxis' : 'servidor≠Praxis';
    console.log(`- ${rotulo.padEnd(24)} esperado ${esp.padEnd(12)} Praxis ${prx.padEnd(14)} servidor ${srv.padEnd(14)} ${marcaEsp}; ${marcaSrv}`);
  }
  resumo.push([caso.titulo.split('.')[0], fmt(caso.esperado.ais), fmt(p.ais),
    caso.servidor.erro ? 'erro' : fmt(caso.servidor.ais)]);
}

console.log('\n## Resumo do grau AIS (caso: esperado / Praxis / servidor)');
for (const [n, e, p, s] of resumo) console.log(`- ${n.padStart(2)}: ${e} / ${p} / ${s}`);
