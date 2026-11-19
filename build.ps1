# Compila a monografia (latex\tcc.pdf). Requer MiKTeX ou TeX Live com latexmk.
# Avisos do MiKTeX em stderr não são erro; só o código de saída indica falha.
Push-Location "$PSScriptRoot\latex"
try { latexmk -pdf -interaction=nonstopmode -halt-on-error tcc.tex; exit $LASTEXITCODE } finally { Pop-Location }