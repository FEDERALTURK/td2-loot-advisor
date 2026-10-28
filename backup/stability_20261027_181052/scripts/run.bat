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

REM 1) Temel paketler (zorunlu) / core packages (required)
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo [HATA] Temel paketler kurulamadi. Yukaridaki hatayi oku.
  echo [ERROR] Core packages failed to install. See the error above.
  pause
  exit /b 1
)

REM 2) Ses paketleri (opsiyonel) / voice packages (optional)
REM Kurulamayan paket optional_skip.txt dosyasina yazilir ve bir daha denenmez.
REM Tekrar denemek icin optional_skip.txt dosyasini sil.
call :opt pyttsx3 pyttsx3
call :opt sounddevice sounddevice
call :opt numpy numpy
call :opt faster-whisper faster_whisper
REM Yeni OCR motoru (onerilen; kurulamazsa Tesseract kullanilir) / new OCR engine (recommended; falls back to Tesseract)
call :opt onnxruntime onnxruntime
call :opt rapidocr rapidocr
REM QR kodu (telefon arkadasi, build paylasimi) / QR codes (optional)
call :opt qrcode qrcode
REM Arka plan videosu (istege bagli) / background video (optional)
call :opt av av

REM 3) Uygulamayi ac / start the app
%PY% app.py
if errorlevel 1 (
  echo.
  echo [HATA] Uygulama hatayla kapandi. Ayrinti: logs\app.log
  echo [ERROR] The app exited with an error. Details: logs\app.log
  pause
)
exit /b

:opt
%PY% -c "import %2" >nul 2>&1 && exit /b 0
findstr /x /c:"%1" optional_skip.txt >nul 2>&1 && exit /b 0
echo Opsiyonel paket kuruluyor / installing optional package: %1
%PY% -m pip install %1 >nul 2>&1
if errorlevel 1 (
  echo [UYARI] %1 kurulamadi, ilgili ozellik kapali. / %1 could not be installed, that feature is off.
  echo %1>>optional_skip.txt
)
exit /b 0
