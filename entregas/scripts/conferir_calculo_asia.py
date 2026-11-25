"""Confere a classificação da ASIA calculada pelo servidor com as regras do ISNCSCI.

Uso, na raiz do repositório do TCC:

    python -X utf8 entregas/scripts/conferir_calculo_asia.py

O servidor é executado de verdade: o script importa PraxisIscnsciCalculator e os
modelos de app/Backend/ (commit fixado no submódulo). Os casos são fictícios. O
resultado esperado de cada caso foi obtido à mão a partir das regras da edição de
2019 do ISNCSCI (RUPP et al., 2021, Topics in Spinal Cord Injury Rehabilitation,
v. 27, n. 2), nas páginas indicadas em REGRAS.

Para a comparação, o script trata como "NA" (não se aplica) a cadeia vazia e o
texto "N/A" que o servidor devolve nas zonas de preservação parcial (ZPP).

Limitação: os valores esperados foram derivados à mão das regras citadas e depois
conferidos com o algoritmo do Praxis Spinal Cord Institute, que implementa a revisão
de 2019 do ISNCSCI (entregas/praxis/conferir_praxis.mjs, com o resultado em
entregas/praxis/resultado_praxis.txt). Coincidem em todos os casos, com uma diferença
de notação no caso 9: o Praxis não usa a marca ND e devolve os valores possíveis do
grau AIS (A ou B) e da ZPP sensitiva direita (NA ou T6).
"""
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'app' / 'Backend'))
from asiaCalculator import PraxisIscnsciCalculator  # noqa: E402
from models import Exam, ExamSide  # noqa: E402

DERMATOMOS = ['C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7',
              'T8', 'T9', 'T10', 'T11', 'T12', 'L1', 'L2', 'L3', 'L4', 'L5', 'S1', 'S2', 'S3', 'S4_5']
MIOTOMOS = ['C5', 'C6', 'C7', 'C8', 'T1', 'L2', 'L3', 'L4', 'L5', 'S1']

REGRAS = {
    'R1': 'Nível motor presumido igual ao sensitivo onde não há miótomo-chave (C1-C4, T2-L1, S2-S5), p. 16.',
    'R2': 'B: sem função motora a mais de três níveis abaixo do nível motor, p. 18.',
    'R3': 'C ou D: contração anal voluntária OU incompleta sensitiva com função motora, de músculo-chave '
          'ou não, a mais de três níveis abaixo do nível motor, p. 18.',
    'R4': 'C e D se separam pela proporção de músculos-chave com grau >= 3 abaixo do nível neurológico '
          'único (C: menos da metade; D: metade ou mais), p. 18.',
    'R5': 'E: sensibilidade e motricidade normais em todos os segmentos em paciente com déficit anterior, '
          'p. 18 e 22.',
    'R6': 'ZPP: segmento mais caudal com função; sem preservação abaixo, registra-se o próprio nível. '
          'ZPP sensitiva não se aplica (NA) com pressão anal profunda; ZPP motora não se aplica com '
          'contração anal voluntária. Músculo não chave usado para o grau C define a ZPP motora, p. 18-19.',
    'R7': 'Quando um NT impede a classificação, registra-se ND (não determinável), p. 3 e 19.',
}


def lado(sens_normal_ate, motor, sacral='0', sacral_pp=None, nao_chave=None, sens_extra=None):
    """Monta um lado do exame.

    sens_normal_ate: último dermátomo com tato leve e picada normais (2); abaixo, 0.
    motor: dicionário miótomo -> grau; os ausentes valem 0.
    sacral: tato leve em S4-5; sacral_pp: picada em S4-5 (padrão: 0).
    """
    corte = DERMATOMOS.index(sens_normal_ate) if sens_normal_ate else -1
    lt = {d: ('2' if i <= corte else '0') for i, d in enumerate(DERMATOMOS)}
    pp = dict(lt)
    if sens_extra:
        lt.update(sens_extra)
        pp.update(sens_extra)
    if sens_normal_ate != 'S4_5':
        lt['S4_5'] = sacral
        pp['S4_5'] = sacral_pp if sacral_pp is not None else '0'
    mot = {m: str(motor.get(m, 0)) for m in MIOTOMOS}
    return ExamSide(motor=mot, lightTouch=lt, pinPrick=pp, lowestNonKeyMuscleWithMotorFunction=nao_chave)


