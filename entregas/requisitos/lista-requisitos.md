# Lista de requisitos para o Apêndice A (rascunho para conferência)

Montada e aprovada em 21/11/2026. A versão completa, com justificativa e critério de aceitação, está em `latex/editaveis/apendices.tex` (Apêndice A), que passa a ser a referência. Esta lista fica como registro das decisões.

- Prioridade pelo critério da Seção 3.5 (redação de 21/11/2026): **alta** para requisito exigido por norma, já implementado no módulo CIF ou que corrige um problema de dados da 4.1 ou uma divergência de cálculo da 4.3; **média** para requisito sem o qual o acompanhamento entre avaliações não funciona ou perde confiabilidade (histórico, estado, versão do formulário, comparação, regras de cálculo e de registro dos valores comparados e representação no padrão de interoperabilidade adotado); **baixa** para requisito que amplia o uso dos dados além do acompanhamento, como a exportação para pesquisa.
- Situação: **implementado**, **proposto** ou **depende da equipe**.
- "Seis formulários" são ASIA, GAS, MEEM, eletrodiagnóstico, densitometria e anamnese.

## Já implementados no módulo CIF (21, Tabela A.1)

RF01–RF07, RN01–RN11 e RNF01–RNF03, sem mudança de texto. Todos com prioridade alta e situação implementado. Fonte: código no commit `a9059f0`; RN02 também cita a planilha da equipe, e RN07 e RN08, a auditoria (`regras-e-auditoria.md`). Critério de aceitação: o teste do app que cobre cada um, a conferir.

## Novos (46)

### 1. Identificação do paciente e do avaliador

| ID | Requisito | Fonte | Prior. | Situação |
|---|---|---|---|---|
| RF08 | Vincular a avaliação dos seis formulários ao identificador do paciente selecionado, como a CIF já faz | PD1 | Alta | Proposto |
| RN12 | A API não cria cadastro de paciente a partir de uma avaliação; avaliação de paciente inexistente é rejeitada | PD1, PD4 | Alta | Proposto |
| RN13 | O CPF é único entre os pacientes | 4.1.1 (`schema.sql`, l. 7); Just *et al.* (2016) | Alta | Proposto |
| RF09 | Registrar em toda avaliação o profissional que a aplicou, a partir do usuário autenticado, com nome completo e número no CREFITO | COFFITO 414/2012, art. 2º, par. único; PD3; lacuna da 4.2; 4.1.1 | Alta | Proposto |
| RF10 | A anamnese usa os dados de identificação do cadastro do paciente, sem repetir nome, celular, e-mail e data de nascimento | 4.1.1 (`schema.sql`, l. 111–114) | Alta | Proposto |

### 2. Registro e estados da avaliação

| ID | Requisito | Fonte | Prior. | Situação |
|---|---|---|---|---|
| RF11 | Gravar os comentários da ASIA | PD2 | Alta | Proposto |
| RN14 | Todo campo exibido no formulário é gravado, ou sai da tela | PD2 | Alta | Proposto |
| RF12 | O profissional informa a data do exame da densitometria, separada da data de registro | PD4 | Alta | Proposto |
| RN15 | Nenhum valor fictício substitui um dado ausente (como "Paciente Teste" ou "Dr. Examinador"); o envio sem paciente ou sem avaliador é rejeitado | PD3, PD4 | Alta | Proposto |
| RF13 | Toda avaliação dos seis formulários guarda a data de aplicação e a data de registro | 4.1.1 (tabelas sem data de registro) | Alta | Proposto |
| RN16 | Valor ausente é gravado como ausente, e não como texto no lugar do valor (caso do "N/A" no índice de acomodação) | 4.1.1 (`eletroFormProvider.dart`, l. 29 e 38; `schema.sql`, l. 138–139) | Alta | Proposto |
| RF14 | Salvar a avaliação dos seis formulários como rascunho e concluí-la depois (extensão de RF02 e RF04) | RF02, RF04; 4.1.1 (tabelas sem estado) | Média | Proposto |
| RN17 | Avaliação concluída dos seis formulários não pode ser editada (extensão de RN10) | RN10; Cysneiros (2002, p. 353) | Média | Proposto |
| RNF04 | Cada avaliação guarda a versão do formulário com que foi aplicada (extensão de RNF01) | RNF01; 4.1.1 (tabelas sem versão) | Média | Proposto |

