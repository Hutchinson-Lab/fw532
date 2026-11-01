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

# Find Quarto: a standalone install on the PATH first, then the copies bundled with Positron
# (which moves into a "_" subfolder while an update is pending) and RStudio.
$candidates = @(
  (Get-Command quarto -ErrorAction SilentlyContinue).Source,
  (Join-Path $env:LOCALAPPDATA "Programs\Positron\resources\app\quarto\bin\quarto.exe"),
  (Join-Path $env:LOCALAPPDATA "Programs\Positron\_\resources\app\quarto\bin\quarto.exe"),
  "C:\Program Files\RStudio\resources\app\bin\quarto\bin\quarto.exe"
)
$quarto = $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $quarto) {
  Write-Error "Couldn't find Quarto. Install it from https://quarto.org/docs/get-started/ and try again."
  exit 1
}
& $quarto @args
