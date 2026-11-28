@echo off
setlocal

REM Proje kok klasorune gec / switch to project root
cd /d "%~dp0.."
set "TD2_ROOT=%CD%"

REM Once projenin OCR ortamini kullan. Bu ortam RapidOCR, DirectML ve Tesseract
REM ile birlikte test edilmistir; sistem Python'una karismamasi icin onceliklidir.
set "TD2_PYTHON=%TD2_ROOT%\.venv-ocr\Scripts\python.exe"
if exist "%TD2_PYTHON%" goto :have_python

REM Sanal ortam yoksa desteklenen Python surumlerini yenisinden eskisine dene.
REM launch.py ile ayni surum araligi kullanilir: 3.15, 3.14, 3.13, 3.12.
set "TD2_PYTHON="
for %%V in (3.15 3.14 3.13 3.12) do (
  if not defined TD2_PYTHON (
    py -%%V -c "import sys" >nul 2>&1
    if not errorlevel 1 set "TD2_PYTHON=py -%%V"
  )
)
if not defined TD2_PYTHON set "TD2_PYTHON=python"

:have_python
echo Kullanilan Python / Python in use: %TD2_PYTHON%
echo Proje / Project root: %TD2_ROOT%

REM Kurulu paketler buyuk modelleri yuklemeden kontrol edilir; normal acilista pip calismaz.
REM Istege bagli ses/video paketleri: scripts\run.bat --extras
REM Gereksinimleri yeniden denetle: scripts\run.bat --repair
REM --check / --repair / --extras tanilama komutlari konsol ciktisini korur.
REM Normal GUI baslatmasinda pythonw kullanilir; CMD penceresi TD2'nin uzerinde
REM kalip ekran goruntusune karismasin. launch.py ve app.log hata kanitini korur.
if /I "%~1"=="--check" goto :console_launch
if /I "%~1"=="--repair" goto :console_launch
if /I "%~1"=="--extras" goto :console_launch

set "TD2_GUI_PYTHON=%TD2_PYTHON%"
if exist "%TD2_ROOT%\.venv-ocr\Scripts\pythonw.exe" set "TD2_GUI_PYTHON=%TD2_ROOT%\.venv-ocr\Scripts\pythonw.exe"
if exist "%TD2_GUI_PYTHON%" (
  start "" /b "%TD2_GUI_PYTHON%" "%TD2_ROOT%\scripts\launch.py" %*
) else (
  start "" /b %TD2_GUI_PYTHON% "%TD2_ROOT%\scripts\launch.py" %*
)
set "TD2_EXIT=0"
goto :done

:console_launch
%TD2_PYTHON% "%TD2_ROOT%\scripts\launch.py" %*
set "TD2_EXIT=%ERRORLEVEL%"
if not "%TD2_EXIT%"=="0" (
  echo.
  echo [HATA] Uygulama hatayla kapandi. Ayrinti: logs\app.log
  echo [ERROR] The app exited with an error. Details: logs\app.log
  pause
)

:done
endlocal & exit /b %TD2_EXIT%