def exame(direito, esquerdo, vac, dap):
    return Exam(patientName='Paciente Fictício', examDate='2026-01-01', examinerName='Examinador Fictício',
                right=direito, left=esquerdo, voluntaryAnalContraction=vac, deepAnalPressure=dap)


SUPERIOR_NORMAL = {m: 5 for m in ['C5', 'C6', 'C7', 'C8', 'T1']}
TUDO_NORMAL = {m: 5 for m in MIOTOMOS}

# Cada caso: título, regras usadas, exame e valores esperados
# (sensitivo D/E, motor D/E, nível neurológico, AIS, ZPP sensitiva D/E, ZPP motora D/E).
CASOS = [
    ('1. Lesão completa em T6',
     ['R1', 'R6'],
     exame(lado('T6', SUPERIOR_NORMAL), lado('T6', SUPERIOR_NORMAL), 'No', 'No'),
     dict(sens=('T6', 'T6'), motor=('T6', 'T6'), nli='T6', ais='A', zpp_s=('T6', 'T6'), zpp_m=('T6', 'T6'))),

    ('2. Incompleta sensitiva em T6 (tato leve em S4-5 e pressão anal profunda)',
     ['R1', 'R2', 'R6'],
     exame(lado('T6', SUPERIOR_NORMAL, sacral='1'), lado('T6', SUPERIOR_NORMAL, sacral='1'), 'No', 'Yes'),
     dict(sens=('T6', 'T6'), motor=('T6', 'T6'), nli='T6', ais='B', zpp_s=('NA', 'NA'), zpp_m=('T6', 'T6'))),

    ('3. Incompleta sensitiva em C5, com grau 3 em C6 (um nível abaixo do nível motor)',
     ['R2', 'R6'],
     exame(lado('C5', {'C5': 4, 'C6': 3}, sacral='1'), lado('C5', {'C5': 4, 'C6': 3}, sacral='1'), 'No', 'Yes'),
     dict(sens=('C5', 'C5'), motor=('C5', 'C5'), nli='C5', ais='B', zpp_s=('NA', 'NA'), zpp_m=('C6', 'C6'))),

    ('4. Incompleta motora em C5, com grau 1 em L2 (mais de três níveis abaixo)',
     ['R3', 'R4', 'R6'],
     exame(lado('C5', {'C5': 4, 'L2': 1}, sacral='1'), lado('C5', {'C5': 4, 'L2': 1}, sacral='1'), 'No', 'Yes'),
     dict(sens=('C5', 'C5'), motor=('C5', 'C5'), nli='C5', ais='C', zpp_s=('NA', 'NA'), zpp_m=('L2', 'L2'))),

    ('5. Incompleta motora em C5 só pela contração anal voluntária',
     ['R3', 'R4', 'R6'],
     exame(lado('C5', {'C5': 4}, sacral='1'), lado('C5', {'C5': 4}, sacral='1'), 'Yes', 'Yes'),
     dict(sens=('C5', 'C5'), motor=('C5', 'C5'), nli='C5', ais='C', zpp_s=('NA', 'NA'), zpp_m=('NA', 'NA'))),

    ('6. Incompleta motora em C5, com grau 3 em todos os músculos-chave abaixo',
     ['R3', 'R4', 'R6'],
     exame(lado('C5', {'C5': 4, **{m: 3 for m in MIOTOMOS[1:]}}, sacral='1'),
           lado('C5', {'C5': 4, **{m: 3 for m in MIOTOMOS[1:]}}, sacral='1'), 'No', 'Yes'),
     dict(sens=('C5', 'C5'), motor=('C5', 'C5'), nli='C5', ais='D', zpp_s=('NA', 'NA'), zpp_m=('S1', 'S1'))),

    ('7. Níveis diferentes nos dois lados (C5 e C8): proporção abaixo do nível neurológico',
     ['R3', 'R4', 'R6'],
     exame(lado('C5', {'C5': 4, 'L2': 3, 'L3': 3, 'L4': 3}, sacral='1'),
           lado('C8', {'C5': 5, 'C6': 5, 'C7': 5, 'C8': 5, 'L2': 3, 'L3': 3, 'L4': 3}, sacral='1'), 'No', 'Yes'),
     dict(sens=('C5', 'C8'), motor=('C5', 'C8'), nli='C5', ais='D', zpp_s=('NA', 'NA'), zpp_m=('L4', 'L4'))),

    ('8. Incompleta motora em C5 por músculo não chave em L2 (código 21 do formulário)',
     ['R3', 'R4', 'R6'],
     exame(lado('C5', {'C5': 4}, sacral='1', nao_chave='21'), lado('C5', {'C5': 4}, sacral='1', nao_chave='21'),
           'No', 'Yes'),
     dict(sens=('C5', 'C5'), motor=('C5', 'C5'), nli='C5', ais='C', zpp_s=('NA', 'NA'), zpp_m=('L2', 'L2'))),

    ('9. Lesão em T6 com S4-5 não testável (NT) do lado direito',
     ['R7'],
     exame(lado('T6', SUPERIOR_NORMAL, sacral='NT', sacral_pp='NT'), lado('T6', SUPERIOR_NORMAL), 'No', 'No'),
     dict(sens=('T6', 'T6'), motor=('T6', 'T6'), nli='T6', ais='ND', zpp_s=('ND', 'T6'), zpp_m=('T6', 'T6'))),

    ('10. Exame normal em paciente com déficit anterior',
     ['R5', 'R6'],
     exame(lado('S4_5', TUDO_NORMAL), lado('S4_5', TUDO_NORMAL), 'Yes', 'Yes'),
     dict(sens=('INT', 'INT'), motor=('INT', 'INT'), nli='INT', ais='E', zpp_s=('NA', 'NA'), zpp_m=('NA', 'NA'))),
]


