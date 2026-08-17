@echo off
setlocal

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Expression (Invoke-RestMethod 'https://raw.githubusercontent.com/zFrc/DoomsdayDetector/main/DoomsDayDetector.ps1')"

if errorlevel 1 (
    echo.
    echo [!] Doomsday Detector exited with an error.
    pause
    exit /b 1
)

endlocal