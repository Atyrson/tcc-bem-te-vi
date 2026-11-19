# Compila a monografia (latex\tcc.pdf). Requer MiKTeX ou TeX Live com latexmk.
# Avisos do MiKTeX em stderr nÃ£o sÃ£o erro; sÃ³ o cÃ³digo de saÃ­da indica falha.
Push-Location "$PSScriptRoot\latex"
try { latexmk -pdf -interaction=nonstopmode -halt-on-error tcc.tex; exit $LASTEXITCODE } finally { Pop-Location }