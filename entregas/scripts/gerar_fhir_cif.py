"""Gera os artefatos FHIR da CIF a partir do catálogo e do calculador do app.

Uso, na raiz do repositório do TCC:

    python entregas/scripts/gerar_fhir_cif.py

Escreve em entregas/fhir/cif/ (artefatos validados pelo validar_fhir.ps1):
- CodeSystem-cif-catalogo.json: os códigos do catálogo (catalogo.v0.1.json), com o pai
  de cada código e as pendências de códigos repetidos na planilha;
- Questionnaire-cif.json: o formulário completo, com as entradas e os campos calculados
  alcançáveis pelo calculador nos dois sexos. As entradas são inteiras de 0 a 4. Os campos
  calculados têm a média como expressão de cálculo do SDC. O sexo vem do cadastro
  (Patient.gender, por initialExpression do SDC) e controla a variação por enableWhen; a data
  da avaliação é um item obrigatório, como a data_avaliacao da tabela avaliacoes_cif;
- Patient-paciente-ficticio.json e Practitioner-avaliador-ficticio.json (BR-Core);
- QuestionnaireResponse-cif-exemplo.json: o exemplo condutor da Seção 4.2 (paciente
  masculino, notas do b167 da Figura e 0 nos demais itens), com os valores calculados
  pelo calculador do app;
- Observation-cif-exemplo-*.json: uma Observation por capítulo e uma por área, com o valor
  exibido pelo calculador; a da área agrupa as dos capítulos com hasMember.

Escreve também entregas/fhirpath/casos.json, usado por conferir_expressoes.mjs para
executar as expressões de cálculo e comparar com o calculador (fora de entregas/fhir/,
porque não é artefato do modelo).

Os textos e as células vêm do catálogo do app (submódulo app/, commit fixado). O endereço
canônico dos artefatos próprios (BASE) é provisório.
"""
from collections import Counter, OrderedDict
import json
from pathlib import Path
import random
import sys

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'app' / 'scripts' / 'cif'))
from calculador import CalculadorCIF, EntradaCIF  # noqa: E402

BASE = 'https://bemtevi.unb.br/fhir'
VERSAO = '0.1.0'
DATA = '2026-11-22'
SAIDA = RAIZ / 'entregas' / 'fhir' / 'cif'
CASOS = RAIZ / 'entregas' / 'fhirpath' / 'casos.json'

CS_URL = f'{BASE}/CodeSystem/cif-catalogo'
SEXO = 'http://hl7.org/fhir/administrative-gender'
SDC = 'http://hl7.org/fhir/uv/sdc/StructureDefinition/'
MIN = 'http://hl7.org/fhir/StructureDefinition/minValue'
MAX = 'http://hl7.org/fhir/StructureDefinition/maxValue'
BR_CORE = 'https://br-core.saude.gov.br/fhir/StructureDefinition/'
SEXO_APP = {'Masculino': 'male', 'Feminino': 'female'}
ROTULO_SEXO = {'Masculino': 'formulário masculino', 'Feminino': 'formulário feminino'}

# Notas fictícias do b167 na Figura do exemplo condutor (Seção 4.2); demais itens com 0.
NOTAS_B167 = {'b:E107': 1, 'b:E108': 2, 'b:E109': 3, 'b:E110': 4, 'b:E113': 0, 'b:E114': 1,
              'b:E115': 1, 'b:E116': 2, 'b:E118': 3, 'b:E119': 4}


def narrativa(texto):
    return {'status': 'generated', 'div': f'<div xmlns="http://www.w3.org/1999/xhtml"><p>{texto}</p></div>'}


def cpf_valido(base9):
    """Completa os dois dígitos verificadores de um CPF fictício."""
    d = [int(c) for c in base9]
    for peso in (10, 11):
        resto = sum(x * (peso - i) for i, x in enumerate(d)) * 10 % 11
        d.append(0 if resto == 10 else resto)
    return ''.join(map(str, d))


def expressao_media(area, referencias):
    """Média das respostas referenciadas, termo a termo (preserva referências repetidas).

    Em FHIRPath, a soma com um operando vazio é vazia; por isso, se faltar alguma
    resposta, o resultado fica vazio, como a pendência do calculador.
    """
    termos = [f"%resource.repeat(item).where(linkId = '{area}:{r}').answer.value" for r in referencias]
    return f"({' + '.join(termos)}) / {len(referencias)}"