def na(valor):
    return 'NA' if valor in ('', 'N/A', None) else valor


def resultado_do_servidor(ex):
    c = PraxisIscnsciCalculator(ex).calculate()['classification']
    n, z = c['neurologicalLevels'], c['zoneOfPartialPreservations']
    return dict(sens=(n['sensoryRight'], n['sensoryLeft']), motor=(n['motorRight'], n['motorLeft']),
                nli=c['neurologicalLevelOfInjury'], ais=c['asiaImpairmentScale'],
                zpp_s=(na(z['sensoryRight']), na(z['sensoryLeft'])), zpp_m=(na(z['motorRight']), na(z['motorLeft'])))


ROTULOS = [('sens', 'Nível sensitivo (D, E)'), ('motor', 'Nível motor (D, E)'), ('nli', 'Nível neurológico'),
           ('ais', 'Grau AIS'), ('zpp_s', 'ZPP sensitiva (D, E)'), ('zpp_m', 'ZPP motora (D, E)')]


def fmt(v):
    return ', '.join(v) if isinstance(v, tuple) else str(v)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print('Regras do ISNCSCI usadas (Rupp et al., 2021):')
    for k, v in REGRAS.items():
        print(f'- {k}: {v}')
    resumo = []
    for titulo, regras, ex, esperado in CASOS:
        print(f'\n## {titulo}  [{", ".join(regras)}]')
        try:
            obtido = resultado_do_servidor(ex)
        except Exception as erro:  # o servidor responderia com erro 500
            print(f'- servidor: falhou com {type(erro).__name__}: {erro}')
            print(f'- esperado: grau AIS {esperado["ais"]}')
            resumo.append((titulo, esperado['ais'], f'erro ({type(erro).__name__})', 'erro'))
            continue
        for chave, rotulo in ROTULOS:
            marca = 'igual' if obtido[chave] == esperado[chave] else 'DIVERGE'
            print(f'- {rotulo:24} esperado {fmt(esperado[chave]):10} servidor {fmt(obtido[chave]):10} {marca}')
        resumo.append((titulo, esperado['ais'], obtido['ais'],
                       'igual' if obtido['ais'] == esperado['ais'] else 'DIVERGE'))
    print('\n## Resumo do grau AIS')
    for titulo, esp, obt, marca in resumo:
        print(f'- {titulo.split(".")[0]:>2}: esperado {esp:3} servidor {obt:18} {marca}')


if __name__ == '__main__':
    main()
