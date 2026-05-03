@echo off
cd /d "C:\Users\yoavl\.claude\projects\amazon-competitor-tracker"
echo ============================================
echo   YGA Tracker — Public Dashboard
echo ============================================
echo.

REM ── Start Streamlit in a separate minimized window ───────────────────────────
echo [1/2] Starting Streamlit (minimized)...
start "YGA Streamlit" /min streamlit run dashboard.py ^
    --server.port 8501 ^
    --server.headless true ^
    --server.address 127.0.0.1

REM ── Give Streamlit a few seconds to initialize ───────────────────────────────
timeout /t 5 /nobreak > nul

REM ── Start Cloudflare Tunnel — public URL will appear in this window ──────────
echo [2/2] Starting Cloudflare Tunnel...
echo.
echo ┌─────────────────────────────────────────────────────────┐
echo │  Look for a line that says:                             │
echo │  https://xxxx-xxxx-xxxx.trycloudflare.com               │
echo │  That is your public URL — open it on any device.       │
echo │                                                         │
echo │  Press Ctrl+C to shut everything down.                  │
echo └─────────────────────────────────────────────────────────┘
echo.
cloudflared tunnel --url http://localhost:8501
