# Valida as instâncias FHIR de entregas/fhir/ com o validador oficial do HL7.
#
# Uso, na raiz do repositório do TCC (PowerShell, com Java 11 ou superior):
#
#     .\entregas\scripts\validar_fhir.ps1                 # valida entregas/fhir/teste
#     .\entregas\scripts\validar_fhir.ps1 entregas/fhir/cif
#
# Na primeira execução, o script baixa o validador e os pacotes brasileiros para
# ferramentas/ (fora do Git) e os instala no cache de pacotes do validador
# (~/.fhir/packages). A primeira execução pode levar alguns minutos para baixar e
# carregar os pacotes; com os pacotes no cache, leva menos de um minuto.
#
# Contorno documentado (17/11/2026): o BR-Core 1.7.1 declara dependência de
# br.gov.saude.terminologia.fhir#1.2.0, versão que não está publicada (a última
# publicada é a 1.1.0). O script instala a 1.1.0 no cache com o número 1.2.0 para
# que o validador consiga carregar o BR-Core.

param([string]$Pasta = 'entregas/fhir/teste')

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$raiz = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$ferramentas = Join-Path $raiz 'ferramentas'
$cache = Join-Path $env:USERPROFILE '.fhir\packages'
New-Item -ItemType Directory -Force $ferramentas, $cache | Out-Null

$validador = Join-Path $ferramentas 'validator_cli.jar'
if (-not (Test-Path $validador)) {
    Invoke-WebRequest -UseBasicParsing -OutFile $validador `
        -Uri 'https://github.com/hapifhir/org.hl7.fhir.core/releases/latest/download/validator_cli.jar'
}

# Pacotes que não estão no registro público de pacotes FHIR.
$pacotes = @{
    'br.gov.saude.br-core.fhir#1.7.1'      = 'https://hl7.org.br/fhir/core/package.tgz'
    'br.gov.saude.ips.fhir#1.0.0'          = 'https://hl7.org.br/fhir/ips/v1.0.0/package.tgz'
    'br.gov.saude.terminologia.fhir#1.1.0' = 'https://terminologia.saude.gov.br/fhir/package.tgz'
    'br.gov.saude.terminologia.fhir#1.0.0' = 'https://terminologia.saude.gov.br/fhir/v1.0.0/package.tgz'
}
foreach ($id in $pacotes.Keys) {
    $destino = Join-Path $cache $id
    if (Test-Path $destino) { continue }
    $arquivo = Join-Path $ferramentas (($id -replace '[#]', '-') + '.tgz')
    Invoke-WebRequest -UseBasicParsing -Uri $pacotes[$id] -OutFile $arquivo
    $temp = Join-Path $env:TEMP ('pacote-' + [guid]::NewGuid())
    New-Item -ItemType Directory $temp | Out-Null
    tar -xzf $arquivo -C $temp
    $versao = (Get-Content -Raw (Join-Path $temp 'package\package.json') | ConvertFrom-Json).version
    if ($id -notlike "*#$versao") { throw "Versão inesperada em $($pacotes[$id]): $versao (esperada: $id)" }
    New-Item -ItemType Directory $destino | Out-Null
    Move-Item (Join-Path $temp 'package') $destino
}

$apelido = Join-Path $cache 'br.gov.saude.terminologia.fhir#1.2.0'
if (-not (Test-Path $apelido)) {
    Copy-Item -Recurse (Join-Path $cache 'br.gov.saude.terminologia.fhir#1.1.0') $apelido
    $pj = Join-Path $apelido 'package\package.json'
    $texto = [IO.File]::ReadAllText($pj) -replace '"version"\s*:\s*"1\.1\.0"', '"version" : "1.2.0"'
    [IO.File]::WriteAllText($pj, $texto, (New-Object System.Text.UTF8Encoding $false))
}

$alvo = Join-Path $raiz $Pasta
$arquivos = Get-ChildItem $alvo -Filter '*.json' | ForEach-Object { $_.FullName }
& java -jar $validador @arquivos -version 4.0.1 `
    -ig 'br.gov.saude.br-core.fhir#1.7.1' -ig 'hl7.fhir.uv.sdc#4.0.0' -ig $alvo
exit $LASTEXITCODE