### 3. Regras de cálculo

| ID | Requisito | Fonte | Prior. | Situação |
|---|---|---|---|---|
| RN18 | Escore T da GAS pela Equação 2.1 com ρ = 0,3 | DC1; Kiresuk e Sherman (1968, p. 449); Turner-Stokes (2009, p. 364) | Alta | Proposto |
| RN19 | A GAS não troca por zero os valores ponderados negativos | PD5 | Alta | Proposto |
| RN20 | Peso da meta da GAS = importância × dificuldade | Turner-Stokes (2009, p. 365); 4.3.2 (conforme) | Média | Implementado |
| RN21 | Total do MEEM = soma dos pontos dos itens, até 30 | Folstein *et al.* (1975, p. 190); 4.3.2 (conforme) | Média | Implementado |
| RN22 | Valor de referência do MEEM para 5 a 8 anos de estudo é 26,5 | DC2; Brucki *et al.* (2003, p. 777) | Alta | Proposto |
| RN23 | Referência por escolaridade adotada no MEEM e rótulo exibido ("mediana" ou "mínima esperada") | 4.3.2; Brucki *et al.* (2003, p. 780) | Média | Depende da equipe |
| RN24 | Níveis sensitivo, motor e neurológico da ASIA conforme o ISNCSCI | Rupp *et al.* (2021, p. 15–22); 4.3.2 (conforme) | Média | Implementado |
| RN25 | Grau AIS pela árvore de decisão do ISNCSCI | DC3; Rupp *et al.* (2021, p. 18 e 22) | Alta | Proposto |
| RN26 | ZPP conforme o ISNCSCI, com NA quando há a função sacral correspondente | DC4; Rupp *et al.* (2021, p. 18–19) | Alta | Proposto |
| RN27 | NT em S4-5 leva a ND, sem erro, e a avaliação é gravada | DC5; Rupp *et al.* (2021, p. 3 e 19) | Alta | Proposto |
| RN28 | IMC = massa / altura², com a unidade da altura explícita na tela, sem a conversão implícita | 4.3.2 (`dex.dart`, l. 233) | Média | Proposto |
| RN29 | Fórmula, arredondamento e fonte do índice de acomodação | 4.3.2; lacuna F3 | Média | Depende da equipe |
| RNF05 | Os valores calculados dos seis formulários são obtidos no servidor e gravados com a avaliação, e a tela exibe o valor devolvido (extensão de RNF02) | RNF02; PD5; 4.3.1 (totais da ASIA e pontuação do MEEM não gravados); 4.1.2 (IMC e índice só na tela) | Alta | Proposto |
| RNF06 | As respostas item a item são gravadas junto com o escore, para permitir o recálculo | Parasuraman *et al.* (2000, p. 292); 4.3.2 | Média | Implementado em parte (CIF, MEEM, GAS, ASIA) |
| RNF07 | Todo cálculo tem teste automatizado com os casos do critério de aceitação | 4.1.2 (nenhum teste fora da CIF); Wiegers e Beatty (2013, p. 348) | Média | Proposto |

### 4. Histórico e comparação

