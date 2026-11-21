"""Gera a tabela de automação item a item dos sete formulários (Seção 4.3).

Uso, na raiz do repositório do TCC:

    python entregas/scripts/gerar_tabela_automacao.py

Saída: entregas/automacao/automacao-itens.csv (UTF-8, separador ";") e, no
terminal, a contagem por instrumento e grau, que é a da tabela da Seção 4.3.1.

Graus (Seção 3.5, critério de P3):
  1 digitado; 2 calculado pelo aplicativo; 3 calculável por regra do
  instrumento; 4 dependente de julgamento clínico.

O que conta como valor: os itens de cada instrumento e os dados que entram em
um cálculo do instrumento (peso e altura no IMC, escolaridade na pontuação
esperada do MEEM). Ficam de fora identificação, datas, nome do examinador,
equipamento e texto livre. A anamnese não tem valor nesse sentido.

CIF: a lista vem do calculador do aplicativo (app/scripts/cif/calculador.py),
no commit fixado no submódulo, com a mesma cadeia de fórmulas que o formulário
usa. Demais formulários: a lista é transcrita do código, com arquivo e linha
na coluna "fonte". O script só lê arquivos.
"""
from collections import Counter
import csv
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[2]
CATALOGO = RAIZ / 'app' / 'catalogos' / 'cif' / 'catalogo.v0.1.json'
SAIDA = RAIZ / 'entregas' / 'automacao' / 'automacao-itens.csv'
sys.path.insert(0, str(RAIZ / 'app' / 'scripts' / 'cif'))
import calculador  # noqa: E402

SCHEMA = 'Backend/schema.sql'
LADOS = ('direito', 'esquerdo')
COLUNAS = ['instrumento', 'grupo', 'valor', 'sexo', 'grau', 'onde_calcula', 'gravado', 'fonte']


def linha(instrumento, grupo, valor, grau, fonte, onde='', gravado='sim', sexo='ambos'):
    return dict(instrumento=instrumento, grupo=grupo, valor=valor, sexo=sexo, grau=grau,
                onde_calcula=onde, gravado=gravado, fonte=fonte)


def cif():
    calc = calculador.CalculadorCIF(catalog_path=CATALOGO)
    por_sexo = {}
    for sexo in calculador.SEXES:
        alcancados, problemas = calc._caminho_referenciado(sexo)
        if problemas:
            raise SystemExit(f'Cadeia de fórmulas com problemas para {sexo}: {problemas}')
        por_sexo[sexo] = alcancados
    chaves = list(dict.fromkeys(k for s in calculador.SEXES for k in por_sexo[s]))
    linhas = []
    for chave in chaves:
        sexos = [s for s in calculador.SEXES if chave in por_sexo[s]]
        campo = (por_sexo[sexos[0]])[chave]
        sexo = 'ambos' if len(sexos) == 2 else sexos[0]
        if campo.formula:
            linhas.append(linha('CIF', campo.area, f'{campo.codigo} ({campo.celula})', 2,
                                f'catalogo.v0.1.json: {campo.formula}', 'servidor', sexo=sexo))
        else:
            linhas.append(linha('CIF', campo.area, f'{campo.codigo} ({campo.celula})', 1,
                                'catalogo.v0.1.json', sexo=sexo))
    return linhas


