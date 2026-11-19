"""Gera as instâncias FHIR de teste do caminho crítico (17/11/2026).

Uso, na raiz do repositório do TCC:

    python entregas/scripts/gerar_fhir_teste.py

Escreve em entregas/fhir/teste/:
- Patient-paciente-ficticio.json: paciente fictício no perfil de paciente do BR-Core;
- Questionnaire-cif-esqueleto.json: esqueleto do questionário da CIF, com o grupo
  do b167 (exemplo condutor) e um item exclusivo do sexo feminino (enableWhen);
- QuestionnaireResponse-cif-esqueleto.json: respostas fictícias do b167, as mesmas
  da Figura do exemplo condutor na Seção 4.2, com os valores do calculador do app.

Os textos e as células vêm do catálogo do app (submódulo app/, commit fixado).
O endereço canônico dos artefatos próprios (BASE) é provisório.
"""
import json
from decimal import Decimal
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'app' / 'scripts' / 'cif'))
from calculador import CalculadorCIF, EntradaCIF  # noqa: E402

BASE = 'https://bemtevi.unb.br/fhir'
SAIDA = RAIZ / 'entregas' / 'fhir' / 'teste'
SDC_CALC = 'http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-calculatedExpression'
SEXO = 'http://hl7.org/fhir/administrative-gender'

# Grupo do b167: célula calculada -> células usadas na média, já com a decisão 1 da
# auditoria (E119 entra uma vez só em E105). Ordem = ordem do formulário.
MEDIAS = {
    'E105': ['E106', 'E112', 'E118', 'E119'],
    'E106': ['E107', 'E108', 'E109', 'E110'],
    'E112': ['E113', 'E114', 'E115', 'E116'],
}
ORDEM = ['E105', 'E106', 'E107', 'E108', 'E109', 'E110', 'E112', 'E113', 'E114', 'E115', 'E116', 'E118', 'E119']
# Notas fictícias da Figura do exemplo condutor (Seção 4.2).
NOTAS = {'E107': 1, 'E108': 2, 'E109': 3, 'E110': 4, 'E113': 0, 'E114': 1, 'E115': 1, 'E116': 2,
         'E118': 3, 'E119': 4}


def narrativa(texto):
    return {'status': 'generated', 'div': f'<div xmlns="http://www.w3.org/1999/xhtml"><p>{texto}</p></div>'}


