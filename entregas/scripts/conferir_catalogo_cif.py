"""Confere a planilha CIF da equipe com o catálogo versionado do aplicativo.

Uso, na raiz do repositório do TCC:

    python entregas/scripts/conferir_catalogo_cif.py

O script só lê arquivos. Ele reutiliza o extrator do aplicativo
(app/scripts/cif/extrair_catalogo.py), no commit fixado no submódulo, sem
alterar o submódulo, e compara o resultado com app/catalogos/cif/catalogo.v0.1.json.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[2]
PLANILHA = RAIZ / 'entregas' / 'dados' / 'PLANILHA CIF de Qualificacao.xlsx'
CATALOGO = RAIZ / 'app' / 'catalogos' / 'cif' / 'catalogo.v0.1.json'
sys.path.insert(0, str(RAIZ / 'app' / 'scripts' / 'cif'))
import extrair_catalogo  # noqa: E402


def campos(no):
    return no['fields']


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    catalogo = json.loads(CATALOGO.read_text(encoding='utf-8'))

    # 1. A planilha guardada no repositório é a mesma usada na extração?
    sha = hashlib.sha256(PLANILHA.read_bytes()).hexdigest()
    fonte = catalogo['sources'][0]
    print('## Origem')
    print(f"- Fonte registrada no catálogo: {fonte['file']} ({fonte['sha256']})")
    print(f'- Planilha em entregas/dados/: {PLANILHA.name} ({sha})')
    print(f"- Mesmo arquivo (SHA-256): {'sim' if sha == fonte['sha256'] else 'NÃO'}")

    # 2. A extração reproduz as áreas do catálogo? O segundo argumento (quadro
    # resumo) só alimenta a auditoria; os nós vêm apenas da primeira planilha.
    reextraido, _ = extrair_catalogo.extract(PLANILHA, PLANILHA)
    iguais = reextraido['areas'] == catalogo['areas']
    print(f"- Extração refeita reproduz as áreas do catálogo: {'sim' if iguais else 'NÃO'}")

    # 3. Contagens por área.
    print('\n## Contagens por área (catálogo)')
    print('| Área | Aba | Nós | Capítulos | Campos | Calculados | Sem fórmula | Variantes Homem |')
    print('|---|---|---:|---:|---:|---:|---:|---:|')
    total = Counter()
    for area in catalogo['areas']:
        nos = area['nodes']
        fs = [f for n in nos for f in campos(n)]
        variantes = [f for n in nos for f in campos(n) if f['value_cell'][0] not in 'E']
        linha = Counter(nos=len(nos), capitulos=sum(len(n['code']) == 2 for n in nos), campos=len(fs),
                        calc=sum(f['kind_observed'] == 'calculated' for f in fs),
                        entrada=sum(f['kind_observed'] == 'input_candidate' for f in fs),
                        variantes=len(variantes))
        total.update(linha)
        print(f"| {area['code']} | {area['name']} | {linha['nos']} | {linha['capitulos']} | {linha['campos']} | "
              f"{linha['calc']} | {linha['entrada']} | {linha['variantes']} |")
    print(f"| Total | | {total['nos']} | {total['capitulos']} | {total['campos']} | {total['calc']} | "
          f"{total['entrada']} | {total['variantes']} |")

    # 4. Códigos repetidos (achado 2).
    print('\n## Códigos em mais de uma linha')
    for area in catalogo['areas']:
        cont = Counter(n['code'] for n in area['nodes'])
        for code, vezes in cont.items():
            if vezes > 1:
                linhas = [n['source_row'] for n in area['nodes'] if n['code'] == code]
                print(f"- {area['name']}: {code} nas linhas {linhas}")

    # 5. Fórmulas com referência repetida (achado 1).
    print('\n## Fórmulas com referência repetida')
    for area in catalogo['areas']:
        for n in area['nodes']:
            for f in campos(n):
                refs = f.get('references') or []
                rep = [r for r, c in Counter(refs).items() if c > 1]
                if rep:
                    print(f"- {area['name']} {f['value_cell']} ({n['code']}): {f['formula']} repete {rep}")

    # 5b. Classificação das ocorrências da auditoria (auditoria.v0.1.json).
    auditoria = json.loads((RAIZ / 'app' / 'catalogos' / 'cif' / 'auditoria.v0.1.json').read_text(encoding='utf-8'))
    tipos = Counter()
    for oc in auditoria['formula_findings']:
        omitidos = oc.get('omitted_prefix_children') or []
        partes = []
        if omitidos:
            partes.append('omite filhos' + (' (todos terminados em 9)' if all(c.endswith('9') for c in omitidos) else ''))
        if oc.get('references_outside_prefix_children'):
            partes.append('referência fora do prefixo')
        if oc.get('repeated_references'):
            partes.append('referência repetida')
        tipos[' + '.join(partes) or 'outro'] += 1
    print(f"\n## Ocorrências da auditoria ({len(auditoria['formula_findings'])})")
    for tipo, n in tipos.most_common():
        print(f'- {n}: {tipo}')

    # 6. Exemplo condutor: b167 e descendentes.
    print('\n## Exemplo condutor: b167')
    print('| Código | Linha | Pai | Célula | Tipo | Fórmula | Descrição |')
    print('|---|---:|---|---|---|---|---|')
    for area in catalogo['areas']:
        for n in area['nodes']:
            if n['code'].startswith('b167'):
                for f in campos(n):
                    print(f"| {n['code']} | {n['source_row']} | {n['parent_by_code']} | {f['value_cell']} | "
                          f"{f['kind_observed']} | {f['formula'] or ''} | {n['description']} |")


if __name__ == '__main__':
    main()
