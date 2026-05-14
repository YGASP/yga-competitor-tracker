@echo off
echo ============================================
echo   YGA Competitor Tracker - Scheduler Setup
echo ============================================
echo.

set TASK_COLLECT=YGA_Competitor_Tracker
set TASK_HEALTH=YGA_Health_Check
set SCRIPT_DIR=%~dp0
set COLLECT_PY=%SCRIPT_DIR%collect_data.py
set HEALTH_PY=%SCRIPT_DIR%health_check.py
set COLLECT_LOG=%SCRIPT_DIR%collect_log.txt
set HEALTH_LOG=%SCRIPT_DIR%health_check_log.txt
set COLLECT_BAT=%SCRIPT_DIR%run_collect_scheduled.bat
set HEALTH_BAT=%SCRIPT_DIR%run_health_check.bat

REM ── Find Python ──────────────────────────────────────────────────────────────
set PYTHON_PATH=
for /f "tokens=* delims=" %%P in ('where python 2^>nul') do (
    if not defined PYTHON_PATH set "PYTHON_PATH=%%P"
)
if not defined PYTHON_PATH (
    echo [ERROR] Python not found in PATH.
    pause
    exit /b 1
)
echo Found Python: %PYTHON_PATH%
echo.

REM ── Write run_collect_scheduled.bat ──────────────────────────────────────────
(
    echo @echo off
    echo set PYTHONIOENCODING=utf-8
    echo set PYTHONUTF8=1
    echo cd /d "%SCRIPT_DIR%"
    echo "%PYTHON_PATH%" -X utf8 "%COLLECT_PY%" --headless ^>^> "%COLLECT_LOG%" 2^>^&1
) > "%COLLECT_BAT%"
echo Updated: %COLLECT_BAT%

REM ── Write run_health_check.bat ───────────────────────────────────────────────
(
    echo @echo off
    echo set PYTHONIOENCODING=utf-8
    echo set PYTHONUTF8=1
    echo cd /d "%SCRIPT_DIR%"
    echo "%PYTHON_PATH%" -X utf8 "%HEALTH_PY%" ^>^> "%HEALTH_LOG%" 2^>^&1
) > "%HEALTH_BAT%"
echo Updated: %HEALTH_BAT%
echo.

REM ── Remove old tasks ─────────────────────────────────────────────────────────
schtasks /delete /tn "%TASK_COLLECT%" /f > nul 2>&1
schtasks /delete /tn "%TASK_HEALTH%"  /f > nul 2>&1

REM ── Task 1: Data collection at 08:00 (current user, no SYSTEM needed) ────────
schtasks /create ^
  /tn "%TASK_COLLECT%" ^
  /tr "cmd /c \"%COLLECT_BAT%\"" ^
  /sc daily ^
  /st 08:00 ^
  /f

if %ERRORLEVEL%==0 (
    echo [OK] Task '%TASK_COLLECT%' - runs daily at 08:00
) else (
    echo [ERROR] Could not create %TASK_COLLECT%
)

REM ── Task 2: Health check + email at 09:00 ────────────────────────────────────
schtasks /create ^
  /tn "%TASK_HEALTH%" ^
  /tr "cmd /c \"%HEALTH_BAT%\"" ^
  /sc daily ^
  /st 09:00 ^
  /f

if %ERRORLEVEL%==0 (
    echo [OK] Task '%TASK_HEALTH%' - runs daily at 09:00
) else (
    echo [ERROR] Could not create %TASK_HEALTH%
)

echo.
echo ============================================
echo   Done. Both tasks registered.
echo   08:00  Data collection
echo   09:00  Health check + email report
echo ============================================
echo.
pause
