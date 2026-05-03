@echo off
cd /d "%~dp0"
echo =======================================
echo  YGA Competitor Tracker — Data Collect
echo =======================================
python collect_data.py
echo.
echo Press any key to close...
pause > nul
