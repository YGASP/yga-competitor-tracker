@echo off
echo ============================================
echo   YGA Competitor Tracker — Scheduler Setup
echo ============================================
echo.

set TASK_NAME=YGA_Competitor_Tracker
set SCRIPT_DIR=%~dp0
set SCRIPT_PATH=%SCRIPT_DIR%collect_data.py
set LOG_PATH=%SCRIPT_DIR%collect_log.txt
set BAT_PATH=%SCRIPT_DIR%run_collect_scheduled.bat

REM ── Find the full path to python.exe ─────────────────────────────────────────
set PYTHON_PATH=
for /f "tokens=* delims=" %%P in ('where python 2^>nul') do (
    if not defined PYTHON_PATH set "PYTHON_PATH=%%P"
)
if not defined PYTHON_PATH (
    for /f "tokens=* delims=" %%P in ('where py 2^>nul') do (
        if not defined PYTHON_PATH set "PYTHON_PATH=%%P"
    )
)
if not defined PYTHON_PATH (
    echo [ERROR] Python not found in PATH.
    echo Please install Python and add it to PATH, then re-run this script.
    pause
    exit /b 1
)
echo Found Python: %PYTHON_PATH%
echo Script:       %SCRIPT_PATH%
echo Log:          %LOG_PATH%
echo.

REM ── Write full Python path into run_collect_scheduled.bat ─────────────────────
REM    Task Scheduler does NOT inherit user PATH, so we bake in the absolute path.
(
    echo @echo off
    echo cd /d "%SCRIPT_DIR%"
    echo "%PYTHON_PATH%" "%SCRIPT_PATH%" --headless ^>^> "%LOG_PATH%" 2^>^&1
) > "%BAT_PATH%"
echo Updated: %BAT_PATH%
echo.

REM ── Remove old task if it exists, then create fresh ──────────────────────────
schtasks /delete /tn "%TASK_NAME%" /f > nul 2>&1

schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "cmd /c \"%BAT_PATH%\"" ^
  /sc daily ^
  /st 08:00 ^
  /ru "%USERNAME%" ^
  /rl HIGHEST ^
  /f

echo.
if %ERRORLEVEL%==0 (
    echo [SUCCESS] Task '%TASK_NAME%' will run every day at 08:00.
    echo.
    echo To test immediately:  schtasks /run /tn "%TASK_NAME%"
    echo To check the log:     type "%LOG_PATH%"
    echo To verify the task:   schtasks /query /tn "%TASK_NAME%" /fo LIST
) else (
    echo [ERROR] Could not create scheduled task.
    echo Right-click this file and choose "Run as administrator".
)
echo.
pause
