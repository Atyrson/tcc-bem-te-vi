# TCC 1: requisitos e modelo de dados em HL7 FHIR para o aplicativo Bem-Te-Vi

Trabalho de ConclusÃ£o de Curso 1 de Engenharia de Software (UnB, Faculdade do Gama), de Atyrson Souto da Silva.

## ConteÃºdo

- `latex/`: texto da monografia (modelo FGA-UnB, abnTeX2). Compile com `.\build.ps1`.
- `entregas/`: material que o texto cita e que permite reproduzir as conferÃªncias.
  - `dados/`: planilha CIF da equipe de fisioterapia, origem do catÃ¡logo do aplicativo. ContÃ©m sÃ³ cÃ³digos, fÃ³rmulas e valores de modelo, sem dados de pacientes.
  - `scripts/`: conferÃªncias em Python e validaÃ§Ã£o das instÃ¢ncias FHIR.
  - `fhir/`: instÃ¢ncias FHIR com dados fictÃ­cios e os relatÃ³rios do validador oficial do HL7.
- `app/`: cÃ³digo do aplicativo, como submÃ³dulo, fixado no commit `a9059f0` analisado no texto.

## Reproduzir

```powershell
git clone --recurse-submodules https://github.com/Atyrson/tcc-bem-te-vi.git
cd tcc-bem-te-vi
python -X utf8 entregas/scripts/conferir_catalogo_cif.py   # planilha x catÃ¡logo
python -X utf8 entregas/scripts/conferir_calculo_cif.py    # nÃºmeros da SeÃ§Ã£o 4.2
python -X utf8 entregas/scripts/conferir_calculo_gas.py    # escore da GAS, tela x servidor
.\entregas\scripts\validar_fhir.ps1                         # validaÃ§Ã£o FHIR (requer Java 11+)
```

Os scripts de conferÃªncia usam Python 3.10+ e as dependÃªncias de `app/Backend` e `app/scripts/cif`.

Todos os exemplos usam dados fictÃ­cios.