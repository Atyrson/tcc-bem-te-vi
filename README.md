# TCC 1: requisitos e modelo de dados em HL7 FHIR para o aplicativo Bem-Te-Vi

Trabalho de Conclusão de Curso 1 de Engenharia de Software (UnB, Faculdade do Gama), de Atyrson Souto da Silva.

## Conteúdo

- `latex/`: texto da monografia (modelo FGA-UnB, abnTeX2). Compile com `.\build.ps1`.
- `entregas/`: material que o texto cita e que permite reproduzir as conferências.
  - `dados/`: planilha CIF da equipe de fisioterapia, origem do catálogo do aplicativo. Contém só códigos, fórmulas e valores de modelo, sem dados de pacientes.
  - `scripts/`: conferências em Python e validação das instâncias FHIR.
  - `fhir/`: instâncias FHIR com dados fictícios e os relatórios do validador oficial do HL7. `fhir/cif/` tem o modelo da CIF (Seção 4.5), gerado do catálogo por `scripts/gerar_fhir_cif.py`.
  - `fhirpath/`: execução das expressões de cálculo do questionário da CIF com o fhirpath.js e comparação com o calculador do aplicativo (Seção 4.5).
  - `automacao/`: classificação de cada valor dos formulários por grau de automação, item a item (Seção 4.3.1).
  - `praxis/`: conferência dos casos fictícios da ASIA com o algoritmo do ISNCSCI do Praxis Spinal Cord Institute (Seção 4.3.2).
- `app/`: código do aplicativo, como submódulo, fixado no commit `a9059f0` analisado no texto.

## Reproduzir

```powershell
git clone --recurse-submodules https://github.com/Atyrson/tcc-bem-te-vi.git
cd tcc-bem-te-vi
python -X utf8 entregas/scripts/conferir_catalogo_cif.py   # planilha x catálogo
python -X utf8 entregas/scripts/conferir_calculo_cif.py    # números da Seção 4.2
python -X utf8 entregas/scripts/conferir_calculo_gas.py    # escore da GAS: tela, servidor e fórmula publicada
python -X utf8 entregas/scripts/conferir_calculo_asia.py   # classificação da ASIA x regras do ISNCSCI
python -X utf8 entregas/scripts/gerar_tabela_automacao.py  # tabela de automação item a item
.\entregas\scripts\validar_fhir.ps1                         # validação FHIR do teste de 17/11 (requer Java 11+)
python -X utf8 entregas/scripts/gerar_fhir_cif.py          # artefatos FHIR da CIF a partir do catálogo
.\entregas\scripts\validar_fhir.ps1 entregas/fhir/cif      # validação FHIR do modelo da CIF

cd entregas/fhirpath
npm install                                                 # fhirpath.js 5.2.3
node conferir_expressoes.mjs                                # 230 expressões de cálculo x calculador do app
cd ../..

cd entregas/praxis
npm install                                                 # algoritmo do ISNCSCI do Praxis (pacote isncsci 2.0.6)
python -X utf8 exportar_casos_asia.py                       # exporta os 10 casos fictícios da ASIA
node conferir_praxis.mjs                                    # Praxis x valor esperado x servidor do app
```

Os scripts de conferência usam Python 3.10+ e as dependências de `app/Backend` e `app/scripts/cif`. A conferência com o Praxis e a das expressões FHIRPath usam Node.js (testadas com a versão 22).

Todos os exemplos usam dados fictícios.