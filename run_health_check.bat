@echo off
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "C:\Users\yoavl\.claude\projects\amazon-competitor-tracker\"
"C:\Users\yoavl\AppData\Local\Programs\Python\Python313\python.exe" -X utf8 "C:\Users\yoavl\.claude\projects\amazon-competitor-tracker\health_check.py" >> "C:\Users\yoavl\.claude\projects\amazon-competitor-tracker\health_check_log.txt" 2>&1
