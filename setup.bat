@echo off
setlocal
cd /d "%~dp0"
echo === Setup Autopost Annafi ATK ===
set "PY="
py -3 -c "import sys; assert sys.version_info >= (3,10)" >nul 2>nul && set "PY=py -3"
if not defined PY python -c "import sys; assert sys.version_info >= (3,10)" >nul 2>nul && set "PY=python"
if not defined PY (
  echo Python 3.10+ belum terpasang.
  echo Install dari https://www.python.org/downloads/ ^(centang "Add python.exe to PATH"^), lalu jalankan setup.bat lagi.
  pause & exit /b 1
)
if not exist .venv %PY% -m venv .venv
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt || (echo Gagal install paket & pause & exit /b 1)
".venv\Scripts\python.exe" -m playwright install chromium || (echo Gagal install Chromium & pause & exit /b 1)
if not exist .env copy .env.example .env >nul
schtasks /Create /F /SC MINUTE /MO 15 /TN "Annafi Autopost" /TR "wscript.exe \"%~dp0jalan.vbs\""
echo.
echo Selesai! Sistem akan jalan otomatis tiap 15 menit selama laptop menyala.
echo Langkah berikutnya: isi file .env lalu double-click jalan.bat untuk tes (lihat log.txt).
pause
