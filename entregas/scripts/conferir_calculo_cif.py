"""Confere, com o calculador do aplicativo, os números citados na Seção 4.2.

Uso, na raiz do repositório do TCC:

    python entregas/scripts/conferir_calculo_cif.py

Só lê arquivos do submódulo app/ (commit fixado). As respostas usadas são
fictícias e servem apenas para exercitar as regras de cálculo.
"""
from collections import Counter
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'app' / 'scripts' / 'cif'))
from calculador import CalculadorCIF, EntradaCIF  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    calc = CalculadorCIF()

    print('## Campos de entrada por sexo')
    entradas = {}
    for sexo in ('Masculino', 'Feminino'):
        campos = calc.campos_entrada_obrigatorios(sexo)
        entradas[sexo] = {c.chave for c in campos}
        por_area = Counter(c.area for c in campos)
        print(f'- {sexo}: {len(campos)} campos ({dict(por_area)})')
    so_f = entradas['Feminino'] - entradas['Masculino']
    so_m = entradas['Masculino'] - entradas['Feminino']
    print(f'- Só no formulário feminino: {len(so_f)}; só no masculino: {len(so_m)}')
    print(f'- Áreas: {calc.areas}; capítulos: {len(calc.capitulos)}')

    # Células sem fórmula do catálogo que ficam fora da cadeia de cálculo.
    import json
    catalogo = json.loads((RAIZ / 'app' / 'catalogos' / 'cif' / 'catalogo.v0.1.json').read_text(encoding='utf-8'))
    sem_formula = {f"{a['code']}:{f['value_cell']}": n['code'] for a in catalogo['areas'] for n in a['nodes']
                   for f in n['fields'] if f['formula'] is None}
    no_formulario = entradas['Masculino'] | entradas['Feminino']
    fora = {k: c for k, c in sem_formula.items() if k.lower() not in {x.lower() for x in no_formulario}}
    terminados_em_9 = sum(1 for c in fora.values() if len(c) >= 4 and c.endswith('9'))
    print(f'- Células sem fórmula no catálogo: {len(sem_formula)}; em algum formulário: {len(no_formulario)}; '
          f'fora da cadeia: {len(fora)} (com código terminado em 9: {terminados_em_9})')

    print('\n## b167 no formulário')
    for sexo in ('Masculino', 'Feminino'):
        b167 = sorted(c.codigo for c in calc.campos_entrada_obrigatorios(sexo) if c.codigo.startswith('b167'))
        print(f'- {sexo}: {b167}')

    # Respostas fictícias: todos os campos com 0, exceto os do grupo b167.
    print('\n## Cálculo de b167 com respostas fictícias')
    respostas = {k: 0 for k in entradas['Masculino']}
    ficticias = {'b:E107': 1, 'b:E108': 2, 'b:E109': 3, 'b:E110': 4,   # b1670 -> 2,5
                 'b:E113': 0, 'b:E114': 1, 'b:E115': 1, 'b:E116': 2,   # b1671 -> 1
                 'b:E118': 3,                                          # b1672
                 'b:E119': 4}                                          # b1678
    respostas.update(ficticias)
    r = calc.calcular(EntradaCIF(sexo='Masculino', respostas=respostas))
    inter = r.intermediarios
    for chave in ('b:E106', 'b:E112', 'b:E105'):
        p = inter[chave]
        print(f'- {chave} ({p.codigo}): exibido {p.valor}, interno {p.valor_interno}')
    print('- Com a fórmula original (E119 duas vezes) seria (2,5 + 1 + 3 + 4 + 4) / 5 = 2,9')
    print(f'- Status: {r.status}; definitivo: {r.definitivo}; resultado geral: {r.resultado_geral}')
    print(f"- Correções registradas: {r.auditoria['formula_correcoes']}")

    print('\n## Pendência e validação')
    sem_um = dict(respostas)
    del sem_um['b:E118']
    r2 = calc.calcular(EntradaCIF(sexo='Masculino', respostas=sem_um))
    print(f"- Sem a nota de b1672: status {r2.status}; b167 = {r2.intermediarios['b:E105'].valor}; "
          f"pendências: {[p.code for p in r2.pendencias]}")
    invalida = dict(respostas)
    invalida['b:E118'] = 2.5
    r3 = calc.calcular(EntradaCIF(sexo='Masculino', respostas=invalida))
    print(f'- Nota 2,5: status {r3.status}; erros: {[e.code for e in r3.erros]}')
    r4 = calc.calcular(EntradaCIF(sexo='Outro', respostas=respostas))
    print(f'- Sexo "Outro": status {r4.status}; erros: {[e.code for e in r4.erros]}')
    r5 = calc.calcular(EntradaCIF(sexo=None, respostas=respostas))
    print(f'- Sexo ausente: status {r5.status}; pendências: {[p.code for p in r5.pendencias][:1]}')


if __name__ == '__main__':
    main()
