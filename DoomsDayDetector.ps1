$ErrorActionPreference = "Stop"

$Repo = "https://github.com/zFrc/DoomsdayDetector/archive/refs/heads/main.zip"
$TempRoot = Join-Path $env:TEMP "DoomsDayDetector_Run"
$ZipPath = Join-Path $env:TEMP "DoomsDayDetector.zip"
$ExtractRoot = Join-Path $env:TEMP "DoomsdayDetector-main"

Write-Host ""
Write-Host "========================================"
Write-Host "        Doomsday Detector"
Write-Host "========================================"
Write-Host ""

try {
    if (Test-Path $TempRoot) {
        Remove-Item $TempRoot -Recurse -Force
    }

    if (Test-Path $ZipPath) {
        Remove-Item $ZipPath -Force
    }

    if (Test-Path $ExtractRoot) {
        Remove-Item $ExtractRoot -Recurse -Force
    }

    Write-Host "[+] Downloading Doomsday Detector..."

    Invoke-WebRequest `
        -Uri $Repo `
        -OutFile $ZipPath `
        -UseBasicParsing

    Write-Host "[+] Extracting files..."

    Expand-Archive `
        -Path $ZipPath `
        -DestinationPath $env:TEMP `
        -Force

    if (-not (Test-Path $ExtractRoot)) {
        throw "Repository extraction failed."
    }

    Rename-Item `
        -Path $ExtractRoot `
        -NewName "DoomsDayDetector_Run"

    if (-not (Test-Path $TempRoot)) {
        throw "Temporary directory was not created."
    }

    Write-Host "[+] Looking for Python..."

    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue

    if (-not $PythonCommand) {
        $PythonCommand = Get-Command py -ErrorAction SilentlyContinue
    }

    if (-not $PythonCommand) {
        throw "Python was not found. Install Python 3.10 or newer."
    }

    $PythonPath = $PythonCommand.Source
    $MainPath = Join-Path $TempRoot "main.py"

    if (-not (Test-Path $MainPath)) {
        throw "main.py was not found in the downloaded repository."
    }

    Write-Host "[+] Starting scanner..."
    Write-Host ""

    & $PythonPath $MainPath

    $ExitCode = $LASTEXITCODE

    Write-Host ""
    Write-Host "========================================"

    if ($ExitCode -eq 0) {
        Write-Host "Scan finished successfully."
    }
    else {
        Write-Host "Scanner exited with code $ExitCode."
    }

    Write-Host "========================================"
    Write-Host ""

    exit $ExitCode
}
catch {
    Write-Host ""
    Write-Host "[!] Error:"
    Write-Host $_.Exception.Message
    Write-Host ""
    exit 1
}
finally {
    if (Test-Path $ZipPath) {
        Remove-Item $ZipPath -Force -ErrorAction SilentlyContinue
    }

    if (Test-Path $TempRoot) {
        Remove-Item $TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}