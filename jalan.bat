@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
echo ===== %date% %time% =====>> log.txt
".venv\Scripts\python.exe" src\main.py jalan >> log.txt 2>&1
