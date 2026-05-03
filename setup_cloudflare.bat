@echo off
echo ============================================
echo   YGA Tracker — Cloudflare Tunnel Setup
echo ============================================
echo.

REM ── Try winget first (built into Windows 10/11) ──────────────────────────────
where winget >nul 2>&1
if %ERRORLEVEL%==0 (
    echo Installing cloudflared via winget...
    winget install Cloudflare.cloudflared --accept-source-agreements --accept-package-agreements
    goto :check
)

REM ── Fallback: download the exe directly ──────────────────────────────────────
echo winget not found. Downloading cloudflared.exe directly...
set OUT=%~dp0cloudflared.exe
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile '%OUT%'"
if exist "%OUT%" (
    echo Downloaded to: %OUT%
) else (
    echo [ERROR] Download failed. Download manually from:
    echo https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
    echo and place cloudflared.exe in this folder.
)
goto :check

:check
echo.
cloudflared --version >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [SUCCESS] cloudflared is ready.
    cloudflared --version
) else (
    echo [ERROR] cloudflared not found. Restart your terminal and try again.
)
echo.
pause
