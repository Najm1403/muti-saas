param(
    [string]$TailwindExecutable = 'tailwindcss'
)

$ErrorActionPreference = 'Stop'
$webRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$inputFile = Join-Path $webRoot 'shared\tailwind.input.css'
$outputFile = Join-Path $webRoot 'shared\tailwind.css'

Push-Location $webRoot
try {
    & $TailwindExecutable `
        --config (Join-Path $webRoot 'tailwind.config.js') `
        --input $inputFile `
        --output $outputFile `
        --minify

    if ($LASTEXITCODE -ne 0) {
        throw "Tailwind CSS compilation failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

Write-Host "Built $outputFile"
