@echo off
REM TD2 Loot Advisor v5 - .exe olusturucu / .exe builder (Windows)
REM NOT: Ses ozellikleri (faster-whisper) .exe'yi cok buyutur (yuzlerce MB).
REM Sorun yasarsan run.bat ile calistirmak en guvenli yoldur.
REM NOTE: the voice features make the .exe very large. If it fails, use run.bat.
REM Proje kok klasorune gec / switch to project root
cd /d "%~dp0.."

REM Python secimi: once 3.13, sonra 3.12, yoksa varsayilan python.
set "PY=python"
py -3.13 -c "import sys" >nul 2>&1 && set "PY=py -3.13" && goto :have_py
py -3.12 -c "import sys" >nul 2>&1 && set "PY=py -3.12" && goto :have_py
:have_py
echo Kullanilan Python / Python in use: %PY%

%PY% -m pip install -r requirements.txt
%PY% -m pip install pyinstaller
REM Ses paketleri opsiyonel; kurulamazsa .exe sessiz surumle derlenir.
REM Voice packages are optional; if they fail, the .exe is built without voice.
%PY% -m pip install -r requirements-voice.txt
REM Yeni OCR motoru (onerilen) / new OCR engine (recommended)
%PY% -m pip install onnxruntime rapidocr qrcode
%PY% -c "import ocr_backend; ocr_backend.Engine('rapidocr').text(__import__('PIL.Image').Image.new('RGB',(64,32)))"

%PY% -m PyInstaller --onefile --noconsole --name TD2LootAdvisor ^
  --add-data "builds.json;." ^
  --add-data "lang;lang" ^
  --add-data "meta;meta" ^
  --hidden-import pyttsx3.drivers --hidden-import pyttsx3.drivers.sapi5 ^
  --hidden-import ocr_backend --hidden-import features --hidden-import stash --hidden-import vendor --hidden-import companion --hidden-import share --hidden-import dropstats --hidden-import fx --hidden-import bgvideo --hidden-import view3d --hidden-import display ^
  --collect-all rapidocr --collect-all onnxruntime --collect-all faster_whisper --collect-all ctranslate2 ^
  app.py

copy /Y builds.json dist\builds.json
if not exist dist\lang mkdir dist\lang
copy /Y lang\*.json dist\lang\
if not exist dist\meta mkdir dist\meta
copy /Y meta\*.json dist\meta\

echo.
echo Bitti / Done: dist\TD2LootAdvisor.exe
echo   dist\builds.json  - ayarlar + build kurallari / settings + build rules
echo   dist\lang\        - dil dosyalari / language files
echo   dist\meta\        - oyun kutuphanesi ve gunluk listeler / game library and feeds
echo Arka plan videolari ilk acilista otomatik uretilir / background videos are generated on first start.
echo Not: RapidOCR pakete dahil; Tesseract yalniz yedek olarak gerekir / RapidOCR is bundled; Tesseract is only a fallback.
pause