def expressao_media(celulas):
    ids = ' | '.join(f"'b:{c}'" for c in celulas)
    respostas = f"%resource.repeat(item).where(linkId in ({ids})).answer.value"
    return f"iif({respostas}.count() = {len(celulas)}, {respostas}.aggregate($total + $this, 0) / {len(celulas)}, {{}})"


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    catalogo = json.loads((RAIZ / 'app' / 'catalogos' / 'cif' / 'catalogo.v0.1.json').read_text(encoding='utf-8'))
    area_b = next(a for a in catalogo['areas'] if a['code'] == 'b')
    por_celula = {f['value_cell']: n for n in area_b['nodes'] for f in n['fields']}
    por_codigo = {n['code']: n for n in area_b['nodes']}

    calc = CalculadorCIF()
    masc = {c.chave for c in calc.campos_entrada_obrigatorios('Masculino')}
    fem = [c for c in calc.campos_entrada_obrigatorios('Feminino') if c.chave not in masc]
    exclusivo = fem[0]  # primeiro item só do formulário feminino

    paciente = {
        'resourceType': 'Patient',
        'id': 'paciente-ficticio',
        'meta': {'profile': ['https://br-core.saude.gov.br/fhir/StructureDefinition/br-core-patient']},
        'text': narrativa('Paciente fictício, criado só para testar o modelo.'),
        'identifier': [{
            'use': 'official',
            'type': {'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/v2-0203', 'code': 'TAX'}]},
            'system': 'https://saude.gov.br/fhir/sid/cpf',
            'value': '12345678909',
        }],
        'name': [{'use': 'official', 'text': 'Paciente Fictício', 'family': 'Fictício', 'given': ['Paciente']}],
        'gender': 'male',
        'birthDate': '1990-05-10',
    }

    def item(celula):
        no = por_celula[celula]
        base = {'linkId': f'b:{celula}', 'text': f"{no['code']} {no['description']}"}
        if celula in MEDIAS:
            return {**base, 'type': 'decimal', 'readOnly': True,
                    'extension': [{'url': SDC_CALC, 'valueExpression': {
                        'language': 'text/fhirpath', 'expression': expressao_media(MEDIAS[celula])}}]}
        return {**base, 'type': 'integer', 'required': True, 'extension': [
            {'url': 'http://hl7.org/fhir/StructureDefinition/minValue', 'valueInteger': 0},
            {'url': 'http://hl7.org/fhir/StructureDefinition/maxValue', 'valueInteger': 4}]}

    no_exclusivo = por_codigo[exclusivo.codigo]
    questionario = {
        'resourceType': 'Questionnaire',
        'id': 'cif-esqueleto',
        'text': narrativa('Esqueleto do questionário da CIF adaptada: grupo do b167 e um item exclusivo do sexo feminino.'),
        'url': f'{BASE}/Questionnaire/cif-esqueleto',
        'version': '0.1.0',
        'name': 'CIFEsqueleto',
        'title': 'Avaliação CIF adaptada (esqueleto de teste)',
        'status': 'draft',
        'subjectType': ['Patient'],
        'item': [
            {'linkId': 'sexo', 'text': 'Sexo do paciente', 'type': 'choice', 'required': True,
             'answerOption': [{'valueCoding': {'system': SEXO, 'code': 'male'}},
                              {'valueCoding': {'system': SEXO, 'code': 'female'}}]},
            {'linkId': 'b', 'text': area_b['name'], 'type': 'group', 'item': [
                {'linkId': 'b1', 'text': f"b1 {por_codigo['b1']['description']}", 'type': 'group',
                 'item': [item(c) for c in ORDEM]},
                {'linkId': 'b6', 'text': f"b6 {por_codigo['b6']['description']}", 'type': 'group', 'item': [
                    {'linkId': exclusivo.chave, 'text': f"{no_exclusivo['code']} {no_exclusivo['description']}",
                     'type': 'integer', 'required': True,
                     'enableWhen': [{'question': 'sexo', 'operator': '=',
                                     'answerCoding': {'system': SEXO, 'code': 'female'}}],
                     'extension': [
                         {'url': 'http://hl7.org/fhir/StructureDefinition/minValue', 'valueInteger': 0},
                         {'url': 'http://hl7.org/fhir/StructureDefinition/maxValue', 'valueInteger': 4}]}]},
            ]},
        ],
    }

    # Valores calculados: os do calculador do app, com as notas fictícias no b167 e 0 no resto.
    respostas = {k: 0 for k in masc}
    respostas.update({f'b:{c}': v for c, v in NOTAS.items()})
    resultado = calc.calcular(EntradaCIF(sexo='Masculino', respostas=respostas))
    calculados = {c: Decimal(str(resultado.intermediarios[f'b:{c}'].valor_interno)) for c in MEDIAS}

    def resposta(celula):
        if celula in calculados:
            return {'linkId': f'b:{celula}', 'answer': [{'valueDecimal': float(calculados[celula])}]}
        return {'linkId': f'b:{celula}', 'answer': [{'valueInteger': NOTAS[celula]}]}

    resposta_q = {
        'resourceType': 'QuestionnaireResponse',
        'id': 'cif-esqueleto-exemplo',
        'text': narrativa('Respostas fictícias do grupo do b167 (exemplo condutor).'),
        'questionnaire': f"{questionario['url']}|{questionario['version']}",
        'status': 'completed',
        'subject': {'reference': 'Patient/paciente-ficticio'},
        'authored': '2026-11-17',
        'item': [
            {'linkId': 'sexo', 'answer': [{'valueCoding': {'system': SEXO, 'code': 'male'}}]},
            {'linkId': 'b', 'item': [{'linkId': 'b1', 'item': [resposta(c) for c in ORDEM]}]},
        ],
    }

    SAIDA.mkdir(parents=True, exist_ok=True)
    for recurso, nome in ((paciente, 'Patient-paciente-ficticio.json'),
                          (questionario, 'Questionnaire-cif-esqueleto.json'),
                          (resposta_q, 'QuestionnaireResponse-cif-esqueleto.json')):
        (SAIDA / nome).write_text(json.dumps(recurso, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'- {nome}')
    print('Valores calculados (calculador do app):', {c: str(v) for c, v in calculados.items()})
    print(f'Item exclusivo do feminino: {exclusivo.chave} ({exclusivo.codigo})')


if __name__ == '__main__':
    main()