| ID | Requisito | Fonte | Prior. | Situação |
|---|---|---|---|---|
| RF15 | Listar as avaliações do paciente em cada um dos seis formulários, em ordem de data (extensão de RF06) | RF06; 4.1.1 (sem rotas de consulta); 4.3.1 | Média | Proposto |
| RF16 | Consultar uma avaliação registrada, com as respostas originais (extensão de RF05) | RF05; 4.1.1 | Média | Proposto |
| RF17 | Comparar duas avaliações concluídas do mesmo instrumento, com a diferença de cada escore (extensão de RF07) | RF07; 4.3.1 | Média | Proposto |
| RN30 | Só se comparam avaliações concluídas do mesmo paciente e da mesma versão do formulário (extensão de RN11) | RN11 | Média | Proposto |
| RN31 | A comparação mostra a diferença sem rótulo de melhora ou piora; a interpretação fica com o profissional | Seção 2.5 (Parasuraman *et al.*, 2000; Onnasch *et al.*, 2014); Jaeschke *et al.* (1989, p. 408); Ahuja *et al.* (2017, p. 9) | Média | Proposto |
| RN32 | Sequência das avaliações e marco dos três meses (avaliação inicial ou início do treino) | 4.6 (`regras-e-auditoria.md`, l. 256–270) | Média | Depende da equipe |
| RN33 | Qualificadores 8 e 9 e itens "não especificados" na CIF | 4.6; 2.2 (WHO, 2013, p. 26–27) | Média | Depende da equipe |
| RN34 | Facilitadores com sinal próprio nos fatores ambientais da CIF | 4.6 | Baixa | Depende da equipe |

### 5. Interoperabilidade

| ID | Requisito | Fonte | Prior. | Situação |
|---|---|---|---|---|
| RNF08 | Exportar as avaliações como recursos HL7 FHIR R4, nos perfis do BR-Core quando existirem | Portaria 1.434/2020; BR-Core 1.7.1 | Média | Proposto |
| RNF09 | Todo paciente tem CPF ou CNS | BR-Core (`br-core-pat-2`) | Alta | Proposto |

### 6. Privacidade, segurança e auditoria

| ID | Requisito | Fonte | Prior. | Situação |
|---|---|---|---|---|
| RNF10 | Só usuário autenticado acessa as rotas da API | LGPD, art. 46 | Alta | Proposto |
| RNF11 | Cada perfil de usuário tem permissões definidas, e a API as aplica | LGPD, art. 46; Cysneiros (2002, p. 353) | Alta | Proposto (permissões dependem da equipe) |
| RNF12 | Senhas guardadas com função de hash | LGPD, art. 46 | Alta | Proposto |
| RNF13 | Registrar quem criou, consultou ou alterou cada avaliação, e quando | LGPD, art. 37; Cysneiros (2002, p. 353) | Alta | Proposto |
| RNF14 | Os dados trafegam criptografados entre o aplicativo e a API | LGPD, art. 46 | Alta | Proposto |

### 7. Dados para o módulo de IA

| ID | Requisito | Fonte | Prior. | Situação |
|---|---|---|---|---|
| RNF15 | Consultar as avaliações do paciente em ordem de data, com o código e a versão de cada instrumento | Ochoa Diaz (2026) | Baixa | Proposto |
| RNF16 | Exportar os dados sem identificação direta do paciente, para pesquisa | LGPD, art. 11, II, c, e art. 13; Ochoa Diaz (2026) | Baixa | Proposto |

A guarda das respostas item a item, terceiro requisito da decisão 5, já é o RNF06.

## Decisões do autor (21/11/2026)

1. **Tamanho:** mantidos os 67 requisitos, sem fusões.
2. **Prioridade:** a 3.5 ganhou definição explícita de média e baixa (acima). RN20, RN21 e RN24 continuam média, pela regra de cálculo dos valores comparados. RNF15 e RNF16 passaram para baixa. RN34 continua baixa, por tratar da representação de um dado e não do acompanhamento.
3. **RNF08:** média, pela representação no padrão de interoperabilidade adotado.
4. **RNF12:** mantido, com a LGPD como fonte e sem citar o achado do código.
5. **Ochoa Diaz (2026):** RNF15 e RNF16 seguem como detalhamento do autor sobre o que o plano prevê; conferir o trecho se o plano for obtido.
6. **LGPD:** arts. 11, 13, 37 e 46 conferidos no site do Planalto em 21/11/2026.

Feito em 21/11/2026: justificativa e critério no Apêndice A; testes do app conferidos para os 21 da CIF (RN09 sem teste próprio para a ausência do resultado geral).
