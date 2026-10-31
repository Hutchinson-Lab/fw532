# Run Quarto for this website with the right R and Python.
#
# Usage (from the project folder, in PowerShell):
#   .\tools\quarto.ps1 preview            # live preview in your browser while you edit
#   .\tools\quarto.ps1 render             # rebuild the whole site into _site/
#   .\tools\quarto.ps1 render r/lab03-cart.qmd   # rebuild one page
#
# Why: this computer has several R versions and R 4.0.3 is first on the PATH; the labs need
# R 4.5. The Python notebooks run in the course virtual environment.

$env:QUARTO_R = "C:\Program Files\R\R-4.5.2\bin"
$env:QUARTO_PYTHON = Join-Path $HOME ".venvs\fw532\Scripts\python.exe"

$quarto = (Get-Command quarto -ErrorAction SilentlyContinue).Source
if (-not $quarto) {
  $quarto = Join-Path $env:LOCALAPPDATA "Programs\Positron\resources\app\quarto\bin\quarto.exe"  # bundled with Positron
}
& $quarto @args