class Modelo:
    def __init__(self):
        self.calc = CalculadorCIF()
        self.catalogo = self.calc.catalogo
        self.alcance = {s: self.calc._caminho_referenciado(s)[0] for s in SEXO_APP}
        self.campos = OrderedDict()  # chave -> _Campo, na ordem das linhas da planilha
        uniao = set(self.alcance['Masculino']) | set(self.alcance['Feminino'])
        for chave, campo in sorted(self.calc._campos.items(),
                                   key=lambda kv: (self.calc.areas.index(kv[1].area), kv[1].linha, kv[1].celula)):
            if chave in uniao:
                self.campos[chave] = campo
        self.fora = [k for k, c in self.calc._campos.items() if c.formula is not None and k not in uniao]
        self.capitulo_do_no = {(a['code'], n['source_row']): n['chapter']
                               for a in self.catalogo['areas'] for n in a['nodes']}

    def sexos(self, chave):
        return [s for s in SEXO_APP if chave in self.alcance[s]]


def gerar_codesystem(m):
    conceitos = OrderedDict()
    ocorrencias = {}
    for area in m.catalogo['areas']:
        for no in area['nodes']:
            codigo = m.calc._codigo_canonico(area['code'], no)
            ocorrencias.setdefault(codigo, []).append(no)
    for codigo, nos in ocorrencias.items():
        no = nos[0]
        conceito = {'code': codigo, 'display': no['description']}
        props = []
        if no['parent_by_code']:
            props.append({'code': 'parent', 'valueCode': no['parent_by_code']})
        if len(nos) > 1:
            linhas = ' e '.join(str(n['source_row']) for n in nos)
            descricoes = {n['description'] for n in nos}
            props.append({'code': 'pendencia', 'valueString':
                          f'Código repetido na planilha (linhas {linhas}, '
                          f"{'mesma descrição' if len(descricoes) == 1 else 'descrições diferentes'}). "
                          'O display é o da primeira linha; a decisão é da equipe de fisioterapia.'})
        if codigo != no['code']:
            props.append({'code': 'pendencia', 'valueString':
                          f"Na planilha, a linha {no['source_row']} traz o código {no['code']}; o título da "
                          f'linha é o de {codigo}, que é o código usado pelo calculador do app.'})
        if props:
            conceito['property'] = props
        conceitos[codigo] = conceito
    return {
        'resourceType': 'CodeSystem',
        'id': 'cif-catalogo',
        'text': narrativa('Códigos e descrições da CIF como estão no catálogo do aplicativo Bem-Te-Vi '
                          f"(catalogo.v0.1.json, versão {m.catalogo['catalog_version']})."),
        'url': CS_URL,
        'version': VERSAO,
        'name': 'CIFCatalogoBemTeVi',
        'title': 'Catálogo CIF do aplicativo Bem-Te-Vi',
        'status': 'draft',
        'experimental': True,
        'date': DATA,
        'description': 'Códigos da CIF usados no formulário adaptado da equipe de fisioterapia, extraídos da '
                       'planilha de qualificação pelo extrator do app. Os códigos repetidos e divergentes da '
                       'planilha estão marcados na propriedade pendencia.',
        'copyright': 'Classificação Internacional de Funcionalidade, Incapacidade e Saúde (CIF), da '
                     'Organização Mundial da Saúde. Descrições como estão na planilha da equipe.',
        'caseSensitive': True,
        'hierarchyMeaning': 'is-a',
        'content': 'complete',
        'count': len(conceitos),
        'property': [
            {'code': 'parent', 'uri': 'http://hl7.org/fhir/concept-properties#parent', 'type': 'code',
             'description': 'Código pai na planilha (parent_by_code do catálogo).'},
            {'code': 'pendencia', 'type': 'string',
             'description': 'Problema da planilha que depende de decisão da equipe.'},
        ],
        'concept': list(conceitos.values()),
    }


