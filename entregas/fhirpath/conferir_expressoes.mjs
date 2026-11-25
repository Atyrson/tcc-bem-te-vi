// Executa as expressões de cálculo (sdc-questionnaire-calculatedExpression) do
// Questionnaire da CIF com o fhirpath.js e compara com o calculador do app.
//
// Uso, na raiz do repositório do TCC (depois de gerar os casos):
//
//     python entregas/scripts/gerar_fhir_cif.py
//     cd entregas/fhirpath; npm install; node conferir_expressoes.mjs > resultado_expressoes.txt
//
// Para cada caso de casos.json, o script parte da resposta só com as entradas e
// avalia todas as expressões dos itens habilitados, repetindo até nenhum valor
// mudar (como um preenchedor do SDC faz). Depois compara cada valor com o do
// calculador: o valor interno, com tolerância de 1e-9, e o valor exibido, com
// duas casas. Um item sem valor deve corresponder a um item pendente no calculador.
import { readFileSync } from 'node:fs';
import fhirpath from 'fhirpath';
import r4 from 'fhirpath/fhir-context/r4/index.js';

const raiz = new URL('../../', import.meta.url);
const questionario = JSON.parse(readFileSync(new URL('entregas/fhir/cif/Questionnaire-cif.json', raiz), 'utf8'));
const casos = JSON.parse(readFileSync(new URL('entregas/fhirpath/casos.json', raiz), 'utf8'));
const URL_CALC = 'http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-calculatedExpression';

const expressoes = new Map();
(function coletar(itens) {
  for (const it of itens ?? []) {
    const ext = (it.extension ?? []).find((e) => e.url === URL_CALC);
    if (ext) expressoes.set(it.linkId, fhirpath.compile(ext.valueExpression.expression, r4));
    coletar(it.item);
  }
})(questionario.item);

function itensSemResposta(itens, saida = new Map()) {
  for (const it of itens ?? []) {
    if (expressoes.has(it.linkId)) saida.set(it.linkId, it);
    itensSemResposta(it.item, saida);
  }
  return saida;
}

const arred = (x) => Math.round((x + Number.EPSILON) * 100) / 100;
const executadas = new Set();
let falhas = 0;
console.log(`fhirpath.js ${fhirpath.version}; expressões no Questionnaire: ${expressoes.size}`);

for (const caso of casos) {
  const qr = caso.resposta;
  const alvos = itensSemResposta(qr.item);
  let passadas = 0;
  for (let mudou = true; mudou; passadas++) {
    mudou = false;
    for (const [linkId, item] of alvos) {
      const r = expressoes.get(linkId)(qr, { resource: qr });
      const novo = r.length ? r[0] : undefined;
      const atual = item.answer?.[0]?.valueDecimal;
      if (novo !== atual) {
        if (novo === undefined) delete item.answer; else item.answer = [{ valueDecimal: novo }];
        mudou = true;
      }
    }
  }
  let ok = 0;
  const erros = [];
  for (const [linkId, item] of alvos) {
    executadas.add(linkId);
    const obtido = item.answer?.[0]?.valueDecimal ?? null;
    const esp = caso.esperado[linkId];
    if (!esp) { erros.push(`${linkId}: item habilitado que o calculador não calcula`); continue; }
    const igual = obtido === null
      ? esp.interno === null
      : esp.interno !== null && Math.abs(obtido - esp.interno) <= 1e-9 && arred(obtido) === esp.exibido;
    if (igual) ok++; else erros.push(`${linkId}: FHIRPath ${obtido}, calculador ${esp.interno} (exibido ${esp.exibido})`);
  }
  for (const k of Object.keys(caso.esperado)) if (!alvos.has(k)) erros.push(`${k}: calculado pelo app, sem item habilitado`);
  const pendentes = [...alvos.values()].filter((i) => !i.answer).length;
  falhas += erros.length;
  console.log(`\n## ${caso.nome}`);
  console.log(`- Expressões executadas: ${alvos.size}; iguais ao calculador: ${ok}; divergentes: ${erros.length}`);
  console.log(`- Itens sem valor (pendentes): ${pendentes}; avaliação definitiva no calculador: ${caso.definitivo ? 'sim' : 'não'}`);
  console.log(`- Passadas até estabilizar: ${passadas}`);
  for (const e of erros) console.log(`  - ${e}`);
}

console.log(`\n## Total`);
console.log(`- Expressões distintas executadas em pelo menos um caso: ${executadas.size} de ${expressoes.size}`);
console.log(`- Divergências: ${falhas}`);
process.exit(falhas ? 1 : 0);
