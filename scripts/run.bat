@echo off
REM Proje kok klasorune gec / switch to project root
cd /d "%~dp0.."

REM Python secimi: once 3.13, sonra 3.12, yoksa varsayilan python.
REM Sesli komut (faster-whisper) en yeni Python surumlerinde kurulamayabiliyor.
set "PY=python"
py -3.13 -c "import sys" >nul 2>&1 && set "PY=py -3.13" && goto :have_py
py -3.12 -c "import sys" >nul 2>&1 && set "PY=py -3.12" && goto :have_py
:have_py
echo Kullanilan Python / Python in use: %PY%

REM Kurulu paketler buyuk modelleri yuklemeden kontrol edilir; normal acilista pip calismaz.
REM Istege bagli ses/video paketleri: scripts\run.bat --extras
REM Gereksinimleri yeniden denetle: scripts\run.bat --repair
%PY% scripts\launch.py %*
set "TD2_EXIT=%ERRORLEVEL%"
if not "%TD2_EXIT%"=="0" (
  echo.
  echo [HATA] Uygulama hatayla kapandi. Ayrinti: logs\app.log
  echo [ERROR] The app exited with an error. Details: logs\app.log
  pause
)
exit /b %TD2_EXIT%