def gerar_questionario(m):
    calc = m.calc

    def habilitacao(chave):
        sexos = m.sexos(chave)
        if len(sexos) == 2:
            return {}
        return {'enableWhen': [{'question': 'sexo', 'operator': '=',
                                'answerCoding': {'system': SEXO, 'code': SEXO_APP[sexos[0]]}}]}

    def item(chave):
        campo = m.campos[chave]
        sexos = m.sexos(chave)
        texto = f'{campo.codigo} {campo.descricao}'
        if len(sexos) == 1:
            texto += f' ({ROTULO_SEXO[sexos[0]]})'
        base = {'linkId': chave, 'code': [{'system': CS_URL, 'code': campo.codigo}], 'text': texto}
        base.update(habilitacao(chave))
        formula = calc._formula(campo)
        if formula is not None:
            return {**base, 'type': 'decimal', 'readOnly': True, 'extension': [
                {'url': SDC + 'sdc-questionnaire-calculatedExpression', 'valueExpression': {
                    'description': f'Média; fórmula usada pelo calculador do app: {formula}',
                    'language': 'text/fhirpath',
                    'expression': expressao_media(campo.area, calc._referencias(campo))}}]}
        return {**base, 'type': 'integer', 'required': True, 'extension': [
            {'url': MIN, 'valueInteger': 0}, {'url': MAX, 'valueInteger': 4}]}

    grupos = []
    for area in m.catalogo['areas']:
        cod = area['code']
        raiz = [k for k, c in m.campos.items() if c.area == cod and c.codigo == cod]
        capitulos = OrderedDict()
        for k, c in m.campos.items():
            if c.area != cod or c.codigo == cod:
                continue
            cap = m.capitulo_do_no[(cod, c.linha)]
            capitulos.setdefault(cap, []).append(k)
        itens_area = [item(k) for k in raiz]
        for cap, chaves in capitulos.items():
            no_cap = next(n for n in area['nodes'] if n['code'] == cap)
            grupo = {'linkId': f'{cod}:{cap}', 'code': [{'system': CS_URL, 'code': cap}],
                     'text': f"{cap} {no_cap['description']}", 'type': 'group', 'item': [item(k) for k in chaves]}
            itens_area.append(grupo)
        grupos.append({'linkId': cod, 'code': [{'system': CS_URL, 'code': cod}], 'text': area['name'],
                       'type': 'group', 'item': itens_area})

    return {
        'resourceType': 'Questionnaire',
        'id': 'cif',
        'text': narrativa('Avaliação CIF adaptada da equipe de fisioterapia (formulário completo do app).'),
        'extension': [{'url': SDC + 'sdc-questionnaire-launchContext', 'extension': [
            {'url': 'name', 'valueCoding': {'system': 'http://hl7.org/fhir/uv/sdc/CodeSystem/launchContext',
                                            'code': 'patient'}},
            {'url': 'type', 'valueCode': 'Patient'},
            {'url': 'description', 'valueString': 'Paciente avaliado; o sexo do cadastro escolhe a variante.'}]}],
        'url': f'{BASE}/Questionnaire/cif',
        'version': VERSAO,
        'name': 'AvaliacaoCIF',
        'title': 'Avaliação CIF adaptada',
        'status': 'draft',
        'experimental': True,
        'subjectType': ['Patient'],
        'date': DATA,
        'description': 'Formulário gerado do catálogo do app (catalogo.v0.1.json). Contém as entradas e os campos '
                       'calculados alcançáveis pelo calculador do app (scripts/cif/calculador.py) no formulário '
                       'masculino ou no feminino. A média de b167 usa a fórmula corrigida pelo calculador.',
        'item': [{'linkId': 'sexo', 'text': 'Sexo do paciente (do cadastro)', 'type': 'choice',
                  'required': True, 'readOnly': True,
                  'extension': [{'url': SDC + 'sdc-questionnaire-initialExpression', 'valueExpression': {
                      'language': 'text/fhirpath', 'expression': '%patient.gender'}}],
                  'answerOption': [{'valueCoding': {'system': SEXO, 'code': 'male', 'display': 'Male'}},
                                   {'valueCoding': {'system': SEXO, 'code': 'female', 'display': 'Female'}}]},
                 {'linkId': 'data-avaliacao', 'text': 'Data da avaliação', 'type': 'date', 'required': True},
                 *grupos],
    }


