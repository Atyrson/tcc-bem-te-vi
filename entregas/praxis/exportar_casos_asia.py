"""Exporta para JSON os dez casos fictícios de conferir_calculo_asia.py.

Uso, na raiz do repositório do TCC:

    python -X utf8 entregas/praxis/exportar_casos_asia.py

Gera entregas/praxis/casos_asia.json com, para cada caso, o exame no formato do
algoritmo do Praxis Spinal Cord Institute, o resultado esperado obtido à mão e o
resultado do servidor do aplicativo. O arquivo é lido por conferir_praxis.mjs.

O formulário do aplicativo registra o músculo não chave por um código (no caso 8,
'21', que corresponde a L2). O algoritmo do Praxis espera o nome do nível, e por
isso o código é convertido com CODIGO_NAO_CHAVE.
"""
from pathlib import Path
import json
import sys

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / 'entregas' / 'scripts'))
from conferir_calculo_asia import CASOS, resultado_do_servidor  # noqa: E402

CODIGO_NAO_CHAVE = {'21': 'L2'}


def lado(side):
    d = {'motor': dict(side.motor), 'lightTouch': dict(side.lightTouch), 'pinPrick': dict(side.pinPrick)}
    nao_chave = side.lowestNonKeyMuscleWithMotorFunction
    if nao_chave:
        d['lowestNonKeyMuscleWithMotorFunction'] = CODIGO_NAO_CHAVE.get(nao_chave, nao_chave)
    return d


def main():
    saida = []
    for titulo, regras, ex, esperado in CASOS:
        try:
            servidor = resultado_do_servidor(ex)
        except Exception as erro:
            servidor = {'erro': type(erro).__name__}
        saida.append({
            'titulo': titulo,
            'exame': {'right': lado(ex.right), 'left': lado(ex.left),
                      'voluntaryAnalContraction': ex.voluntaryAnalContraction,
                      'deepAnalPressure': ex.deepAnalPressure},
            'esperado': esperado,
            'servidor': servidor,
        })
    destino = Path(__file__).with_name('casos_asia.json')
    destino.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(saida)} casos gravados em {destino}')


if __name__ == '__main__':
    main()