def asia():
    # Níveis na ordem de Backend/asiaCalculator.py, linhas 14-15.
    dermatomos = ['C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7',
                  'T8', 'T9', 'T10', 'T11', 'T12', 'L1', 'L2', 'L3', 'L4', 'L5', 'S1', 'S2', 'S3', 'S4_5']
    miotomos = ['C5', 'C6', 'C7', 'C8', 'T1', 'L2', 'L3', 'L4', 'L5', 'S1']
    a = []
    for m in miotomos:
        for lado in LADOS:
            a.append(linha('ASIA', 'motor', f'força {m} {lado}', 1, f'{SCHEMA}: 58-59'))
    for d in dermatomos:
        for modal in ('tato leve', 'picada'):
            for lado in LADOS:
                a.append(linha('ASIA', 'sensorial', f'{modal} {d} {lado}', 1, f'{SCHEMA}: 66-69'))
    a.append(linha('ASIA', 'sacral', 'contração anal voluntária', 1, f'{SCHEMA}: 29'))
    a.append(linha('ASIA', 'sacral', 'pressão anal profunda', 1, f'{SCHEMA}: 30'))
    for lado in LADOS:
        a.append(linha('ASIA', 'motor', f'músculo não chave mais baixo {lado}', 1, f'{SCHEMA}: 31-32'))
    calc = 'Backend/asiaCalculator.py: 22-50'
    for nome in ('nível sensorial', 'nível motor'):
        for lado in LADOS:
            a.append(linha('ASIA', 'classificação', f'{nome} {lado}', 2, calc, 'servidor'))
    for nome in ('nível neurológico da lesão', 'completude', 'grau AIS'):
        a.append(linha('ASIA', 'classificação', nome, 2, calc, 'servidor'))
    for nome in ('ZPP sensorial', 'ZPP motora'):
        for lado in LADOS:
            a.append(linha('ASIA', 'classificação', f'{nome} {lado}', 2, calc, 'servidor'))
    for nome in ('UEMS', 'LEMS', 'tato leve', 'picada'):
        for lado in LADOS:
            a.append(linha('ASIA', 'totais', f'total {nome} {lado}', 2, calc, 'servidor'))
    for nome in ('UEMS', 'LEMS', 'tato leve', 'picada'):
        a.append(linha('ASIA', 'totais', f'total {nome} (direito + esquerdo)', 2,
                       'lib/Core/Models/resultsModels.dart: 75-80', 'tela', 'não'))
    return a


def gas():
    # O formulário tem 13 metas fixas (lib/Presentation/Screens/gasForm.dart, linhas 147-231).
    g = []
    calc = 'Backend/gasCalculator.py: 10-46; lib/Presentation/Screens/gasForm.dart: 59-90'
    for meta in range(1, 14):
        grupo = f'meta {meta}'
        for nome, lin in (('importância', 93), ('dificuldade', 94), ('linha de base', 95), ('alcançado', 96)):
            g.append(linha('GAS', grupo, nome, 1, f'{SCHEMA}: {lin}'))
        for nome in ('ponderação 1 (importância x dificuldade)', 'ponderação 2 (quadrado da 1)',
                     'ponderação 3 (base ponderada)', 'ponderação 4 (alcançado ponderado)'):
            g.append(linha('GAS', grupo, nome, 2, calc, 'tela e servidor'))
    for nome in ('somatório p1', 'somatório p2', 'somatório p3', 'somatório p4',
                 'escore T inicial', 'escore T alcançado', 'evolução'):
        g.append(linha('GAS', 'avaliação', nome, 2, calc, 'tela e servidor'))
    return g


def meem():
    itens = (['orientação temporal'] * 5 + ['orientação espacial'] * 5 + ['memória imediata'] * 3
             + ['atenção e cálculo'] * 5 + ['memória evocativa'] * 3 + ['linguagem'] * 9)
    m = [linha('MEEM', grupo, f'item {i}', 1, f'{SCHEMA}: {148 + i}') for i, grupo in enumerate(itens, 1)]
    m.append(linha('MEEM', 'dado do cálculo', 'escolaridade', 1, f'{SCHEMA}: 148'))
    m.append(linha('MEEM', 'escore', 'pontuação total', 2,
                   'lib/Core/Providers/meemFormProvider.dart: 45-70; Backend/main.py: 354-366',
                   'tela e servidor'))
    m.append(linha('MEEM', 'escore', 'pontuação esperada para a escolaridade', 2,
                   'lib/Core/Providers/meemFormProvider.dart: 72-88', 'tela', 'não'))
    return m


