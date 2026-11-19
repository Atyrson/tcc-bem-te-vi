"""Confere a diferença entre o escore da GAS calculado no servidor e na tela.

Uso, na raiz do repositório do TCC:

    python entregas/scripts/conferir_calculo_gas.py

O servidor é executado de verdade: o script importa GasCalculator e os modelos
de app/Backend/ (commit fixado no submódulo). A tela é escrita em Dart e não
roda aqui; a função conta_da_tela() transcreve a conta de
lib/Presentation/Screens/gasForm.dart (linhas 59-90) e de
lib/Core/Models/GoalsModels.dart (linhas 46-49). As metas são fictícias.
"""
from math import sqrt
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'app' / 'Backend'))
from gasCalculator import GasCalculator  # noqa: E402
from models import GasEvaluation, Goal  # noqa: E402


def conta_da_tela(metas):
    """Mesma conta do aplicativo Flutter, sem trocar valores negativos por zero."""
    p1 = [m['importance'] * m['difficulty'] for m in metas]
    p2 = sum(x ** 2 for x in p1)
    p3 = sum(m['baseline'] * x for m, x in zip(metas, p1))
    p4 = sum(m['achieved'] * x for m, x in zip(metas, p1))
    if p2 <= 0:
        return 0.0, 0.0, 0.0
    base = 50.0 + 10 * p3 / sqrt(p2)
    alcancado = 50.0 + 10 * p4 / sqrt(p2)
    return base, alcancado, alcancado - base


def conta_do_servidor(metas):
    goals = [Goal(id=i, description=f'Meta fictícia {i}', **m) for i, m in enumerate(metas, start=1)]
    avaliacao = GasEvaluation(patientIdentifier='Paciente Fictício', planningDate='2026-01-01',
                              revaluationDate='2026-04-01', interventionPlan='', iq='', goals=goals)
    s = GasCalculator(avaliacao).calculate_all()['summary']
    return s['gasScoreBase'], s['gasScoreAchieved'], s['evolution']


CASOS = [
    ('Uma meta: linha de base -1, alcançado 0 (resultado esperado)',
     [{'importance': 2, 'difficulty': 2, 'baseline': -1, 'achieved': 0}]),
    ('Uma meta: linha de base -1, alcançado 1 (melhor que o esperado)',
     [{'importance': 2, 'difficulty': 2, 'baseline': -1, 'achieved': 1}]),
    ('Duas metas: linhas de base -1 e -2, ambas alcançam 0',
     [{'importance': 2, 'difficulty': 2, 'baseline': -1, 'achieved': 0},
      {'importance': 3, 'difficulty': 1, 'baseline': -2, 'achieved': 0}]),
]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    for titulo, metas in CASOS:
        print(f'## {titulo}')
        for nome, conta in (('servidor', conta_do_servidor), ('tela', conta_da_tela)):
            base, alcancado, evolucao = conta(metas)
            print(f'- {nome:8}: escore inicial {base:.1f}; alcançado {alcancado:.1f}; evolução {evolucao:+.1f}')


if __name__ == '__main__':
    main()