def respostas_qr(questionario, sexo, valores):
    """Monta os itens da resposta, só com os itens habilitados para o sexo.

    valores: linkId -> número (entrada ou calculado) ou None (sem resposta). Itens
    calculados sem valor entram sem answer, para o conferidor preencher.
    """
    def habilitado(it):
        return all(c['answerCoding']['code'] == SEXO_APP[sexo] for c in it.get('enableWhen', []))

    def montar(it):
        if it['type'] == 'group':
            filhos = [montar(f) for f in it['item'] if habilitado(f)]
            return {'linkId': it['linkId'], 'item': [f for f in filhos if f is not None]}
        v = valores.get(it['linkId'])
        if v is None:
            return {'linkId': it['linkId']} if it['type'] == 'decimal' else None
        chave = 'valueDecimal' if it['type'] == 'decimal' else 'valueInteger'
        return {'linkId': it['linkId'], 'answer': [{chave: v}]}

    itens = [{'linkId': 'sexo', 'answer': [{'valueCoding': {'system': SEXO, 'code': SEXO_APP[sexo]}}]},
             {'linkId': 'data-avaliacao', 'answer': [{'valueDate': DATA}]}]
    itens += [montar(g) for g in questionario['item'][2:]]
    return itens


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    m = Modelo()
    calc = m.calc
    cs = gerar_codesystem(m)
    q = gerar_questionario(m)

    pac_ref, prof_ref = 'Patient/paciente-ficticio', 'Practitioner/avaliador-ficticio'
    paciente = json.loads((RAIZ / 'entregas' / 'fhir' / 'teste' / 'Patient-paciente-ficticio.json')
                          .read_text(encoding='utf-8'))
    profissional = {
        'resourceType': 'Practitioner',
        'id': 'avaliador-ficticio',
        'meta': {'profile': [BR_CORE + 'br-core-practitioner']},
        'text': narrativa('Fisioterapeuta fictício, criado só para testar o modelo.'),
        'identifier': [{'use': 'official',
                        'type': {'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/v2-0203', 'code': 'TAX'}]},
                        'system': 'https://saude.gov.br/fhir/sid/cpf', 'value': cpf_valido('987654321')}],
        'active': True,
        'name': [{'use': 'official', 'text': 'Avaliador Fictício', 'family': 'Fictício', 'given': ['Avaliador']}],
    }

    # Exemplo condutor: masculino, b167 da Figura, 0 no resto.
    entradas = {c.chave: 0 for c in calc.campos_entrada_obrigatorios('Masculino')}
    entradas.update(NOTAS_B167)
    res = calc.calcular(EntradaCIF(sexo='Masculino', respostas=entradas))
    assert res.definitivo and not res.erros, res.erros
    valores = dict(entradas)
    valores.update({k: p.valor_interno for k, p in res.intermediarios.items()})
    qr = {
        'resourceType': 'QuestionnaireResponse',
        'id': 'cif-exemplo',
        'text': narrativa('Avaliação CIF fictícia do exemplo condutor (Seção 4.2): notas do b167 da Figura e 0 '
                          'nos demais itens; valores calculados pelo calculador do app.'),
        'questionnaire': f"{q['url']}|{q['version']}",
        'status': 'completed',
        'subject': {'reference': pac_ref},
        'authored': DATA,
        'author': {'reference': prof_ref},
        'item': respostas_qr(q, 'Masculino', valores),
    }

    def observacao(oid, codigo, display, parcial, membros=()):
        obs = {
            'resourceType': 'Observation',
            'id': oid,
            'meta': {'profile': [BR_CORE + 'br-core-observation']},
            'text': narrativa(f'{codigo} {display}: média {parcial.valor} (exemplo condutor).'),
            'status': 'final',
            'category': [{'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/observation-category',
                                      'code': 'survey'}]}],
            # Só o CodeSystem próprio: o da CIF no HL7 Terminology (ICF) exige versão, e a
            # versão da CIF usada pela planilha da equipe não está documentada.
            'code': {'coding': [{'system': CS_URL, 'version': VERSAO, 'code': codigo, 'display': display}],
                     'text': f'Média dos qualificadores de {codigo}'},
            'subject': {'reference': pac_ref},
            'effectiveDateTime': DATA,
            'performer': [{'reference': prof_ref}],
            'valueQuantity': {'value': parcial.valor, 'unit': '1', 'system': 'http://unitsofmeasure.org', 'code': '1'},
            'derivedFrom': [{'reference': 'QuestionnaireResponse/cif-exemplo'}],
        }
        if membros:
            obs['hasMember'] = [{'reference': f'Observation/{x}'} for x in membros]
        return obs

    displays = {c['code']: c['display'] for c in cs['concept']}
    observacoes = []
    for cod_area, area in res.areas.items():
        caps = [c for c, p in res.capitulos.items() if p.area == cod_area]
        ids = [f'cif-exemplo-{c}' for c in caps]
        for c, oid in zip(caps, ids):
            observacoes.append(observacao(oid, c, displays[c], res.capitulos[c]))
        observacoes.append(observacao(f'cif-exemplo-{cod_area}', cod_area, displays[cod_area], area, ids))

    SAIDA.mkdir(parents=True, exist_ok=True)
    for velho in SAIDA.glob('*.json'):
        velho.unlink()
    arquivos = [(cs, 'CodeSystem-cif-catalogo.json'), (q, 'Questionnaire-cif.json'),
                (paciente, 'Patient-paciente-ficticio.json'), (profissional, 'Practitioner-avaliador-ficticio.json'),
                (qr, 'QuestionnaireResponse-cif-exemplo.json')]
    arquivos += [(o, f"Observation-{o['id']}.json") for o in observacoes]
    for recurso, nome in arquivos:
        (SAIDA / nome).write_text(json.dumps(recurso, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    # Casos para a conferência das expressões (respostas sem os valores calculados).
    casos = []

    def caso(nome, sexo, entradas, retirar=()):
        entradas = {k: v for k, v in entradas.items() if k not in retirar}
        r = calc.calcular(EntradaCIF(sexo=sexo, respostas=entradas))
        assert not r.erros, r.erros
        esperado = {k: {'interno': p.valor_interno, 'exibido': p.valor} for k, p in r.intermediarios.items()}
        casos.append({'nome': nome, 'sexo': sexo, 'definitivo': r.definitivo, 'esperado': esperado,
                      'resposta': {'resourceType': 'QuestionnaireResponse', 'status': 'in-progress',
                                   'item': respostas_qr(q, sexo, entradas)}})

    caso('exemplo condutor (masculino)', 'Masculino', entradas)
    for semente, sexo in ((1, 'Masculino'), (2, 'Feminino')):
        rng = random.Random(semente)
        aleatorias = {c.chave: rng.randint(0, 4) for c in calc.campos_entrada_obrigatorios(sexo)}
        caso(f'notas aleatórias, semente {semente} ({sexo.lower()})', sexo, aleatorias)
        if sexo == 'Feminino':
            # Retira uma entrada exclusiva do formulário feminino em b6: a pendência deve subir até b.
            exclusiva = next(k for k in aleatorias if m.sexos(k) == ['Feminino'])
            caso(f'semente {semente} sem a resposta {exclusiva} (feminino)', sexo, aleatorias, [exclusiva])
    CASOS.parent.mkdir(parents=True, exist_ok=True)
    CASOS.write_text(json.dumps(casos, ensure_ascii=False) + '\n', encoding='utf-8')

    # Resumo.
    tipos = Counter('calculado' if calc._formula(c) else 'entrada' for c in m.campos.values())
    por_sexo = {s: Counter('calculado' if calc._formula(m.campos[k]) else 'entrada'
                           for k in m.campos if m.sexos(k) == [s]) for s in SEXO_APP}
    print(f"- CodeSystem: {cs['count']} códigos; com pendência: "
          f"{sum(1 for c in cs['concept'] if any(p['code'] == 'pendencia' for p in c.get('property', [])))}")
    print(f'- Questionnaire: {len(m.campos)} itens de dados ({dict(tipos)}); só masculino: {dict(por_sexo["Masculino"])}; '
          f'só feminino: {dict(por_sexo["Feminino"])}')
    print(f'- Campos calculados do catálogo fora do formulário (não alcançados pelo calculador): {m.fora}')
    print(f'- QuestionnaireResponse do exemplo: {len(valores)} respostas; Observation: {len(observacoes)}')
    print(f"- b167 no exemplo: E106={res.intermediarios['b:E106'].valor}, E112={res.intermediarios['b:E112'].valor}, "
          f"E105={res.intermediarios['b:E105'].valor}; b1={res.capitulos['b1'].valor}; b={res.areas['b'].valor}")
    print(f'- Casos para conferência: {[c["nome"] for c in casos]}')


if __name__ == '__main__':
    main()