def eletro():
    # Músculos de lib/Core/Providers/eletroFormProvider.dart, linhas 61-72.
    musculos = ['Bíceps Braquial', 'Extensores de Punho', 'Tríceps Braquial', 'Grande Dorsal', 'Deltóide',
                'Reto Abdominal', 'Vasto Medial', 'Vasto Lateral', 'Tibial Anterior', 'Tríceps Sural',
                'Glúteos', 'Isquiotibiais']
    e = []
    for mus in musculos:
        for lado in LADOS:
            for medida in ('reobase', 'acomodação', 'cronaxia'):
                e.append(linha('Eletrodiagnóstico', mus, f'{medida} {lado}', 1, f'{SCHEMA}: 131-136'))
            e.append(linha('Eletrodiagnóstico', mus, f'índice de acomodação {lado}', 2,
                           'lib/Core/Providers/eletroFormProvider.dart: 23-39', 'tela'))
    return e


def densitometria():
    fonte_tela = 'lib/Presentation/Screens/dex.dart: 68-101'
    d = [linha('Densitometria', 'dados do cálculo', 'peso', 1, f'{SCHEMA}: 186'),
         linha('Densitometria', 'dados do cálculo', 'altura', 1, f'{SCHEMA}: 187'),
         linha('Densitometria', 'dados do cálculo', 'IMC', 2, 'lib/Presentation/Screens/dex.dart: 225-235',
               'tela')]
    secoes = {
        'coluna lombar': ['L1', 'L2', 'L3', 'L4', 'L1-L2', 'L1-L3', 'L1-L4', 'L2-L3', 'L2-L4', 'L3-L4'],
        'corpo inteiro': ['Cabeça', 'Braços', 'Pernas', 'Tronco', 'Costelas', 'Coluna', 'Pelve', 'Total'],
        'fêmur direito': ['Colo', 'Total'],
        'fêmur esquerdo': ['Colo', 'Total'],
    }
    for secao, regioes in secoes.items():
        for r in regioes:
            d.append(linha('Densitometria', secao, f'BMD {r}', 1, f'{SCHEMA}: 196; {fonte_tela}'))
        d.append(linha('Densitometria', secao, 'BMD da tendência', 1, f'{SCHEMA}: 205'))
    for nome, lin in (('% de gordura', 206), ('massa total', 207), ('massa gorda', 208), ('massa magra', 209)):
        d.append(linha('Densitometria', 'composição corporal', nome, 1, f'{SCHEMA}: {lin}'))
    return d


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    linhas = cif() + asia() + gas() + meem() + eletro() + densitometria()
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS, delimiter=';')
        w.writeheader()
        w.writerows(linhas)
    print(f'Gravado: {SAIDA.relative_to(RAIZ)} ({len(linhas)} linhas)\n')

    print('| Instrumento | Recorte | Grau 1 | Grau 2 | Grau 3 | Grau 4 |')
    print('|---|---|---:|---:|---:|---:|')
    ordem = ['CIF', 'ASIA', 'GAS', 'MEEM', 'Eletrodiagnóstico', 'Densitometria']
    for inst in ordem:
        doi = [l for l in linhas if l['instrumento'] == inst]
        if inst == 'CIF':
            for sexo in calculador.SEXES:
                c = Counter(l['grau'] for l in doi if l['sexo'] in ('ambos', sexo))
                print(f"| CIF | {sexo} | {c[1]} | {c[2]} | {c[3]} | {c[4]} |")
            continue
        c = Counter(l['grau'] for l in doi)
        print(f"| {inst} | | {c[1]} | {c[2]} | {c[3]} | {c[4]} |")
    print('| Anamnese | | 0 | 0 | 0 | 0 |')

    calc_tela = Counter(l['instrumento'] for l in linhas if l['grau'] == 2 and l['gravado'] == 'não')
    print('\nCalculados sem gravação:', dict(calc_tela))


if __name__ == '__main__':
    main()
